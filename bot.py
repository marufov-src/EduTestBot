import os
import asyncio
from flask import Flask
from threading import Thread
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command

# --- 1. RENDER UCHUN "TIRIK SAQLASH" (KEEP ALIVE) QISMI ---
app = Flask('')

@app.route('/')
def home():
    return "Bot muvaffaqiyatli ishlayapti!"

def run():
    # Render avtomatik beradigan PORT ni olamiz
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.daemon = True # Bot o'chsa, bu ham o'chadi
    t.start()
# -------------------------------------------------------

# --- 2. BOT SOZLAMALARI ---
TOKEN = os.getenv('BOT_TOKEN')
ADMIN_ID = os.getenv('ADMIN_ID')

bot = Bot(token=TOKEN)
dp = Dispatcher()

# --- 3. BOT KOMANDALARI ---

# /start komandasi
@dp.message(Command("start"))
async def start_handler(message: types.Message):
    markup = types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text="Matematika ➕"), types.KeyboardButton(text="Mantiq 🧠")],
            [types.KeyboardButton(text="Statistika 📊")]
        ],
        resize_keyboard=True
    )
    await message.answer(
        f"Xush kelibsiz, {message.from_user.full_name}!\n\n"
        "Men AI yordamida yaratilgan Test Botman. Fanlardan birini tanlang:",
        reply_markup=markup
    )

# Matematika testi uchun misol
@dp.message(lambda message: message.text == "Matematika ➕")
async def math_test(message: types.Message):
    await message.answer("Misolni yeching: 15 * 3 + 5 = ?\n\nJavobni yozing:")

# Statistika (Admin uchun yoki hamma uchun)
@dp.message(lambda message: message.text == "Statistika 📊")
async def show_stats(message: types.Message):
    await message.answer("Hozircha bot test rejimida ishlamoqda. 🛠️")

# --- 4. ASOSIY ISHGA TUSHIRISH FUNKSIYASI ---
async def main():
    # Birinchi bo'lib Render-ni aldash uchun veb-serverni yoqamiz
    keep_alive()
    print("Veb-server ishga tushdi!")
    
    print("Bot Telegramga ulanmoqda...")
    try:
        await dp.start_polling(bot)
    except Exception as e:
        print(f"Xatolik yuz berdi: {e}")

if __name__ == "__main__":
    asyncio.run(main())
