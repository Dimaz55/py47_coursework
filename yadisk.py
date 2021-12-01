from time import sleep
import requests


def check_path_validity(path):
    try:
        with open(path, 'r'):
            pass
    except FileNotFoundError:
        pass
    except OSError:
        print('Введён недопустимый символ!')
        return False
    return True


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
            print('> Получение ссылки для загрузки локального файла...')
            try:
                response = requests.get(url,
                                    headers=self.get_headers(),
                                    params=upload_params,
                                    timeout=5)
            except ValueError:
                print('Исключение')
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
        mode - режим выгрузки: 'local' - файл с локального диска,
                               'remote' - с удалённых ресурсов по url
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

        # Получение ссылки для загрузки локального файла
        with open(path, 'rb') as f:
            upload_link = self._get_upload_link(target_path)
            try:
                response = requests.put(upload_link,
                                    files={"file": f}
                                    )
            except:
                print('Исключение при выгрузке')
                return 0

            print(f'>>> Файл {path} успешно загружен: Я.Диск:{target_path}')
            return response.status_code

        return 0

    def makedir(self, path):
        """Создаёт папку по пути path на Я.Диске"""
        print(f'> Cоздаём путь {path} на Я.Диске...')
        pathes = path.lstrip('/').split('/')  # Если указаны вложенные папки
        path = ''
        for directory in pathes:
            path += '/' + directory
            params = {'path': path}
            if not self.check_dir_name(path):
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

    def get_upload_dir_name(self, default_dir_name):
        """Формирование пути загрузки файлов на Я.Диск: либо из ввода пользователя,
        либо из имени по умолчанию"""
        answer = False
        while not answer:
            path = input('> Введите имя целевой папки либо нажмите Enter:')
            if path == '':
                path = default_dir_name
            else:
                if not check_path_validity(path):
                    answer = False
                    continue

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
                s_len = len(pathes)
                for i in range(len(pathes)):
                    if pathes[i] != '':
                        pathes.append(pathes[i])
                pathes = pathes[s_len:]
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
