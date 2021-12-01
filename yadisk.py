import json
import requests


class YaUploader:
    def __init__(self):
        self.token = self._get_ya_token()
        self.url = 'https://cloud-api.yandex.net/v1/disk/resources/'
        self.headers = {
            'Content-type': 'application/json',
            'Authorization': f'OAuth {self.token}',
        }

    @staticmethod
    def _get_ya_token():
        with open('ya_token.txt') as file:
            ya_token = file.readline().strip()
        return ya_token

    def _get_upload_link(self, file_path):
        url = self.url + 'upload'
        upload_params = {'path': file_path, 'overwrite': 'false'}
        run = True
        while run:
            print('> Получение ссылки для загрузки локального файла...')
            try:
                response = requests.get(
                    url,
                    headers=self.headers,
                    params=upload_params
                )
            except ValueError:
                print(response.json()['error']['error_msg'])
            print('>> Ссылка успешно получена.')
            res = response.json()
            if 'error' in res:
                print('>>> Ошибка:', res['message'])
                if res['description'].endswith('already exists.'):
                    ans = input('> Перезаписать файл? [y/n] ')
                    if ans in ['Y', 'y', '']:
                        upload_params['overwrite'] = 'true'
                    else:
                        return {'error': 'Отменено'}
                else:
                    return {'error': 'Отменено'}
            else:
                run = False
        upload_url = res['href']
        return upload_url

    def upload(self, mode='local', path=None, url=None, target_path=None):
        """Выгружает файл с локального диска если указан только path либо с
        внешнего ресурса по адресу url в папку path на Я.Диске
        mode - режим выгрузки: 'remote' - с удалённых ресурсов по url,
                                остальные значения - с локального диска
        """
        params = {
            'path': path,
            'url': url,
        }
        if mode == 'remote':
            response = requests.post(
                self.url + 'upload',
                headers=self.headers,
                params=params
            )
            return response

        # Получение ссылки для загрузки локального файла
        with open(path, 'rb') as f:
            upload_link = self._get_upload_link(target_path)
            response = requests.put(
                upload_link,
                files={"file": f}
            )
            print(f'>>> Файл {path} успешно загружен: Я.Диск:{target_path}')
            return response.status_code
        return 0

    def makedir(self, path):
        """Создаёт папку по пути path на Я.Диске"""
        print(f'> Создаём путь {path} на Я.Диске...')
        pathes = path.lstrip('/').split('/')  # Если указаны вложенные папки
        path = ''
        for directory in pathes:
            path += '/' + directory
            params = {'path': path}
            if not self.check_dir_name(path):
                response = requests.put(
                    self.url,
                    headers=self.headers,
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
            headers=self.headers,
            params=params
        )
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
            headers=self.headers,
            params=params
        )
        return response

    def get_upload_dir_name(self, default_dir_name):
        """Формирование пути загрузки файлов на Я.Диск: либо из ввода пользователя,
        либо из имени по умолчанию"""
        answer = False
        while not answer:
            path = input('> Введите имя целевой папки либо нажмите Enter:')
            if path == '':
                path = default_dir_name
            # проверка существования пути path на Я.Диске
            if self.check_dir_name(path):
                ans = input(
                    '>> Папка уже существует. Записать в неё? При совпадении '
                    'имён файлы будут переименованы.[y/n] ')
                if ans in ['y', 'Y', '']:
                    break
            else:
                # разбор пути, удаление лишних слэшей
                pathes = path.lstrip('/').split('/')
                pathes = [i for i in pathes if i != '']
                path = ''
                for el in pathes:
                    path += '/' + el
                # Создаём папку на Я.Диске для дальнейшей загрузки файлов
                self.makedir(path)
                answer = True
        if path.startswith('/'):
            path = path + '/'
        else:
            path = '/' + path + '/'  # слеши для формирования полного пути
        return path


    def upload_file_list(self, photos_list, upload_path):
        # Кол-во фото + log.json
        print(f'Количество файлов для выгрузки: {len(photos_list) + 1}')
        json_list = []
        for file_name, prop in photos_list.items():
            path_to_file = upload_path + file_name
            print(f"> Загружаем файл по ссылке: {prop['url'][:50] + '...'}")

            self.upload('remote', path_to_file, url=prop['url'])
            print(f'>> Файл успешно сохранён: Я.Диск:{path_to_file}')
            json_list.append({'file_name': file_name, 'size': prop['size_type']})

        with open('log.json', 'w') as file:
            json.dump(json_list, file)
        self.upload('local', 'log.json', target_path=upload_path + 'log.json')
        return None
