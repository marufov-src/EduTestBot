import telebot
from telebot import types
import random
# data.py faylingizdan barcha bazalarni chaqirib olamiz
from data import matematika_test_base, english_test_base, biology_test_base

bot = telebot.TeleBot("BOT_TOKENINGIZNI_YOZING")

# Foydalanuvchi holatini saqlash uchun lug'at
user_data = {}

@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    item1 = types.KeyboardButton("Matematika")
    item2 = types.KeyboardButton("English")
    item3 = types.KeyboardButton("Biologiya") # Yangi bo'lim
    markup.add(item1, item2, item3)
    bot.send_message(message.chat.id, "Salom! Fanlardan birini tanlang:", reply_markup=markup)

@bot.message_handler(func=lambda message: message.text in ["Matematika", "English", "Biologiya"])
def select_subject(message):
    subject = message.text
    user_data[message.chat.id] = {'subject': subject}
    
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    # 5-11 sinf tugmalari
    btns = [types.KeyboardButton(f"{i}-sinf") for i in range(5, 12)]
    markup.add(*btns)
    bot.send_message(message.chat.id, f"{subject} fanidan sinfingizni tanlang:", reply_markup=markup)

@bot.message_handler(func=lambda message: "sinf" in message.text)
def select_class(message):
    chat_id = message.chat.id
    sinf_num = message.text.split("-")[0] # "5-sinf" -> "5"
    
    if chat_id not in user_data:
        bot.send_message(chat_id, "Iltimos, avval fanni tanlang.")
        return

    subject = user_data[chat_id]['subject']
    
    # Qaysi bazadan olishni aniqlaymiz
    if subject == "Matematika":
        questions = matematika_test_base.get(sinf_num)
    elif subject == "English":
        questions = english_test_base.get(sinf_num)
    else: # Biologiya
        questions = biology_test_base.get(sinf_num)

    if questions:
        # Savollarni aralashtirib, birinchisini chiqaramiz
        random.shuffle(questions)
        user_data[chat_id]['questions'] = questions
        user_data[chat_id]['score'] = 0
        user_data[chat_id]['current_q'] = 0
        
        send_question(chat_id)
    else:
        bot.send_message(chat_id, "Kechirasiz, bu sinf uchun savollar hali yuklanmagan.")

def send_question(chat_id):
    data = user_data[chat_id]
    q_index = data['current_q']
    questions = data['questions']

    if q_index < len(questions):
        q_item = questions[q_index]
        markup = types.InlineKeyboardMarkup()
        
        # Variantlarni chiqarish
        for option in q_item['o']:
            callback_data = "correct" if option == q_item['a'] else "wrong"
            markup.add(types.InlineKeyboardButton(text=option, callback_data=callback_data))
            
        bot.send_message(chat_id, q_item['q'], reply_markup=markup)
    else:
        # Test tugaganda
        score = data['score']
        total = len(questions)
        bot.send_message(chat_id, f"Test tugadi! \nNatijangiz: {total} tadan {score} ta to'g'ri. ✅")
        # Holatni tozalash
        del user_data[chat_id]

@bot.callback_query_handler(func=lambda call: True)
def handle_answer(call):
    chat_id = call.message.chat.id
    if chat_id not in user_data: return

    if call.data == "correct":
        user_data[chat_id]['score'] += 1
        bot.answer_callback_query(call.id, "To'g'ri!")
    else:
        bot.answer_callback_query(call.id, "Xato!")

    user_data[chat_id]['current_q'] += 1
    # Keyingi savolga o'tish uchun eski xabarni o'chiramiz yoki yangilaymiz
    bot.delete_message(chat_id, call.message.message_id)
    send_question(chat_id)

bot.polling(none_stop=True)
