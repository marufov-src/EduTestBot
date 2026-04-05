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

# 2. DATA IMPORT
try:
    from data import matematika_test_base, english_test_base, biology_test_base, tarix_test_base
except ImportError:
    matematika_test_base = english_test_base = biology_test_base = tarix_test_base = {}

user_data = {}
leaderboards = {"Matematika": {}, "English": {}, "Biologiya": {}, "Tarix": {}}

# --- RENDER DUMMY SERVER ---
def run_dummy_server():
    PORT = int(os.environ.get("PORT", 8080))
    class MyHandler(http.server.SimpleHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"Bot is active!")
    with socketserver.TCPServer(("", PORT), MyHandler) as httpd:
        httpd.serve_forever()

# --- SERTIFIKAT YARATISH ---
def create_certificate(name, subject, score, sinf):
    try:
        img = Image.open("template.jpg")
        draw = ImageDraw.Draw(img)
        W, H = img.size
        dark_blue = (0, 32, 96) 
        gray_text = (80, 80, 80)

        try:
            font_title = ImageFont.truetype("myfont.ttf", 35) 
            font_name = ImageFont.truetype("myfont.ttf", 45)  
            font_small = ImageFont.truetype("myfont.ttf", 25) 
        except:
            font_title = font_name = font_small = ImageFont.load_default()

        title = "SERTIFIKAT"
        tw = draw.textlength(title, font=font_title)
        draw.text(((W - tw) / 2, H * 0.18), title, fill=dark_blue, font=font_title)
        
        sub_text = "Ushbu sertifikat bilan taqdirlanadi:"
        sw = draw.textlength(sub_text, font=font_small)
        draw.text(((W - sw) / 2, H * 0.3), sub_text, fill=gray_text, font=font_small)

        full_name = str(name).upper()
        nw = draw.textlength(full_name, font=font_name)
        draw.text(((W - nw) / 2, H * 0.42), full_name, fill=dark_blue, font=font_name)

        desc = f"Bilimlar bellashuvida {subject} fanidan"
        dw = draw.textlength(desc, font=font_small)
        draw.text(((W - dw) / 2, H * 0.58), desc, fill=gray_text, font=font_small)
        
        desc2 = f"ko'rsatgan 10/10 natijasi uchun."
        dw2 = draw.textlength(desc2, font=font_small)
        draw.text(((W - dw2) / 2, H * 0.65), desc2, fill=gray_text, font=font_small)

        sana = time.strftime("%d.%m.%Y")
        snw = draw.textlength(sana, font=font_small)
        draw.text(((W - snw) / 2, H * 0.78), sana, fill=dark_blue, font=font_small)

        bio = io.BytesIO()
        bio.name = 'certificate.png'
        img.save(bio, 'PNG')
        bio.seek(0)
        return bio
    except: return None

# --- TEST YAKUNLASH FUNKSIYASI ---
def finish_test(chat_id, call, force_stop=False):
    if chat_id not in user_data: return
    data = user_data[chat_id]
    
    total_time = int(time.time() - data['start_time'])
    score = data['score']
    sinf = int(data['sinf'])
    sub = data['subject']
    time_limit = data['time_limit']
    
    # Reyting balli
    rating_points = round(score * (1 + (sinf - 5) * 0.1), 1)
    
    # Reytingni yangilash
    if chat_id not in leaderboards[sub] or rating_points > leaderboards[sub][chat_id]['rating']:
        leaderboards[sub][chat_id] = {'name': data['name'], 'rating': rating_points, 'time': total_time}

    msg = "⏰ <b>VAQT TUGADI!</b>\n\n" if force_stop else "🏁 <b>Test yakunlandi!</b>\n\n"
    msg += f"✅ To'g'ri javoblar: {score}/10\n🏆 Reyting ball: {rating_points}\n⏱ Sarflangan vaqt: {total_time}s"
    
    bot.send_message(chat_id, msg, parse_mode="HTML")

    # Sertifikat tekshiruvi (Faqat vaqtida ulgurgan va 10/10 yig'ganlarga)
    if score == 10 and total_time <= time_limit:
        bot.send_message(chat_id, "Ajoyib! Limit ichida 10/10 natija! ⏳")
        cert = create_certificate(data['name'], sub, score, sinf)
        if cert: bot.send_photo(chat_id, cert)
    elif score == 10 and total_time > time_limit:
        bot.send_message(chat_id, "Siz 10/10 yig'dingiz, lekin vaqt limitidan o'tib ketganingiz uchun sertifikat berilmadi. ✨")

    user_data.pop(chat_id)
    start(call.message)

# --- BOT HANDLERS ---
@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("Matematika", "English", "Biologiya", "Tarix")
    markup.add("🏆 Reyting")
    bot.send_message(message.chat.id, "<b>Fanlardan birini tanlang:</b>", reply_markup=markup, parse_mode="HTML")

@bot.message_handler(func=lambda m: m.text in ["Matematika", "English", "Biologiya", "Tarix"])
def subject_select(message):
    first = message.from_user.first_name or ""
    last = message.from_user.last_name or ""
    user_data[message.chat.id] = {'subject': message.text, 'name': f"{first} {last}".strip() or "O'quvchi"}
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(*[types.KeyboardButton(f"{i}-sinf") for i in range(5, 12)])
    bot.send_message(message.chat.id, f"📌 {message.text}. Sinvingizni tanlang:", reply_markup=markup)

@bot.message_handler(func=lambda m: "sinf" in m.text)
def select_class(message):
    chat_id = message.chat.id
    if chat_id not in user_data: return start(message)
    sinf_nomi = message.text.split("-")[0]
    sinf_int = int(sinf_nomi)
    
    # Vaqt limitlari
    if sinf_int <= 7: limit = 300
    elif sinf_int <= 9: limit = 600
    else: limit = 900

    sub = user_data[chat_id]['subject']
    bases = {"Matematika": matematika_test_base, "English": english_test_base, "Biologiya": biology_test_base, "Tarix": tarix_test_base}
    questions = bases[sub].get(sinf_nomi)
    
    if questions:
        q_list = random.sample(questions, min(len(questions), 10))
        user_data[chat_id].update({'questions': q_list, 'score': 0, 'current_q': 0, 'sinf': sinf_nomi, 'start_time': time.time(), 'time_limit': limit})
        bot.send_message(chat_id, f"🚀 Test boshlandi! Limit: {limit // 60} daqiqa.")
        send_question(chat_id)
    else:
        bot.send_message(chat_id, "Testlar topilmadi.")

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

    # --- VAQT TEKSHIROVI (MUHIM!) ---
    data = user_data[chat_id]
    if int(time.time() - data['start_time']) > data['time_limit']:
        try: bot.delete_message(chat_id, call.message.message_id)
        except: pass
        return finish_test(chat_id, call, force_stop=True)

    if call.data == "correct": user_data[chat_id]['score'] += 1
    user_data[chat_id]['current_q'] += 1
    
    try: bot.delete_message(chat_id, call.message.message_id)
    except: pass
    
    if user_data[chat_id]['current_q'] < len(user_data[chat_id]['questions']):
        send_question(chat_id)
    else:
        finish_test(chat_id, call)

@bot.callback_query_handler(func=lambda call: call.data.startswith("lb_"))
def handle_lb_view(call):
    sub = call.data.split("_")[1]
    lb = leaderboards.get(sub, {})
    if not lb: return bot.answer_callback_query(call.id, "Bo'sh")
    sorted_lb = sorted(lb.items(), key=lambda x: x[1]['rating'], reverse=True)
    text = f"<b>🏆 {sub} Reytingi:</b>\n\n"
    for i, (uid, d) in enumerate(sorted_lb[:10], 1):
        text += f"{i}. {d['name']} — {d['rating']} ball ({d['time']}s)\n"
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, parse_mode="HTML")

if __name__ == "__main__":
    threading.Thread(target=run_dummy_server, daemon=True).start()
    bot.infinity_polling()
