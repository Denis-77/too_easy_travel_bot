import os
import sqlite3
import re
from sqlite3 import Error
from cls_user import User


def request_change(query: str) -> None:
    """
    Функция для внесения изменений в БД

    :param query: запрос на языке SQL
    :return: None
    """
    try:
        with sqlite3.connect('bot_data/bot_database.db') as connection:
            cursor = connection.cursor()
            cursor.execute(query)
            connection.commit()
            print('Query executed successfully')
    except Error as err:
        print('The error "{err}" occurred'.format(err=err))


def request_extract(query: str) -> list:
    """
    Функция для извлечения информации из БД
    :param query: запрос на языке SQL
    :return: возвращает ответ БД в виде списка кортежей,
             каждый кортеж - строка ответа БД
    """
    try:
        with sqlite3.connect('bot_data/bot_database.db') as connection:
            cursor = connection.cursor()
            cursor.execute(query)
            result = cursor.fetchall()
            print('Successfully')
            print(result)
            print(type(result))
            return result
    except Error as err:
        print('The error "{err}" occurred'.format(err=err))


def create_db_dir() -> None:
    """
    Функция для создания БД
    requests - для хранения информации о запросах
    hotels - для хранения информации о найденных отелях
    connections - для связи многие ко многим(requests и hotels)
    :return: None
    """
    if not os.path.exists('bot_data/bot_database.db'):
        if not os.path.exists('bot_data'):
            os.makedirs('bot_data')
        request_change('CREATE TABLE IF NOT EXISTS requests ('
                       'id INTEGER PRIMARY KEY AUTOINCREMENT, '
                       'user_id INTEGER NOT NULL, '
                       'command VARCHAR(50), '
                       'city VARCHAR(50), '
                       'city_name VARCHAR(50), '
                       'price VARCHAR(50), '
                       'distance VARCHAR(50), '
                       'check_in VARCHAR(50), '
                       'check_out VARCHAR(50), '
                       'hotels_count INTEGER, '
                       'photo_count INTEGER, '
                       'date_time DATETIME DEFAULT CURRENT_TIMESTAMP);')
        request_change('CREATE TABLE IF NOT EXISTS hotels ('
                       'id INTEGER PRIMARY KEY AUTOINCREMENT, '
                       'hotel_id INTEGER NOT NULL, '
                       'name VARCHAR(50), '
                       'stars VARCHAR(10), '
                       'hotel_to_centre VARCHAR(20), '
                       'price VARCHAR(20), '
                       'address VARCHAR(70), '
                       'locate VARCHAR(5));')
        request_change('CREATE TABLE IF NOT EXISTS connections ('
                       'id INTEGER PRIMARY KEY AUTOINCREMENT, '
                       'request_id INTEGER NOT NULL, '
                       'hotel_id INTEGER NOT NULL, '
                       'FOREIGN KEY (request_id) REFERENCES requests (id), '
                       'FOREIGN KEY (hotel_id) REFERENCES hotels (id));')


def save_request(user_id: int, response: list) -> None:
    """
    Функция для сохранения запроса и результата
    :param user_id: id пользователя(для сохранения параметров запроса)
    :param response: список найденных отелей(для сохранения
                     параметров найденных отелей)
    :return: None
    """
    user = User.users[user_id]
    if user.command == '/bestdeal':
        request_change('INSERT INTO requests ('
                       'user_id, command, city, city_name, price, '
                       'distance, hotels_count, photo_count, check_in, check_out'
                       ') '
                       'VALUES ('
                       '{id_u}, "{com}", "{city}", "{city_name}", '
                       '"{price}", "{dist}", {hotels}, {photo}, "{c_in}", "{c_out}"'
                       ');'.format(id_u=user_id,
                                   com=user.command,
                                   city=user.city,
                                   city_name=user.city_name,
                                   price=user.price,
                                   dist=user.distance,
                                   hotels=user.hotels,
                                   photo=user.photo,
                                   c_in=user.check_in,
                                   c_out=user.check_out))
    else:
        request_change('INSERT INTO requests ('
                       'user_id, command, city, '
                       'city_name, hotels_count, photo_count, check_in, check_out'
                       ') '
                       'VALUES ('
                       '{id_u}, "{com}", "{city}", '
                       '"{city_name}", {hotels}, {photo}, "{c_in}", "{c_out}"'
                       ');'.format(id_u=user_id,
                                   com=user.command,
                                   city=user.city,
                                   city_name=user.city_name,
                                   hotels=user.hotels,
                                   photo=user.photo,
                                   c_in=user.check_in,
                                   c_out=user.check_out))

    max_id = request_extract('SELECT MAX(id) FROM requests;')
    max_id = max_id[0][0]
    for hotel in response:

        # Чтобы не сохранять один и тот же отель дважды
        hotel_id = request_extract(
            'SELECT id FROM hotels WHERE'
            ' hotel_id={hotel_id} AND'
            ' locate="{loc}";'.format(hotel_id=hotel['hotel_id'],
                                      loc=user.locate))

        # Если найден такой отель - создается его связь с запросом
        if len(hotel_id) != 0:
            hotel_id = hotel_id[0][0]
            print('найдено совпадение')
            request_change(
                'INSERT INTO connections (request_id, hotel_id)'
                'VALUES ('
                '{req_id}, {hotel_id}'
                ');'.format(req_id=max_id,
                            hotel_id=hotel_id)
            )
        else:
            pattern = ' ,'
            address = re.sub(pattern, '', hotel['hotel_address'])
            request_change('INSERT INTO hotels ('
                           'hotel_id,  name, stars, hotel_to_centre, '
                           'price, address, locate'
                           ') '
                           'VALUES ('
                           '{id_h}, "{name}", "{stars}", "{dist}", '
                           '"{price}", "{address}", "{loc}"'
                           ');'.format(id_h=hotel['hotel_id'],
                                       name=hotel['hotel_name'],
                                       stars=hotel['hotel_star_rating'],
                                       dist=hotel['hotel_to_centre'],
                                       price=hotel['hotel_price'],
                                       address=address,
                                       loc=user.locate))
            last_hot_id = request_extract(
                'SELECT MAX(id) FROM hotels;'
            )
            last_hot_id = last_hot_id[0][0]
            request_change('INSERT INTO connections (request_id, hotel_id) '
                           'VALUES ('
                           '{id_req}, {id_hotel}'
                           ');'.format(id_req=max_id,
                                       id_hotel=last_hot_id))


def history(user_id: int) -> list:
    """
    Функция получения истории поиска
    :param user_id: id пользователя
    :return: возвращает историю поиска в виде списка кортежей,
             каждый кортеж - строка ответа БД
    """
    result = request_extract(
        'SELECT '
        'requests.id, requests.command, '
        'requests.city, requests.city_name, '
        'requests.price, requests.distance, '
        'requests.hotels_count, requests.date_time, '
        'hotels.hotel_id, hotels.name, '
        'hotels.locate, requests.check_in, requests.check_out '  
        'FROM requests '
        'JOIN connections ON connections.request_id = requests.id '
        'JOIN hotels ON hotels.id = connections.hotel_id '
        'WHERE user_id = {} ORDER BY date_time DESC LIMIT 50;'.format(user_id)
    )
    print(result)
    return result


def get_save_hotel(hotel_id: int, locate: str) -> tuple:
    """
    Функция получения информации о найденном отеле
    по id отеля и локации
    :param hotel_id: id отеля
    :param locate: переменная локации
    :return: возвращает информацию об отеле в виде кортежа внутри списка
    """
    hotel_info: list = request_extract(
        'SELECT *'
        'FROM hotels WHERE hotel_id={id_h} AND '
        'locate="{loc}";'.format(id_h=hotel_id,
                                 loc=locate)
    )
    hotel_info: tuple = hotel_info[0]
    return hotel_info


if __name__ == '__main__':
    with sqlite3.connect('../bot_data/bot_database.db') as connection:
        cursor = connection.cursor()
        cursor.execute(
            'SELECT * FROM requests;'
        )
    result1 = cursor.fetchall()
    with sqlite3.connect('../bot_data/bot_database.db') as connection:
        cursor = connection.cursor()
        cursor.execute(
            'SELECT * FROM connections;'
        )
    result2 = cursor.fetchall()
    with sqlite3.connect('../bot_data/bot_database.db') as connection:
        cursor = connection.cursor()
        cursor.execute(
            'SELECT * FROM hotels;'
        )
    result3 = cursor.fetchall()
    for line in result1:
        print(line)
    for line in result2:
        print(line)
    for line in result3:
        print(line)

