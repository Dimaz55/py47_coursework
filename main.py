import datetime as dt
import requests
from pprint import pprint
import re
from yadisk import YaUploader


def get_photos_urls_from_vk(token: str, user_id=0, photo_count=5, album_type='profile'):
    """Возвращает словарь составленный из ссылок на фотографии и типа
    изображения из аккаунта Вконтакте.
    token - токен VK API

    user_id - идентификатор аккаунта откуда нужно скачать фотографии
    (по-умолчанию 0 - фотографии берутся из аккаунта владельца токена).

    photo_count (по-умолчанию 5, максимум 1000) - количество требуемых фото.

    album_type: тип альбома, по-умолчанию 'profile' - фотографии профиля,
                'wall' - фотографии со стены, saved — сохраненные фотографии.

    Формат ответа:
    {'file_name': {'url': url, 'size': size_type},...}

    file_name формируется из количества лайков фотографии. Если лайки
    отсутствуют для имени берутся дата и время фотографии.

    size_type - Обозначение размера и пропорций копии. Подробнее:
    https://vk.com/dev/objects/photo_sizes
    """
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
    try:
        response = response['response']
    except KeyError:
        print(response['error']['error_msg'])
        return 0
    photos_total = response['count']
    photos_list = response['items']
    result_urls_dict = {}

    for photo in photos_list[::-1]:  # Начинаем с самых ранних фото
        photo_url = photo['sizes'][-1]['url']
        photo_date = photo['date']
        size_type = photo['sizes'][-1]['type']
        file_ext = re.findall(r'\.?(.png|.gif|.jpg|.jpeg|.tiff)?\?s', photo_url)[0]
        try:
            likes = str(photo['likes']['count'])
        except KeyError:
            print('У фотографии нет лайков, файл будет назван: ', end='')
        if likes + file_ext in result_urls_dict or likes == '':
            timestamp = dt.datetime.fromtimestamp(photo_date)
            likes = timestamp.strftime('%Y-%m-%d_%H:%M:%S')
        file_name = str(likes) + file_ext
        result_urls_dict[file_name] = {
            'url': photo_url,
            'size_type': size_type
        }
        likes = ''

    return result_urls_dict


if __name__ == '__main__':
    # try:
    #     with open('vk_token.txt') as f:
    #         vk_token = f.readline().strip()
    # except FileNotFoundError:
    #     print('Файл с токеном VK на найден.')
    #     exit()
    #
    # pprint(get_photos_urls_from_vk(token))
    #
    try:
        with open('ya_token.txt') as file:
            ya_token = file.readline().strip()
    except FileNotFoundError:
        print('Файл с токеном Yandex на найден.')
        exit()
    y = YaUploader(ya_token)

    answer = False
    while not answer:
        path = input('Введите имя папки для загрузки либо нажмите Enter - имя будет создано автоматически:')
        if path=='':
            path = None
            break
        try:
            with open(path) as f:
                pass
            answer = True
        except FileNotFoundError:
            pass
        except OSError:
            print('Введён недопустимый символ!')
            continue

        if y.check_dir_name(path):
            ans = input('Папка уже существует. Записать в неё? [y/n]')
            if ans in ['n','N']:
                answer = False
                continue
        else:
            print(f'Cоздаём папку {path} на Я.Диске')
            y.makedir(path)
        print('Записываем в папку', path)
        answer = True

    # print(y.makedir('Ya').json())
    # res = y.upload(file_name='/Ya/1.jpg',
    # url='https://sun9-28.userapi.com/impf/c850732/v850732336/16fa43/3b7pxN3vzmI.jpg')
    # print(res.json())
