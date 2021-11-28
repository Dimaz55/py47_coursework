from time import sleep
import requests
from pprint import pprint


def loader() -> None:
    print('Загрузка файла...')
    for i in range(1, 20):
        e = '=' * i
        u = ' ' * (20-i-1)
        print(f'[{e}{u}] {i*5+5}%', end='')
        sleep(0.1)
        print('\r', end='')
    print()


def get_ya_token():
    try:
        with open('ya_token.txt') as file:
            ya_token = file.readline().strip()
    except FileNotFoundError:
        print('Файл с токеном Yandex на найден. Можете ввести вручную (0 для выхода): ')
        if ya_token == '0':
            exit()
    return ya_token


class YaUploader:
    def __init__(self, token):
        self.token = token
        self.url = 'https://cloud-api.yandex.net/v1/disk/resources/'

    def get_headers(self):
        return {
            'Content-type': 'application/json',
            'Authorization': f'OAuth {self.token}',
        }

    def _get_upload_link(self, file_path):
        url = self.url + 'upload'
        upload_params = {'path': file_path, 'overwrite': 'false'}
        run = True
        while run:
            response = requests.get(url,
                                    headers=self.get_headers(),
                                    params=upload_params)
            res = response.json()
            if 'error' in res:
                print('Ошибка:', res['message'])
                if res['description'].endswith('already exists.'):
                    ans = input('> Перезаписать файл? [y/n] ')
                    if ans in ['Y', 'y', '']:
                        upload_params['overwrite'] = 'true'
                    else:
                        return 'Error'
            else:
                upload_url = res['href']
                run = False
        return upload_url


    def upload(self, mode, path=None, url=None, target_path=None):
        """Выгружает файл с локального диска если указан только path либо с
        внешнего ресурса по адресу url в папку path на Я.Диске
        """
        params = {
            'path': path,
            'url': url,
        }
        if mode == 'remote':
            response = requests.post(
                self.url + 'upload',
                headers=self.get_headers(),
                params=params
            )
            return response

        print('> Получение ссылки для загрузки локального файла...')
        with open(path, 'rb') as f:
            try:
                response = requests.put(self._get_upload_link(target_path),
                                        files={"file": f})
            except requests.exceptions.MissingSchema:
                print('>> Отмена операции.')
                return 0
            print('>> Ссылка успешно получена.')
            print(f'>>> Файл {path} успешно загружен: Я.Диск:{target_path}')
            return response.status_code
        print('>> Ошибка получения ссылки.')
        return 0

    def makedir(self, path):
        """Создаёт папку по пути path на Я.Диске"""
        print(f'> Cоздаём путь {path} на Я.Диске...')
        pathes = path.lstrip('/').split('/')  # Если указаны вложенные папки
        path = ''
        for directory in pathes:
            path += '/' + directory
            params = {'path': path}
            response = requests.put(
                self.url,
                headers=self.get_headers(),
                params=params
            )
            if 'error' in response.json():
                print('>> Ошибка создания папки.')
                print(response.json()['error'])
                return False
        print('>> Папка успешно создана.')
        return True

    def check_dir_name(self, path):
        """Проверяет существование папки по пути path на Я.Диске"""
        params = {
            'path': path,
        }
        response = requests.get(
            self.url,
            headers=self.get_headers(),
            params=params
        )
        # pprint(response.json())
        if 'error' in response.json():
            return False
        elif response.json()['type'] == 'dir':
            return True
        return False

    def delete_dir(self, path):
        params = {
            'path': path,
        }
        response = requests.delete(
            self.url,
            headers=self.get_headers(),
            params=params
        )
        return response
