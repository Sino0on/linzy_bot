from aiogram import Bot
from decouple import config

bot = Bot(config("BOT_TOKEN_POS"))
