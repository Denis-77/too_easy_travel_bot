import requests
import time
import re
from decouple import config

headers = {
    'x-rapidapi-host': "hotels4.p.rapidapi.com",
    'x-rapidapi-key': config('x-rapidapi-key')
}


def photo(hotel: int, num_photo: str, quality: str) -> tuple:
    """
    Создает запрос на получение фото к заданному отелю
    :param: hotel - id отеля
    :param: num_photo - кол-во фото
    :param: quality - кач. фото
    :return: photos - кортеж URL фотографий
    """
    url = "https://hotels4.p.rapidapi.com/properties/get-hotel-photos"

    querystring = {"id": str(hotel)}
    print(num_photo)
    print(hotel)

    response = requests.request("GET", url, headers=headers, params=querystring)

    # десериализация json
    print(response)
    if len(response.text) == 0:
        return ()
    if response.status_code != 200:
        counter = 0
        print('Сайт вернул не 200')
        while response.status_code != 200 and counter < 2:
            counter += 1
            time.sleep(0.22)
            response = requests.request("GET", url, headers=headers, params=querystring)

    data: dict = response.json()

    if len(data) == 0:
        print('Сайт прилег отдохнуть((')
        print('На запрос фото')
        repeat_counter = 0
        while repeat_counter < 3:
            repeat_counter += 1

            response = requests.request(method="GET",
                                        url=url,
                                        headers=headers,
                                        params=querystring)
            if len(response.json()) > 0:
                break
        if len(response.json()) == 0:
            print('Ничего не вышло')
            return ()

    photos = []
    for i_photo in range(int(num_photo)):
        try:
            ph_url = data['hotelImages'][i_photo]['baseUrl']
            pattern = '{size}'
            ph_url = re.sub(pattern=pattern, repl=quality, string=ph_url)
            photos.append(ph_url)
        except IndexError:
            print('Фото меньше заданного пользователем кол-ва')
            break
        except TypeError:
            print('Сайт вернул пустой список!')
            break
        except KeyError:
            print('Сайт вернул 504')
            break
    photos = tuple(photos)
    print(photos)
    return photos
