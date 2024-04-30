import telebot
from telebot import types

import os
import json
import hashlib

from model import Model
from constants import ERRORS, RESPONSE


######
#
#       Configuration
#       
#####

LOCAL_PATH = "./photos/"
FIREBASE_PATH = "gallery/"

model = Model(local_path=LOCAL_PATH, firebase_path=FIREBASE_PATH)

telegram_token = json.load(open('telegram.json', 'rb'))
bot = telebot.TeleBot(telegram_token["TOKEN"])

waiting_for = {}


######
#
#       Handlers
#       
#####

# Обработчик старта
@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)

    btnInfo = types.InlineKeyboardButton("/Информация")
    btnCompare = types.InlineKeyboardButton("/Сравнение")
    btnAnalys = types.InlineKeyboardButton("/Анализ")
    btnFind = types.InlineKeyboardButton("/Поиск")
    btnAdd = types.InlineKeyboardButton("/Добавление")

    markup.add(btnInfo, btnCompare, btnAnalys, btnFind, btnAdd)

    bot.reply_to(message=message, text=RESPONSE.WAITING["hello"].format(message.from_user), reply_markup=markup)

# Обработчик для получения фотографии
@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    type: str = "NULL"
    data: str = "NULL"
    status: str = "NULL"

    chat_id = message.chat.id

    # Получаем информацию о фотографии
    file_id = message.photo[-1].file_id
    file_info = bot.get_file(file_id)
    file = bot.download_file(file_info.file_path)
    
    # Вычисляем хэш от фотографии (используем md5)
    file_hash = hashlib.md5(file).hexdigest()
    
    if not os.path.exists('photos'):
        os.makedirs('photos')
    
    absolute_path = f'photos/{file_hash}.jpg'

    # Сохраняем фотографию с использованием ее хэша в качестве имени файла
    with open(absolute_path, 'wb') as new_file:
        new_file.write(file)

    if chat_id in waiting_for:
        waiting_for[chat_id]['count'] -= 1

        if waiting_for[chat_id]['need'] == 1 and waiting_for[chat_id]['count'] == 0:
            bot.reply_to(message, RESPONSE.PROCESS["getPhoto"])

            if waiting_for[chat_id]["type"] == "ANAL":
                whatTheProcess = RESPONSE.PROCESS["processAnal"]
            elif waiting_for[chat_id]["type"] == "FIND":
                whatTheProcess = RESPONSE.PROCESS["processFind"]
            elif waiting_for[chat_id]["type"] == "ADD":
                whatTheProcess = RESPONSE.PROCESS["processAdd"]
            
            bot.send_message(chat_id, whatTheProcess)
            type, data, status = waiting_for[chat_id]['function'](absolute_path)
            del waiting_for[chat_id] # Очищаем очередь

        elif waiting_for[chat_id]['need'] == 2 and waiting_for[chat_id]['count'] == 1:
            waiting_for[chat_id]['photo1'] = absolute_path
            bot.reply_to(message, RESPONSE.WAITING["wait2Photo"])
            return
        
        elif waiting_for[chat_id]['need'] == 2 and waiting_for[chat_id]['count'] == 0:
            absolute_path_photo_1 = waiting_for[chat_id]['photo1']
            bot.reply_to(message, RESPONSE.PROCESS["getAllPhoto"])
            bot.send_message(chat_id, RESPONSE.PROCESS["processVerif"])
            type, data, status = waiting_for[chat_id]['function'](absolute_path_photo_1, absolute_path)
            del waiting_for[chat_id] # Очищаем очередь

        else:
            print(ERRORS.CLIENT["handlerPhoto"])
    else:
        bot.send_message(chat_id, RESPONSE.ERRORS["noOptions"])

    if status == "ERR":
        bot.send_message(chat_id, text=RESPONSE.ERRORS["noFace"])
        if type == "FIND":
            print(ERRORS.CLIENT["rejFind"])
        elif type == "ANLS":
            print(ERRORS.CLIENT["rejAnal"])
        elif type == "CMPR":
            print(ERRORS.CLIENT["rejCmpr"])
        elif type == "ADD":
            print(ERRORS.CLIENT["rejAdd"])
        else:
            print(ERRORS.CLIENT["noType"])
    elif status == "OK":
        if type == "FIND":
            bot.send_photo(chat_id=chat_id, photo=open(LOCAL_PATH+data[0][1], 'rb'))
            bot.send_photo(chat_id=chat_id, photo=open(LOCAL_PATH+data[1][1], 'rb'))
            bot.send_message(chat_id, RESPONSE.WAITING["take2Photo"])
        elif type == "ANLS":
            bot.send_message(chat_id, data)
        elif type == "CMPR":
            bot.send_message(chat_id, data)
        elif type == "ADD":
            bot.send_message(chat_id, data)
        else:
            print(ERRORS.CLIENT["noType"])
    else:
        print(ERRORS.CLIENT["noStatus"])

def verifyCommand(chat_id):
    # Какая-то команда уже находится в очереди?
    if chat_id in waiting_for:
        reject = ""
        if waiting_for[chat_id]["type"] == "CMPR":
            reject = RESPONSE.ERRORS["rejectCmpr"]
        elif waiting_for[chat_id]["type"] == "ANAL":
            reject = RESPONSE.ERRORS["rejectAnal"]
        elif waiting_for[chat_id]["type"] == "FIND":
            reject = RESPONSE.ERRORS["rejectFind"]
        elif waiting_for[chat_id]["type"] == "ADD":
            reject = RESPONSE.ERRORS["rejectAdd"]
        del waiting_for[chat_id]
        return reject
    return None


######
#
#       Buttons
#       
#####
        
@bot.message_handler(commands=["Информация"])
def info_btn(message):
    chat_id = message.chat.id
    bot.send_message(chat_id=chat_id, text=RESPONSE.COMMANDS["info"])


@bot.message_handler(commands=["Сравнение"])
def compare_btn(message):
    chat_id = message.chat.id

    isAlready = verifyCommand(chat_id)
    if isAlready != None:
        bot.send_message(chat_id=chat_id, text=isAlready)

    waiting_for[chat_id] = {'need': 2, 'count': 2, 'type': 'CMPR', 'function': model.compare_photos}
    bot.send_message(chat_id=chat_id, text=RESPONSE.COMMANDS["compare"])  


@bot.message_handler(commands=['Анализ'])
def analysis_btn(message):
    chat_id = message.chat.id

    isAlready = verifyCommand(chat_id)
    if isAlready != None:
        bot.send_message(chat_id=chat_id, text=isAlready)

    waiting_for[chat_id] = {'need': 1, 'count': 1, 'type': 'ANAL', 'function': model.analysis_photo}
    bot.send_message(chat_id=chat_id, text=RESPONSE.COMMANDS["analysis"])  


@bot.message_handler(commands=['Поиск'])
def find_btn(message):
    chat_id = message.chat.id

    isAlready = verifyCommand(chat_id)
    if isAlready != None:
        bot.send_message(chat_id=chat_id, text=isAlready)

    waiting_for[chat_id] = {'need': 1, 'count': 1, 'type': 'FIND', 'function': model.find_photo}
    bot.send_message(chat_id=chat_id, text=RESPONSE.COMMANDS["find"])


@bot.message_handler(commands=['Добавление'])
def add_btn(message):
    chat_id = message.chat.id

    isAlready = verifyCommand(chat_id)
    if isAlready != None:
        bot.send_message(chat_id=chat_id, text=isAlready)

    waiting_for[chat_id] = {'need': 1, 'count': 1, 'type': 'ADD', 'function': model.add_photo}
    bot.send_message(chat_id=chat_id, text=RESPONSE.COMMANDS["add"])


bot.polling(none_stop=True)

