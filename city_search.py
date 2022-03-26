from typing import Union
import requests
import re
from botrequests.photo_search import headers


def city_search(city: str, locate: str) -> Union[dict, str]:
    """
    Функция поиска городов
    :param: city - введенный пользователем запрос
    :param: locate - локализация
    """

    url = "https://hotels4.p.rapidapi.com/locations/v2/search"

    # Запасной вариант
    url2 = "https://hotels4.p.rapidapi.com/locations/search"
    if locate == 'en_US':
        querystring = {"query": city, "locale": "en_US", "currency": "USD"}
    else:
        querystring = {"query": city, "locale": "ru_RU", "currency": "RUB"}

    # Запасной вариант
    querystring2 = {"query": city, "locale": locate}

    response = requests.request(method="GET",
                                url=url,
                                headers=headers,
                                params=querystring)

    # Десериализация json
    data: dict = response.json()

    if len(data) == 0:
        print('Сайт прилег отдохнуть((')
        repeat_counter = 0
        while repeat_counter <= 10:
            repeat_counter += 1
            if repeat_counter <= 5:
                response = requests.request(method="GET",
                                            url=url,
                                            headers=headers,
                                            params=querystring)
            else:
                response = requests.request(method="GET",
                                            url=url2,
                                            headers=headers,
                                            params=querystring2)
            if len(response.json()) > 0:
                break
        if len(response.json()) == 0:
            print('Ничего не вышло')
            return 'Сайт не отвечает на запросы, попробуйте позже'

    # Приведение результата запроса к требуемому виду
    found: dict = {}
    if 'suggestions' not in data:
        return 'Город не найден'
    for city_dict in data["suggestions"][0]['entities']:
        pattern = '<[^<]*>'
        caption_list = re.split(pattern, city_dict['caption'])
        caption_str = ''.join(caption_list)
        found[city_dict['destinationId']] = caption_str
    print(found)
    return found


if __name__ == '__main__':
    found = city_search('New', 'en_US')
    for id_c, name in found.items():
        print('id_c: {type} = {id_c}, name: {type2} = {name}'.format(
            type=type(id_c),
            id_c=id_c,
            type2=type(name),
            name=name
        ))
