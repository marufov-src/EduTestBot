import os
import telebot
import random
from telebot import types
from data import matematika_test_base, english_test_base, biology_test_base, tarix_test_base

TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(TOKEN)
user_data = {}

@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("Matematika", "English", "Biologiya", "Tarix")
    bot.send_message(message.chat.id, "Salom! Fanlardan birini tanlang:", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text in ["Matematika", "English", "Biologiya", "Tarix"])
def subject(message):
    user_data[message.chat.id] = {'subject': message.text}
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btns = [types.KeyboardButton(f"{i}-sinf") for i in range(5, 12)]
    markup.add(*btns)
    bot.send_message(message.chat.id, f"{message.text} fanini tanladingiz. Sinfni belgilang:", reply_markup=markup)

@bot.message_handler(func=lambda m: "sinf" in m.text)
def select_class(message):
    chat_id = message.chat.id
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
        # Savollarni nusxalab, aralashtirib olamiz
        q_list = random.sample(questions, len(questions)) 
        user_data[chat_id].update({'questions': q_list, 'score': 0, 'current_q': 0})
        send_q(chat_id)

def send_q(chat_id):
    data = user_data[chat_id]
    current_index = data['current_q']
    q = data['questions'][current_index]
    
    # Savol raqamini shu yerda qo'shamiz (current_index + 1)
    question_text = f"*{current_index + 1}-savol:*\n\n{q['q']}"
    
    markup = types.InlineKeyboardMarkup()
    # Variantlarni har safar aralashtirib chiqarish (ixtiyoriy)
    options = q['o'].copy()
    random.shuffle(options)
    
    for o in options:
        markup.add(types.InlineKeyboardButton(o, callback_data="correct" if o == q['a'] else "wrong"))
    
    bot.send_message(chat_id, question_text, reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: True)
def handle_answer(call):
    chat_id = call.message.chat.id
    
    if chat_id not in user_data:
        return

    if call.data == "correct":
        user_data[chat_id]['score'] += 1
        bot.answer_callback_query(call.id, "To'g'ri! ✅")
    else:
        bot.answer_callback_query(call.id, "Noto'g'ri! ❌")

    user_data[chat_id]['current_q'] += 1
    
    # Eskisini o'chirib, yangisini yuboramiz
    bot.delete_message(chat_id, call.message.message_id)
    
    if user_data[chat_id]['current_q'] < len(user_data[chat_id]['questions']):
        send_q(chat_id)
    else:
        score = user_data[chat_id]['score']
        total = len(user_data[chat_id]['questions'])
        bot.send_message(chat_id, f"🎉 Test yakunlandi!\n\nSiz 10 tadan *{score}* tasiga to'g'ri javob berdingiz.", parse_mode="Markdown")
        # Qayta boshlash uchun menyuni ko'rsatish
        start(call.message)

bot.infinity_polling()
