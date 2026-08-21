
import re
import sqlite3
import telebot

TOKEN = "8834370706:AAGpsUbPhKxroPekH9bdpie8rMfhdFPVwt8"
bot = telebot.TeleBot(TOKEN, threaded=False)

db = sqlite3.connect("gift.db", check_same_thread=False)
sql = db.cursor()

sql.execute("CREATE TABLE IF NOT EXISTS gifts(code TEXT PRIMARY KEY,buy REAL)")
sql.execute("CREATE TABLE IF NOT EXISTS total(id INTEGER PRIMARY KEY,total REAL)")
sql.execute("INSERT OR IGNORE INTO total VALUES(1,0)")
db.commit()

buy_pattern = re.compile(r"\d{2}\.\d{2}\s+\d{2}:\d{2}\s+(\d+)\s+(\d+)")
sale_pattern = re.compile(r"#([\d,]+).*?пополнен на ([\d.]+)", re.S)

@bot.message_handler(commands=["start"])
def start(m):
    bot.reply_to(m, "🎁 Gift Hisob Bot tayyor!")

@bot.message_handler(commands=["jami"])
def jami(m):
    t = sql.execute("SELECT total FROM total").fetchone()[0]
    bot.reply_to(m, f"Jami foyda: {t:.1f} ⭐")

@bot.message_handler(func=lambda m: True)
def msg(m):
    text = m.text.strip()

    b = buy_pattern.search(text)
    if b:
        code, price = b.groups()
        sql.execute("REPLACE INTO gifts VALUES(?,?)", (code, float(price)))
        db.commit()
        bot.reply_to(m, f"✅ Saqlandi\nKod: {code}\nNarx: {price}⭐")
        return

    s = sale_pattern.search(text)
    if s:
        code = s.group(1).replace(",", "")
        income = float(s.group(2))

        row = sql.execute("SELECT buy FROM gifts WHERE code=?", (code,)).fetchone()
        if not row:
            bot.reply_to(m, "❌ Bu kod topilmadi.")
            return

        buy = row[0]
        profit = income - buy

        sql.execute("UPDATE total SET total=total+?", (profit,))
        sql.execute("DELETE FROM gifts WHERE code=?", (code,))
        db.commit()

        total = sql.execute("SELECT total FROM total").fetchone()[0]

        bot.reply_to(
            m,
            f"✅ Sotildi!\n\nKod: {code}\nXarid: {buy}⭐\nTushdi: {income}⭐\nFoyda: {profit:.1f}⭐\n\nJami: {total:.1f}⭐"
        )
        return

    bot.reply_to(m, "Format noto'g'ri.")

bot.infinity_polling()
