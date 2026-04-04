from flask import Flask
from threading import Thread
import os

app = Flask('')

@app.route('/')
def home():
    return "Bot is alive!"

def run():
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))

def keep_alive():
    t = Thread(target=run)
    t.start()

import asyncio
import json
import random
import os  # Bu kutubxona token va ID ni o'qish uchun shart
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder

# Token va Admin ID ni tizimdan (Render'dan) olamiz
API_TOKEN = os.getenv('BOT_TOKEN')
# os.getenv hamma narsani tekst (string) sifatida oladi, shuning uchun ADMIN_ID ni int (son) qilamiz
ADMIN_ID = int(os.getenv('ADMIN_ID', 0))

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

DB_FILE = 'stats.json'
USERS_FILE = 'users.json'

# --- YORDAMCHI FUNKSIYALAR ---
def save_user(user_id):
    try:
        with open(USERS_FILE, 'r') as f: users = json.load(f)
    except: users = []
    if user_id not in users:
        users.append(user_id)
        with open(USERS_FILE, 'w') as f: json.dump(users, f)

def save_score(user_name, score):
    try:
        with open(DB_FILE, 'r') as f: data = json.load(f)
    except: data = {}
    if user_name not in data or score > data.get(user_name, 0):
        data[user_name] = score
        with open(DB_FILE, 'w') as f: json.dump(data, f)

def get_top_scores():
    try:
        with open(DB_FILE, 'r') as f: data = json.load(f)
        return sorted(data.items(), key=lambda x: x[1], reverse=True)[:10]
    except: return []

# --- SAVOLLAR ---
QUESTIONS = {
    "Matematika": [
        {"q": "5 + 7 = ?", "o": ["10", "12", "14"], "c": "12"},
        {"q": "100 / 4 = ?", "o": ["20", "25", "30"], "c": "25"},
        {"q": "9 * 9 = ?", "o": ["72", "81", "90"], "c": "81"}
    ],
    "Tarix": [
        {"q": "Amir Temur nechanchi yilda tug'ilgan?", "o": ["1336", "1405", "1342"], "c": "1336"},
        {"q": "O'zbekiston qachon mustaqil bo'lgan?", "o": ["1990", "1991", "1992"], "c": "1991"}
    ]
}

class QuizStates(StatesGroup):
    answering = State()
    broadcasting = State()

# --- HANDLERLAR ---
@dp.message(Command("start"))
async def start_handler(message: types.Message):
    save_user(message.from_user.id)
    builder = ReplyKeyboardBuilder()
    for subject in QUESTIONS.keys():
        builder.add(types.KeyboardButton(text=subject))
    builder.add(types.KeyboardButton(text="📊 Statistika"))
    builder.adjust(2)
    await message.answer(f"Salom {message.from_user.full_name}!\nEdu Test Botga xush kelibsiz. Fan tanlang:", 
                         reply_markup=builder.as_markup(resize_keyboard=True))

@dp.message(F.text == "📊 Statistika")
async def show_stats(message: types.Message):
    top_list = get_top_scores()
    if not top_list:
        await message.answer("Hozircha natijalar yo'q.")
        return
    text = "🏆 **Top 10 talik natijalar:**\n\n"
    for i, (name, score) in enumerate(top_list, 1):
        text += f"{i}. {name} — {score} ball\n"
    await message.answer(text, parse_mode="Markdown")

@dp.message(Command("admin"))
async def admin_panel(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        builder = InlineKeyboardBuilder()
        builder.add(types.InlineKeyboardButton(text="📢 Xabar yuborish", callback_data="broadcast"))
        await message.answer("Admin panel:", reply_markup=builder.as_markup())
    else:
        await message.answer("Kechirasiz, bu bo'lim faqat adminlar uchun.")

@dp.callback_query(F.data == "broadcast")
async def start_broadcast(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer("Xabaringizni yozing:")
    await state.set_state(QuizStates.broadcasting)

@dp.message(QuizStates.broadcasting)
async def send_broadcast(message: types.Message, state: FSMContext):
    try:
        with open(USERS_FILE, 'r') as f: users = json.load(f)
    except: users = []
    
    sent = 0
    for user_id in users:
        try:
            await bot.send_message(user_id, message.text)
            sent += 1
        except: pass
    await message.answer(f"Xabar {sent} ta foydalanuvchiga yuborildi!")
    await state.clear()

@dp.message(F.text.in_(QUESTIONS.keys()))
async def start_quiz(message: types.Message, state: FSMContext):
    subject = message.text
    q_list = QUESTIONS[subject].copy()
    random.shuffle(q_list)
    await state.update_data(subject=subject, questions=q_list, current_q=0, score=0)
    await send_question(message, state)

async def send_question(message, state: FSMContext):
    data = await state.get_data()
    q_list, idx = data['questions'], data['current_q']
    
    if idx < len(q_list):
        q_data = q_list[idx]
        opts = q_data['o'].copy()
        random.shuffle(opts)
        
        builder = InlineKeyboardBuilder()
        for opt in opts:
            builder.add(types.InlineKeyboardButton(text=opt, callback_data=f"ans_{opt}"))
        builder.adjust(1)
        
        text = f"**{data['subject']}**\n\nSavol {idx+1}: {q_data['q']}"
        if isinstance(message, types.Message):
            await message.answer(text, reply_markup=builder.as_markup(), parse_mode="Markdown")
        else: # Agar callback bo'lsa
            await message.message.answer(text, reply_markup=builder.as_markup(), parse_mode="Markdown")
        await state.set_state(QuizStates.answering)
    else:
        score = data['score']
        save_score(message.from_user.first_name, score)
        await (message.answer if isinstance(message, types.Message) else message.message.answer)(
            f"Test tugadi! 🎉\nSizning natijangiz: {score}\nStatistikani tekshirib ko'ring."
        )
        await state.clear()

@dp.callback_query(F.data.startswith("ans_"))
async def check_ans(callback: types.CallbackQuery, state: FSMContext):
    ans = callback.data.split("_")[1]
    data = await state.get_data()
    correct = data['questions'][data['current_q']]['c']
    
    if ans == correct:
        await callback.answer("To'g'ri! ✅")
        await state.update_data(score=data['score'] + 1)
    else:
        await callback.answer(f"Xato! ❌ To'g'ri: {correct}")

    await state.update_data(current_q=data['current_q'] + 1)
    await callback.message.delete()
    await send_question(callback, state)

async def main():
    keep_alive()  # Render uchun veb-serverni ishga tushiradi
    print("Bot muvaffaqiyatli ishga tushdi!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
