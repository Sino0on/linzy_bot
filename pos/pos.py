import asyncio
import logging
import sys

import aiohttp
from aiogram import Dispatcher, F, types
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, ReplyKeyboardRemove

from aiogram.enums.parse_mode import ParseMode

from clients import find_client_by_user_id, get_user_id_by_phone, get_user_info_by_id, check_manager
from router import router
from core.init import bot
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

from decouple import config

# Bot token can be obtained via https://t.me/BotFather

# All handlers should be attached to the Router (or Dispatcher)
dp = Dispatcher()


class Registration(StatesGroup):
    waiting_for_contact = State()


def get_contact_button():
    buttons = [
        [KeyboardButton(text="📞 Поделиться контактом", request_contact=True)]
    ]
    keyboard = types.ReplyKeyboardMarkup(keyboard=buttons)
    return keyboard


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
    if user_id in [795677145, 7698119272]:
        buttons.append([
            KeyboardButton(text="✍️ Отправить рассылку"),
            KeyboardButton(text="🛠 Обработать"),
            KeyboardButton(text="📊 Экспортировать клиентов"),
            KeyboardButton(text="🧠 Добавить менеджера"),
        ])
    elif check_manager(user_id):
        buttons.append([
            KeyboardButton(text="✍️ Отправить рассылку"),
            KeyboardButton(text="🛠 Обработать"),
            KeyboardButton(text="📊 Экспортировать клиентов"),
            KeyboardButton(text="🧠 В разработке ..."),
        ])
    keyboard = types.ReplyKeyboardMarkup(keyboard=buttons)
    return keyboard


@dp.message(CommandStart())
async def command_start_handler(message: Message, state: FSMContext) -> None:
    user = find_client_by_user_id(message.from_user.id)
    print(user)
    if user:
        user = get_user_info_by_id(user['id'])
        await message.answer(
            f'Здравствуйте, {user["name"]} 💚', reply_markup=get_keyboard_buttons(message.from_user.id)
        )
        return
    await message.answer(
        'Для продолжения работы необходим ваш контакт. Нажмите на кнопку "📞 Поделиться контактом".',
        reply_markup=get_contact_button(),
    )
    await state.set_state(Registration.waiting_for_contact)


# Хэндлер для получения контакта
@dp.message(Registration.waiting_for_contact)
async def process_contact(message: types.Message, state: FSMContext):
    if message.contact is not None:
        user_phone = message.contact.phone_number
        await message.answer(
            f"""Приветствуем вас в магазине – Linzy Kg!
Этот бот – ваш личный помощник: следите за бонусами, историей покупок. А также бот будет вас оповещать о новостях магазина
""",
            reply_markup=get_keyboard_buttons(message.from_user.id),
        )
        # Здесь можно добавить логику сохранения номера телефона в базу данных
        user = get_user_id_by_phone(str(user_phone), message.from_user.id)
        if not user:
            await message.answer(
                "Вашего номера нет в базе данных магазина, пожалуйста пару минут, ваша заявка на создание бонусную карту была отправлена администраторам ☺️"
            )
            await send_personal_message(user=message.from_user, phone=user_phone)
        await state.clear()
    else:
        await message.answer(
            "Пожалуйста, используйте кнопку для отправки номера телефона."
        )


async def send_personal_message(user: types.User, phone):
    API_URL = f"https://api.telegram.org/bot{config('BOT_TOKEN_POS')}"
    text = f"""ЗАЯВКА\nИмя - {user.first_name} {user.last_name}\nUsername - {user.username}\nНомер телефона - {phone}"""

    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(f"{API_URL}/sendMessage",
                                    json={"chat_id": -1002726653428, "text": text}) as resp:
                response = await resp.json()
                if not response.get("ok"):
                    print(f"Ошибка отправки текста пользователю {user.id}: {response}")
        except Exception as e:
            print(f"Ошибка при отправке пользователю {user}: {e}")


async def main() -> None:
    # Initialize Bot instance with a default parse mode which will be passed to all API calls
    # And the run events dispatching
    dp.include_router(router)
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
