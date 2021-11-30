import datetime as dt
import requests
import re
from pprint import pprint


def get_vk_token():
    try:
        with open('vk_token.txt') as f:
            vk_token = f.readline().strip()
    except FileNotFoundError:
        vk_token = input('Файл с токеном VK на найден. Можете ввести вручную (0 для выхода): ')
        if vk_token == '0':
            exit()
    return vk_token


def get_photo_urls_from_vk(token, request_params):
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

    url = 'https://api.vk.com/method/photos.get'

    def_params = {
        'access_token': token,
        'v': '5.131',
        'extended': 1,  # доп.инфо: likes, comments, tags, can_comment, reposts
        'rev': 0,  # порядок сортировки 0 — хронологический, 1 - наоборот
    }

    response = requests.get(url, params={**def_params, **request_params}).json()

    try:
        response = response['response']
    except KeyError:
        return {'error': 'KeyError'}
    if 'error' in response and response['error']['error_code'] == 200:
        err = f"Доступ к альбому '{request_params['album_type']}' запрещён пользователем."
        return {'error': err}
    photos_list = response['items']
    owner_id = response['items'][0]['id']
    result_urls_dict = {}
    likes = ''
    pprint(response)
    if photos_list:
        for photo in photos_list:
            photo_url = photo['sizes'][-1]['url']
            photo_date = photo['date']
            size_type = photo['sizes'][-1]['type']
            file_ext = re.findall(r'\.?(.png|.gif|.jpg|.jpeg|.tiff)?\?s', photo_url)[0]
            try:
                likes = str(photo['likes']['count'])
            except KeyError:
                print('У фотографии нет лайков, файл будет назван по его дате.')
            if likes + file_ext in result_urls_dict or likes == '':
                timestamp = dt.datetime.fromtimestamp(photo_date)
                likes = timestamp.strftime('%Y-%m-%d_%H-%M-%S')
            file_name = str(likes) + file_ext
            result_urls_dict[file_name] = {
                'url': photo_url,
                'size_type': size_type
            }
            likes = ''
        result_urls_dict['default_dirname'] = \
            f"VK_"\
            f"{int(request_params['user_id']) or owner_id}"\
            f"_{request_params['album_id']}"
    return result_urls_dict
