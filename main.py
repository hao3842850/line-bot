from fastapi import FastAPI, Request, Header, HTTPException
from fastapi.responses import PlainTextResponse
import uvicorn
import json
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
import os
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import TextSendMessage, MessageEvent, TextMessage

# Load env (production should set env vars instead of .env)
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET", "")
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN", "")

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN) if LINE_CHANNEL_ACCESS_TOKEN else None
handler = WebhookHandler(LINE_CHANNEL_SECRET) if LINE_CHANNEL_SECRET else None

app = FastAPI()

DATA_FILE = "database.json"
BOSSES_FILE = "bosses.json"

# Load boss CD config
with open(BOSSES_FILE, "r", encoding="utf-8") as f:
    boss_cd = json.load(f)

# Load database (records + subscribers)
if os.path.exists(DATA_FILE):
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        db = json.load(f)
else:
    db = {"records": {}, "subscribers": []}

def save_db():
    with open(DATA_FILE, "w", encoding='utf-8') as f:
        json.dump(db, f, ensure_ascii=False, indent=2)

# Scheduler to send reminders at respawn time
scheduler = BackgroundScheduler()
scheduler.start()

def schedule_respawn_notification(boss_name, respawn_dt, target):
    job_id = f"{boss_name}_{int(respawn_dt.timestamp())}_{target}"
    # remove job if exists
    try:
        scheduler.remove_job(job_id)
    except Exception:
        pass

    def job_func():
        try:
            text = f"提醒：{boss_name} 已重生！時間：{respawn_dt.strftime('%Y-%m-%d %H:%M')}"
            if line_bot_api:
                line_bot_api.push_message(target, TextSendMessage(text=text))
        except Exception as e:
            print("Push failed:", e)

    scheduler.add_job(job_func, 'date', run_date=respawn_dt, id=job_id)
    print(f"Scheduled job {job_id} for {respawn_dt} to {target}")

# Reschedule existing records on startup (best-effort)
def reschedule_all():
    for name, rec in db.get("records", {}).items():
        try:
            respawn = datetime.strptime(rec["respawn"], "%Y-%m-%d %H:%M")
            target = rec.get("target")
            if respawn > datetime.now() and target:
                schedule_respawn_notification(name, respawn, target)
        except Exception:
            continue

reschedule_all()

@app.post("/callback", response_class=PlainTextResponse)
async def callback(request: Request, x_line_signature: str = Header(None)):
    body = await request.body()
    signature = x_line_signature

    if not handler:
        # Incomplete configuration
        return PlainTextResponse("Missing LINE keys", status_code=500)

    try:
        handler.handle(body.decode('utf-8'), signature)
    except InvalidSignatureError:
        raise HTTPException(status_code=400, detail="Invalid signature")

    return "OK"

# Handler for messages
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    text = event.message.text.strip()
    source = event.source
    # determine reply/push target (group > room > user)
    target = None
    try:
        if hasattr(source, "group_id") and source.group_id:
            target = source.group_id
        elif hasattr(source, "room_id") and source.room_id:
            target = source.room_id
        else:
            target = source.user_id
    except Exception:
        target = None

    # Commands:
    if text == "王表":
        lines = [f"{name}：{cd}小時" for name, cd in boss_cd.items()]
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text="王表：\n" + "\n".join(lines)))
        return

    if text.startswith("查"):
        name = text.replace("查", "", 1).strip()
        rec = db.get("records", {}).get(name)
        if rec:
            respawn = rec.get("respawn")
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f"{name} 預計重生：{respawn}"))
        else:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f"{name} 尚未記錄死亡時間"))
        return

    if text == "綁定":
        if target and target not in db["subscribers"]:
            db["subscribers"].append(target)
            save_db()
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text="已綁定此聊天室為提醒目標"))
        return

    if text == "解除綁定":
        if target and target in db["subscribers"]:
            db["subscribers"].remove(target)
            save_db()
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text="已解除綁定"))
        return

    # Try to find boss name in message and extract time
    for name in boss_cd.keys():
        if name in text:
            time_str = extract_time(text)
            if not time_str:
                death_dt = datetime.now()
            else:
                hh, mm = map(int, time_str.split(":"))
                now = datetime.now()
                death_dt = now.replace(hour=hh, minute=mm, second=0, microsecond=0)
                if death_dt > now + timedelta(minutes=1):
                    death_dt = death_dt - timedelta(days=1)

            cd_hours = boss_cd.get(name)
            respawn_dt = death_dt + timedelta(hours=cd_hours)
            respawn_str = respawn_dt.strftime("%Y-%m-%d %H:%M")
            notify_target = db["subscribers"][0] if db["subscribers"] else (target or "")
            db["records"][name] = {"death": death_dt.strftime("%Y-%m-%d %H:%M"),
                                    "respawn": respawn_str,
                                    "target": notify_target}
            save_db()
            try:
                if respawn_dt > datetime.now() and notify_target:
                    schedule_respawn_notification(name, respawn_dt, notify_target)
            except Exception as e:
                print("Schedule error:", e)

            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f"{name} 下一次重生：{respawn_str}"))
            return

    help_text = ("指令說明：\n"
                 "1) 記錄：王名 時間 (例如：巨蟻女王 13:20)，時間可省略(則視為現在)\n"
                 "2) 查 王名 (例如：查 巨蟻女王)\n"
                 "3) 王表 -> 顯示所有王和 CD\n"
                 "4) 綁定 -> 將本聊天室綁定為提醒目標\n"
                 "5) 解除綁定")
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=help_text))

def extract_time(text):
    import re
    m = re.search(r"(?:\b|^)(\d{1,2}:\d{2})(?:\b|$)", text)
    return m.group(1) if m else None

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
