import vk_api
from my_func import *


AGE_FROM = -3  # На сколько лет младше может быть объект поиска (отрицательная велечина)
AGE_TO = 3  # На сколько лет старше может быть объект поиска
token = ''  # Token авторизации VK

if not token:
    token = input('Введите token или оставьте поле пустым для авторизации по логину и паролю:\n')

if token.strip() == '':
    login = input('Введите логин:\n')
    password = input('Введите пароль:\n')
    vk_session = vk_api.VkApi(login=login, password=password)
    vk_session.auth()
else:
    vk_session = vk_api.VkApi(token=token)

vk = vk_session.get_api()

user_info = get_user_info(vk)
q_sex = int(not (user_info['sex'] - 1)) + 1

search_result = {}
offset = 0
db = read_json()
while len(search_result) < 10:
    search = vk.users.search(sort=0, city=user_info['city'], sex=q_sex, age_from=user_info['age'] + AGE_FROM,
                             age_to=user_info['age'] + AGE_TO, has_photo=1, status=6, is_closed=False,
                             offset=offset, count=100)
    if len(search['items']) == 0:
        break
    for item in search['items']:
        link = 'https://vk.com/id' + str(item['id'])
        if link in db.keys():
            continue
        if not item['is_closed']:
            photos = get_top3_photo(item['id'], vk)
            if photos:
                search_result.update({link: photos})
            if len(search_result) == 10:
                break
    offset += 100

write_json(search_result)
write_html(search_result)
db.update(search_result)
write_json(db, 'db.json')
write_html(db, 'db.html')
os.system('start output.html')
