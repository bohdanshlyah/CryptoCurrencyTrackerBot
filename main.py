import logging
import requests
import os
import asyncio

from aiogram import Bot, Dispatcher, executor, types
from aiogram.utils.exceptions import MessageNotModified
from aiogram.dispatcher.filters import Text
from config import Config
from contextlib import suppress
from dotenv import load_dotenv
from datetime import timedelta

load_dotenv()


API_TOKEN = os.getenv("API_TOKEN")

# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize bot and dispatcher
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

button_parameters = types.KeyboardButton("Parameters")
button_change_pair = types.KeyboardButton("Change pair")
button_change_interval = types.KeyboardButton("Change interval")

INFORMATION = """Hello!\nI am a crypto currency exchange tracker bot.\n
By default bot tracking BTC_USD pair with 1 hour periodicity.\n
You can change it by typing buttons(but not less than 10 seconds!)\n
If You want stop bot just type <b>/stop</b> command\n
IF You want resume tracking - type <b>/resume</b> command"""


active_coro_list = []


# Get active pairs
def get_active_pairs():
    r = requests.get("https://coinpay.org.ua//api/v1/pair")
    data = r.json()
    pairs = []
    for i in data["pairs"]:
        pairs.append(i["name"])
    return pairs


# Add keybord for changing interval
def get_keyboard():
    button_1 = types.InlineKeyboardButton(text="-1 hour", callback_data="hour_decr")
    button_2 = types.InlineKeyboardButton(text="+1 hour", callback_data="hour_incr")
    button_3 = types.InlineKeyboardButton(text="-1 minute", callback_data="min_decr")
    button_4 = types.InlineKeyboardButton(text="+1 minute", callback_data="min_incr")
    button_5 = types.InlineKeyboardButton(text="-10 second", callback_data="sec_decr")
    button_6 = types.InlineKeyboardButton(text="+10 second", callback_data="sec_incr")
    button_7 = types.InlineKeyboardButton(text="Submit", callback_data="submit")

    keyboard = types.InlineKeyboardMarkup().row(button_1, button_2)
    keyboard.row(button_3, button_4)
    keyboard.row(button_5, button_6)
    keyboard.add(button_7)
    return keyboard


async def update_interval_text(message: types.Message, new_value: int):
    with suppress(MessageNotModified):
        new_value = timedelta(seconds=config.interval)
        await message.edit_text(
            f"Set interval: {new_value}", reply_markup=get_keyboard()
        )


# Parse adding hours
@dp.callback_query_handler(Text(startswith="hour_"))
async def callbacks_num(call: types.CallbackQuery):
    user_value = config.interval
    action = call.data.split("_")[1]
    if action == "incr":
        config.interval = config.interval + 3600
        await update_interval_text(call.message, user_value + 3600)
    elif action == "decr":
        if (user_value - 3600) > 0:
            config.interval = config.interval - 3600
            await update_interval_text(call.message, user_value - 3600)
        else:
            config.interval = 10
            await update_interval_text(call.message, config.interval)
    await call.answer()


# Parse adding minutes
@dp.callback_query_handler(Text(startswith="min_"))
async def callbacks_num(call: types.CallbackQuery):
    user_value = config.interval
    action = call.data.split("_")[1]
    if action == "incr":
        config.interval = config.interval + 60
        await update_interval_text(call.message, user_value + 60)
    elif action == "decr":
        if (user_value - 60) > 0:
            config.interval = config.interval - 60
            await update_interval_text(call.message, user_value - 60)
        else:
            config.interval = 10
            await update_interval_text(call.message, config.interval)
    await call.answer()


# Parse adding seconds
@dp.callback_query_handler(Text(startswith="sec_"))
async def callbacks_num(call: types.CallbackQuery):
    user_value = config.interval
    action = call.data.split("_")[1]
    if action == "incr":
        config.interval = config.interval + 10
        await update_interval_text(call.message, user_value + 10)
    elif action == "decr":
        if (user_value - 10) > 0:
            config.interval = config.interval - 10
            await update_interval_text(call.message, user_value - 10)
    await call.answer()


@dp.callback_query_handler(Text(equals="submit"))
async def callbacks_num(call: types.CallbackQuery):
    new_value = timedelta(seconds=config.interval)
    await call.message.edit_text(f"New interval: {new_value}")
    await call.answer()
    if len(active_coro_list) != 0:
        active_coro_list.pop(0)
    loop.create_task(periodic(config._interval))


@dp.message_handler(text=("Change interval"))
async def stop_bot(message: types.Message):
    await message.answer(
        f"Set interval: {timedelta(seconds=config.interval)}",
        reply_markup=get_keyboard(),
    )


# Answer to /start command
@dp.message_handler(commands=["start"])
async def send_welcome(message: types.Message):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(button_change_pair, button_change_interval, button_parameters)

    await message.answer(INFORMATION, reply_markup=keyboard, parse_mode="HTML")

    config.status = True
    config.chat_id = types.chat.Chat.get_current()["id"]

    if len(active_coro_list) != 0:
        active_coro_list.pop(0)
    loop.create_task(periodic(config._interval))


# Answer to /stop command
@dp.message_handler(commands=["stop"])
async def stop_bot(message: types.Message):
    await message.answer("Stop tracking!")
    config.status = False


# Answer to /resume command
@dp.message_handler(commands=["resume"])
async def stop_bot(message: types.Message):
    await message.answer("Start tracking!")
    config.status = True
    # loop.create_task(periodic(config._interval))


# Parametrs
@dp.message_handler(text=("Parameters"))
async def parameters(message: types.Message):
    conversion = timedelta(seconds=config.interval)
    if config.status:
        await message.answer(
            f"""Now bot tracking {config.pair} pair with: {conversion} interval\n
Tracking status: ACTIVE"""
    )
    else:
        await message.answer(
            f"""Now bot tracking {config.pair} pair with: {conversion} interval\n
Tracking status: INACTIVE"""
    )


# Answer to /help command
@dp.message_handler(commands=["help"])
async def send_welcome(message: types.Message):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(button_change_pair, button_change_interval, button_parameters)

    await message.answer(INFORMATION, reply_markup=keyboard, parse_mode="HTML")


# Create buttons for changing pairs
@dp.message_handler(text=("Change pair"))
async def stop_bot(message: types.Message):
    keybord = types.InlineKeyboardMarkup()
    for i in get_active_pairs():
        keybord.add(types.InlineKeyboardButton(text=i, callback_data=i))

    await message.answer("Choose pair for tracking", reply_markup=keybord)


# Changing current tracking pair
@dp.callback_query_handler(text=tuple(get_active_pairs()))
async def dsfsf(call: types.CallbackQuery):
    config.pair = call.data
    await call.answer(f"Change tracking pair to: {config.pair}")


# Function for periodic
async def periodic(sleep_for):
    while True:
        if asyncio.tasks.current_task() in active_coro_list:
            if config.status:
                r = requests.get("https://coinpay.org.ua/api/v1/exchange_rate/")
                data = r.json()
                if data["status"] == "success":
                    for i in data["rates"]:
                        if i["pair"] == config.pair:
                            await bot.send_message(
                                config.chat_id, f"{config.pair}: {i['price']}"
                            )
                else:
                    await bot.send_message(config.chat_id, "Something went wrong =(")

            await asyncio.sleep(sleep_for)
        else:
            if len(active_coro_list) == 0:
                active_coro_list.append(asyncio.tasks.current_task())
            else:
                asyncio.Task.cancel(asyncio.tasks.current_task())
                await asyncio.sleep(1)
                break


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    config = Config()
    executor.start_polling(dp, skip_updates=True)
