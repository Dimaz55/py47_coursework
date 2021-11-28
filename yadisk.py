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


class YaUploader:
    def __init__(self, token):
        self.token = token
        self.url = 'https://cloud-api.yandex.net'
        self.upload_url = '/v1/disk/resources/upload'

    def get_headers(self):
        return {
            'Content-type': 'application/json',
            'Authorization': f'OAuth {self.token}',
        }

    def _get_upload_link(self, file_path: str) -> str:
        url = self.url + self.upload_url
        upload_params = {'path': file_path, 'overwrite': 'true'}
        response = requests.get(url,
                                headers=self.get_headers(),
                                params=upload_params)
        try:
            upload_url = response.json()['href']
        except KeyError:
            if response.json()['message']:
                print('Ошибка:', response.json()['message'])
            return 'Error'
        return upload_url

    def upload(self, file_name=None, url=None):
        if url:
            params = {
                'path': file_name,
                'url': url
            }
            response = requests.post(
                self.url+self.upload_url,
                headers=self.get_headers(),
                params=params
            )
            return response

        print('Получение ссылки для загрузки...')
        if self._get_upload_link(file_name):
            with open(file_name, 'rb') as f:
                response = requests.put(self._get_upload_link(file_name),
                                        files={"file": f})
            print('Ссылка успешно получена.')
            return response.status_code
        print('Ошибка получения ссылки.')
        return 0

    def makedir(self, path):
        pathes = path.lstrip('/').split('/')  # Если указаны вложенные папки
        path = ''
        for dir in pathes:
            path += '/' + dir
            params = {
            'path': path,
            }
            response = requests.put(
                self.url + '/v1/disk/resources',
                headers=self.get_headers(),
                params=params
            )
            if 'error' in response.json():
                print('Ошибка создания папки')
                print(response.json()['error'])
                return False
        return True

    def check_dir_name(self, path):
        params = {
            'path': path,
        }
        response = requests.get(
            self.url + '/v1/disk/resources',
            headers=self.get_headers(),
            params=params
        )
        # pprint(response.json())
        if 'error' in response.json():
            return False
        elif response.json()['type'] == 'dir':
            return True
        return False
