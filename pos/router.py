from aiogram import Router

import bonus

router = Router()

router.include_router(bonus.router)
