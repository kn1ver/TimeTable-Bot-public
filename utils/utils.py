from datetime import datetime, timedelta, date, time
from utils.logger import logger
from config import URL, API_TOKEN
from aiogram import Bot
from aiogram.types import CallbackQuery, FSInputFile

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt 

import os
import json
import base64
import asyncio
import aiohttp
import requests
import pathlib

# BASE_DIR = pathlib.Path(__file__).parent

INPUT_FILE = "files/"  # путь к Excel относительно папки скрипта
CLASS_NAME = "11А"                    # нужный класс
BASE_DIR = os.path.dirname(os.path.abspath(__file__))


# load_dotenv()
# URL = os.getenv("URL")
# API_TOKEN = os.getenv("API_TOKEN")

logger_default = logger
last_anns = {}

def save_xlsx_to_img(file_name: str, class_id="11А"):
    input_path = os.path.join(BASE_DIR_, INPUT_FILE + file_name)
    output_path = os.path.join(BASE_DIR_, f"files/{file_name[:-5]}.png")

    logger.debug(input_path)
    logger.debug(output_path)
    logger.debug(file_name)

    # Создадим директорию, если её нет
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # 1. Читаем файл
    df = pd.read_excel(input_path, header=None)

    # 2. Ищем ячейку с названием класса
    pos = np.where(df.astype(str).eq(CLASS_NAME))
    if len(pos[0]) == 0:
        raise ValueError(f"Класс {CLASS_NAME} не найден")

    row_class, col_class = pos[0][0], pos[1][0]

    # 3. Заголовки предположительно на строку ниже
    row_header = row_class + 1

    # 4. Поиск столбцов 'Предмет' и 'Каб.'
    subj_col = None
    cab_col = None

    for c in range(df.shape[1]):
        cell = str(df.iloc[row_header, c]).strip().lower()
        if cell == "предмет":
            subj_col = c
        if cell == "каб.":
            cab_col = c

    if subj_col is None or cab_col is None:
        raise ValueError("Не найдены столбцы Предмет/Каб.")

    # 5. Поиск конца блока — следующей строки c текстом 'Время урока'
    end_row = None
    for r in range(row_class + 1, len(df)):
        if str(df.iloc[r, 0]).startswith("Время урока"):
            end_row = r
            break

    if end_row is None:
        end_row = len(df)

    # 6. Извлекаем блок расписания
    schedule = df.iloc[row_header + 1 : end_row, :]

    # 7. Достаём нужные столбцы
    result = schedule[[0, subj_col, cab_col]].copy()
    result.columns = ["Время", "Предмет", "Кабинет"]
    result = result[result["Предмет"].notna()]

    logger.debug(result)

    # 8. Создание изображения
    fig, ax = plt.subplots(figsize=(8, len(result) * 0.6))
    ax.axis("off")

    table_data = [result.columns.tolist()] + result.values.tolist()

    table = ax.table(
        cellText=table_data,
        loc='center',
        cellLoc='center'
    )
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1, 1.3)

    plt.tight_layout()
    plt.savefig(output_path, dpi=200)
    plt.close()

    logger.info(f"Создан файл {output_path}")

def save_bytes_to_file(data: bytes, path: str):
    # создаём директорию, если её нет
    os.makedirs(os.path.dirname(path), exist_ok=True)

    # сохраняем
    with open(path, "wb") as f:
        f.write(data)

async def get_announcements():
    async with aiohttp.ClientSession() as s:
        headers = {"X-API-Token": API_TOKEN}
        async with s.get(f"{URL}/announcements", headers=headers) as r:
            r.raise_for_status()
            result = await r.json()
            logger.debug(result)
            return result

async def download_file():
    async with aiohttp.ClientSession() as s:
        headers = {"X-API-Token": API_TOKEN}
        async with s.post(f"{URL}/attachment", headers=headers) as r:
            r.raise_for_status()
            json_data = await r.json()

            return json_data


async def post_timetable(file_name: str, callback: CallbackQuery):
    logger.debug(f"Отправляю файл {file_name[:-5]}.png")
    file = FSInputFile(f"files/{file_name[:-5]}.png")
    await callback.message.answer_photo(file)
    os.remove(f"files/{file_name[:-5]}.png")
    os.remove(f"files/{file_name}")

async def daemon(callback: CallbackQuery, logger=logger_default):
    output_path = os.path.join(BASE_DIR_, "files", json_data['name'])
    chat_id = callback.message.chat.id
    long_sleep = False
    try: last_anns[chat_id]
    except KeyError: last_anns[chat_id] = ""
    now = datetime.now().replace(microsecond=0)
    day = datetime.combine(date.today() + timedelta(1), time(0, 0, 0))

    # задаем промежутки времени работы: 6:00-8:00 и 14:00-21:00
    dt_1 = [datetime.combine(date.today(), time(14, 0, 0)), datetime.combine(date.today(), time(21, 0, 0))]
    dt_2 = [datetime.combine(date.today(), time( 0, 0, 0)), datetime.combine(date.today(), time( 8, 0, 0))]
    
    # проверяем находится ли время сейчас в одном из промежутков
    if dt_1[0] < now < dt_1[1] or dt_2[0] < now < dt_2[1]:
        # если да - опрашиваем api на наличие нового объявления с файлом
        logger.info("Опрашиваю API...")
        last_ann = await get_announcements()

        if last_ann[list(last_ann)[0]]['id'] != last_anns[chat_id]:
            last_anns[chat_id] = last_ann[list(last_ann)[0]]['id']

            logger.info("Найден новый файл.")
            logger.info("Скачиваю файл...")

            json_data = await download_file()
            file_bytes = base64.b64decode(json_data['data'])
            save_bytes_to_file(file_bytes, output_path)
            logger.info("Файл успешно скачан.")
            logger.info("Преобразую в изображение...")
            save_xlsx_to_img(json_data['name'])

            await post_timetable(json_data['name'], callback)
            long_sleep = True
        else:
            long_sleep = False
            logger.info("Засыпаю на 300 секунд")
            await asyncio.sleep(300)

    else:
        # если нет - засыпаем на время равное времени до ближайшего промежутка работы
        long_sleep = True

    if long_sleep:
        sleep_time = day - now + timedelta(hours=6) if now > dt_1[0] else dt_1[0] - now
        logger.info(f"Засыпаю на {sleep_time.total_seconds()} секунд")
        await asyncio.sleep(sleep_time.total_seconds())

if __name__ == "__main__":
    while True:
        asyncio.run(daemon())

