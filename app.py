import telebot
from telebot import types

import os
import json
import hashlib

from model import Model


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

    bot.reply_to(message=message, text="Привет, {0.first_name}, рад знакомству!\nРекомендую перед началом ознакомиться с моими возможностями по кнопке \"Информация\".".format(message.from_user), reply_markup=markup)

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
            bot.reply_to(message, "Я получил фотографию. Спасибо!")
            # bot.send_message(message, f"Подождите немного! Происходит обаботка.. ⏳")
            type, data, status = waiting_for[chat_id]['function'](absolute_path)
            del waiting_for[chat_id] # Очищаем очередь

        elif waiting_for[chat_id]['need'] == 2 and waiting_for[chat_id]['count'] == 1:
            waiting_for[chat_id]['photo1'] = absolute_path
            bot.reply_to(message, "Отлично, я получил первую фотографию! Отправляйте вторую")
            return
        
        elif waiting_for[chat_id]['need'] == 2 and waiting_for[chat_id]['count'] == 0:
            absolute_path_photo_1 = waiting_for[chat_id]['photo1']
            bot.reply_to(message, "Я получил вторую фотографию. Спасибо!")
            # bot.send_message(message, "Подождите немного! Происходит верификация человека.. ⏳")
            type, data, status = waiting_for[chat_id]['function'](absolute_path_photo_1, absolute_path)
            del waiting_for[chat_id] # Очищаем очередь

        else:
            print(f"ERROR: Возникла ошибка при добавлении фотографии! Кол-во добавленных != Кол-во требуемых \n")
    else:
        bot.send_message(chat_id, "Пожалуйста, сначала выберите любую из опций бота")

    if status == "ERR":
        if type == "FIND":
            bot.send_message(chat_id, text=f'{type} + ERROR')
        elif type == "ANLS":
            bot.send_message(chat_id, text=f'{type} + ERROR')
        elif type == "CMPR":
            bot.send_message(chat_id, text=f'{type} + ERROR')
        elif type == "ADD":
            bot.send_message(chat_id, text=f'{type} + ERROR')
        else:
            print(f"ERROR: type ERR not define\n")
    elif status == "OK":
        if type == "FIND":
            bot.send_photo(chat_id=chat_id, photo=open(LOCAL_PATH+data[0][1], 'rb'))
            bot.send_photo(chat_id=chat_id, photo=open(LOCAL_PATH+data[1][1], 'rb'))
            bot.send_message(chat_id, 'Вот две самые близкие по смыслу изображения!')
        elif type == "ANLS":
            bot.send_message(chat_id, data)
        elif type == "CMPR":
            bot.send_message(chat_id, data)
        elif type == "ADD":
            bot.send_message(chat_id, data)
        else:
            print(f"ERROR: type ERR not define\n")
    else:
        print(f"ERROR: status ERR not define\n")

def verifyCommand(chat_id):
    # Какая-то команда уже находится в очереди?
    if chat_id in waiting_for:
        reject = ""
        if waiting_for[chat_id]["type"] == "CMPR":
            reject = "Сравнение было отменено"
        elif waiting_for[chat_id]["type"] == "ANAL":
            reject = "Анализ фотографии был отменён"
        elif waiting_for[chat_id]["type"] == "FIND":
            reject = "Поиск фотографии был отменён"
        elif waiting_for[chat_id]["type"] == "ADD":
            reject = "Добавление фотографии было отменено"
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
    bot.send_message(chat_id=chat_id, text='Этот бот разработан командой GoodAI:\n- Петросов Арсен\n- Четверина Александра\n- Уткин Тимофей\n- Шемет Александра\n- Шевченко Алексей\n\nМои возможности:\n   1) Сравнение людей на двух изображениях\n(необходимо загрузить два изображения) и бот ответит, один ли человек изображён на фотографиях.\n   2) Поиск человека по базе данных\n(необходимо загрузить одно изображение) и бот ответит двумя фотографиями с самыми похожими людьми.\n   3) Анализ человекечких признаков - пол, возраст, рассовую принадлежность и текущую эмоцю\n(необходимо отправить 1 фото)\n   4) Добавить фотографию в общую базу данных всех фотографий!\nДля выбора опций нажмите далее на соотвествующую команду')


@bot.message_handler(commands=["Сравнение"])
def compare_btn(message):
    chat_id = message.chat.id

    isAlready = verifyCommand(chat_id)
    if isAlready != None:
        bot.send_message(chat_id=chat_id, text=isAlready)

    waiting_for[chat_id] = {'need': 2, 'count': 2, 'type': 'CMPR', 'function': model.compare_photos}
    bot.send_message(chat_id=chat_id, text='Отлично, вы выбрали сравнение людей на 2-х фотографиях! Теперь отправьте две фотографии')  


@bot.message_handler(commands=['Анализ'])
def analysis_btn(message):
    chat_id = message.chat.id

    isAlready = verifyCommand(chat_id)
    if isAlready != None:
        bot.send_message(chat_id=chat_id, text=isAlready)

    waiting_for[chat_id] = {'need': 1, 'count': 1, 'type': 'ANAL', 'function': model.analysis_photo}
    bot.send_message(chat_id=chat_id, text='Отлично, вы выбрали анализ признаков человека! Теперь отправьте фотографию')  


@bot.message_handler(commands=['Поиск'])
def find_btn(message):
    chat_id = message.chat.id

    isAlready = verifyCommand(chat_id)
    if isAlready != None:
        bot.send_message(chat_id=chat_id, text=isAlready)

    waiting_for[chat_id] = {'need': 1, 'count': 1, 'type': 'FIND', 'function': model.find_photo}
    bot.send_message(chat_id=chat_id, text='Отлично, вы выбрали поиск человека! Теперь отправьте фотографию')


@bot.message_handler(commands=['Добавление'])
def add_btn(message):
    chat_id = message.chat.id

    isAlready = verifyCommand(chat_id)
    if isAlready != None:
        bot.send_message(chat_id=chat_id, text=isAlready)

    waiting_for[chat_id] = {'need': 1, 'count': 1, 'type': 'ADD', 'function': model.add_photo}
    bot.send_message(chat_id=chat_id, text='Отлично, вы выбрали поиск человека! Теперь отправьте фотографию')


bot.polling(none_stop=True)

