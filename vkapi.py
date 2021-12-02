import datetime as dt
import requests
import re


class VkApi:
    def __init__(self, params):
        self.params = params
        self._api_url = 'https://api.vk.com/method/photos.get'
        self._default_params = {
            'access_token': self._get_token(),
            'v': '5.131',
            'extended': 1,  # доп.инфо: likes, comments, tags...
            'rev': 0,  # порядок сортировки 0 — хронологический, 1 - наоборот
        }

    @staticmethod
    def _get_token():
        with open('vk_token.txt') as f:
            vk_token = f.readline().strip()
        return vk_token

    def get_photo_list(self):
        """Возвращает словарь составленный из ссылок на фотографии и типа
        изображения из аккаунта Вконтакте.

        Формат ответа:
        {'file_name': {'url': url, 'size': size_type},...,}

        file_name формируется из количества лайков фотографии. Если лайки
        отсутствуют для имени берутся дата и время фотографии.

        size_type - Обозначение размера и пропорций копии.
        """
        self._response = requests.get(
                self._api_url,
                params={**self._default_params, **self.params}).json()

        if 'error' in self._response:
            print('Ошибка', self._response['error']['error_code'])
            print(self._response['error']['error_msg'])
            exit()

        photos_list = self._response['response']['items']
        owner_id = self._response['response']['items'][0]['owner_id']
        result = {}

        for photo in photos_list:
            photo_url = photo['sizes'][-1]['url']
            photo_date = photo['date']
            size_type = photo['sizes'][-1]['type']
            file_ext = re.findall(r'(?:jpg|jpeg|png|tiff|bmp|gif)',
                                  photo_url)[0]

            if 'count' in photo['likes'] and photo['likes']['count'] > 0:
                likes = str(photo['likes']['count'])
            else:
                likes = ''

            file_name = likes + '.' + file_ext
            if likes == '' or file_name in result:
                timestamp = dt.datetime.fromtimestamp(photo_date)
                file_name = timestamp.strftime('%Y-%m-%d_%H-%M-%S') + \
                    '.' + file_ext

            result[file_name] = {
                'url': photo_url,
                'size_type': size_type
            }
        # 'default_dirname' имя директории для выгрузки на Я.Диск в том
        # случае если пользователь явно не задаёт имя.
        self.default_dirname = f"VK_{owner_id}"\
                               f"_{self.params['album_id']}"
        return result
