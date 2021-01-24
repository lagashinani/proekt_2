import vk_api
import os
from my_func import *


def vk_auth(vk_token=''):
    """Авторизация в ВК"""
    if not vk_token:
        get_web_token = input('Хотите получить новый токен авторизации в полуатоматическом режиме (да/нет)?:\n')
        if get_web_token.lower().strip() == 'да' or get_web_token.lower().strip() == 'lf':
            _msg = 'Для получения токена необходимо открыть браузер, в котором нужно будет предоставить права\n' + \
                   'приложению с названием vk_api_test (внизу нужно нажать кнопку Разрешить). Нажмите на ссылку \n' + \
                   'если это возможно, или вручную скопируйте строку ниже и вставить в браузер. После нажатия\n' + \
                   'кнопки Разрешить, скопируйте и вставьте url адрес из браузер (не смотря на все\n' + \
                   'предупреждения системы безопастности). Для продолжения нажмите ENTER'
            _ = input(_msg)
            print('Ссылка для получения токена:')
            print(get_token_link(scope=4))
            while not vk_token:
                token_url = input(
                    'Введите url адрес строки из браузера или оставьте поле пустым для авторизации по логину/паролю' +\
                    'и нажмите ENTER\n')
                if token_url.strip() == '':
                    break
                else:
                    try:
                        vk_token = token_url.split('access_token=')[1].split('&')[0]
                        print('Ваш токен:', vk_token, 'Сохраните его в файле config.txt для автоматической авторизации',
                              sep='\n')
                    except IndexError:
                        print('Неверный формат URL, повторите ввод')
                        continue

        else:
            vk_token = input('Введите token или оставьте поле пустым для авторизации по логину и паролю:\n')

    if vk_token.strip() == '':
        login = input('Введите логин:\n')
        password = input('Введите пароль:\n')
        session = vk_api.VkApi(login=login, password=password, auth_handler=auth_handler)
        session.auth()
    else:
        session = vk_api.VkApi(token=vk_token)
    return session


def main():
    file_settings = read_settings()
    token = file_settings.setdefault('token', '')
    AGE_FROM = int(file_settings.setdefault('AGE_FROM', '-3'))
    AGE_TO = int(file_settings.setdefault('AGE_TO', '3'))

    vk_session = vk_auth(token)
    print('Авторизация прошла успешно')
    print('Выполняем поиск...')

    vk = vk_session.get_api()

    user_info = get_user_info(vk)
    q_sex = int(not (user_info['sex'] - 1)) + 1

    search_result = {}
    offset = 0
    db = read_users()
    while len(search_result) < 10:
        search = vk.users.search(sort=0, city=user_info['city'], sex=q_sex, age_from=user_info['age'] + AGE_FROM,
                                 age_to=user_info['age'] + AGE_TO, has_photo=1, status=6, is_closed=False,
                                 offset=offset, count=100)
        if len(search['items']) == 0:
            break
        for item in search['items']:
            link = 'https://vk.com/id' + str(item['id'])
            if link in db:
                continue
            if not item['is_closed']:
                photos = get_top3_photo(item['id'], vk)
                if photos:
                    search_result.update({link: photos})
                if len(search_result) == 10:
                    break
        offset += 100

    write_db(search_result)
    write_json(search_result)
    write_html(search_result)
    os.system('start output.html')
    print('Поиск завершен')


if __name__ == '__main__':
    main()
