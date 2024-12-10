import nest_asyncio
import asyncio
import requests
import pandas as pd
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, CallbackContext
from time import sleep

# Патчим текущий цикл событий
nest_asyncio.apply()

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Функция для получения высоты по координатам с использованием Google Maps Elevation API
def get_elevation(lat, lon, retries=3, delay=2):
    api_key = "AIzaSyBNOsJcoqfSRrNyz5Z0H3UsoM7oA-32rX0"
    api_url = f"https://maps.googleapis.com/maps/api/elevation/json?locations={lat},{lon}&key={api_key}"
    for attempt in range(retries):
        try:
            response = requests.get(api_url)
            response.raise_for_status()  # Проверка на успешный ответ
            logger.info(f"API response: {response.text}")  # Логирование ответа API
            data = response.json()
            return data['results'][0]['elevation']
        except requests.exceptions.RequestException as e:
            logger.error(f"Ошибка при запросе к API: {e}")
            if attempt < retries - 1:
                sleep(delay)  # Задержка перед повторной попыткой
            else:
                return None
        except ValueError as e:
            logger.error(f"Ошибка при обработке JSON: {e}")
            return None

# Функция для обработки команды /start
async def start(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text(
        'Привет Качественник! Отправьте мне Excel файл с данными в формате:\n'
        'широта долгота; азимут; дистанция\n'
        'Например:\n'
        '40.53648 70.94076;120;1000\n'
        '40.53648 70.94076;120;1000\n'
        '40.53648 70.94076;120;1000'
    )

# Функция для обработки команды /help
async def help_command(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text(
        'Для использования этого бота, отправьте Excel файл с данными в следующем формате:\n\n'
        'Столбцы:\n'
        '- coords: широта и долгота, разделенные пробелом (например, "40.53648 70.94076")\n'
        '- azimuth: азимут (например, "120")\n'
        '- distance: дистанция в метрах (например, "1000")\n\n'
        'Пример содержимого Excel файла:\n'
        'coords          azimuth  distance\n'
        '40.53648 70.94076;120;1000\n'
        '40.53648 70.94076;120;1000\n'
        '40.53648 70.94076;120;1000\n\n'
        'После отправки файла бот вычислит разницу высот и отправит вам результат.'
    )

# Функция для обработки документов
async def handle_document(update: Update, context: CallbackContext) -> None:
    try:
        # Получаем файл из сообщения
        file = await context.bot.get_file(update.message.document.file_id)
        file_path = file.file_path
        
        # Читаем данные из Excel файла
        df = pd.read_excel(file_path)
        
        results = []
        for index, row in df.iterrows():
            # Получаем координаты, азимут и дистанцию из каждой строки
            parts = row['coords'].strip().split(';')
            if len(parts) != 3:
                raise ValueError("Неверный формат ввода. Ожидается три части, разделенные точкой с запятой.")
            
            coords = parts[0].strip().split()
            if len(coords) != 2:
                raise ValueError("Неверный формат координат. Ожидается широта и долгота, разделенные пробелом.")
            
            lat, lon = map(float, coords)
            azimuth = float(parts[1].strip())
            distance = float(parts[2].strip())
            
            # Проверяем диапазоны значений
            if not (-90 <= lat <= 90):
                raise ValueError("Широта должна быть в диапазоне от -90 до 90.")
            if not (-180 <= lon <= 180):
                raise ValueError("Долгота должна быть в диапазоне от -180 до 180.")
            if not (0 <= azimuth <= 360):
                raise ValueError("Азимут должен быть в диапазоне от 0 до 360.")
            if distance < 0:
                raise ValueError("Дистанция должна быть положительным числом.")
            
            # Вычисляем конечные координаты (упрощенно, без учета кривизны Земли)
            import math
            R = 6371e3  # Радиус Земли в метрах
            delta_lat = distance * math.cos(math.radians(azimuth)) / R
            delta_lon = distance * math.sin(math.radians(azimuth)) / (R * math.cos(math.radians(lat)))
            
            end_lat = lat + math.degrees(delta_lat)
            end_lon = lon + math.degrees(delta_lon)
            
            # Получаем высоты начальной и конечной точек
            start_elevation = get_elevation(lat, lon)
            end_elevation = get_elevation(end_lat, end_lon)
            
            if start_elevation is None or end_elevation is None:
                raise ValueError("Не удалось получить данные о высоте. Пожалуйста, попробуйте позже.")
            
            # Вычисляем разницу высот
            elevation_difference = end_elevation - start_elevation
            
            # Определяем знак разницы высот
            if elevation_difference > 0:
                elevation_difference = -abs(elevation_difference)
            else:
                elevation_difference = abs(elevation_difference)
            
            results.append(elevation_difference)
        
        # Добавляем результаты в исходный DataFrame рядом с исходными данными
        df['Elevation Difference'] = results
        
        # Записываем результаты в новый Excel файл
        df.to_excel('elevation_results.xlsx', index=False)
        
        # Отправляем ответ пользователю с результатами в виде файла Excel
        await context.bot.send_document(chat_id=update.message.chat_id, document=open('elevation_results.xlsx', 'rb'))
    except ValueError as ve:
        logger.error(f'Ошибка ввода: {ve}')
        await update.message.reply_text(f'Ошибка ввода: {ve}\n'
                                        'Пожалуйста, используйте формат:\n'
                                        'широта долгота; азимут; дистанция\n'
                                        'Например:\n'
                                        '40.53648 70.94076;120;1000\n'
                                        '40.53648 70.94076;120;1000\n'
                                        '40.53648 70.94076;120;1000')
    except Exception as e:
        logger.error(f'Произошла ошибка: {e}')
        await update.message.reply_text(f'Произошла ошибка: {e}')

async def main():
    # Вставьте сюда ваш токен
    application = ApplicationBuilder().token("7691215008:AAGgkRjMnkTwevgdaPKXWXrSVFHB_vNB844").build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    
    await application.run_polling()

if __name__ == '__main__':
    asyncio.run(main())
