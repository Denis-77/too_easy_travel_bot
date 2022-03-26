from typing import Any
import re


class User:
    """
    Класс для хранения оперативных данных
    пользователя
    :param: users(dict) - словарь содержащий все объекты
            класса
    Args:
        user_id - id пользователя
        name - никнейм
        locate - локализация
        command - введенная команда
        city - выбранный город
        price - диапазон цен
        distance - расстояние до центра города
        hotels - кол-во выводимых отелей
        photo - кол-во выводимых фото
    """
    users = {}

    def __init__(self, user_id: int, name: str) -> None:
        self.user_id = user_id
        self.name = name
        self.locate = 'en_US'
        self.command = None
        self.city = None
        self.city_name = None
        self.price = None
        self.distance = None
        self.check_in = None
        self.check_out = None
        self.hotels = None
        self.photo = None

    @classmethod
    def add_user(cls, user_id: int, name: str) -> None:
        """Метод добавления нового пользователя"""
        cls.users[user_id] = User(user_id=user_id, name=name)

    @classmethod
    def get_user(cls, user_id: int, name: str) -> 'User':
        """Метод получения объекта класса пользователя"""
        if user_id not in cls.users:
            User.add_user(user_id, name)
        return cls.users[user_id]

    @property
    def user_id(self) -> int:
        return self._user_id

    @user_id.setter
    def user_id(self, user_id: int) -> None:
        if isinstance(user_id, int):
            self._user_id = user_id
        else:
            raise ValueError('Неверное значение User.user_id')

    @property
    def locate(self) -> str:
        return self._locate

    @locate.setter
    def locate(self, locate: str) -> None:
        if locate in ('en_US', 'ru_RU', None):
            self._locate = locate
        else:
            raise ValueError('Неверное значение User.locate')

    @property
    def command(self) -> Any:
        return self._command

    @command.setter
    def command(self, command: str) -> None:
        if command in (
                '/help', '/lowprice', '/highprice',
                '/bestdeal', '/history', None
        ):
            self._command = command
        else:
            raise ValueError('Неверное значение User.command')

    @property
    def city(self) -> str:
        return self._city

    @city.setter
    def city(self, city: str) -> None:
        if city is None or city.isdigit():
            self._city = city
        else:
            raise ValueError('Неверное значение User.city')

    @property
    def price(self) -> str:
        return self._price

    @price.setter
    def price(self, price: str) -> None:
        if price is None:
            self._price = price
            return
        else:
            pattern = '\d+_\d+'
            pr_list = price.split('_')
            if (
                    re.fullmatch(pattern, price) and
                    int(pr_list[0]) <= int(pr_list[1])
            ):
                self._price = price
            else:
                raise ValueError('Неверное значение User.price')

    @property
    def distance(self) -> str:
        return self._distance

    @distance.setter
    def distance(self, distance: str) -> None:
        if distance is None:
            self._distance = distance
            return
        else:
            pattern = '\d+[.,]?\d*_\d+[.,]?\d*'
            dist_list = distance.split('_')
            if (
                    re.fullmatch(pattern, distance) and
                    float(dist_list[0]) <= float(dist_list[1])
            ):
                self._distance = distance
            else:
                raise ValueError('Неверное значение User.distance')

    @property
    def hotels(self) -> str:
        return self._hotels

    @hotels.setter
    def hotels(self, hotels: str) -> None:
        if hotels is None or hotels.isdigit():
            self._hotels = hotels
        else:
            raise ValueError('Неверное значение User.hotels')

    @property
    def photo(self) -> str:
        return self._photo

    @photo.setter
    def photo(self, photo: str) -> None:
        if photo is None or photo.isdigit():
            self._photo = photo
        else:
            raise ValueError('Неверное значение User.photo')
