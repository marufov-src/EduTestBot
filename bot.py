import os, asyncio
from flask import Flask
from threading import Thread
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from data import TEST_BAZA

# --- RENDER KEEP ALIVE (Server o'chib qolmasligi uchun) ---
app = Flask('')
@app.route('/')
def home(): return "EduTestBot ishlamoqda!"

def run(): app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
def keep_alive():
    t = Thread(target=run); t.daemon = True; t.start()

# --- BOT KONFIGURATSIYASI ---
TOKEN = os.getenv('BOT_TOKEN')
bot = Bot(token=TOKEN)
dp = Dispatcher()
user_state = {}

@dp.message(Command("start"))
async def start_handler(message: types.Message):
    builder = ReplyKeyboardBuilder()
    for fan in TEST_BAZA.keys():
        builder.add(types.KeyboardButton(text=fan))
    builder.adjust(2)
    await message.answer(f"Salom {message.from_user.first_name}! Test fanni tanlang:", 
                         reply_markup=builder.as_markup(resize_keyboard=True))

@dp.message(F.text.in_(TEST_BAZA.keys()))
async def fan_tanlash(message: types.Message):
    fan = message.text
    builder = ReplyKeyboardBuilder()
    for sinf in range(5, 12):
        builder.add(types.KeyboardButton(text=f"{fan} | {sinf}-sinf"))
    builder.adjust(3)
    await message.answer(f"{fan} fani tanlandi. Sinfni tanlang:", 
                         reply_markup=builder.as_markup(resize_keyboard=True))

@dp.message(F.text.contains("|"))
async def test_boshlash(message: types.Message):
    try:
        parts = message.text.split(" | ")
        fan, sinf = parts[0], parts[1].split("-")[0]
        savollar = TEST_BAZA.get(fan, {}).get(sinf, [])
        
        if not savollar:
            await message.answer(f"Uzur, {fan} {sinf}-sinf bazasi hali bo'sh.")
            return

        user_state[message.from_user.id] = {
            "fan": fan, "sinf": sinf, "index": 0, "ball": 0, "total": len(savollar)
        }
        await savol_yuborish(message.from_user.id)
    except:
        await message.answer("Xatolik! /start bosing.")

async def savol_yuborish(user_id):
    data = user_state[user_id]
    savol = TEST_BAZA[data['fan']][data['sinf']][data['index']]
    
    builder = InlineKeyboardBuilder()
    for variant in savol['o']:
        builder.add(types.InlineKeyboardButton(text=variant, callback_data=f"ans_{variant}"))
    builder.adjust(2)
    
    text = f"📚 {data['fan']} | {data['sinf']}-sinf\n"
    text += f"Savol {data['index']+1}/{data['total']}:\n\n<b>{savol['q']}</b>"
    
    await bot.send_message(user_id, text, reply_markup=builder.as_markup(), parse_mode="HTML")

@dp.callback_query(F.data.startswith("ans_"))
async def tekshirish(call: types.CallbackQuery):
    u_id = call.from_user.id
    if u_id not in user_state: return

    tanlov = call.data.replace("ans_", "")
    data = user_state[u_id]
    javob = TEST_BAZA[data['fan']][data['sinf']][data['index']]['a']

    if tanlov == javob:
        data['ball'] += 1
    
    data['index'] += 1
    await call.message.delete()

    if data['index'] < data['total']:
        await savol_yuborish(u_id)
    else:
        foiz = int((data['ball'] / data['total']) * 100)
        await bot.send_message(u_id, f"🏆 Test yakunlandi!\n\nNatijangiz: {data['ball']}/{data['total']}\nSifat: {foiz}%")
        del user_state[u_id]

async def main():
    keep_alive()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
