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

# --- RENDER UCHUN DUMMY SERVER ---
def run_dummy_server():
    PORT = int(os.environ.get("PORT", 8080))
    class MyHandler(http.server.SimpleHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"Bot is active!")
    with socketserver.TCPServer(("", PORT), MyHandler) as httpd:
        httpd.serve_forever()

# --- SERTIFIKAT YARATISH (ENG XAVFSIZ VARIANT) ---
def create_certificate(name, subject, score, sinf):
    try:
        img = Image.open("template.jpg")
        draw = ImageDraw.Draw(img)
        W, H = img.size
        
        # Ranglar (Sertifikat bezaklariga mos tilla va to'q ko'k)
        dark_blue = (0, 32, 96) 
        gold_text = (184, 134, 11)
        gray_text = (80, 80, 80)

        # Shriftlarni o'lchami bilan yuklaymiz
        try:
            # myfont.ttf - siz yuklagan shrift nomi
            font_title = ImageFont.truetype("myfont.ttf", 90) # SERTIFIKAT so'zi uchun
            font_name = ImageFont.truetype("myfont.ttf", 110) # Ism uchun (Katta)
            font_small = ImageFont.truetype("myfont.ttf", 45) # Qolgan matnlar uchun
        except:
            # Agar shrift yuklanmasa, standart shrift
            font_title = font_name = font_small = ImageFont.load_default()

        # 1. Sarlavha: SERTIFIKAT
        title = "SERTIFIKAT"
        # Matnni markazga hisoblash
        tw = draw.textlength(title, font=font_title)
        draw.text(((W - tw) / 2, H * 0.22), title, fill=dark_blue, font=font_title)
        
        # 2. Taqdim etish so'zi
        sub_text = "Ushbu sertifikat bilan taqdirlanadi:"
        sw = draw.textlength(sub_text, font=font_small)
        draw.text(((W - sw) / 2, H * 0.38), sub_text, fill=gray_text, font=font_small)

        # 3. FOYDALANUVCHI ISMI (Asosiy urg'u)
        full_name = str(name).upper()
        nw = draw.textlength(full_name, font=font_name)
        draw.text(((W - nw) / 2, H * 0.48), full_name, fill=dark_blue, font=font_name)

        # 4. Nima uchun berilgani
        desc = f"Bilimlar bellashuvida {subject} fanidan"
        dw = draw.textlength(desc, font=font_small)
        draw.text(((W - dw) / 2, H * 0.65), desc, fill=gray_text, font=font_small)
        
        desc2 = f"ko'rsatgan 10/10 natijasi uchun."
        dw2 = draw.textlength(desc2, font=font_small)
        draw.text(((W - dw2) / 2, H * 0.72), desc2, fill=gray_text, font=font_small)

        # 5. Sana (Pastda o'ngroqda yoki markazda)
        sana = time.strftime("%d.%m.%Y")
        snw = draw.textlength(sana, font=font_small)
        draw.text(((W - snw) / 2, H * 0.85), sana, fill=gold_text, font=font_small)

        # Saqlash
        bio = io.BytesIO()
        bio.name = 'certificate.png'
        img.save(bio, 'PNG')
        bio.seek(0)
        return bio
    except Exception as e:
        print(f"Dizayn xatosi: {e}")
        return None
        
# --- BOT LOGIKASI ---
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
    # Ism va familiyani to'liq olish
    first = message.from_user.first_name if message.from_user.first_name else ""
    last = message.from_user.last_name if message.from_user.last_name else ""
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
    sub = user_data[chat_id]['subject']
    
    bases = {"Matematika": matematika_test_base, "English": english_test_base, "Biologiya": biology_test_base, "Tarix": tariax_test_base if 'tariax_test_base' in locals() else tarix_test_base}
    questions = bases[sub].get(sinf_nomi)
    
    if questions:
        q_list = random.sample(questions, min(len(questions), 10))
        user_data[chat_id].update({
            'questions': q_list, 'score': 0, 'current_q': 0, 
            'sinf': sinf_nomi, 'start_time': time.time()
        })
        send_question(chat_id)
    else:
        bot.send_message(chat_id, "Hozircha testlar yo'q.")

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
        # TEST TUGADI
        total_time = int(time.time() - data['start_time'])
        score = data['score']
        sinf = int(data['sinf'])
        sub = data['subject']
        rating_points = round(score * (1 + (sinf - 5) * 0.1), 1)

        # Reytingni yangilash
        if chat_id not in leaderboards[sub] or rating_points > leaderboards[sub][chat_id]['rating']:
            leaderboards[sub][chat_id] = {'name': data['name'], 'rating': rating_points, 'time': total_time}

        res_msg = (f"<b>🏁 Test yakunlandi!</b>\n\n✅ To'g'ri: {score}/10\n"
                   f"🏆 Reyting ball: {rating_points}\n⏱ Vaqt: {total_time} soniya")
        bot.send_message(chat_id, res_msg, parse_mode="HTML")

        # --- SERTIFIKAT YUBORISH ---
        if score == 10:
            bot.send_message(chat_id, "Ajoyib! Sertifikatingiz tayyorlanmoqda... ⏳")
            cert = create_certificate(data['name'], sub, score, sinf)
            if cert:
                bot.send_photo(chat_id, cert, caption=f"Tabriklaymiz {data['name']}! 🏆")
            else:
                bot.send_message(chat_id, "Kechirasiz, rasm yaratishda xato bo'ldi.")
        
        start(call.message)

@bot.callback_query_handler(func=lambda call: call.data.startswith("lb_"))
def handle_lb_view(call):
    sub = call.data.split("_")[1]
    lb = leaderboards.get(sub, {})
    if not lb:
        bot.answer_callback_query(call.id, "Hali natijalar yo'q.")
        return
    sorted_lb = sorted(lb.items(), key=lambda x: x[1]['rating'], reverse=True)
    text = f"<b>🏆 {sub} Reytingi:</b>\n\n"
    for i, (uid, d) in enumerate(sorted_lb[:10], 1):
        text += f"{i}. {d['name']} — {d['rating']} ball ({d['time']}s)\n"
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, parse_mode="HTML")

if __name__ == "__main__":
    threading.Thread(target=run_dummy_server, daemon=True).start()
    bot.infinity_polling(timeout=20, long_polling_timeout=10)
