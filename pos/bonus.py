import json
from pprint import pprint

import qrcode
from io import BytesIO
from aiogram import F, Router, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InputFile, KeyboardButton, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from clients import find_client_by_user_id, get_user_info_by_id, send_mailing, update_clients_status_pos

router = Router()


class Mailing(StatesGroup):
    text = State()
    images = State()


def get_keyboard_buttons(user_id: int = None):
    buttons = [
        [
            KeyboardButton(text="📊 Информация по счету"),
            KeyboardButton(text="📇 Баланс счёта"),
        ],
        [
            KeyboardButton(text="💳 Виртуальная карта"),
            KeyboardButton(text="📝 Заказать линзы"),
        ],
    ]

    if user_id == 795677145:
        buttons.append([
            KeyboardButton(text="✍️ Отправить рассылку"),
            KeyboardButton(text="🧠 Добавить менеджера"),
        ])

    keyboard = types.ReplyKeyboardMarkup(keyboard=buttons)
    return keyboard


@router.message(F.text == "📊 Информация по счету")
async def send_product(message: types.Message) -> None:
    await message.answer("Отчет формируется, подождите немного. ⏳")
    userid = find_client_by_user_id(message.from_user.id)
    user = get_user_info_by_id(userid['id'])
    pprint(user)
    text = ''
    if user.get('debt', None):
        money = int(str(int(float(user["debt"])))[:-2])
        if userid['status'] in [0, 1]:
            text = f'Вам осталось еще {35000 - money} сом до второго уровня'
        elif userid['status'] == 2:
            text = f'Вам осталось еще {75000 - money} сом до третьего уровня'
        elif userid['status'] == 2:
            text = f'Вам осталось еще {135000 - money} сом до четвертого уровня'
    else:
        text = f'Вам осталось еще {35000 - 0} сом до второго уровня'
    await message.answer(f'💰 Потрачено всего: {0 if user.get("debt", None) else user.get("debt", None)}\n{text}')


@router.message(F.text == "📇 Баланс счёта")
async def send_product(message: types.Message) -> None:
    await message.answer("Баланс вычисляется, подождите немного. ⏳")
    user = find_client_by_user_id(message.from_user.id)
    user = get_user_info_by_id(user['id'])
    await message.answer(f'🧾 Баланс бонусов: {user.get("debt")}')


@router.message(F.text == "💳 Виртуальная карта")
async def send_product(message: types.Message) -> None:
    await message.answer("Виртуальная карта формируется, подождите немного. ⏳")
    user = find_client_by_user_id(message.from_user.id)
    user = get_user_info_by_id(user['id'])
    generate_qr_code(user["discount_card"])

    await message.answer_photo(
        photo=types.FSInputFile(path=f'pos/qr_codes/{user["discount_card"]}.png'),
        # photo=f'qr_codes/{user["_id"]}.png',
        caption=(
            "💳 Этот QR-код вы можете предъявить вместо пластиковой карты лояльности.\n"
        )
    )


@router.message(F.text == "📝 Заказать линзы")
async def send_product(message: types.Message) -> None:
    url = 'https://linzy.kg/'
    url2 = 'https://api.whatsapp.com/send?phone=996705501056&text=%D0%9F%D0%B8%D1%88%D1%83%20%D1%87%D0%B5%D1%80%D0%B5%D0%B7%20%D0%B1%D0%BE%D1%82%D0%B0%20'
    buttons = [
        [InlineKeyboardButton(text="Заказать линзы", url=url)],
        [InlineKeyboardButton(text="Написать на вотсап", url=url2)],
    ]
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
    await message.answer("Заказать линзы",  reply_markup=keyboard)
    # user = find_client_by_user_id(str(message.from_user.id))
    # await message.answer(f'💰 Всего: {user["bonus_spent"]}')


def generate_qr_code(user_id):
    # Генерация QR-кода
    # Data to be encoded

    # Encoding data using make() function
    img = qrcode.make(user_id)

    # Saving as an image file
    img.save(f'pos/qr_codes/{user_id}.png')
    return img


@router.message(F.text == "✍️ Отправить рассылку")
async def send_product(message: types.Message, state: FSMContext) -> None:
    await message.answer(
        f"Отправьте текст для рассылки",
        reply_markup=types.ReplyKeyboardRemove()
    )
    await state.update_data(canals=message.text)
    await state.set_state(Mailing.text)





@router.message(Mailing.text)
async def process_contact(message: types.Message, state: FSMContext):
    if message.text is not None:
        await message.answer(
            f"Отправьте одно изображение",
        )
        await state.update_data(text=message.text)
        await state.set_state(Mailing.images)
    else:
        await message.answer(
            "Отправьте текст для рассылки"
        )



@router.message(Mailing.images)
async def process_images(message: types.Message, state: FSMContext, bot):
    data = await state.get_data()
    images = data.get("images", [])

    if message.photo:  # Если отправлено фото
        file_id = message.photo[-1].file_id  # Получаем file_id самого большого изображения
        images.append(file_id)
        await state.update_data(images=images)
        await message.answer("Фото добавлено. Отправьте еще или напишите 'все' для завершения.")

    elif message.text and message.text.lower() == "все":
        await message.answer("Начинаю рассылку... ⏳⏳")
        data = await state.get_data()
        text = data.get("text")
        images = data.get("images")
        canal = data.get("canals")
        await send_mailing(canal, text, images)
        await message.answer("Рассылка закончена ✅✅", reply_markup=get_keyboard_buttons(message.from_user.id))
        await state.clear()


@router.message(F.text == "🛠 Обработать")
async def send_product(message: types.Message) -> None:
    await message.answer("Клиенты обрабатываются...")
    await update_clients_status_pos()
    await message.answer(f'Готово ✅✅')


# @router.message(F.text == "📊 Экспортировать клиентов")
# async def send_excel_file(message: types.Message):
#     """
#     Генерирует Excel-файл и отправляет его пользователю в Telegram.
#     """
#     await message.answer("Генерирую файл...")
#
#     file_path = await generate_excel_from_db()
#
#     if file_path:
#         await message.answer_document(FSInputFile(file_path), caption="Вот ваш Excel-файл с клиентами 📂")
#     else:
#         await message.answer("Ошибка при генерации файла. Проверьте данные.")