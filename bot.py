import os
import telebot
import random
import time
import http.server
import socketserver
import threading
from telebot import types

# 1. TOKENNI O'RNATING (Render Environment-dan oladi)
TOKEN = os.environ.get("BOT_TOKEN")
bot = telebot.TeleBot(TOKEN)

# 2. DATA IMPORT (data.py fayli borligiga ishonch hosil qiling)
try:
    from data import matematika_test_base, english_test_base, biology_test_base, tarix_test_base
except ImportError:
    matematika_test_base = english_test_base = biology_test_base = tarix_test_base = {}

# Foydalanuvchi ma'lumotlari va Reyting (Vaqtinchalik RAMda saqlanadi)
user_data = {}
leaderboards = {
    "Matematika": {},
    "English": {},
    "Biologiya": {},
    "Tarix": {}
}

# --- RENDER UCHUN DUMMY SERVER (Botni uyg'oq saqlash uchun) ---
def run_dummy_server():
    # Render avtomatik port beradi, bo'lmasa 8080 ishlaydi
    PORT = int(os.environ.get("PORT", 8080))
    class MyHandler(http.server.SimpleHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b"Bot is alive!") # Cron-job uchun javob

    with socketserver.TCPServer(("", PORT), MyHandler) as httpd:
        print(f"Server {PORT}-portda ishlamoqda...")
        httpd.serve_forever()

# --- BOT FUNKSIYALARI ---

@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("Matematika", "English", "Biologiya", "Tarix")
    markup.add("🏆 Reyting")
    bot.send_message(message.chat.id, "<b>Fanlardan birini tanlang yoki Reytingni ko'ring:</b>", 
                     reply_markup=markup, parse_mode="HTML")

@bot.message_handler(func=lambda m: m.text == "🏆 Reyting")
def show_leaderboard_menu(message):
    markup = types.InlineKeyboardMarkup()
    for sub in leaderboards.keys():
        markup.add(types.InlineKeyboardButton(f"📊 {sub}", callback_data=f"lb_{sub}"))
    bot.send_message(message.chat.id, "Qaysi fan bo'yicha reytingni ko'rmoqchisiz?", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text in ["Matematika", "English", "Biologiya", "Tarix"])
def subject_select(message):
    user_data[message.chat.id] = {
        'subject': message.text,
        'name': message.from_user.first_name
    }
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btns = [types.KeyboardButton(f"{i}-sinf") for i in range(5, 12)]
    markup.add(*btns)
    bot.send_message(message.chat.id, f"📌 {message.text} tanlandi. Sinvingizni tanlang:", reply_markup=markup)

@bot.message_handler(func=lambda m: "sinf" in m.text)
def select_class(message):
    chat_id = message.chat.id
    if chat_id not in user_data: return start(message)
    
    sinf_nomi = message.text.split("-")[0]
    sub = user_data[chat_id]['subject']
    
    bases = {
        "Matematika": matematika_test_base, 
        "English": english_test_base, 
        "Biologiya": biology_test_base, 
        "Tarix": tarix_test_base
    }
    questions = bases[sub].get(sinf_nomi)
    
    if questions:
        count = min(len(questions), 10) # 10 ta tasodifiy savol
        q_list = random.sample(questions, count)
        
        user_data[chat_id].update({
            'questions': q_list, 
            'score': 0, 
            'current_q': 0, 
            'sinf': sinf_nomi,
            'start_time': time.time()
        })
        send_question(chat_id)
    else:
        bot.send_message(chat_id, "Hozircha bu sinf uchun testlar yo'q.")

def send_question(chat_id):
    data = user_data[chat_id]
    q = data['questions'][data['current_q']]
    
    markup = types.InlineKeyboardMarkup()
    opts = q['o'].copy()
    random.shuffle(opts)
    
    for o in opts:
        # To'g'ri (c) yoki Noto'g'ri (w) ekanini callback_data orqali yuboramiz
        callback = "correct" if o == q['a'] else "wrong"
        markup.add(types.InlineKeyboardButton(o, callback_data=callback))
    
    bot.send_message(chat_id, f"<b>{data['current_q'] + 1}-savol:</b>\n\n{q['q']}", 
                     reply_markup=markup, parse_mode="HTML")

@bot.callback_query_handler(func=lambda call: call.data.startswith("lb_"))
def handle_lb_view(call):
    sub = call.data.split("_")[1]
    lb = leaderboards.get(sub, {})
    if not lb:
        bot.answer_callback_query(call.id, f"{sub} fani bo'yicha hali natijalar yo'q.")
        return

    # Reyting balli bo'yicha tartiblash
    sorted_lb = sorted(lb.items(), key=lambda x: x[1]['rating'], reverse=True)
    text = f"<b>🏆 {sub} Reytingi (Top 10):</b>\n\n"
    for i, (uid, d) in enumerate(sorted_lb[:10], 1):
        text += f"{i}. {d['name']} — <b>{d['rating']} ball</b> ({d['time']}s)\n"
    
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, parse_mode="HTML")

@bot.callback_query_handler(func=lambda call: call.data in ["correct", "wrong"])
def handle_answer(call):
    chat_id = call.message.chat.id
    if chat_id not in user_data: return

    if call.data == "correct":
        user_data[chat_id]['score'] += 1
    
    user_data[chat_id]['current_q'] += 1
    
    # Eskisini o'chirish (tozalik uchun)
    try: bot.delete_message(chat_id, call.message.message_id)
    except: pass
    
    data = user_data[chat_id]
    if data['current_q'] < len(data['questions']):
        send_question(chat_id)
    else:
        # TEST TUGADI
        total_time = round(time.time() - data['start_time'], 1)
        score = data['score']
        sinf = int(data['sinf'])
        sub = data['subject']
        
        # MANTIQ: Yuqori sinfga ko'proq ball (Adolat uchun)
        # 5-sinf (1.0 koeff), 11-sinf (1.6 koeff)
        rating_points = round(score * (1 + (sinf - 5) * 0.1), 1)

        # Leaderboardni yangilash
        if chat_id not in leaderboards[sub] or rating_points > leaderboards[sub][chat_id]['rating']:
            leaderboards[sub][chat_id] = {
                'name': data['name'],
                'rating': rating_points,
                'time': total_time
            }

        res = (f"<b>🏁 Test yakunlandi!</b>\n\n"
               f"📚 Fan: {sub} ({sinf}-sinf)\n"
               f"✅ To'g'ri: {score}/{len(data['questions'])}\n"
               f"<b>🏆 Reyting ballingiz: {rating_points}</b>\n"
               f"⏱ Vaqt: {total_time} soniya")
        
        bot.send_message(chat_id, res, parse_mode="HTML")
        start(call.message)

# --- BOTNI ISHGA TUSHIRISH ---
if __name__ == "__main__":
    # 1. Dummy serverni alohida "oqim"da yoqish
    threading.Thread(target=run_dummy_server, daemon=True).start()
    
    # 2. Botni polling rejimida yoqish
    print("Bot Render-da muvaffaqiyatli ishga tushdi...")
    bot.infinity_polling(timeout=10, long_polling_timeout=5)
