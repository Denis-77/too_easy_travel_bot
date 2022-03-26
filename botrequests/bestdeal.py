import time
import requests
import re

from cls_user import User
from botrequests.photo_search import photo
from botrequests.photo_search import headers


def find_best_deal(user_id: int, quality: str, recursion_level: int, found: list) -> list[dict]:
    """
    Функция делает запрос по возр. цене
    :param: user_id - id пользователя
    :param: quality - качество фото
    :return hotels - список отелей
    """

    global headers

    user = User.users[user_id]

    url = "https://hotels4.p.rapidapi.com/properties/list"

    # Определение валюты от локализации
    if user.locate == 'en_US':
        curr = 'USD'
    else:
        curr = 'RUB'

    price = user.price.split('_')
    distance = user.distance.split('_')
    min_dist = float(distance[0])
    max_dist = float(distance[1])
    max_hotels = int(user.hotels)

    querystring = {
        "destinationId": user.city,
        "pageNumber": str(recursion_level),
        "pageSize": "25",
        "checkIn": user.check_in,
        "checkOut": user.check_out,
        "adults1": "1",
        "priceMin": price[0],
        "priceMax": price[1],
        "sortOrder": 'PRICE',
        "locale": user.locate,
        "currency": curr
    }
    if recursion_level > 1:
        time.sleep(0.22)
    response = requests.request(method="GET",
                                url=url,
                                headers=headers,
                                params=querystring)
    # десериализация json
    data: dict = response.json()
    print(response)

    # выбор нужных параметров
    for hotel in data['data']['body']['searchResults']['results']:
        new_hotel = {
            'hotel_id': hotel['id'],
            'hotel_name': hotel['name'],
            'hotel_star_rating': hotel['starRating'],
            'hotel_to_centre': hotel['landmarks'][0]['distance'],
            'hotel_locate': user.locate
        }
        if 'ratePlan' in hotel:
            new_hotel['hotel_price'] = (str(hotel['ratePlan']['price']['exactCurrent']) +
                            ' ' + curr)
        else:
            new_hotel['hotel_price'] = 'Цена не указана'
        hotel_address = []
        for val in hotel['address'].values():
            if isinstance(val, str):
                hotel_address.append(val)
        hotel_address = ', '.join(hotel_address)
        new_hotel['hotel_address'] = hotel_address

        # получаем дистанцию до центра
        pattern = '\d+\.?\d*'
        hotel_dist = re.findall(
            pattern=pattern, string=new_hotel['hotel_to_centre']
        )
        hotel_dist = float(hotel_dist[0])
        new_hotel['exact_dist'] = hotel_dist

        # добавляем в результат если дистанция соответствует
        if min_dist <= hotel_dist <= max_dist:
            found.append(new_hotel)
            if len(found) >= max_hotels:
                break

    if len(found) < max_hotels and recursion_level <= 3:
        recursion_level += 1
        print('Уровень рекурсии: ', recursion_level)

        find_best_deal(
            user_id=user.user_id,
            quality=quality,
            recursion_level=recursion_level,
            found=found
        )
    if user.photo == '0':
        return found
    else:

        # Если запрос с фото, то вызывается ф-ция поиска фото
        for hotel in found:

            # ограничение по скорости запросов 5/сек
            time.sleep(0.22)

            url_photo: tuple = photo(
                hotel=hotel['hotel_id'],
                num_photo=user.photo,
                quality=quality
            )
            hotel['photos'] = url_photo
        return found


if __name__ == '__main__':
    User.add_user(111, 'Test')
    my_user = User.users[111]
    my_user.command = '/bestdeal'
    my_user.city = '1404711'
    my_user.price = '1_500'
    my_user.distance = '0_5.5'
    my_user.hotels = '10'
    my_user.photo = '4'
    import json
    data = find_best_deal(111, 'l', 1, [])
    with open('hotels22.json', 'w') as file:
        json.dump(data, file, indent=4)
