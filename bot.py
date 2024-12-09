import nest_asyncio
import asyncio
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackContext

# Патчим текущий цикл событий
nest_asyncio.apply()

# Функция для получения высоты по координатам
def get_elevation(lat, lon):
    api_url = f"https://api.open-elevation.com/api/v1/lookup?locations={lat},{lon}"
    response = requests.get(api_url).json()
    return response['results'][0]['elevation']

# Функция для обработки команды /start
async def start(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text(
        'Привет Качественник! Отправьте мне команду в формате:\n'
        '/elevation <широта1> <долгота1> <азимут1> <дистанция1>\n'
        '<широта2> <долгота2> <азимут2> <дистанция2>\n'
        '...\n'
        'Например:\n'
        '/elevation \n'
        '41.2995 69.2401 45 1000\n'
        '41.2995 69.2401 45 1000'
    )

# Функция для обработки команды /elevation
async def elevation(update: Update, context: CallbackContext) -> None:
    try:
        # Разделяем запросы по строкам
        requests = update.message.text.split('\n')[1:]
        
        results = []
        for req in requests:
            # Получаем координаты, азимут и дистанцию из каждого запроса
            args = req.strip().split()
            if len(args) != 4:
                raise ValueError("Неверное количество аргументов. Ожидается 4 аргумента: широта, долгота, азимут, дистанция.")
            
            lat, lon, azimuth, distance = map(float, args)
            
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
            
            # Вычисляем разницу высот
            elevation_difference = end_elevation - start_elevation
            
            # Определяем знак разницы высот
            if elevation_difference > 0:
                elevation_difference = -abs(elevation_difference)
            else:
                elevation_difference = abs(elevation_difference)
            
            results.append(f'Разница высот: {elevation_difference:.2f} метров')
        
        # Отправляем ответ пользователю
        await update.message.reply_text('\n'.join(results))
    except ValueError as ve:
        await update.message.reply_text(f'Ошибка ввода: {ve}\n'
                                        'Пожалуйста, используйте формат:\n'
                                        '/elevation <широта1> <долгота1> <азимут1> <дистанция1>\n'
                                        '<широта2> <долгота2> <азимут2> <дистанция2>\n'
                                        '...\n'
                                        'Например:\n'
                                        '/elevation 41.2995 69.2401 45 1000\n'
                                        '41.2995 69.2401 45 1000\n'
                                        '41.2995 69.2401 45 1000')
    except Exception as e:
        await update.message.reply_text(f'Произошла ошибка: {e}')

async def main():
    # Вставьте сюда ваш токен
    application = ApplicationBuilder().token("7691215008:AAGgkRjMnkTwevgdaPKXWXrSVFHB_vNB844").build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("elevation", elevation))
    
    await application.run_polling()

if __name__ == '__main__':
    asyncio.run(main())

bot.polling(none_stop=True, interval=2)
