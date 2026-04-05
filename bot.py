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
active_timers = {} # Taymerlarni boshqarish uchun

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
        
        full_name = str(name).upper()
        nw = draw.textlength(full_name, font=font_name)
        draw.text(((W - nw) / 2, H * 0.42), full_name, fill=dark_blue, font=font_name)
        
        sana = time.strftime("%d.%m.%Y")
        draw.text(((W - 80) / 2, H * 0.78), sana, fill=dark_blue, font=font_small)
        
        bio = io.BytesIO()
        bio.name = 'certificate.png'
        img.save(bio, 'PNG')
        bio.seek(0)
        return bio
    except: return None

# --- AVTOMATIK TO'XTATISH FUNKSIYASI ---
def auto_stop_test(chat_id):
    if chat_id in user_data:
        data = user_data[chat_id]
        score = data['score']
        sub = data['subject']
        name = data['name']
        
        # Testni yakunlash xabari
        bot.send_message(chat_id, f"⏰ <b>VAQT TUGADI!</b>\n\nTest avtomatik ravishda yakunlandi.\n✅ Natijangiz: {score}/10", parse_mode="HTML")
        
        # Ma'lumotlarni o'chirish
        user_data.pop(chat_id, None)
        active_timers.pop(chat_id, None)
        
        # Menyuga qaytarish
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add("Matematika", "English", "Biologiya", "Tarix", "🏆 Reyting")
        bot.send_message(chat_id, "Yana urinib ko'rasizmi?", reply_markup=markup)

# --- TEST YAKUNLASH (FOYDALANUVCHI O'ZI TUGATSADA) ---
def finish_test(chat_id):
    if chat_id in user_data:
        # Taymerni to'xtatish (chunki o'quvchi o'zi ulgurdi)
        if chat_id in active_timers:
            active_timers[chat_id].cancel()
            active_timers.pop(chat_id)

        data = user_data[chat_id]
        score = data['score']
        sub = data['subject']
        name = data['name']
        sinf = data['sinf']

        bot.send_message(chat_id, f"🏁 <b>Test tugadi!</b>\n✅ Natija: {score}/10", parse_mode="HTML")

        if score == 10:
            cert = create_certificate(name, sub, score, sinf)
            if cert: bot.send_photo(chat_id, cert, caption="Tabriklaymiz! 🏆")

        user_data.pop(chat_id, None)

# --- BOT HANDLERS ---
@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("Matematika", "English", "Biologiya", "Tarix", "🏆 Reyting")
    bot.send_message(message.chat.id, "Fanlardan birini tanlang:", reply_markup=markup, parse_mode="HTML")

@bot.message_handler(func=lambda m: m.text in ["Matematika", "English", "Biologiya", "Tarix"])
def subject_select(message):
    first = message.from_user.first_name or ""
    last = message.from_user.last_name or ""
    user_data[message.chat.id] = {'subject': message.text, 'name': f"{first} {last}".strip()}
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(*[types.KeyboardButton(f"{i}-sinf") for i in range(5, 12)])
    bot.send_message(message.chat.id, "Sinfingizni tanlang:", reply_markup=markup)

@bot.message_handler(func=lambda m: "sinf" in m.text)
def select_class(message):
    chat_id = message.chat.id
    sinf_nomi = message.text.split("-")[0]
    sinf_int = int(sinf_nomi)
    
    # Vaqt limitlari
    limit = 300 if sinf_int <= 7 else 600 if sinf_int <= 9 else 900
    
    sub = user_data[chat_id]['subject']
    bases = {"Matematika": matematika_test_base, "English": english_test_base, "Biologiya": biology_test_base, "Tarix": tarix_test_base}
    questions = bases[sub].get(sinf_nomi)

    if questions:
        q_list = random.sample(questions, min(len(questions), 10))
        user_data[chat_id].update({'questions': q_list, 'score': 0, 'current_q': 0, 'sinf': sinf_nomi, 'start_time': time.time()})
        
        # --- TAYMERNI ISHGA TUSHIRISH ---
        t = threading.Timer(limit, auto_stop_test, args=[chat_id])
        t.start()
        active_timers[chat_id] = t
        
        bot.send_message(chat_id, f"🚀 Test boshlandi! {limit//60} daqiqa vaqtingiz bor.")
        send_question(chat_id)

def send_question(chat_id):
    if chat_id not in user_data: return
    data = user_data[chat_id]
    q = data['questions'][data['current_q']]
    markup = types.InlineKeyboardMarkup()
    for o in q['o']:
        markup.add(types.InlineKeyboardButton(o, callback_data="correct" if o == q['a'] else "wrong"))
    bot.send_message(chat_id, f" Savol {data['current_q']+1}:\n{q['q']}", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data in ["correct", "wrong"])
def handle_answer(call):
    chat_id = call.message.chat.id
    if chat_id not in user_data: 
        bot.answer_callback_query(call.id, "Vaqt tugagan yoki test to'xtatilgan!")
        return

    if call.data == "correct": user_data[chat_id]['score'] += 1
    user_data[chat_id]['current_q'] += 1
    
    bot.delete_message(chat_id, call.message.message_id)
    
    if user_data[chat_id]['current_q'] < 10:
        send_question(chat_id)
    else:
        finish_test(chat_id)

if __name__ == "__main__":
    threading.Thread(target=run_dummy_server, daemon=True).start()
    bot.infinity_polling()
