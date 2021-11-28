import datetime as dt
import requests
# from pprint import pprint
import re
from yadisk import YaUploader


def get_photos_from_vk(user_id=0, photo_count=5, album_type='profile'):
    url = 'https://api.vk.com/method/photos.get'
    with open('vk_token.txt') as f:
        token = f.readline().strip()
    auth_params = {
        'user_id': user_id,
        'access_token': token,
        'v': '5.131'
    }
    request_params = {
        'album_id': album_type,  # profile - из профиля, wall — со стены; saved — сохраненные.
        'extended': 1,  # доп.инфо: likes, comments, tags, can_comment, reposts
        'rev': 0,  # порядок сортировки фотографий 1 — антихронологический; 0 — хронологический.
        'count': photo_count,
    }

    response = requests.get(url, params={**auth_params, **request_params}).json()
    # pprint(response)
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
    get_photos_from_vk()

    # y = YaUploader(ya_token)
    # print(y.makedir('Ya').json())
    # res = y.upload(file_name='/Ya/1.jpg',
    # url='https://sun9-28.userapi.com/impf/c850732/v850732336/16fa43/3b7pxN3vzmI.jpg')
    # print(res.json())
