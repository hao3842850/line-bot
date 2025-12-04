\
    # Boss helper final main.py
    # FastAPI + LINE Bot webhook implementation with CD-boss + fixed-boss logic
    from fastapi import FastAPI, Request, Header, HTTPException
    from fastapi.responses import PlainTextResponse
    import os, json, re, math
    from datetime import datetime, timedelta

    from linebot import LineBotApi, WebhookHandler
    from linebot.exceptions import InvalidSignatureError
    from linebot.models import TextSendMessage, MessageEvent, TextMessage

    # --- Configuration (set these in environment variables on your host) ---
    LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET", "")
    LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN", "")

    # Line SDK init (will raise if tokens missing when used)
    line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN) if LINE_CHANNEL_ACCESS_TOKEN else None
    handler = WebhookHandler(LINE_CHANNEL_SECRET) if LINE_CHANNEL_SECRET else None

    app = FastAPI()

    DATA_FILE = "database.json"

    # --- Alias map (user-provided list) ---
    alias_map = {
        "76":"四色","四色":"四色","4":"四色","4色":"四色","四":"四色",
        "55":"小紅","小紅":"小紅","紅":"小紅","r":"小紅","R":"小紅",
        "54":"小綠","小綠":"小綠","綠":"小綠","g":"小綠","G":"小綠",
        "29":"守護螞蟻","螞蟻":"守護螞蟻","守護螞蟻":"守護螞蟻",
        "6":"巨大蜈蚣","蜈蚣":"巨大蜈蚣","巨大蜈蚣":"巨大蜈蚣","海4":"巨大蜈蚣","海蟲":"巨大蜈蚣","姐夫":"巨大蜈蚣",
        "861":"左飛龍","86左飛龍":"左飛龍","左":"左飛龍","86下":"左飛龍","86左":"左飛龍","下":"左飛龍",
        "862":"右飛龍","86右":"右飛龍","86右飛龍":"右飛龍","右":"右飛龍","86上":"右飛龍","上":"右飛龍",
        "451":"伊弗利特","伊弗利特":"伊弗利特","伊弗":"伊弗利特","ef":"伊弗利特","EF":"伊弗利特","伊佛":"伊弗利特","衣服":"伊弗利特",
        "69":"大腳瑪幽","大腳":"大腳瑪幽","大腳瑪幽":"大腳瑪幽","腳":"大腳瑪幽",
        "82":"巨大飛龍","巨大飛龍":"巨大飛龍","gf":"巨大飛龍","GF":"巨大飛龍","巨飛":"巨大飛龍","巨龍":"巨大飛龍",
        "83":"中飛龍","中":"中飛龍","中央":"中飛龍","中央龍":"中飛龍","中龍":"中飛龍","83飛龍":"中飛龍","83龍":"中飛龍",
        "85":"東飛龍","東":"東飛龍","東邊":"東飛龍","東邊龍":"東飛龍","東龍":"東飛龍","85飛龍":"東飛龍","85龍":"東飛龍",
        "863":"大黑長者","大黑長者":"大黑長者","大黑":"大黑長者","黑":"大黑長者","黑老":"大黑長者",
        "22":"力卡溫","力卡溫":"力卡溫","狼":"力卡溫","狼人":"力卡溫","狼王":"力卡溫",
        "25":"卡司特","卡司特":"卡司特","卡王":"卡司特","卡":"卡司特",
        "51":"巨大鱷魚","鱷魚":"巨大鱷魚","巨大鱷魚":"巨大鱷魚","巨鱷":"巨大鱷魚",
        "32":"強盜頭目","強盜":"強盜頭目","強盜頭目":"強盜頭目",
        "23":"樹精","24":"樹精","57":"樹精","樹精":"樹精","樹":"樹精",
        "39":"蜘蛛","蜘蛛":"蜘蛛","d":"蜘蛛","D":"蜘蛛","喇牙":"蜘蛛",
        "68":"變形怪首領","變形怪":"變形怪首領","變形怪首領":"變形怪首領","變怪":"變形怪首領",
        "78":"古代巨人","古代巨人":"古代巨人","古巨":"古代巨人","巨人":"古代巨人",
        "惡魔監視者":"惡魔監視者","監視者":"惡魔監視者","象七":"惡魔監視者","監視":"惡魔監視者","象7":"惡魔監視者","7":"惡魔監視者","惡監":"惡魔監視者","藍":"惡魔監視者","藍惡魔":"惡魔監視者",
        "452":"不死鳥","不死鳥":"不死鳥","鳥":"不死鳥","鳥鳥":"不死鳥",
        "05":"死亡騎士","死亡騎士":"死亡騎士","死騎":"死亡騎士","亡":"死亡騎士","死":"死亡騎士",
        "12":"克特","克特":"克特","克":"克特",
        "曼波王":"曼波王","兔子":"曼波王","兔":"曼波王","兔王":"曼波王","曼波兔王":"曼波王",
        "81":"賽尼斯的分身","賽尼斯的分身":"賽尼斯的分身","賽尼斯":"賽尼斯的分身","304":"賽尼斯的分身","塞":"賽尼斯的分身","瘋婆":"賽尼斯的分身","瘋婆子":"賽尼斯的分身","肖婆":"賽尼斯的分身","肖查某":"賽尼斯的分身","賽":"賽尼斯的分身",
        "821":"貝里斯","貝里斯":"貝里斯","大克特":"貝里斯","大將軍":"貝里斯","將軍":"貝里斯","貝":"貝里斯","黑騎將軍":"貝里斯","黑騎隊長":"貝里斯","暗黑將軍":"貝里斯","海邊":"貝里斯","海邊王":"貝里斯",
        "231":"烏勒庫斯","烏勒庫斯":"烏勒庫斯","烏":"烏勒庫斯",
        "571":"奈克偌斯","奈克偌斯":"奈克偌斯","奈":"奈克偌斯","571":"奈克偌斯"
    }

    # --- CD hours mapping ---
    cd_map = {
        "四色": 2.0, "小紅":2.0, "小綠":2.0, "守護螞蟻":3.5, "巨大蜈蚣":2.0,
        "左飛龍":2.0, "右飛龍":2.0, "伊弗利特":2.0, "大腳瑪幽":3.0, "巨大飛龍":6.0,
        "中飛龍":3.0, "東飛龍":3.0, "大黑長者":3.0, "力卡溫":8.0, "卡司特":7.5,
        "巨大鱷魚":3.0, "強盜頭目":3.0, "樹精":6.0, "蜘蛛":4.0, "變形怪首領":3.5,
        "古代巨人":8.5, "惡魔監視者":6.0, "不死鳥":8.0, "死亡騎士":4.0, "克特":10.0,
        "曼波王":3.0, "賽尼斯的分身":3.0, "貝里斯":6.0, "烏勒庫斯":6.0, "奈克偌斯":4.0
    }

    # --- Fixed bosses schedule (times are strings "HH:MM" or "HH:MM:SS") ---
    fixed_bosses = {
        "奇岩一樓王": ["00:00","06:00","12:00","18:00"],
        "奇岩二樓王": ["07:00","14:00","21:00"],
        "奇岩三樓王": ["20:15"],
        "奇岩四樓王": ["21:15"],
        "黑暗四樓王": ["00:00","18:00"],
        "三王": ["19:15"],
        "惡魔": ["22:00"],
        "巴風特": ["14:00","20:00"],
        "異界炎魔": ["23:00"],
        "魔法師": [f"{h:02d}:00" for h in range(1,24,2)]  # odd hours 01:00,03:00,...23:00
    }

    # --- Helper / DB load & save ---
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            db = json.load(f)
    else:
        # db structure
        db = {
            "records": {},    # boss -> [ {death, respawn, note, user} ... ]
            "miss_count": {}, # boss -> int
            "pending_clear": False, # waiting for confirmation '是'
            "last_clear_request_by": None
        }

    def save_db():
        with open(DATA_FILE, "w", encoding='utf-8') as f:
            json.dump(db, f, ensure_ascii=False, indent=2)

    # --- Utility functions ---
    def canonicalize(name):
        if not name: return None
        key = name.strip()
        if key in alias_map: return alias_map[key]
        low = key.lower()
        if low in alias_map: return alias_map[low]
        simple = re.sub(r'[^0-9A-Za-z\u4e00-\u9fff]+', '', key)
        if simple in alias_map: return alias_map[simple]
        if simple.lower() in alias_map: return alias_map[simple.lower()]
        return None

    def parse_time_token(token, now_dt):
        token = token.strip()
        if token == "6666":
            return now_dt
        if re.fullmatch(r"\d{4}", token):
            hh = int(token[:2]); mm = int(token[2:4])
            dt = now_dt.replace(hour=hh, minute=mm, second=0, microsecond=0)
            if dt > now_dt + timedelta(minutes=1):
                dt -= timedelta(days=1)
            return dt
        if re.fullmatch(r"\d{6}", token):
            hh = int(token[:2]); mm = int(token[2:4]); ss = int(token[4:6])
            dt = now_dt.replace(hour=hh, minute=mm, second=ss, microsecond=0)
            if dt > now_dt + timedelta(minutes=1):
                dt -= timedelta(days=1)
            return dt
        return None

    def compute_respawn(death_dt, boss_name):
        cd = cd_map.get(boss_name)
        if cd is None: return None
        return death_dt + timedelta(seconds=int(cd*3600))

    def next_fixed_time_for_boss(boss_name, now_dt):
        # returns datetime of next fixed occurrence for fixed boss
        times = fixed_bosses.get(boss_name)
        if not times: return None
        today = now_dt.date()
        candidates = []
        for t in times:
            parts = t.split(":")
            hh = int(parts[0]); mm = int(parts[1])
            ss = int(parts[2]) if len(parts) > 2 else 0
            dt = datetime.combine(today, datetime.min.time()).replace(hour=hh, minute=mm, second=ss)
            if dt <= now_dt:
                dt = dt + timedelta(days=1)
            candidates.append(dt)
        candidates.sort()
        return candidates[0]

    def compute_missed_count(respawn_dt, boss_name, now_dt):
        if respawn_dt > now_dt: return 0
        cd = cd_map.get(boss_name, None)
        if cd is None or cd <= 0: return 0
        seconds = (now_dt - respawn_dt).total_seconds()
        missed = int(math.floor(seconds / (cd*3600))) + 1
        return missed

    def format_miss_suffix(miss):
        if miss <= 0: return ""
        chinese = ["一","二","三","四","五","六","七","八","九","十"]
        if miss <= len(chinese):
            return f"(過{chinese[miss-1]})"
        return f"(過{miss})"

    # --- Webhook endpoint ---
    @app.post("/callback", response_class=PlainTextResponse)
    async def callback(request: Request, x_line_signature: str = Header(None)):
        body = await request.body()
        signature = x_line_signature
        if not handler:
            return PlainTextResponse("Missing LINE keys", status_code=500)
        try:
            handler.handle(body.decode('utf-8'), signature)
        except InvalidSignatureError:
            raise HTTPException(status_code=400, detail="Invalid signature")
        return "OK"

    # --- Message handler ---
    @handler.add(MessageEvent, message=TextMessage)
    def handle_message(event):
        text = event.message.text.strip()
        user_id = getattr(event.source, "user_id", "unknown")
        now = datetime.now()
        parts = re.split(r"\s+", text)
        lower = text.strip().lower()

        # HELP
        if lower == "help":
            help_text = (
                "【指令說明】\n\n"
                "1️⃣ 登記王死亡\n  6666 王名 [備註]\n  HHMM 王名 [備註]\n  HHMMSS 王名 [備註]\n\n"
                "2️⃣ 查詢單一王（最新狀態）\n  王名\n\n"
                "3️⃣ 查詢登記歷史（最多5筆）\n  查 王名\n\n"
                "4️⃣ 查全部（出）\n  出 / 全部\n\n"
                "5️⃣ 顯示王簡稱\n  王列表\n\n"
                "6️⃣ 清除所有登記\n  clear -> 回覆 是\n\n"
                "7️⃣ 刪除單王紀錄\n  刪除 王名 / del 王名\n"
            )
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=help_text))
            return

        # 王列表
        if lower == "王列表":
            lines = ["【王的簡稱列表】", ""]
            # create reverse map: canonical -> [aliases]
            rev = {}
            for k, v in alias_map.items():
                rev.setdefault(v, []).append(k)
            # ensure fixed bosses included
            for b in fixed_bosses.keys():
                rev.setdefault(b, [])
            for canonical in sorted(set(list(rev.keys()) + list(cd_map.keys()))):
                aliases = sorted(set(rev.get(canonical, [])))
                line = f"{canonical} : " + ", ".join(aliases) if aliases else f"{canonical} : "
                lines.append(line)
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="\\n".join(lines)))
            return

        # clear flow: ask confirm
        if lower == "clear":
            db["pending_clear"] = True
            db["last_clear_request_by"] = user_id
            save_db()
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="請輸入確認碼 [是] 以清除所有王的紀錄"))
            return
        if lower == "是" and db.get("pending_clear") and db.get("last_clear_request_by") == user_id:
            # perform clear
            db["records"] = {}
            db["miss_count"] = {}
            db["pending_clear"] = False
            db["last_clear_request_by"] = None
            save_db()
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="所有王的紀錄已清除"))
            return
        if lower == "是":
            # someone typed 是 but no pending clear by them
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="沒有待確認的 clear 指令"))
            return

        # delete single
        if parts[0] in ("刪除","del") and len(parts) >= 2:
            target = canonicalize(parts[1])
            if not target:
                line_bot_api.reply_message(event.reply_token, TextSendMessage(text="找不到該王名"))
                return
            db.get("records", {}).pop(target, None)
            db.get("miss_count", {}).pop(target, None)
            save_db()
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f"已刪除 {target} 的所有紀錄"))
            return
        if len(parts) == 2 and parts[1] in ("刪除","刪","清除"):
            target = canonicalize(parts[0])
            if not target:
                line_bot_api.reply_message(event.reply_token, TextSendMessage(text="找不到該王名"))
                return
            db.get("records", {}).pop(target, None)
            db.get("miss_count", {}).pop(target, None)
            save_db()
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f"已刪除 {target} 的所有紀錄"))
            return

        # 查 (history) command: 查 王名
        if parts[0] == "查" and len(parts) >= 2:
            target = canonicalize(" ".join(parts[1:]))
            if not target:
                line_bot_api.reply_message(event.reply_token, TextSendMessage(text="找不到該王名"))
                return
            # fixed boss -> no records
            if target in fixed_bosses:
                line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f"{target} 為固定王，沒有登記紀錄"))
                return
            recs = db.get("records", {}).get(target, [])
            if not recs:
                line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f"{target} 尚無紀錄"))
                return
            # show recent up to 5 entries (newest first)
            lines = [f"{target} 最近 {min(5,len(recs))} 筆紀錄：", ""]
            for i, r in enumerate(reversed(recs[-5:]), 1):
                # r['death'] stored as "YYYY-MM-DD HH:MM:SS"
                lines.append(f"{i}. {r['death']}　登記者：{r.get('user','unknown')}" + (f"　備註：{r['note']}" if r.get('note') else ""))
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="\\n".join(lines)))
            return

        # single boss query: if user inputs only boss name -> show latest status
        if len(parts) == 1:
            target = canonicalize(parts[0])
            if target:
                # fixed boss: show next fixed time + fixed schedule
                if target in fixed_bosses:
                    next_dt = next_fixed_time_for_boss(target, now)
                    timestr = next_dt.strftime("%Y-%m-%d %H:%M:%S") if next_dt else "未知"
                    schedule = " / ".join(fixed_bosses.get(target, []))
                    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f"{target}\\n下一次出現時間：{timestr}\\n固定時段：{schedule}"))
                    return
                # CD boss
                recs = db.get("records", {}).get(target, [])
                if not recs:
                    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f"{target} 尚無紀錄"))
                    return
                last = recs[-1]
                line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f"{target}\\n最近登記：\\n死亡：{last['death']}\\n登記者：{last.get('user','unknown')}\\n備註：{last.get('note','')}"))
                return

        # 出 / 全部 -> compile upcoming list (merge CD respawn and fixed next times)
        if lower in ("出","全部","查全部","all","王狀況"):
            items = []  # tuples of (next_dt, boss, note, is_fixed, miss_count)
            now_dt = now
            # CD bosses: if recorded -> use last respawn; compute miss_count suffix
            for boss, recs in db.get("records", {}).items():
                if not recs: continue
                last = recs[-1]
                respawn_dt = datetime.strptime(last["respawn"], "%Y-%m-%d %H:%M:%S")
                miss = compute_missed_count(respawn_dt, boss, now_dt)
                note = last.get("note","") or ""
                suffix = format_miss_suffix(miss)
                if suffix:
                    note = (note + " " + suffix).strip() if note else suffix
                items.append((respawn_dt, boss, note, False, miss))
            # Fixed bosses: compute next occurrence
            for boss, times in fixed_bosses.items():
                next_dt = next_fixed_time_for_boss(boss, now_dt)
                if next_dt:
                    items.append((next_dt, boss, "", True, 0))
            # sort by datetime ascending (soonest first)
            items.sort(key=lambda x: x[0])
            if not items:
                line_bot_api.reply_message(event.reply_token, TextSendMessage(text="目前尚無任何登記或固定王資料"))
                return
            lines = ["【即將重生列表】", ""]
            for dt, boss, note, is_fixed, miss in items:
                timestr = dt.strftime("%H:%M:%S")
                if note:
                    lines.append(f"{timestr}  {boss}   {note}")
                else:
                    lines.append(f"{timestr}  {boss}")
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="\\n".join(lines)))
            return

        # Try parse registration command (time token + boss + optional note)
        # identify time token (6666, 4-digit, 6-digit)
        time_token = None
        for p in parts:
            if p == "6666" or re.fullmatch(r"\d{4}", p) or re.fullmatch(r"\d{6}", p):
                time_token = p
                break
        # identify boss token (first part mapping to alias)
        boss_token = None
        for p in parts:
            if p == time_token: continue
            if canonicalize(p):
                boss_token = p
                break
        if not boss_token:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="找不到王名，或格式錯誤；請使用：6666 王名 備註 或 1202 王名 備註"))
            return
        boss_name = canonicalize(boss_token)
        # fixed bosses cannot be registered
        if boss_name in fixed_bosses:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f"{boss_name} 為固定王，無需登記"))
            return
        if not time_token:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="請輸入死亡時間（6666=現在 或 四位數時間 例如1202 或 六位數 120230）"))
            return
        death_dt = parse_time_token(time_token, now)
        if death_dt is None:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="時間格式錯誤，請使用 6666 / 四位 / 六位格式"))
            return
        respawn_dt = compute_respawn(death_dt, boss_name)
        if respawn_dt is None:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="找不到該王的 CD 設定，無法計算重生時間"))
            return
        # compose note (remaining parts after removing first occurrence of time_token and boss_token)
        note_parts = []
        skip_once = set([time_token, boss_token])
        for p in parts:
            if p in skip_once:
                skip_once.remove(p)
                continue
            if p.strip():
                note_parts.append(p)
        note = " ".join(note_parts).strip()
        entry = {
            "death": death_dt.strftime("%Y-%m-%d %H:%M:%S"),
            "respawn": respawn_dt.strftime("%Y-%m-%d %H:%M:%S"),
            "note": note,
            "user": user_id or "unknown"
        }
        db.setdefault("records", {}).setdefault(boss_name, []).append(entry)
        # reset miss_count for boss
        db.setdefault("miss_count", {})[boss_name] = 0
        save_db()
        # reply in 3-line format requested
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f"已登記 {boss_name}\\n死亡時間：{entry['death'].split()[1]}\\n下次重生時間：{entry['respawn'].split()[1]}"))
        return

    if __name__ == "__main__":
        import uvicorn
        uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT","8000")))
