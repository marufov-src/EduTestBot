import os
import telebot
import random
import time
import http.server
import socketserver
import threading
import io
from telebot import types
from PIL import Image, ImageDraw, ImageFont

# 1. TOKEN VA BOT SOZLAMALARI
TOKEN = os.environ.get("BOT_TOKEN")
bot = telebot.TeleBot(TOKEN)

# 2. DATA IMPORT (Agar fayllar bo'lmasa, bo'sh lug'at yaratadi)
try:
    from data import matematika_test_base, english_test_base, biology_test_base, tarix_test_base
except ImportError:
    matematika_test_base = english_test_base = biology_test_base = tarix_test_base = {}

user_data = {}
leaderboards = {"Matematika": {}, "English": {}, "Biologiya": {}, "Tarix": {}}

# --- RENDER UCHUN DUMMY SERVER (O'chib qolmasligi uchun) ---
def run_dummy_server():
    PORT = int(os.environ.get("PORT", 8080))
    class MyHandler(http.server.SimpleHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"Bot is active!")
    with socketserver.TCPServer(("", PORT), MyHandler) as httpd:
        httpd.serve_forever()

# --- PROFESSIONAL SERTIFIKAT YARATISH (Galafera TTF bilan) ---
def create_certificate(name, subject, score, sinf):
    try:
        img = Image.open("template.jpg")
        draw = ImageDraw.Draw(img)
        W, H = img.size
        
        dark_blue = (0, 32, 96) 
        gray_text = (80, 80, 80)

        # Shriftlarni yuklash (Galafera TTF uchun o'lchamlar sozlangan)
        try:
            font_title = ImageFont.truetype("myfont.ttf", 35) 
            font_name = ImageFont.truetype("myfont.ttf", 45)  
            font_small = ImageFont.truetype("myfont.ttf", 25) 
        except:
            font_title = font_name = font_small = ImageFont.load_default()

        # 1. Sarlavha
        title = "SERTIFIKAT"
        tw = draw.textlength(title, font=font_title)
        draw.text(((W - tw) / 2, H * 0.18), title, fill=dark_blue, font=font_title)
        
        # 2. Taqdim etish matni
        sub_text = "Ushbu sertifikat bilan taqdirlanadi:"
        sw = draw.textlength(sub_text, font=font_small)
        draw.text(((W - sw) / 2, H * 0.3), sub_text, fill=gray_text, font=font_small)

        # 3. ISM (Markazda)
        full_name = str(name).upper()
        nw = draw.textlength(full_name, font=font_name)
        draw.text(((W - nw) / 2, H * 0.42), full_name, fill=dark_blue, font=font_name)

        # 4. Natija va Fan
        desc = f"Bilimlar bellashuvida {subject} fanidan"
        dw = draw.textlength(desc, font=font_small)
        draw.text(((W - dw) / 2, H * 0.58), desc, fill=gray_text, font=font_small)
        
        desc2 = f"ko'rsatgan 10/10 natijasi uchun."
        dw2 = draw.textlength(desc2, font=font_small)
        draw.text(((W - dw2) / 2, H * 0.65), desc2, fill=gray_text, font=font_small)

        # 5. Avtomatik Sana
        sana = time.strftime("%d.%m.%Y")
        snw = draw.textlength(sana, font=font_small)
        draw.text(((W - snw) / 2, H * 0.78), sana, fill=dark_blue, font=font_small)

        bio = io.BytesIO()
        bio.name = 'certificate.png'
        img.save(bio, 'PNG')
        bio.seek(0)
        return bio
    except Exception as e:
        print(f"Xato: {e}")
        return None

# --- BOTNING ASOSIY LOGIKASI ---

@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("Matematika", "English", "Biologiya", "Tarix")
    markup.add("🏆 Reyting")
    bot.send_message(message.chat.id, "<b>Fanlardan birini tanlang va testni boshlang:</b>", 
                     reply_markup=markup, parse_mode="HTML")

@bot.message_handler(func=lambda m: m.text == "🏆 Reyting")
def show_leaderboard_menu(message):
    markup = types.InlineKeyboardMarkup()
    for sub in leaderboards.keys():
        markup.add(types.InlineKeyboardButton(f"📊 {sub}", callback_data=f"lb_{sub}"))
    bot.send_message(message.chat.id, "Qaysi fan reytingini ko'rmoqchisiz?", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text in ["Matematika", "English", "Biologiya", "Tarix"])
def subject_select(message):
    first = message.from_user.first_name or ""
    last = message.from_user.last_name or ""
    full_name = f"{first} {last}".strip()
    
    user_data[message.chat.id] = {
        'subject': message.text,
        'name': full_name if full_name else "O'quvchi"
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
    sinf_int = int(sinf_nomi)
    sub = user_data[chat_id]['subject']
    
    # 1. VAQT LIMITINI BELGILASH
    if sinf_int <= 7:
        time_limit = 300  # 5 daqiqa
    elif sinf_int <= 9:
        time_limit = 600  # 10 daqiqa
    else:
        time_limit = 900  # 15 daqiqa

    bases = {"Matematika": matematika_test_base, "English": english_test_base, "Biologiya": biology_test_base, "Tarix": tarix_test_base}
    questions = bases[sub].get(sinf_nomi)
    
    if questions:
        q_list = random.sample(questions, min(len(questions), 10))
        user_data[chat_id].update({
            'questions': q_list, 'score': 0, 'current_q': 0, 
            'sinf': sinf_nomi, 'start_time': time.time(),
            'time_limit': time_limit
        })
        
        bot.send_message(chat_id, f"🚀 Test boshlandi!\n⏱ Limit: <b>{time_limit // 60} daqiqa</b>. Omad!", parse_mode="HTML")
        send_question(chat_id)
    else:
        bot.send_message(chat_id, "Hozircha savollar yuklanmagan.")

def send_question(chat_id):
    data = user_data[chat_id]
    q = data['questions'][data['current_q']]
    markup = types.InlineKeyboardMarkup()
    opts = q['o'].copy()
    random.shuffle(opts)
    for o in opts:
        markup.add(types.InlineKeyboardButton(o, callback_data="correct" if o == q['a'] else "wrong"))
    bot.send_message(chat_id, f"<b>{data['current_q'] + 1}-savol:</b>\n\n{q['q']}", reply_markup=markup, parse_mode="HTML")

@bot.callback_query_handler(func=lambda call: call.data in ["correct", "wrong"])
def handle_answer(call):
    chat_id = call.message.chat.id
    if chat_id not in user_data: return

    if call.data == "correct": user_data[chat_id]['score'] += 1
    user_data[chat_id]['current_q'] += 1
    
    try: bot.delete_message(chat_id, call.message.message_id)
    except: pass
    
    data = user_data[chat_id]
    if data['current_q'] < len(data['questions']):
        send_question(chat_id)
    else:
        # TEST YAKUNLANDI
        total_time = int(time.time() - data['start_time'])
        score = data['score']
        sinf = int(data['sinf'])
        sub = data['subject']
        time_limit = data['time_limit']
        
        rating_points = round(score * (1 + (sinf - 5) * 0.1), 1)

        # Reytingni yangilash
        if chat_id not in leaderboards[sub] or rating_points > leaderboards[sub][chat_id]['rating']:
            leaderboards[sub][chat_id] = {'name': data['name'], 'rating': rating_points, 'time': total_time}

        res_msg = (f"<b>🏁 Test yakunlandi!</b>\n\n✅ To'g'ri: {score}/10\n"
                   f"🏆 Ball: {rating_points}\n⏱ Vaqt: {total_time}s / {time_limit}s")
        bot.send_message(chat_id, res_msg, parse_mode="HTML")

        # 2. SERTIFIKAT VA VAQT TEKSHIROVI
        if score == 10:
            if total_time <= time_limit:
                bot.send_message(chat_id, "Ajoyib! Limit ichida ulgurdingiz. ⏳")
                cert = create_certificate(data['name'], sub, score, sinf)
                if cert:
                    bot.send_photo(chat_id, cert, caption=f"Tabriklaymiz {data['name']}! 🏆")
            else:
                bot.send_message(chat_id, f"😔 10/10 ball! Lekin {time_limit // 60} daqiqalik limitdan o'tib ketdingiz. Sertifikat berilmadi.")
        
        start(call.message)

@bot.callback_query_handler(func=lambda call: call.data.startswith("lb_"))
def handle_lb_view(call):
    sub = call.data.split("_")[1]
    lb = leaderboards.get(sub, {})
    if not lb:
        bot.answer_callback_query(call.id, "Reyting bo'sh.")
        return
    sorted_lb = sorted(lb.items(), key=lambda x: x[1]['rating'], reverse=True)
    text = f"<b>🏆 {sub} Reytingi:</b>\n\n"
    for i, (uid, d) in enumerate(sorted_lb[:10], 1):
        text += f"{i}. {d['name']} — {d['rating']} ball ({d['time']}s)\n"
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, parse_mode="HTML")

if __name__ == "__main__":
    threading.Thread(target=run_dummy_server, daemon=True).start()
    bot.infinity_polling(timeout=20, long_polling_timeout=10)
