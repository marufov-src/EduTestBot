import os, asyncio, time
from flask import Flask
from threading import Thread
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from data import TEST_BAZA

# --- RENDER KEEP ALIVE ---
app = Flask('')
@app.route('/')
def home(): return "Bot is Online!"
def run(): app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
def keep_alive():
    t = Thread(target=run); t.daemon = True; t.start()

# --- BOT SOZLAMALARI ---
TOKEN = os.getenv('BOT_TOKEN')
bot = Bot(token=TOKEN)
dp = Dispatcher()
user_state = {}

def get_main_menu():
    builder = ReplyKeyboardBuilder()
    for fan in TEST_BAZA.keys():
        builder.add(types.KeyboardButton(text=fan))
    builder.adjust(2)
    return builder.as_markup(resize_keyboard=True)

@dp.message(Command("start"))
async def start_handler(message: types.Message):
    await message.answer(f"Assalomu alaykum, {message.from_user.first_name}!\nFanni tanlang:", 
                         reply_markup=get_main_menu())

@dp.message(F.text == "⬅️ Orqaga")
async def back_to_main(message: types.Message):
    await message.answer("Asosiy menyuga qaytdingiz. Fanni tanlang:", reply_markup=get_main_menu())

@dp.message(F.text.in_(TEST_BAZA.keys()))
async def fan_tanlash(message: types.Message):
    fan = message.text
    builder = ReplyKeyboardBuilder()
    for sinf in range(5, 12):
        builder.add(types.KeyboardButton(text=f"{fan} | {sinf}-sinf"))
    builder.add(types.KeyboardButton(text="⬅️ Orqaga"))
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
            "fan": fan, "sinf": sinf, "index": 0, "ball": 0, 
            "total": len(savollar), "start_time": time.time()
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
        end_time = time.time()
        sarflangan_vaqt = int(end_time - data['start_time'])
        minut = sarflangan_vaqt // 60
        soniya = sarflangan_vaqt % 60
        
        vaqt_text = f"{minut} daqiqa {soniya} soniya" if minut > 0 else f"{soniya} soniya"
        foiz = int((data['ball'] / data['total']) * 100)
        
        await bot.send_message(u_id, 
            f"🏆 <b>Test yakunlandi!</b>\n\n"
            f"📊 Natija: {data['ball']}/{data['total']}\n"
            f"📈 Sifat: {foiz}%\n"
            f"⏱ Sarflangan vaqt: {vaqt_text}\n\n"
            f"Yangi test boshlash uchun fanni tanlang 👇", 
            reply_markup=get_main_menu(), parse_mode="HTML")
        del user_state[u_id]

async def main():
    keep_alive()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
