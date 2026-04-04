import os
import telebot
import random
from telebot import types
from data import matematika_test_base, english_test_base, biology_test_base, tarix_test_base

# TOKENNI TO'G'RIDAN-TO'G'RI YOZMAYMIZ
# Render yoki boshqa hostingda "BOT_TOKEN" nomli o'zgaruvchi yaratasiz
TOKEN = os.environ.get("BOT_TOKEN") 
bot = telebot.TeleBot(TOKEN)

user_data = {}

@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("Matematika", "English", "Biologiya", "Tarix")
    bot.send_message(message.chat.id, "<b>Fanlardan birini tanlang:</b>", reply_markup=markup, parse_mode="HTML")

@bot.message_handler(func=lambda m: m.text in ["Matematika", "English", "Biologiya", "Tarix"])
def subject(message):
    user_data[message.chat.id] = {'subject': message.text}
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btns = [types.KeyboardButton(f"{i}-sinf") for i in range(5, 12)]
    markup.add(*btns)
    bot.send_message(message.chat.id, f"📌 {message.text}. Sinfni tanlang:", reply_markup=markup)

@bot.message_handler(func=lambda m: "sinf" in m.text)
def select_class(message):
    chat_id = message.chat.id
    if chat_id not in user_data: return
    
    sinf = message.text.split("-")[0]
    sub = user_data[chat_id]['subject']
    
    bases = {
        "Matematika": matematika_test_base,
        "English": english_test_base,
        "Biologiya": biology_test_base,
        "Tarix": tarix_test_base
    }
    
    questions = bases[sub].get(sinf)
    if questions:
        # To'liq 10 ta savolni aralashtirib olamiz
        q_list = random.sample(questions, len(questions)) 
        user_data[chat_id].update({'questions': q_list, 'score': 0, 'current_q': 0})
        send_q(chat_id)

def send_q(chat_id):
    data = user_data[chat_id]
    curr = data['current_q']
    q = data['questions'][curr]
    
    # SAVOL RAQAMINI SHU YERDA AVTOMAT QO'YAMIZ
    text = f"<b>{curr + 1}-savol:</b>\n\n{q['q']}"
    
    markup = types.InlineKeyboardMarkup()
    opts = q['o'].copy()
    random.shuffle(opts) # Variantlarni ham aralashtiramiz
    
    for o in opts:
        # Callback_data orqali to'g'ri (c) yoki noto'g'ri (w) ekanini yuboramiz
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
    
    # Eski xabarni o'chirib turish (ekran toza bo'lishi uchun)
    bot.delete_message(chat_id, call.message.message_id)
    
    if user_data[chat_id]['current_q'] < len(user_data[chat_id]['questions']):
        send_q(chat_id)
    else:
        score = user_data[chat_id]['score']
        bot.send_message(chat_id, f"<b>🏁 Test yakunlandi!</b>\n\nSiz 10 tadan <b>{score}</b> tasiga to'g'ri javob berdingiz.", parse_mode="HTML")
        start(call.message)

bot.infinity_polling()
