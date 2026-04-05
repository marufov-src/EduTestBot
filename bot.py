import os
import telebot
import random
import time  # Vaqtni o'lchash uchun
from telebot import types

TOKEN = os.environ.get("BOT_TOKEN")bot = telebot.TeleBot(TOKEN)

# Test ma'lumotlarini import qilish
from data import matematika_test_base, english_test_base, biology_test_base, tarix_test_base

user_data = {}
leaderboard = {} # Natijalarni saqlash uchun (Vaqtincha xotirada)

@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("Matematika", "English", "Biologiya", "Tarix", "🏆 Leaderboard")
    bot.send_message(message.chat.id, "<b>Fanlardan birini tanlang yoki natijalarni ko'ring:</b>", reply_markup=markup, parse_mode="HTML")

@bot.message_handler(func=lambda m: m.text == "🏆 Leaderboard")
def show_leaderboard(message):
    if not leaderboard:
        bot.send_message(message.chat.id, "Hozircha natijalar yo'q. Birinchi bo'lib test yeching!")
        return
    
    # Ballar bo'yicha saralash
    sorted_lb = sorted(leaderboard.items(), key=lambda x: x[1]['score'], reverse=True)
    text = "<b>🏆 ENG YAXSHI NATIJALAR:</b>\n\n"
    for i, (user, data) in enumerate(sorted_lb[:10], 1):
        text += f"{i}. {data['name']} — {data['score']} ball ({data['time']} sek)\n"
    
    bot.send_message(message.chat.id, text, parse_mode="HTML")

@bot.message_handler(func=lambda m: m.text in ["Matematika", "English", "Biologiya", "Tarix"])
def subject(message):
    user_data[message.chat.id] = {
        'subject': message.text, 
        'start_time': time.time(), # Test boshlangan vaqt
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
        q_list = random.sample(questions, len(questions))
        user_data[chat_id].update({'questions': q_list, 'score': 0, 'current_q': 0, 'start_time': time.time()})
        send_q(chat_id)
    else:
        bot.send_message(chat_id, "Hozircha bu sinf uchun testlar yo'q.")

def send_q(chat_id):
    data = user_data[chat_id]
    curr = data['current_q']
    q = data['questions'][curr]
    
    text = f"<b>{curr + 1}-savol:</b>\n\n{q['q']}"
    markup = types.InlineKeyboardMarkup()
    opts = q['o'].copy()
    random.shuffle(opts)
    
    for o in opts:
        callback = "c" if o == q['a'] else "w"
        markup.add(types.InlineKeyboardButton(o, callback_data=callback))
    
    bot.send_message(chat_id, text, reply_markup=markup, parse_mode="HTML")

@bot.callback_query_handler(func=lambda call: True)
def handle_answer(call):
    chat_id = call.message.chat.id
    if chat_id not in user_data: return

    if call.data == "c":
        user_data[chat_id]['score'] += 1
    
    user_data[chat_id]['current_q'] += 1
    
    try:
        bot.delete_message(chat_id, call.message.message_id)
    except:
        pass
    
    if user_data[chat_id]['current_q'] < len(user_data[chat_id]['questions']):
        send_q(chat_id)
    else:
        # Test tugadi - Vaqtni hisoblash
        end_time = time.time()
        total_time = round(end_time - user_data[chat_id]['start_time'], 1)
        score = user_data[chat_id]['score']
        total = len(user_data[chat_id]['questions'])
        user_name = user_data[chat_id]['name']

        # Leaderboardga qo'shish (agar natija yaxshi bo'lsa yangilaydi)
        if chat_id not in leaderboard or score > leaderboard[chat_id]['score']:
            leaderboard[chat_id] = {'name': user_name, 'score': score, 'time': total_time}

        result_text = (
            f"<b>🏁 Test yakunlandi!</b>\n\n"
            f"👤 Ism: <b>{user_name}</b>\n"
            f"✅ To'g'ri javoblar: <b>{score}/{total}</b>\n"
            f"⏱ Sarflangan vaqt: <b>{total_time} soniya</b>"
        )
        
        bot.send_message(chat_id, result_text, parse_mode="HTML")
        start(call.message)

if __name__ == "__main__":
    print("Bot Leaderboard va Taymer bilan ishga tushdi...")
    import http.server
import socketserver
import threading

def run_dummy_server():
    PORT = int(os.environ.get("PORT", 8080))
    handler = http.server.SimpleHTTPRequestHandler
    with socketserver.TCPServer(("", PORT), handler) as httpd:
        httpd.serve_forever()

threading.Thread(target=run_dummy_server, daemon=True).start()
    bot.infinity_polling()
# ishla
