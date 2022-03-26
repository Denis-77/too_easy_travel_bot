import time
import requests

from cls_user import User
from botrequests.photo_search import photo
from botrequests.photo_search import headers


def find_hotels(user_id: int, quality: str) -> list[dict]:
    """
    Функция делает запрос по данным собранным в классе User
    и возвращает список найденных отелей
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

    if user.command == '/lowprice':
        sort_by = 'PRICE'
    else:
        sort_by = 'PRICE_HIGHEST_FIRST'

    querystring = {
        "destinationId": user.city,
        "pageNumber": "1",
        "pageSize": user.hotels,
        "checkIn": user.check_in,
        "checkOut": user.check_out,
        "adults1": "1",
        "sortOrder": sort_by,
        "locale": user.locate,
        "currency": curr
    }

    response = requests.request(method="GET",
                                url=url,
                                headers=headers,
                                params=querystring)
    # десериализация json
    data: dict = response.json()
    # выбор нужных параметров
    hotels = []
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
        hotels.append(new_hotel)

    if user.photo == '0':
        return hotels
    else:

        # Если запрос с фото, то вызывается ф-ция поиска фото
        for hotel in hotels:

            # ограничение по скорости запросов 5/сек
            time.sleep(0.22)

            url_photo: tuple = photo(
                hotel=hotel['hotel_id'],
                num_photo=user.photo,
                quality=quality
            )
            hotel['photos'] = url_photo
        return hotels


if __name__ == '__main__':
    User.add_user(111, 'Test')
    my_user = User.users[111]
    my_user.command = '/lowprice'
    my_user.city = '1404711'
    my_user.price = None
    my_user.distance = None
    my_user.hotels = '10'
    my_user.photo = '4'
    import json
    data = find_hotels(111, 'l')
    with open('hotels22.json', 'w') as file:
        json.dump(data, file, indent=4)
