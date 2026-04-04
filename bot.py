import os
import telebot
import random
from telebot import types

# data.py faylingdan barcha test bazalarini import qilamiz
try:
    from data import matematika_test_base, english_test_base, biology_test_base
except ImportError:
    print("Xato: data.py fayli topilmadi yoki unda xatolik bor!")

# Render-da 'Environment Variables' bo'limiga kiritgan 'BOT_TOKEN'ni oqiydi
TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    print("Xato: BOT_TOKEN topilmadi! Render-da 'Environment Variables'ni sozlang.")
else:
    bot = telebot.TeleBot(TOKEN)

# Foydalanuvchilarning joriy holatini saqlash uchun lug'at
user_data = {}

@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("Matematika", "English", "Biologiya")
    bot.send_message(
        message.chat.id, 
        f"Salom {message.from_user.first_name}! Test botga xush kelibsiz.\nFanni tanlang:", 
        reply_markup=markup
    )

@bot.message_handler(func=lambda message: message.text in ["Matematika", "English", "Biologiya"])
def select_subject(message):
    chat_id = message.chat.id
    user_data[chat_id] = {'subject': message.text}
    
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    # 5-11 sinflar uchun tugmalar
    btns = [types.KeyboardButton(f"{i}-sinf") for i in range(5, 12)]
    markup.add(*btns)
    bot.send_message(chat_id, f"{message.text} fanidan sinfingizni tanlang:", reply_markup=markup)

@bot.message_handler(func=lambda message: "sinf" in message.text)
def select_class(message):
    chat_id = message.chat.id
    sinf_num = message.text.split("-")[0]
    
    if chat_id not in user_data:
        bot.send_message(chat_id, "Iltimos, avval fanni tanlang.")
        return start(message)

    subject = user_data[chat_id]['subject']
    
    # Tegishli bazani tanlash
    if subject == "Matematika":
        questions = matematika_test_base.get(sinf_num)
    elif subject == "English":
        questions = english_test_base.get(sinf_num)
    elif subject == "Biologiya":
        questions = biology_test_base.get(sinf_num)
    else:
        questions = None

    if questions:
        # Savollarni aralashtirib berish
        random_questions = questions.copy()
        random.shuffle(random_questions)
        
        user_data[chat_id].update({
            'questions': random_questions,
            'score': 0,
            'current_q': 0
        })
        send_question(chat_id)
    else:
        bot.send_message(chat_id, f"Kechirasiz, {subject} fanidan {sinf_num}-sinf uchun savollar hali yuklanmagan.")

def send_question(chat_id):
    data = user_data[chat_id]
    q_index = data['current_q']
    questions = data['questions']

    if q_index < len(questions):
        q_item = questions[q_index]
        markup = types.InlineKeyboardMarkup()
        
        # Variantlarni tugma qilib chiqarish
        for option in q_item['o']:
            # Agar variant to'g'ri bo'lsa 'correct', aks holda 'wrong' jo'natiladi
            callback_data = "correct" if option == q_item['a'] else "wrong"
            markup.add(types.InlineKeyboardButton(text=option, callback_data=callback_data))
            
        bot.send_message(chat_id, q_item['q'], reply_markup=markup)
    else:
        # Test natijasini ko'rsatish
        score = data['score']
        total = len(questions)
        bot.send_message(chat_id, f"Test tugadi! 🎉\n\nNatijangiz: {total} tadan {score} ta to'g'ri javob. ✅")
        # Foydalanuvchi ma'lumotlarini tozalash
        del user_data[chat_id]

@bot.callback_query_handler(func=lambda call: True)
def handle_answer(call):
    chat_id = call.message.chat.id
    if chat_id not in user_data:
        return

    if call.data == "correct":
        user_data[chat_id]['score'] += 1
        bot.answer_callback_query(call.id, "To'g'ri! ✅")
    else:
        bot.answer_callback_query(call.id, "Xato! ❌")

    user_data[chat_id]['current_q'] += 1
    # Keyingi savolga o'tish uchun eski savolni o'chirib yuboramiz
    bot.delete_message(chat_id, call.message.message_id)
    send_question(chat_id)

# Botni ishga tushirish
if __name__ == "__main__":
    print("Bot ishga tushdi...")
    bot.infinity_polling()
