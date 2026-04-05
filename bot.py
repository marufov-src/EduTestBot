import os
import telebot
import random
import time
import http.server
import socketserver
import threading
from telebot import types

# 1. TOKENNI TEKSHIRING: @BotFather bergan tokenni to'liq qo'ying
TOKEN = os.environ.get("BOT_TOKEN") 
bot = telebot.TeleBot(TOKEN)

# 2. DATA IMPORT (data.py fayli GitHubda borligini tekshiring)
try:
    from data import matematika_test_base, english_test_base, biology_test_base, tarix_test_base
except ImportError:
    matematika_test_base = english_test_base = biology_test_base = tarix_test_base = {}

user_data = {}
# Fanlar bo'yicha alohida leaderboard
leaderboards = {
    "Matematika": {},
    "English": {},
    "Biologiya": {},
    "Tarix": {}
}

# --- RENDER UCHUN DUMMY SERVER (PORT HATOSINI OLISH UCHUN) ---
def run_dummy_server():
    PORT = int(os.environ.get("PORT", 8080))
    handler = http.server.SimpleHTTPRequestHandler
    with socketserver.TCPServer(("", PORT), handler) as httpd:
        httpd.serve_forever()

threading.Thread(target=run_dummy_server, daemon=True).start()
# ---------------------------------------------------------

@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("Matematika", "English", "Biologiya", "Tarix")
    markup.add("🏆 Reyting")
    bot.send_message(message.chat.id, "<b>Fanlardan birini tanlang:</b>", reply_markup=markup, parse_mode="HTML")

@bot.message_handler(func=lambda m: m.text == "🏆 Reyting")
def show_leaderboard_menu(message):
    markup = types.InlineKeyboardMarkup()
    for sub in leaderboards.keys():
        markup.add(types.InlineKeyboardButton(sub, callback_data=f"lb_{sub}"))
    bot.send_message(message.chat.id, "Qaysi fan bo'yicha reytingni ko'rmoqchisiz?", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text in ["Matematika", "English", "Biologiya", "Tarix"])
def subject(message):
    user_data[message.chat.id] = {
        'subject': message.text,
        'name': message.from_user.first_name
    }
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btns = [types.KeyboardButton(f"{i}-sinf") for i in range(5, 12)]
    markup.add(*btns)
    bot.send_message(message.chat.id, f"📌 {message.text}. Sinvingizni tanlang:", reply_markup=markup)

@bot.message_handler(func=lambda m: "sinf" in m.text)
def select_class(message):
    chat_id = message.chat.id
    if chat_id not in user_data: return start(message)
    
    sinf_nomi = message.text.split("-")[0]
    sub = user_data[chat_id]['subject']
    
    bases = {"Matematika": matematika_test_base, "English": english_test_base, "Biologiya": biology_test_base, "Tarix": tarix_test_base}
    questions = bases[sub].get(sinf_nomi)
    
    if questions:
        # Har doim 10 ta tasodifiy savol olish (qiziqarli bo'lishi uchun)
        count = min(len(questions), 10)
        q_list = random.sample(questions, count)
        
        user_data[chat_id].update({
            'questions': q_list, 
            'score': 0, 
            'current_q': 0, 
            'sinf': sinf_nomi,
            'start_time': time.time()
        })
        send_q(chat_id)
    else:
        bot.send_message(chat_id, "Hozircha bu sinf uchun testlar yo'q.")

def send_q(chat_id):
    data = user_data[chat_id]
    q = data['questions'][data['current_q']]
    
    markup = types.InlineKeyboardMarkup()
    opts = q['o'].copy()
    random.shuffle(opts)
    
    for o in opts:
        callback = "c" if o == q['a'] else "w"
        markup.add(types.InlineKeyboardButton(o, callback_data=callback))
    
    bot.send_message(chat_id, f"<b>{data['current_q'] + 1}-savol:</b>\n\n{q['q']}", reply_markup=markup, parse_mode="HTML")

@bot.callback_query_handler(func=lambda call: call.data.startswith("lb_"))
def handle_lb_view(call):
    sub = call.data.split("_")[1]
    lb = leaderboards.get(sub, {})
    if not lb:
        bot.answer_callback_query(call.id, f"{sub} fani bo'yicha hali natijalar yo'q.")
        return

    sorted_lb = sorted(lb.items(), key=lambda x: x[1]['rating'], reverse=True)
    text = f"<b>🏆 {sub} Reytingi (Top 10):</b>\n\n"
    for i, (uid, d) in enumerate(sorted_lb[:10], 1):
        text += f"{i}. {d['name']} — {d['rating']} ball ({d['time']}s)\n"
    
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, parse_mode="HTML")

@bot.callback_query_handler(func=lambda call: call.data in ["c", "w"])
def handle_answer(call):
    chat_id = call.message.chat.id
    if chat_id not in user_data: return

    if call.data == "c":
        user_data[chat_id]['score'] += 1
    
    user_data[chat_id]['current_q'] += 1
    
    try: bot.delete_message(chat_id, call.message.message_id)
    except: pass
    
    data = user_data[chat_id]
    if data['current_q'] < len(data['questions']):
        send_q(chat_id)
    else:
        # TEST TUGADI: Reyting hisoblash
        total_time = round(time.time() - data['start_time'], 1)
        score = data['score']
        sinf = int(data['sinf'])
        sub = data['subject']
        
        # Mantiq: Sinf qancha yuqori bo'lsa, ball shuncha ko'p (qiyinchilik uchun)
        # 5-sinf coef: 1.0, 11-sinf coef: 1.6
        rating_points = round(score * (1 + (sinf - 5) * 0.1), 1)

        # Leaderboardga yozish
        if chat_id not in leaderboards[sub] or rating_points > leaderboards[sub][chat_id]['rating']:
            leaderboards[sub][chat_id] = {
                'name': data['name'],
                'rating': rating_points,
                'time': total_time
            }

        res = (f"<b>🏁 Test yakunlandi!</b>\n\n"
               f"Fan: {sub} ({sinf}-sinf)\n"
               f"Natija: {score}/{len(data['questions'])}\n"
               f"<b>Reyting ballingiz: {rating_points}</b>\n"
               f"Vaqt: {total_time} soniya")
        
        bot.send_message(chat_id, res, parse_mode="HTML")
        start(call.message)

if __name__ == "__main__":
    bot.infinity_polling()
