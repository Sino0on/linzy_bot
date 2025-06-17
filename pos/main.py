import json
from pprint import pprint

import requests
from decouple import config


# URL для запроса
url = "https://app.pos-service.kg/proxy/?path=%2Fdata%2F64abd976dac244c8d30a926c%2Fcatalog%2F%3Flimit%3D1000%26offset%3D0&api=v3&timezone=21600"

# Заголовок с cookies
cookies = {
    "connect.sid": config("CONNECT_ID"),
    "company_id": config("COMPANY_ID"),
}


response = requests.get(url, cookies=cookies)

if response.status_code == 200:
    # print("Ответ получен успешно!")
    data = response.json()
    j = 0
    print(len(data['data']))
    for i in range(len(data['data'])):
        if data["data"][i]['type'] != 'group':
            pprint(data["data"][i])

        #     j += 1
        # else:
        #     pprint(data["data"][i])
    print(j)
else:
    print('net')