import json
import datetime
import os


def get_user_age():
    """Заставляем пользователя ввести свой возраст"""
    user_age = ''
    while not (user_age.isdigit() and int(user_age) in range(100)):
        user_age = input('Введите свой возраст:\n')
    return user_age


def get_user_sex():
    """Заставляем пользователя выбрать пол, если он не указан"""
    user_sex = ''
    while not (user_sex == 'ж' or user_sex == 'м'):
        user_sex = input('Введите свой пол (м/ж):\n')
        user_sex = user_sex.lower()
    return 1 if user_sex == 'ж' else 2


def get_city(api):
    """Если у пользователя не указан город, заставляет его выбрать"""
    user_info = api.account.getProfileInfo()
    try:
        user_country = user_info['country']['id']
    except KeyError:
        user_country = 0
        vk_countries = api.database.getCountries(need_all=1, count=1000)
        countries_list = {}
        for item in vk_countries['items']:
            countries_list.update({item['title']: item['id']})

        while not user_country:
            user_country_str = input('Введите название вашей страны, например Россия:\n')
            if user_country_str in countries_list.keys():
                user_country = countries_list[user_country_str]

        user_city = 0
        while not user_city:
            q_city = ''
            while len(q_city) < 2:
                q_city = input('Введите название населеннго пункта или его часть (не менее 2 букв):\n')
            vk_cities = api.database.getCities(country_id=user_country, q=q_city)

            if len(vk_cities['items']) == 0:
                print('По вашему запросу ничего не найдено, уточните запрос.')
                continue

            i = 1
            for item in vk_cities['items']:
                region = item['region'].strip() + ', ' if 'region' in item.keys() else ''
                area = item['area'] if 'area' in item.keys() else ''
                print(i, item['title'] + ',', region, area)
                i += 1

            u_city = -1
            print('- ' * 20)
            while u_city not in range(len(vk_cities['items'])):
                u_city = input('Уточните населенный пункт (введите его номер по списку):\n')
                u_city = int(u_city) - 1

            return vk_cities['items'][u_city]['id']


def get_user_info(api):
    vk_user_info = api.account.getProfileInfo()
    try:
        user_day = int(vk_user_info['bdate'].split('.')[0])
        user_month = int(vk_user_info['bdate'].split('.')[1])
        user_year = int(vk_user_info['bdate'].split('.')[2])
        user_date = datetime.date(user_year, user_month, user_day)
        now_date = datetime.datetime.date(datetime.datetime.now())
        user_age = int((now_date - user_date).days / 365.25)
    except IndexError:
        user_age = get_user_age()

    user_sex = int(vk_user_info['sex'])
    if user_sex not in [1, 2]:
        user_sex = get_user_sex()

    try:
        user_city = vk_user_info['city']['id']
    except IndexError:
        user_city = get_city(api)

    return {'age': user_age, 'sex': user_sex, 'city': user_city}


def get_comments_count(user_id, api):
    """Возвращает словарь, где ключи это id фотографий, а значения - кол-во комментариев"""
    comments = api.photos.getAllComments(owner_id=user_id, count=100)
    all_comments = comments['items']  # Список самих комментариев
    if comments['count'] > 100:  # Если комментариев больше 100, получаем все вплоть до 10000 (макс. в ВК)
        max_comment = 10100 if comments['count'] > 10000 else ((comments['count'] - 1) // 100 + 1) * 100
        for i in range(100, max_comment, 100):
            comments = vk.photos.getAllComments(owner_id=user_id, count=100, offset=i)
            all_comments.extend(comments['items'])

    comments_count = {}
    for comment in all_comments:
        if comment['pid'] in comments_count.keys():
            comments_count[comment['pid']] += 1
        else:
            comments_count.update({comment['pid']: 1})
    return comments_count


def get_top3_photo(user_id, api):
    """Возвращает топ-3 фото пользователя по лайкам и комментам ВК в виде списка url
    ссылка на фото в максимальном разрешении.
    Если кол-во фото меньше 3, возвращает False
    """
    photos = api.photos.getAll(owner_id=user_id, extended=1, count=200)
    if photos['count'] < 3:
        return False
    comments_count = get_comments_count(user_id, api)
    sorted_list = []
    for photo in photos['items']:
        max_size = -1
        max_size_url = ''
        for size in photo['sizes']:
            if size['width'] >= max_size:
                max_size = size['width']
                max_size_url = size['url']
        likes = comments_count.setdefault(photo['id'], 0) + photo['likes']['count']
        sorted_list.append([likes, max_size_url])
    sorted_list.sort(reverse=True)
    result_list = [i[1] for i in sorted_list[0:3]]
    return result_list


def write_json(data, filename='output.json'):
    """Записывает объект в JSON формате"""
    with open(filename, 'w', encoding='utf-8') as file:
        json.dump(data, file)


def read_json(filename='db.json'):
    """Читаем файл JSON в объект"""
    if os.path.isfile(filename):
        with open(filename, 'r', encoding='utf-8') as file:
            return json.load(file)
    else:
        return {}


def write_html(data, filename='output.html'):
    """Генерирует простую html страничку, что бы показать результаты поиска в наглядном виде"""

    caption = 'Последние 10 записей' if filename == 'output.html' else 'Вся база (текущий запрос + предыдущие)'
    html = f"""<html>
    <head>
        <meta charset="UTF-8">
        <title>VK Tinder</title>
    </head>
    <body>
    <h2 align="center">{caption}</h2>
    <table align="center" width="800" border="0">
    """
    for key in data:
        html += f'<tr><td colspan="3" align="center"><a href="{key}" target="_blank">{key}</a></td></tr>'
        html += '<tr>'
        for img in data[key]:
            html += f"""<td align="center"><a href="{img}" target="_blank">
            <img src="{img}" height="250" border="0"></a></td>"""
        html += """</tr>
        <td colspan="3" align="center">---</td></tr>"""
    footer = '"db.html">посмотреть всю базу' if filename == 'output.html' else '"output.html">Последние 10 записей'
    html += f"""	</table>
    <div align="center"><a href={footer}</a></div>	
    </body>
    </html>
    """
    with open(filename, 'w', encoding='utf-8') as file:
        file.write(html)