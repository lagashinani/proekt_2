import vk_api
from my_func import *


def vk_auth(vk_token=''):
    """Авторизация в ВК"""
    if not vk_token:
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

    vk = vk_session.get_api()

    user_info = get_user_info(vk)
    q_sex = int(not (user_info['sex'] - 1)) + 1

    search_result = {}
    offset = 0
    db = read_users()
    while len(search_result) < 10:
        search = vk.users.search(sort=1, city=user_info['city'], sex=q_sex, age_from=user_info['age'] + AGE_FROM,
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


if __name__ == '__main__':
    main()
