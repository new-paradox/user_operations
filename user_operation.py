# -*- coding: utf-8 -*-

from dataclasses import dataclass
from typing import List
import re
from datetime import datetime
import json
from operator import attrgetter


@dataclass
class BaseCurrency:
    """
    Описание и типизация базового класса currency - вложенного словаря
    объекта BaseOperationAmount;
    """
    name: str
    code: str


@dataclass
class BaseOperationAmount:
    """
    Описание и типизация базового класса operationAmount - вложенного словаря
    объекта BaseOperation;
    """
    amount: str
    currency: BaseCurrency


@dataclass
class BaseOperation:
    """
    Описание и типизация базового класса палтежной операции;
    """
    id: int
    state: str
    date: datetime
    operation_amount: BaseOperationAmount
    description: str
    from_card: str
    to_card: str


class Currency(BaseCurrency):
    """
    Инициализация объекта Currency;
    """

    def __init__(self, currency):
        self.code = currency['code']
        self.name = currency['name']


class OperationAmount(BaseOperationAmount):
    """
    Инициализация объекта OperationAmount;
    """

    def __init__(self, operation_amount):
        self.amount = operation_amount['amount']
        self.currency = Currency(operation_amount['currency'])


class Operation(BaseOperation):
    """
    Инициализация объекта Operation;
    """

    def __init__(self, operation):
        self.id = operation['id']
        self.state = operation['state']
        self.date = datetime.fromisoformat(operation['date'])
        self.operation_amount = OperationAmount(operation['operationAmount'])
        self.description = operation['description']
        self.from_card = operation['from']
        self.to_card = operation['to']


class View:
    """
    Объект служит для представления клиенту отформатированного ответа.
    На вход принимает массив из валидированных объектов Operation ->
    метод data_masking запускает цепочку методов, которые в рамках своей зоны ответсвтенности маскируют или
    форматируют участки ответа клиенту;

    Пример ответа:
    19.08.2018 Перевод организации
    7756 67** **** 2839 -> **9453
    31957.58 руб.

    Методы:
    data_masking - формирует окончательный ответ и запускает методы форматирования;
    reformat_data_time - форматирует объект типа datetime в строковое представление прим. 19.08.2018;
    hide_from - маскирует поле from в структуре данных прим. Visa Gold 7756 67** **** 2839;
    hide_to - маскирует поле to в структуре данных прим. Счет **9453;
    """

    def __init__(self, operations: List[Operation]):
        self.operations = operations

    def data_masking(self) -> str:
        result = ''
        for operation in self.operations:
            result += f'{self.reformat_data_time(date=operation.date)} {operation.description} \n' \
                      f'{self.hide_from(number_from=operation.from_card)} -> ' \
                      f'{self.hide_to(number_to=operation.to_card)}\n' \
                      f'{operation.operation_amount.amount} {operation.operation_amount.currency.code}\n\n'
        return result

    @staticmethod
    def reformat_data_time(date: datetime) -> str:
        return datetime.strftime(date, '%d.%m.%Y')

    @staticmethod
    def hide_from(number_from: str) -> str:
        numbers = len(''.join(re.findall(r"[\d]", number_from))) - 10
        first = ''.join(re.findall(r"[\d]", number_from))[:6]
        last = ''.join(re.findall(r"[\d]", number_from))[-4:]
        mask = first + "*" * numbers + last
        reformat_code = ' '.join([mask[i:i + 4] for i in range(0, len(mask), 4)])
        number_from = '{} {}'.format("".join(re.findall(r"[\D]", number_from)), reformat_code)
        return number_from.replace('  ', ' ')

    @staticmethod
    def hide_to(number_to: str) -> str:
        number_to = ''.join(re.findall(r"[\D]", number_to)) + '**' + ''.join(re.findall(r"[\d]", number_to))[-4:]
        return number_to


class Controller:
    """
    Controller обеспечивает связь между чтением файла, валидацией, сортировкой и форматированием данных:
    Парсинг файла - read_json_file(json_file);
    Валидация - validate_operations;
    Сортировка - return_last_n_operation;
    Форматирвоание и маскировка - View(self.last_n_operations).data_masking();

    Порядок работы скрипта:
    При инициализации запрашивается путь до файла .json ->
    И желаемое количество выведенных последних по дате операций count_row ->
    Дескриптор json файла передается в self.file ->

    validate_operations:
    Формируется массив из объектов Operation, OperationAmount и Currency представляющие собой структуру данных ->
    В случае если структура данных не соотвествует интерфейсу -> сработает try catch.
    Валидация происходит по атрибуту структуры даных - state, где оно должно равняться "EXECUTED" - выполнено ->
    Все валидные значения добавяться в массив operations ->

    last_n_operations:
    Производится сортировка и срез массива operations по количеству запрашиваемых последних по дате операций ->

    masking_and_return_result:
    Инициализируется объект View, он получает аргумент last_n_operations,
    Где по заданному в View шаблону маскирует данные и возвращает строковый ответ.
    """

    def __init__(self, json_file: str, count_row: int):
        self.file = read_json_file(json_file)
        self.count_row = count_row
        self.operations = self.validate_operations()
        self.last_n_operations = self.return_last_n_operation()
        self.masking_and_return_result = View(operations=self.last_n_operations).data_masking()

    def __str__(self):
        return View(operations=self.last_n_operations).data_masking()

    def validate_operations(self) -> List:
        operations = []
        for index, elem in enumerate(self.file):
            try:
                valid_elem = Operation(elem)
                if valid_elem.state == "EXECUTED":
                    operations.append(Operation(elem))

            except LookupError as exc:
                print(f'Возникла ошибка типа: {type(exc)} - {exc} в строке - {index + 1}')
        return operations

    def return_last_n_operation(self) -> List[Operation]:
        result = sorted(self.operations, key=attrgetter('date'), reverse=True)[:self.count_row]
        return result


def read_json_file(src: str):
    if not src.endswith('.json'):
        raise FileNotFoundError
    with open(src, 'r') as json_file:
        file = json.load(json_file)
        return file
