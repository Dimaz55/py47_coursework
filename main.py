import json
from pprint import pprint
from yadisk import get_ya_token, YaUploader
from vkapi import get_vk_token, get_photo_urls_from_vk


def check_path_validity(path):
    try:
        with open(path, 'r') as f:
            pass
    except FileNotFoundError:
        pass
    except OSError:
        print('Введён недопустимый символ!')
        return False
    return True


if __name__ == '__main__':
    vk_token = get_vk_token()
    ya_token = get_ya_token()

    photos_from_vk = get_photo_urls_from_vk(vk_token, 0, 'wall', '122')
    if 'error' in photos_from_vk:
        print(photos_from_vk['error'])
        exit()

    y = YaUploader(ya_token)

    print('----------------------------------------------------------------')
    print('Во всех диалогах Enter выбирает первый ответ в списке возможных.')
    print('----------------------------------------------------------------')
    answer = False
    while not answer:
        path = input('Введите имя целевой папки либо нажмите Enter:')
        if path == '':
            path = photos_from_vk.pop('default_dirname')
        else:
            if not check_path_validity(path):
                answer = False
            photos_from_vk.pop('default_dirname')

        if y.check_dir_name(path):
            ans = input('> Папка уже существует. Записать в неё? При совпадении имён файлы будут переименованы.[y/n] ')
            if ans in ['y', 'Y', '']:
                break
        else:
            y.makedir(path)
            answer = True
    path = '/' + path + '/'
    print(f'Количество файлов для выгрузки: {len(photos_from_vk) + 1}')
    json_list = []
    for file_name, prop in photos_from_vk.items():
        pth_to_file = path + file_name
        print(f"> Загружаем файл по ссылке: {prop['url'][:50] + '...'}")

        res = y.upload('remote', pth_to_file, url=prop['url'])
        print(f'>> Файл успешно сохранён: Я.Диск:{pth_to_file}')
        json_list.append({'file_name': file_name, 'size': prop['size_type']})

    with open('log.json', 'w') as file:
        json.dump(json_list, file)
    res = y.upload('local', 'log.json', target_path=path+'log.json')
