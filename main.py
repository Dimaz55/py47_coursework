from yadisk import YaUploader
from vkapi import VkApi


def welcome():
    print('Photo reaper v0.1.0')
    print('Вас приветствует сборщик фотографий из соц.сетей!')
    print('Во всех диалогах Enter выбирает первый ответ в списке возможных.')
    return None


SOCIAL_PARAMS = {
    'vk': {
        1: {'name': 'Вконтакте'},
        2: {'name': 'идентификатор пользователя',
            'field': 'user_id',
            'default': '0'},
        3: {'name': 'количество фотографий для загрузки',
            'field': 'count',
            'default': '5'},
        4: {'name': 'альбом',
            'field': 'album_id',
            'default': 'profile',
            'select':
                {
                    'profile': 'фотографии из профиля',
                    'wall': 'фотографии со стены',
                    'saved': 'сохранённые фотографии'
                }
            }
    }
}

CLOUD_STORAGE = {
    'ya.disk': {
        'name': 'Яндекс Диск'
    },
    'g.drive': {
        'name': 'Google Drive'
    }
}

USER_CAN_CHANGE = [2, 3, 4]  # Опции доступные для изменения пользователем


def get_params(net, params):
    u_id = params[net][2]
    p_count = params[net][3]
    album_id = params[net][4]
    cloud_id = CLOUD_STORAGE['ya.disk']['name']

    print(f"Текущий режим работы:\n"
          f"1. Соц.сеть: {net}\n"
          f"2. ID пользователя: {u_id['default']}\n"
          f"3. Количество фото для загрузки: {p_count['default']}\n"
          f"4. Альбом: {album_id['default']}\n"
          f"5. Облачное хранилище: {cloud_id}\n")

    out_params = {u_id['field']: u_id['default'],
                  p_count['field']: p_count['default'],
                  album_id['field']: album_id['default']}
    change_mode = input("Хотите изменить параметры? [y/n]: ")
    if change_mode in ['y', 'Y']:
        return change_params(net, out_params)
    else:
        return out_params
    return out_params


def check_params(net, params):
    if net == 'vk':
        for key, value in params.items():
            if key == 'user_id':
                try:
                    value = int(value)
                    if value < 0:
                        print('>>> Ошибка! user_id не может быть меньше 0.')
                        return False
                except ValueError:
                    print('>>> Ошибка! user_id может быть только положительным'
                          'числом либо 0.')
                    return False

            if key == 'album_id' and value not in ['profile', 'wall', 'saved']:
                print('>>> Ошибка! album_type неверен, выберите один из '
                      'вариантов: "profile", "wall", "saved".')
                return False

            if key == 'count':
                try:
                    value = int(value)
                    if value < 1 or value > 1000:
                        print('Ошибка! '
                              'photo_count может быть числом от 1 до 1000.')
                        return False
                except ValueError:
                    print('>>> Ошибка! '
                          'photo_count может быть только числом (1..1000).')
                    return False
        return True
    else:
        print('Другие соц.сети пока не поддерживаются.')
        return False


def change_params(net, params):
    print('Внимание! Параметры 1 и 5 пока изменить нельзя.')
    answer_list = input('Какие пункты хотите изменить? '
                        'Введите нужные цифры списком: ')
    answer_list = set(answer_list)  # Удаляем дубликаты
    answer_list = list(answer_list)  # Переводим в изменяемый тип
    answers = []
    for answer in answer_list:
        if answer.isnumeric() and int(answer) in USER_CAN_CHANGE:
            answers.append(int(answer))
    params_map = {2: 'user_id', 3: 'count', 4: 'album_id'}
    for param in sorted(answers):
        answered = False
        while not answered:
            print(f"> Введите новое значение {params_map[param]}: ", end='')
            ans = input()
            if ans == '':
                answered = False
            else:
                answered = check_params(net, {params_map[param]: ans})
                if answered:
                    params[params_map[param]] = ans
    return params


if __name__ == '__main__':
    welcome()

    net = 'vk'
    # формирование  параметров запроса для нужной соц.сети
    params = get_params(net, SOCIAL_PARAMS)

    v = VkApi(params)
    photos_list = v.get_photo_list()

    y = YaUploader()

    upload_path = y.get_upload_dir_name(v.default_dirname)
    y.upload_file_list(photos_list, upload_path)

    print('-= The End =-')
