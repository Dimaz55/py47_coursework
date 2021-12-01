import datetime as dt
import requests
import re
from pprint import pprint


class VkApi():
    # params = {'user_id': 0,
    #           'album_id': 'profile',
    #           'count': 5}
    def __init__(self, params):
        self.params = params
        self._api_url = 'https://api.vk.com/method/photos.get'
        self._default_params = {
            'access_token': self._get_token(),
            'v': '5.131',
            'extended': 1,  # доп.инфо: likes, comments, tags, can_comment, reposts
            'rev': 0,  # порядок сортировки 0 — хронологический, 1 - наоборот
        }

    def _get_token(self):
        token_not_found = True
        while token_not_found:
            try:
                with open('vk_token.txt') as f:
                    vk_token = f.readline().strip()
            except FileNotFoundError:
                print('> Ошибка! Файл с токеном vk_token.txt не найден в текущем каталоге.')
                vk_token = input('> Можете ввести его вручную (0 - для выхода, Enter - попытаться ещё раз): ')
                if vk_token == '0':
                    return None
            token_not_found = False
        return vk_token


    def get_photo_list(self):
        """Возвращает словарь составленный из ссылок на фотографии и типа
        изображения из аккаунта Вконтакте.
        token - токен VK API

        Формат ответа:
        {'file_name': {'url': url, 'size': size_type},..., 'default_dirname': dir}

        file_name формируется из количества лайков фотографии. Если лайки
        отсутствуют для имени берутся дата и время фотографии.

        size_type - Обозначение размера и пропорций копии. Подробнее:
        https://vk.com/dev/objects/photo_sizes

        По ключу 'default_dirname' формируется значение имени директории для
        выгрузки на Я.Диск в том случае если пользователь явно не задаёт имя.
        Формат имени: 'VK_{user_id}_{album_type}'
        """
        try:
            self._response = requests.get(
                self._api_url,
                params={**self._default_params, **self.params})
            self._response = self._response.json()
        except:
            pprint(self._response.json())

        photos_list = self._response['response']['items']
        # pprint(self._response['response']['items'])
        owner_id = self._response['response']['items'][0]['owner_id']
        result = {}
        likes = ''
        for photo in photos_list:
            photo_url = photo['sizes'][-1]['url']
            photo_date = photo['date']
            size_type = photo['sizes'][-1]['type']
            file_ext = re.findall(r'(?:jpg|jpeg|png|tiff|bmp|gif)', photo_url)[0]
            try:
                likes = str(photo['likes']['count'])
            except KeyError:
                print('У фотографии нет лайков, файл будет назван по его дате.')
                likes = ''
            file_name = likes + '.' + file_ext
            if likes == '' or file_name in result:
                timestamp = dt.datetime.fromtimestamp(photo_date)
                file_name = timestamp.strftime('%Y-%m-%d_%H-%M-%S') + '.' + file_ext

            result[file_name] = {
                'url': photo_url,
                'size_type': size_type
            }
        self.default_dirname = f"VK_{owner_id}"\
                               f"_{self.params['album_id']}"
        return result

    def get_default_folder_name(self):
        return self.default_dirname

    def _check_errors(self):
        # pprint(self._response)
        try:
            response = self._response['response']
        except KeyError:
            if 'error' in self._response:
                if response['error']['error_code'] == 100:
                    return {'error': response['error']['error_msg']}
                if response['error']['error_code'] == 200:
                    return {'error': response['error']['error_msg']}
            return {'error': self._response}
        # pprint(response)
        if response['count'] == 0:
            return {'error': 'У пользователя нет фотографий в данном альбоме.'}
        try:
            self.photos_list = response['items']
            self.owner_id = response['items'][0]['id']
        except KeyError:
            print('ERR:', self._response)
            return {'error': 'Some error.'}

    def vk_check_params(key, value):
        if key == 'user_id':
            try:
                value = int(value)
                if value < 0:
                    print('>>> Ошибка! user_id не может быть меньше 0.')
                    return False
            except ValueError:
                print('>>> Ошибка! user_id может быть только положительным числом либо 0.')
                return False

        if key == 'album_id' and value not in ['profile', 'wall', 'saved']:
            print('>>> Ошибка! album_type неверен, выберите один из вариантов: "profile", "wall", "saved".')
            return False

        if key == 'count':
            try:
                value = int(value)
                if value < 1 or value > 1000:
                    print('Ошибка! photo_count может быть числом от 1 до 1000.')
                    return False
            except ValueError:
                return {'>>> Ошибка! photo_count может быть только числом (1..1000).'}
        return True
