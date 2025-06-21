import json
from pprint import pprint

import requests
from decouple import config
from aiogram.client.session import aiohttp

# URL для запроса
url = "https://app.pos-service.kg/proxy/?path=%2Fdata%2F65c07ccea38b589f01033a20%2Fclients%2F%3Flimit%3D1000%26offset%3D0&api=v3&timezone=21600"

# Заголовок с cookies
cookies = {
    "connect.sid": config("CONNECT_ID"),
    "company_id": config("COMPANY_ID"),
}

def get_users_info_pos():
    # Выполнение GET-запроса
    response = requests.get(url, cookies=cookies)

    # Проверка статуса ответа и вывод результата
    if response.status_code == 200:
        # print("Ответ получен успешно!")
        return  response.json()
    else:
        return None

def get_user_info_by_id(user_id: str):
    # Выполнение GET-запроса
    response = requests.get(url, cookies=cookies)

    # Проверка статуса ответа и вывод результата
    if response.status_code == 200:
        print("Ответ получен успешно!")
        result = response.json()
    else:
        return None
    pprint(result["data"])
    for user in result["data"]:
        if user["_id"] == user_id:
            pprint(user)
            return user
    return None

def get_all_user_ids_pos():
    """
    Возвращает список всех user_id из JSON-файла db.json.

    :return: Список user_id (строки) или пустой список, если данных нет.
    """
    try:
        with open("pos/db.json", "r", encoding="utf-8") as file:
            data = json.load(file)

        if "clients" in data and isinstance(data["clients"], list):
            return [client["user_id"] for client in data["clients"]]  # Берем только user_id

    except (FileNotFoundError, json.JSONDecodeError):
        pass  # Если файл отсутствует или поврежден

    return []



def get_user_id_by_phone(user_phone: str, user_id: int):
    # Выполнение GET-запроса
    response = requests.get(url, cookies=cookies)

    # Проверка статуса ответа и вывод результата
    if response.status_code == 200:
        print("Ответ получен успешно!")
        result = response.json()
    else:
        return None
    for user in result["data"]:
        for phone in user.get("phones", ""):
            if user_phone[::-1][:9][::-1] in phone:
                print(user)
                add_client_to_json(user_id, user["_id"])
                return user["_id"]
    return None


def find_client_by_user_id(user_id: int):
    """
    Ищет клиента по Telegram user_id в JSON-файле.

    :param user_id: Telegram ID пользователя.
    :return: Найденный словарь или None.
    """
    try:
        with open("pos/db.json", "r", encoding="utf-8") as file:
            data = json.load(file)

        if "clients" in data and isinstance(data["clients"], list):
            for client in data["clients"]:
                if client["user_id"] == user_id:
                    return client  # Возвращаем всю информацию о клиенте

    except (FileNotFoundError, json.JSONDecodeError):
        pass  # Если файл отсутствует или поврежден

    return None  # Если клиент не найден


def add_client_to_json(user_id: str, user_id_pos: str, status: str = ""):
    """
    Добавляет нового клиента в список clients внутри JSON-файла в новом формате.

    :param user_id: Telegram ID пользователя.
    :param user_id_pos: ID пользователя из POS-системы.
    :param status: Статус пользователя (по умолчанию пустая строка).
    """
    default_data = {"clients": []}

    try:
        # Читаем текущие данные из файла
        with open("pos/db.json", "r", encoding="utf-8") as file:
            data = json.load(file)

        if "clients" not in data or not isinstance(data["clients"], list):
            data = default_data
    except (FileNotFoundError, json.JSONDecodeError):
        data = default_data  # Если файл отсутствует или JSON поврежден

    # Проверяем, есть ли уже этот пользователь
    for client in data["clients"]:
        if client["user_id"] == user_id:
            return  # Если клиент уже есть, не добавляем повторно

    # Добавляем нового клиента
    new_client = {
        "user_id": user_id,
        "id": user_id_pos,
        "status": status
    }
    data["clients"].append(new_client)

    # Записываем обновленные данные обратно в файл
    with open("pos/db.json", "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4, ensure_ascii=False)


# Пример использования:

# print(get_user_id_by_phone("+996555895822", 795677145))
# Функция отправки сообщений пользователям POS

# Получение всех user_id (из нового формата db.json)
def get_all_user_ids(canal):
    try:
        with open(f"{canal}/db.json", "r", encoding="utf-8") as file:
            data = json.load(file)

        if "clients" in data and isinstance(data["clients"], list):
            return [client["user_id"] for client in data["clients"]]
    except (FileNotFoundError, json.JSONDecodeError):
        pass
    return []

async def send_canal_pos(text, images):
    users = get_all_user_ids('pos')
    async with aiohttp.ClientSession() as session:
        API_URL = f"https://api.telegram.org/bot{config('BOT_TOKEN_POS')}"
        for user_id in users:
            try:
                if images:
                    media = [{"type": "photo", "media": file_id} for file_id in images]
                    async with session.post(f"{API_URL}/sendMediaGroup",
                                            json={"chat_id": user_id, "media": media}) as resp:
                        response = await resp.json()
                        if not response.get("ok"):
                            print(f"Ошибка отправки фото пользователю {user_id}: {response}")

                async with session.post(f"{API_URL}/sendMessage", json={"chat_id": user_id, "text": text}) as resp:
                    response = await resp.json()
                    if not response.get("ok"):
                        print(f"Ошибка отправки текста пользователю {user_id}: {response}")

            except Exception as e:
                print(f"Ошибка при отправке пользователю {user_id}: {e}")


async def send_mailing(canal, text, images):
    await send_canal_pos(text, images)


# Проверка, является ли пользователь менеджером
def check_manager(user_id: str):
    try:
        with open("moy/db.json", "r", encoding="utf-8") as file:
            data = json.load(file)

        return user_id in data.get("managers", [])
    except (FileNotFoundError, json.JSONDecodeError):
        pass
    return False



async def update_clients_status_pos():
    """
    Обновляет статус всех клиентов в db.json на переданный статус.

    :param new_status: Новый статус, который нужно установить всем клиентам.
    """
    try:
        with open("pos/db.json", "r", encoding="utf-8") as file:
            data = json.load(file)

        if "clients" in data and isinstance(data["clients"], list):
            # Перебираем всех клиентов и обновляем статус
            new_status = 1
            for client in data["clients"]:
                users = get_users_info_pos()
                user = ''
                for user in users['data']:
                    if user == client['id']:
                        break

                if user:
                    if not dict(user).get("bonus_spent", ''):
                        new_status = 1
                    elif int(str(int(float(user['bonus_spent'])))[:-2]) >= 35000:
                        new_status = 2
                    elif int(str(int(float(user['bonus_spent'])))[:-2]) >= 75000:
                        new_status = 3
                    elif int(str(int(float(user['bonus_spent'])))[:-2]) >= 135000:
                        new_status = 3
                    print(dict(user).get("bonus_spent", ''))
                    print(client["status"] != new_status)
                    if client["status"] != new_status:
                        client["status"] = new_status
                        print(new_status)
                        await send_message_to_user_pos(client['user_id'], new_status)

            # Записываем обновленный JSON обратно в файл
            with open("pos/db.json", "w", encoding="utf-8") as file:
                json.dump(data, file, indent=4, ensure_ascii=False)
            return True  # Успешно обновлено

    except (FileNotFoundError, json.JSONDecodeError):
        print("Ошибка: Файл db.json отсутствует или поврежден.")
        return False  # Ошибка при обновлении

    return False  # Если структура файла некорректна

