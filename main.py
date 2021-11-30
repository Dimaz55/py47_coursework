import json
from yadisk import get_ya_token, YaUploader
from vkapi import get_vk_token, get_photo_urls_from_vk


if __name__ == '__main__':
    vk_token = get_vk_token()
    ya_token = get_ya_token()

    photos_from_vk = get_photo_urls_from_vk(vk_token)
    if 'error' in photos_from_vk:
        print(photos_from_vk['error'])
        exit()

    y = YaUploader(ya_token)

    print('----------------------------------------------------------------')
    print('Во всех диалогах Enter выбирает первый ответ в списке возможных.')
    print('----------------------------------------------------------------')

    default_dir_name = photos_from_vk.pop('default_dirname')
    upload_path = y.get_upload_dir_name(default_dir_name)

    print(f'Количество файлов для выгрузки: {len(photos_from_vk) + 1}')
    json_list = []
    for file_name, prop in photos_from_vk.items():
        path_to_file = upload_path + file_name
        print(f"> Загружаем файл по ссылке: {prop['url'][:50] + '...'}")

        res = y.upload('remote', path_to_file, url=prop['url'])
        print(f'>> Файл успешно сохранён: Я.Диск:{path_to_file}')
        json_list.append({'file_name': file_name, 'size': prop['size_type']})

    with open('log.json', 'w') as file:
        json.dump(json_list, file)
    res = y.upload('local', 'log.json', target_path=upload_path + 'log.json')
