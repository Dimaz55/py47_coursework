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


def get_photo_urls_from_vk(token, user_id=0, album_type='profile', photo_count=5):
    """Возвращает словарь составленный из ссылок на фотографии и типа
    изображения из аккаунта Вконтакте.
    token - токен VK API

    user_id - идентификатор аккаунта откуда нужно скачать фотографии
    (по-умолчанию 0 - фотографии берутся из аккаунта владельца токена).

    photo_count (по-умолчанию 5, максимум 1000) - количество требуемых фото.

    album_type: тип альбома, по-умолчанию 'profile' - фотографии профиля,
                'wall' - фотографии со стены, saved — сохраненные фотографии.

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
        user_id = int(user_id)
        if user_id < 0:
            return {'error': 'user_id не может быть меньше 0.'}
    except ValueError:
        return {'error': 'user_id может быть только положительным числом либо 0.'}

    if album_type not in ['wall', 'saved']:
        return {'error': 'album_type неверен, выберите один из вариантов: "profile", "wall", "saved".'}

    try:
        photo_count = int(photo_count)
        if photo_count < 1 or photo_count > 1000:
            return {'error': 'photo_count может быть только числом от 1 до 1000.'}
    except ValueError:
        return {'error': 'photo_count может быть только числом (1..1000).'}

    url = 'https://api.vk.com/method/photos.get'

    auth_params = {
        'user_id': user_id,
        'access_token': token,
        'v': '5.131'
    }
    request_params = {
        'album_id': album_type,
        'extended': 1,  # доп.инфо: likes, comments, tags, can_comment, reposts
        'rev': 0,  # порядок сортировки 0 — хронологический, 1 - наоборот
        'count': photo_count,
    }

    response = requests.get(url, params={**auth_params, **request_params}).json()
    # pprint(response)
    try:
        response = response['response']
    except KeyError:
        print(response['error']['error_msg'])
        return 0
    # photos_total = response['count']
    photos_list = response['items']
    owner_id = response['items'][0]['id']
    result_urls_dict = {}
    likes = ''

    for photo in photos_list[::-1]:  # Начинаем с самых ранних фото
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
    result_urls_dict['default_dirname'] = f'VK_{user_id or owner_id}_{album_type}'
    return result_urls_dict
