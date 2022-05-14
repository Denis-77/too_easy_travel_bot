import datetime
import logging
import telebot
import re

from telegram_bot_calendar import DetailedTelegramCalendar, LSTEP
from decouple import config
from telebot import custom_filters, types

from botrequests.photo_search import photo
from botrequests.low_high_price import find_hotels
from botrequests.bestdeal import find_best_deal
from botrequests.history import create_db_dir
from botrequests.history import save_request
from botrequests.history import history
from botrequests.history import get_save_hotel
from cls_user import User
from city_search import city_search

create_db_dir()

bot = telebot.TeleBot(config('TooEasy_Travel_Bot'))


MAX_HOTELS: int = 10
MAX_PHOTO: int = 5
QUALITY: str = 's'
BETTER_QUALITY: str = 'b'
TIME_ZONE: float = 3.0   # hours

rus = {'year': 'год',
       'month': 'месяц',
       'day': 'день'}


@bot.message_handler(commands=['start'])
def greetings(message: telebot.types.Message) -> None:
    """
    Вызывается при вводе команды 'start',
    создает объект User если еще не создан,
    обнуляет состояние(state)
    выводит текст приветствия список доступных команд,
    добавляет кнопки с командами
    """

    if message.from_user.id not in User.users:
        User.add_user(message.from_user.id, message.from_user.first_name)
    bot.set_state(message.from_user.id, 0)
    bot.send_message(message.from_user.id,
                     'Привет, я бот Too Easy Travel и я найду тебе'
                     ' подходящий отель\n'
                     '/help - список допустимых команд\n')


@bot.message_handler(commands=[
    'help', 'lowprice', 'highprice', 'bestdeal', 'history'
])
def get_command_messages(message: telebot.types.Message) -> None:
    """
    Вызывается при вводе команд:
    'help', 'lowprice', 'highprice', 'bestdeal', 'history'
    создает объект User если еще не создан
    """
    if message.from_user.id not in User.users:
        User.add_user(message.from_user.id, message.from_user.first_name)
    if message.text == '/help':
        """
        При вводе команды 'help' отправляет сообщение
        со списком доступных команд
        """
        bot.send_message(message.from_user.id,
                         'Вы можете обращаться ко мне через'
                         ' следующие команды:\n'
                         '/help - список допустимых команд\n'
                         '/lowprice - поиск самых дешевых отелей\n'
                         '/highprice - поиск самых дорогих отелей\n'
                         '/bestdeal - поиск отелей по цене и близости к центру города\n'
                         '/history - история поиска\n'
                         'Привет - приветствие')
        bot.set_state(message.from_user.id, 0)

    elif message.text == '/history':
        user_history = history(message.from_user.id)
        print(user_history)
        request_id = 0
        text = '*'
        keyboard = types.InlineKeyboardMarkup()
        for num, line in enumerate(user_history):

            if line[0] != request_id:
                if num != 0:
                    bot.send_message(message.from_user.id, text=text, reply_markup=keyboard)
                    keyboard = types.InlineKeyboardMarkup()
                request_id = line[0]
                pattern = '\d+'
                req_date_list = re.findall(pattern=pattern, string=line[7])
                dt = datetime.datetime(int(req_date_list[0]),
                                       int(req_date_list[1]),
                                       int(req_date_list[2]),
                                       int(req_date_list[3]),
                                       int(req_date_list[4]),
                                       int(req_date_list[5]))
                dt = dt + datetime.timedelta(hours=TIME_ZONE)
                text = (
                    'Дата/время: {dt}\n'
                    'Введенная команда: {com},\n'
                    'город: {city},\n'
                    'дата заселения: {c_in},\n'
                    'дата выезда: {c_out},\n'
                    'количество отелей: {count}'.format(dt=dt,
                                                        com=line[1],
                                                        city=line[3],
                                                        count=line[6],
                                                        c_in=line[11],
                                                        c_out=line[12]))
                if line[1] == '/bestdeal':
                    price = line[4].split('_')
                    dist = line[5].split('_')
                    text += (
                        '\nЦена: от {pr_min} до {pr_max},\n'
                        'Дистанция: от {dist_min} до {dist_max}'.format(
                            pr_min=price[0],
                            pr_max=price[1],
                            dist_min=dist[0],
                            dist_max=dist[1]
                        )
                    )
            hotel_id: int = line[8]
            name = line[9]
            locate = line[10]
            keyboard.add(types.InlineKeyboardButton(text=name,
                                                    callback_data='_'.join(
                                                        ['hotel',
                                                         str(hotel_id),
                                                         locate]
                                                    )))
        bot.send_message(message.from_user.id,
                         text=text,
                         reply_markup=keyboard)
        bot.send_message(message.from_user.id,
                         'Вы можете обращаться ко мне через'
                         ' следующие команды:\n'
                         '/help - список допустимых команд\n'
                         '/lowprice - поиск самых дешевых отелей\n'
                         '/highprice - поиск самых дорогих отелей\n'
                         '/bestdeal - поиск отелей по цене и близости к центру города\n'
                         '/history - история поиска\n'
                         'Привет - приветствие')
        bot.set_state(message.from_user.id, 0)
    else:
        """
        При вводе команд:
        'lowprice', 'highprice', 'bestdeal'
        записывает команду в атрибут класса User.command,
        запрашивает город поиска,
        присваивает состояние(state) 1
        """
        user = User.users[message.from_user.id]
        user.command = message.text
        bot.send_message(user.user_id, 'Введите город поиска')
        bot.set_state(message.from_user.id, 1)


@bot.message_handler(content_types=['text'], state=1)
def get_first_step_messages(message: telebot.types.Message) -> None:
    """
    Вызывается при получении сообщения в состоянии 1
    и введенных пользователем командах:
    'lowprice', 'highprice', 'bestdeal'
    устанавливает по тексту сообщения
    локализацию пользователя, отправляет сообщение
    и локализацию в ф-цию city_search, которая возвращает dict:
    ключ - city_id
    значение - полное название найденного места
    после чего изменяет состояние на 2
    """

    pattern = '[abcdefghijklmnopqrstuvwxyz]'
    if len(re.findall(pattern, message.text.lower())) > 0:
        loc = 'en_US'
    else:
        loc = 'ru_RU'
    User.users[message.from_user.id].locate = loc

    response: dict = city_search(message.text, loc)
    if isinstance(response, str):
        bot.send_message(message.from_user.id, response)
        return

    # Варианты выводятся в виде кнопок
    keyboard = types.InlineKeyboardMarkup()
    for city_id, caption in response.items():
        back_caption: str = caption.split(',')[0]

        # Ограничение callback_data(64) уменьшено до 25 с
        # учетом добавлений
        if len(back_caption) > 25:
            back_caption = back_caption[:25]
        keyboard.add(types.InlineKeyboardButton(text=caption,
                                                callback_data='_'.join(
                                                    ['city',
                                                     city_id,
                                                     back_caption]
                                                )))

    # Доп кнопка - отмена
    keyboard.add(types.InlineKeyboardButton(text='Изменить город',
                                            callback_data='city_change'))

    # вывод вариантов в виде кнопок
    bot.send_message(message.from_user.id,
                     'Возможные варианты:\n',
                     reply_markup=keyboard)

    # изменяет на состояние 2

    bot.set_state(message.from_user.id, 2)


@bot.message_handler(content_types=['text'], state=3)
def get_second_step_messages(message: telebot.types.Message) -> None:
    """
    Вызывается при получении сообщения в состоянии 3
    только для команды bestdeal
    """

    pattern = '\d+'
    price_list = re.findall(pattern=pattern, string=message.text)
    if len(price_list) != 2:
        bot.send_message(message.from_user.id,
                         'Неверно введен диапазон цен, попробуйте еще раз:'
                         )
    else:

        print(price_list)
        if int(price_list[0]) > int(price_list[1]):
            price_list[0], price_list[1] = price_list[1], price_list[0]
        print(price_list)
        User.users[message.from_user.id].price = '_'.join(price_list)
        bot.send_message(
            message.from_user.id,
            'Выбранный диапазон цен:\nот {min_pr} до {max_pr}'.format(
                min_pr=price_list[0],
                max_pr=price_list[1]
            )
        )
        bot.send_message(
            message.from_user.id,
            'Введите диапазон  расстояния от центра, на котором '
            'должен находится отель (например через"-")'
        )
        bot.set_state(message.from_user.id, 4)


@bot.message_handler(content_types=['text'], state=4)
def distance(message: telebot.types.Message) -> None:
    """
    Вызывается при получении сообщения в состоянии 4
    только для команды bestdeal
    """

    pattern = '\d+[.,]?\d*'
    dist_list = re.findall(pattern=pattern, string=message.text)
    if len(dist_list) != 2:
        bot.send_message(message.from_user.id,
                         'Неверно введен диапазон расстояний,'
                         ' попробуйте еще раз:'
                         )
    else:

        print(dist_list)
        if float(dist_list[0]) > float(dist_list[1]):
            dist_list[0], dist_list[1] = dist_list[1], dist_list[0]
        User.users[message.from_user.id].distance = '_'.join(dist_list)
        bot.send_message(
            message.from_user.id,
            'Выбранный диапазон расстояния:'
            '\nот {min_dist} до {max_dist}'.format(
                min_dist=dist_list[0],
                max_dist=dist_list[1]
            )
        )
        bot.send_message(
            message.from_user.id,
            'Введите количество отелей которые необходимо вывести'
            '(не более {max_h}):'.format(max_h=MAX_HOTELS)
        )
        bot.set_state(message.from_user.id, 5)


@bot.message_handler(content_types=['text'], state=5)
def num_photos(message: telebot.types.Message) -> None:
    """
    Вызывается при получении сообщения в состоянии 5
    запрашивает надо ли фото с помощью добавления кнопок
    """
    if message.text.isdigit():
        user_max_hotels = message.text
        if 0 < int(user_max_hotels) <= MAX_HOTELS:
            User.users[message.from_user.id].hotels = user_max_hotels
        else:
            User.users[message.from_user.id].hotels = str(MAX_HOTELS)
        bot.set_state(message.from_user.id, 6)
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(types.InlineKeyboardButton(text='✅   ДА',
                                                callback_data='yes'))
        keyboard.add(types.InlineKeyboardButton(text='🚫   НЕТ',
                                                callback_data='no'))
        bot.send_message(message.from_user.id,
                         'Вывести результат с фото?\n',
                         reply_markup=keyboard)
    else:
        bot.send_message(
            message.from_user.id,
            'Попробуйте ввести количество отелей еще раз'
            ' (не более {max_h})'.format(max_h=MAX_HOTELS)
        )


@bot.message_handler(content_types=['text'], state=6)
def num_photos(message: telebot.types.Message) -> None:
    """
    Вызывается при получении сообщения в состоянии 6
    запрашивает у пользователя количество фото к каждому отелю
    и выводит результаты поиска
    в конце изменяет состояние на 0
    """

    if message.text.isdigit():
        user_max_ph = message.text

        # Проверка на корректность введенного числа
        if 0 < int(user_max_ph) <= MAX_PHOTO:
            User.users[message.from_user.id].photo = user_max_ph
        else:
            User.users[message.from_user.id].photo = str(MAX_PHOTO)

        # в ф-цию отправляется id пользователя и кач. фото
        # ф-ция возвращает отели в виде list[dict, dict, ...]
        bot.send_message(message.from_user.id, 'Идет поиск... ⏱')
        if User.users[message.from_user.id].command != '/bestdeal':
            response: list = find_hotels(message.from_user.id, quality=QUALITY)
        else:
            response: list = find_best_deal(message.from_user.id,
                                            quality=QUALITY,
                                            recursion_level=1,
                                            found=[])
            if len(response) == 0:
                bot.send_message(
                    message.from_user.id,
                    'По Вашему запросу ничего не найдено, попробуйте поменять'
                    ' параметры')
                bot.send_message(message.from_user.id,
                                 'Введите диапазон цен(например через "-" ):'
                                 )
                bot.set_state(message.from_user.id, 3)
                return
            response = sorted(response, key=lambda i_hotel: i_hotel['exact_dist'])

        save_request(message.from_user.id, response=response)

        for hotel in response:
            pattern = ' ,'
            address = re.sub(pattern, '', hotel['hotel_address'])
            text = '{name}\n' \
                   'рейтинг: {stars} ⭐\n' \
                   'расстояние до центра города: {centre}\n' \
                   'цена: {price}\n' \
                   'адрес: {address}'.format(name=hotel['hotel_name'],
                                             stars=hotel['hotel_star_rating'],
                                             centre=hotel['hotel_to_centre'],
                                             price=hotel['hotel_price'],
                                             address=address)

            media = []
            if len(hotel['photos']) == 0:
                # На случай если сайт не выдаст фото
                text = 'НЕТ ФОТО\n{}'.format(text)
                bot.send_message(message.from_user.id, text=text)
            elif len(hotel['photos']) == 1:
                # Если выдаст одно
                bot.send_photo(message.from_user.id, hotel['photos'][0], text)
            else:
                for num, url_photo in enumerate(hotel['photos']):
                    if num == 0:

                        # текст подписи прикрепляется к первому фото
                        media.append(types.InputMediaPhoto(
                            url_photo, caption=text)
                        )
                    else:
                        media.append(types.InputMediaPhoto(url_photo))
                try:
                    bot.send_media_group(message.from_user.id, media=media)
                except telebot.apihelper.ApiTelegramException:
                    print('Не получается отправить медиа')
                    text = 'Ошибка при получении фото\n' + text
                    bot.send_message(message.from_user.id, text=text)

            hotel_id: int = hotel['hotel_id']
            keyboard = types.InlineKeyboardMarkup()
            locate = hotel['hotel_locate']
            keyboard.add(types.InlineKeyboardButton(text='Показать',
                                                    callback_data='_'.join(
                                                        ['hotel',
                                                         str(hotel_id),
                                                         locate]
                                                    )))
            bot.send_message(message.from_user.id,
                             'Больше фотографий:',
                             reply_markup=keyboard)
        bot.send_message(message.from_user.id,
                         'Вы можете обращаться ко мне через'
                         ' следующие команды:\n'
                         '/help - список допустимых команд\n'
                         '/lowprice - поиск самых дешевых отелей\n'
                         '/highprice - поиск самых дорогих отелей\n'
                         '/bestdeal - поиск отелей по цене и близости к центру города\n'
                         '/history - история поиска\n'
                         'Привет - приветствие')
        bot.set_state(message.from_user.id, 0)

    else:
        bot.send_message(message.from_user.id,
                         'кол-во фотографий введено не корректно,'
                         'попробуйте еще раз:')


@bot.message_handler(content_types=['text'])
def get_universal_text_messages(message: telebot.types.Message) -> None:
    """
    Вызывается всегда, когда полученное сообщение не
    подходит ни под одно из условий выше.
    Создает объект класса User если его нет в списке
    """

    if message.from_user.id not in User.users:
        User.add_user(message.from_user.id, message.from_user.first_name)
    if ('привет' in message.text.lower() or
            'ghbdtn' in message.text.lower()):
        bot.send_message(message.from_user.id,
                         "Привет, чем я могу тебе помочь?")
    else:
        bot.send_message(message.from_user.id, 'я не знаю такой команды, '
                                               'попробуйте /help')


@bot.callback_query_handler(func=DetailedTelegramCalendar.func())
def callback_calendar(call: telebot.types.CallbackQuery) -> None:
    """
    Вызывается в случае получения запроса обратного вызова от
    кнопок календаря telegram_bot_calendar
    """
    result, key, step = DetailedTelegramCalendar().process(call.data)
    if not result and key:

        step = rus[LSTEP[step]]
        bot.edit_message_text(
            'Выберите {step}'.format(step=step),
            call.message.chat.id,
            call.message.message_id,
            reply_markup=key
        )
    elif result:
        bot.edit_message_text('Вы выбрали {result}'.format(result=result),
                              call.message.chat.id,
                              call.message.message_id)
        user = User.users[call.from_user.id]
        if bot.get_state(call.from_user.id) == 2:

            user.check_in = str(result)
            bot.set_state(call.from_user.id, 3)
            min_date = result
            calendar, step = DetailedTelegramCalendar(min_date=min_date).build()
            step = rus[LSTEP[step]]
            bot.send_message(call.from_user.id, 'Выезд:')
            bot.send_message(call.from_user.id,
                             "Выберите {step}".format(step=step),
                             reply_markup=calendar)
        else:
            user.check_out = str(result)
            if User.users[call.from_user.id].command == '/bestdeal':

                bot.send_message(call.from_user.id,
                                 'Введите диапазон цен(например через "-" ):'
                                 )
            else:
                bot.set_state(call.from_user.id, 5)
                bot.send_message(
                    call.from_user.id,
                    'Введите количество отелей которые необходимо вывести'
                    '(не более {max_h}):'.format(max_h=MAX_HOTELS)
                )


@bot.callback_query_handler(func=lambda call: True)
def callback(call: telebot.types.CallbackQuery) -> None:
    """
    Обработка входящих запросов обратного вызова
    от нажатых пользователем кнопок прикрепленных к сообщению
    """
    if call.data.startswith('city'):
        # Префикс city - присутствует в кнопках выбора города

        # Замена кнопок выбора города сообщением об успешном выборе
        bot.edit_message_text(chat_id=call.message.chat.id,
                              message_id=call.message.message_id,
                              text='👌')
        if call.data == 'city_change':

            # Обработка кнопки изменить город поиска
            bot.send_message(call.from_user.id, 'Отменено!')
            bot.set_state(call.from_user.id, 1)
            bot.send_message(call.from_user.id, 'Введите город поиска:')
        else:

            # Обработка выбранного пользователем города
            city: list = call.data.split('_')
            city_id: str = city[1]
            city_name: str = city[2]
            User.users[call.from_user.id].city = city_id
            User.users[call.from_user.id].city_name = city_name
            bot.send_message(
                call.from_user.id, 'Вы выбрали:\n{city}'.format(
                    city=city_name
                )
            )
            today = datetime.date.today()
            calendar, step = DetailedTelegramCalendar(min_date=today).build()
            step = rus[LSTEP[step]]
            bot.send_message(call.from_user.id, 'Дата заезда:')

            bot.send_message(call.from_user.id,
                             "Выберите {step}".format(step=step),
                             reply_markup=calendar)

    elif call.data.startswith('hotel'):
        # Префикс hotel - присутствует в кнопках выбора отеля

        # Замена кнопок выбора отеля сообщением об успешном выборе
        bot.edit_message_text(chat_id=call.message.chat.id,
                              message_id=call.message.message_id,
                              text='Смотри ниже   ⬇️')
        hotel_info: list = call.data.split('_')
        print(call.data)
        hotel_id = int(hotel_info[1])
        locate = '_'.join(hotel_info[2:])
        more_photo: tuple = photo(hotel_id, '10', quality=BETTER_QUALITY)
        media = []
        hotel_data = get_save_hotel(hotel_id, locate)
        text = '{name}\n' \
               'рейтинг: {stars} ⭐\n' \
               'расстояние до центра города: {centre}\n' \
               'цена: {price}\n' \
               'адрес: {address}'.format(name=hotel_data[2],
                                         stars=hotel_data[3],
                                         centre=hotel_data[4],
                                         price=hotel_data[5],
                                         address=hotel_data[6])
        if len(more_photo) == 0:
            # На случай если сайт не выдаст фото
            text = 'НЕТ ФОТО\n' + text
            bot.send_message(call.from_user.id, text=text)
        elif len(more_photo) == 1:
            # Если выдаст одно
            bot.send_photo(call.from_user.id, more_photo[0], caption=text)
        else:
            for num, url_photo in enumerate(more_photo):
                if num == 0:
                    media.append(types.InputMediaPhoto(url_photo, caption=text))
                else:
                    media.append(types.InputMediaPhoto(url_photo))

            try:
                bot.send_media_group(call.from_user.id, media=media)
            except telebot.apihelper.ApiTelegramException:
                print('Не получается отправить медиа')
                text = 'Ошибка при получении фото\n'
                bot.send_message(call.from_user.id, text=text)

    # Обработка кнопок выбора с фотографиями или без
    elif call.data == 'yes':

        # Изменения состояния на 6
        bot.set_state(call.from_user.id, 6)

        # Удаление кнопок
        bot.delete_message(chat_id=call.message.chat.id,
                           message_id=call.message.message_id)
        bot.send_message(
            call.from_user.id,
            'Сколько фото вывести для каждого?(не более {max_ph})'.format(
                max_ph=MAX_PHOTO
            )
        )
    else:
        # Обработка выбора 'вывод без фото'

        # Удаление кнопок
        bot.delete_message(chat_id=call.message.chat.id,
                           message_id=call.message.message_id)
        User.users[call.from_user.id].photo = '0'

        # Так как выбран 'вывод без фото' на этом этапе
        # выводится результат поиска

        bot.send_message(call.from_user.id, 'Идет поиск... ⏱')
        if User.users[call.from_user.id].command != '/bestdeal':
            response: list = find_hotels(call.from_user.id, quality=QUALITY)
        else:
            response: list = find_best_deal(call.from_user.id,
                                            quality=QUALITY,
                                            recursion_level=1,
                                            found=[])
            if len(response) == 0:
                bot.send_message(
                    call.from_user.id,
                    'По Вашему запросу ничего не найдено, попробуйте поменять'
                    ' параметры')
                bot.send_message(call.from_user.id,
                                 'Введите диапазон цен(например через "-" ):'
                                 )
                bot.set_state(call.from_user.id, 3)
                return
            response = sorted(response, key=lambda x: x['exact_dist'])

        save_request(call.from_user.id, response=response)

        for hotel in response:
            pattern = ' ,'
            address = re.sub(pattern, '', hotel['hotel_address'])
            text = '{name}\n' \
                   'рейтинг: {stars} ⭐\n' \
                   'расстояние: {centre}\n' \
                   'цена: {price}\n' \
                   'адрес: {address}'.format(name=hotel['hotel_name'],
                                             stars=hotel['hotel_star_rating'],
                                             centre=hotel['hotel_to_centre'],
                                             price=hotel['hotel_price'],
                                             address=address)
            bot.send_message(call.from_user.id, text)
            hotel_id: int = hotel['hotel_id']
            locate = hotel['hotel_locate']
            keyboard = types.InlineKeyboardMarkup()
            keyboard.add(types.InlineKeyboardButton(text='Показать',
                                                    callback_data='_'.join(
                                                        ['hotel',
                                                         str(hotel_id),
                                                         locate]
                                                    )))
            bot.send_message(call.from_user.id,
                             'Показать фотографии?',
                             reply_markup=keyboard)

        bot.send_message(call.from_user.id,
                         'Вы можете обращаться ко мне через'
                         ' следующие команды:\n'
                         '/help - список допустимых команд\n'
                         '/lowprice - поиск самых дешевых отелей\n'
                         '/highprice - поиск самых дорогих отелей\n'
                         '/bestdeal - поиск отелей по цене и близости к центру города\n'
                         '/history - история поиска\n'
                         'Привет - приветствие')
        bot.set_state(call.from_user.id, 0)


logging.basicConfig(
    filename='excs.log', filemode='a',
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


bot.add_custom_filter(custom_filters.StateFilter(bot))
bot.polling(none_stop=True, interval=0)
