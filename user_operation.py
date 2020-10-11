# -*- coding: utf-8 -*-
# python 3.8.5

import re
from datetime import datetime
import os
import argparse
import json


class UserOperation:
    """
    Скрипт на вход принимает путь до json файла
    Считывает операции пользователя
    Выводит на экран список из 5 последних совершенных
    (выполненных) операций клиента
    """

    def __init__(self, src, path_to_no_validate=None):
        """

        :param src: путь к json
        :param path_to_no_validate: по умолчанию None, опциональный аргумент,
        путь к файлу с трассировкой ошибок переданных данных в json
        """
        self.src = os.path.normpath(src)
        self.total_data = []  # [[('2019-08-26T10:50:58.294041', {'description': 'Перевод организации',..),..]
        self.path_to_no_validate = path_to_no_validate

    def read_file(self):
        """
        Читает json файл
        выполняет normpath_to_dir
        отдает данные manage_data
        :return: None
        """
        try:
            self.normpath_to_dir()
            if not self.src.endswith('.json'):
                raise FileNotFoundError
            with open(self.src, 'r') as json_file:
                operations = json.load(json_file)
                for operation in operations:
                    self.prepare_data(operation)
        except FileNotFoundError as exc:
            print(f'json file not found {exc} type {type(exc)}')

    def normpath_to_dir(self):
        """
        если опциональный аргумент есть -> нормализует путь
        :return: None
        """
        if self.path_to_no_validate:
            self.path_to_no_validate = os.path.normpath(self.path_to_no_validate)

    def prepare_data(self, operation):
        """
        Подготавливает данные к обработке, извлекая их из operation
        проверяет условие выполнения операции
        В обработке исключения пишет в лог невалидные данные, если путь передан
        :param operation: {'id': 441945886, 'state': 'EXECUTED',..'}
        :return: None
        """
        try:
            if 'state' in operation:
                if operation['state'] != "EXECUTED":
                    raise ValueError(f'no validate {operation}')
                else:
                    if 'from' not in operation:
                        operation_from = 'No data'
                    else:
                        operation_from = operation['from']
                        data_operation = operation['date']
                        description = operation['description']
                        operation_to = operation['to']
                        operation_amount = operation['operationAmount']
                        operation_amount_sum = operation_amount['amount']
                        code = operation_amount['currency']['name']
                        self.total_data.append(
                            (data_operation,
                             {'description': description,
                              'operation_from': operation_from,
                              'operation_to': operation_to,
                              'operation_amount_sum': operation_amount_sum,
                              'code': code}
                             ))
            else:
                raise ValueError(f'no validate {operation}')

        except (ValueError, KeyError) as exc:
            if self.path_to_no_validate:
                with open(self.path_to_no_validate, "a", encoding='utf-8') as log_file:
                    log_file.write(f'Поймано исключение {exc} тип {type(exc)} \n')

    def sorted_all_data(self):
        """
        сортирует sel.total_data по дате и времени
        :return: None
        """
        self.total_data = sorted(self.total_data, reverse=True)

    def display(self):
        """
        Выводит на консоль 5 последних выполненных операций
        Выводит сумму и код денежных единиц
        Форматирует дату reformat_data_time(data_time)
        скрывает номер счета отправителя hide_number_from
        скрывает номер счет получателя hide_number_to
        :return:
        """
        for index, (data_time, other) in enumerate(self.total_data):
            if index == 5:
                break
            data_time = self.reformat_data_time(data_time)
            number_to = self.hide_number_to(other["operation_to"])
            number_from = self.hide_number_from(other["operation_from"])
            print('')
            print(f'{data_time} {other["description"]}')
            print(f'{number_from} -> {number_to}')
            print(f'{other["operation_amount_sum"]} {other["code"]}')

    def reformat_data_time(self, data_time):
        """
        Форматирует дату
        :param data_time: <str> 2018-08-19T04:27:37.904916
        :return: <str> 19.08.2018
        """
        data_time = data_time[:-16].split('-')
        data_time = datetime(year=int(data_time[0]), month=int(data_time[1]), day=int(data_time[2]))
        return data_time.strftime("%d.%m.%Y")

    def hide_number_from(self, number_from):
        """
        скрывает номер счета отправителя
        :param number_from: <str> Visa Gold 7756673469642839
        :return: <str> Visa Gold  7756 67** **** 2839
        """
        numbers = len(''.join(re.findall(r"[\d]", number_from))) - 10
        first = ''.join(re.findall(r"[\d]", number_from))[:6]
        last = ''.join(re.findall(r"[\d]", number_from))[-4:]
        code = first + "*" * numbers + last
        reformat_code = ' '.join([code[i:i + 4] for i in range(0, len(code), 4)])
        return '{} {}'.format("".join(re.findall(r"[\D]", number_from)), reformat_code)

    def hide_number_to(self, number_to):
        """
        скрывает номер счет получателя
        :param number_to: <str> Счет 48943806953649539453
        :return: <str> **9453
        """
        return ''.join(re.findall(r"[\D]", number_to)) + '**' + ''.join(re.findall(r"[\d]", number_to))[-4:]

    def run_script(self):
        """
        Запуск скрипта
        :return: None
        """
        self.read_file()
        self.sorted_all_data()
        self.display()


if __name__ == '__main__':
    manager = argparse.ArgumentParser(description='Users operation')
    manager.add_argument('-S', '--src', type=str, metavar='', help='input file')
    manager.add_argument('-B', '--bad_log', type=str, metavar='', help='no validate operation directory',
                         required=False)

    args = manager.parse_args()
    parser = UserOperation(src=args.src, path_to_no_validate=args.bad_log)
    parser.run_script()

# Примеры запуска:
# python3 user_operation.py -S 'operations.json'
# python3 user_operation.py -S 'operations.json' -B 'bad.log'
