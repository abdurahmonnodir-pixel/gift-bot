import os
import re
import time
import sqlite3
import telebot

TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(TOKEN, threaded=False)

db = sqlite3.connect("gift.db", check_same_thread=False)

db.execute("""
CREATE TABLE IF NOT EXISTS gifts(
    code TEXT PRIMARY KEY,
    buy REAL
)
""")

db.execute("""
CREATE TABLE IF NOT EXISTS total(
    id INTEGER PRIMARY KEY,
    profit REAL
)
""")

db.execute("INSERT OR IGNORE INTO total VALUES(1,0)")
db.commit()

buy_pattern = re.compile(r"\d{1,2}\.\d{1,2}\s+\d{2}:\d{2}\s+(\d+)\s+(\d+)")
sale_pattern = re.compile(r"#([\d,\s]+).*?пополнен на\s+([\d.]+)", re.S)

@bot.message_handler(commands=["start"])
def start(m):
    bot.reply_to(
        m,
        "🎁 Gift Hisob Bot tayyor!\n\n"
        "Xarid ro'yxatini yoki sotuv xabarini yuboring."
    )

@bot.message_handler(commands=["jami"])
def jami(m):
    total = db.execute(
        "SELECT profit FROM total WHERE id=1"
    ).fetchone()[0]

    bot.reply_to(m, f"💰 Jami foyda: {total:.1f} ⭐")

@bot.message_handler(func=lambda m: True)
def text(m):
    try:
        txt = m.text.strip()

        # ===== Xaridlarni saqlash =====
        saved = 0

        for line in txt.splitlines():
            x = buy_pattern.match(line.strip())

            if x:
                code, price = x.groups()

                code = re.sub(r"\D", "", code)

                db.execute(
                    "INSERT OR REPLACE INTO gifts VALUES(?,?)",
                    (code, float(price))
                )

                saved += 1

        if saved:
            db.commit()
            bot.reply_to(m, f"✅ {saved} ta gift saqlandi")
            return

                # ===== Bir nechta sotuvni qabul qilish =====
        sales = list(sale_pattern.finditer(txt))

        if sales:
            result = []

            for s in sales:
                code = re.sub(r"\D", "", s.group(1))
                income = float(s.group(2))

                row = db.execute(
                    "SELECT buy FROM gifts WHERE code=?",
                    (code,)
                ).fetchone()

                if row is None:
                    result.append(f"❌ {code} topilmadi")
                    continue

                buy = row[0]
                profit = income - buy

                db.execute("DELETE FROM gifts WHERE code=?", (code,))
                db.execute(
                    "UPDATE total SET profit=profit+? WHERE id=1",
                    (profit,)
                )

                result.append(f"✅ {code}  +{profit:.1f}⭐")

            db.commit()

            total = db.execute(
                "SELECT profit FROM total WHERE id=1"
            ).fetchone()[0]

            bot.reply_to(
                m,
                "\n".join(result) + f"\n\n💰 Jami: {total:.1f}⭐"
            )
            return

        bot.reply_to(m, "❌ Format noto'g'ri")

    except Exception as e:
        bot.reply_to(m, f"Xato: {e}")

while True:
    try:
        print("Bot ishlayapti...")
        bot.infinity_polling(skip_pending=True, timeout=20)
    except Exception as e:
        print("Qayta ulanmoqda:", e)
        time.sleep(5)
  
