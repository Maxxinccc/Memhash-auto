import time
import pyautogui
import pytesseract
from PIL import Image
from datetime import datetime, timezone
import os
from pathlib import Path
from dotenv import load_dotenv

# Укажите полный путь к файлу .env
dotenv_path = Path("C:/Users/Administrator/Desktop/memhash autostart/settings.env")
load_dotenv(dotenv_path=dotenv_path)

print("Значения из .env:")
print("X_COORD:", os.getenv("X_COORD"))
print("Y_COORD:", os.getenv("Y_COORD"))
print("ENERGY_AREA:", os.getenv("ENERGY_AREA"))

x_coord = int(os.getenv("X_COORD"))
y_coord = int(os.getenv("Y_COORD"))
energy_area = tuple(map(int, os.getenv("ENERGY_AREA").split(',')))  # Координаты области для OCR
energy_min = int(os.getenv("ENERGY_MIN"))  # Минимальный уровень энергии для выключения
energy_max = int(os.getenv("ENERGY_MAX"))  # Максимальное значение энергии для включения
start_time_str = os.getenv("START_TIME")  # Время отложенного старта (часы и минуты)
energy_check_interval = int(os.getenv("ENERGY_CHECK_INTERVAL"))  # Интервал проверки энергии (минуты)
use_start_time = os.getenv("USE_START_TIME", "False").lower() == "true"  # Включение/выключение режима времени старта

# Укажите путь к Tesseract, если он не в PATH
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Переменные состояния
last_energy_state = None  # Может быть "low", "high" или None
start_time_reached = not use_start_time  # Если режим старта отключён, флаг сразу True

def save_energy_screenshot():
    """Сохраняет скриншот области энергии для упрощения настройки"""
    screenshot = pyautogui.screenshot(region=energy_area)  # Делаем скриншот указанной области
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")  # Уникальное имя файла
    file_name = f"energy_area_{timestamp}.png"
    screenshot.save(file_name)
    print(f"Скриншот сохранён: {file_name}")

def click_button():
    """Клик по кнопке"""
    pyautogui.click(x=x_coord, y=y_coord)
    print(f"Клик выполнен по координатам ({x_coord}, {y_coord})")

def get_energy_value():
    """Распознавание значения энергии с помощью OCR"""
    screenshot = pyautogui.screenshot(region=energy_area)  # Делаем скриншот указанной области
    text = pytesseract.image_to_string(screenshot).strip()  # Распознаём текст
    print(f"Распознанный текст: {text}")
    
    # Попробуем извлечь числовое значение
    try:
        energy = int(''.join(filter(str.isdigit, text)))  # Оставляем только цифры
        return energy
    except ValueError:
        print("Не удалось распознать значение энергии. Считаем, что энергия = 0.")
        return 0

def check_start_time():
    """Проверяет, наступило ли указанное время старта"""
    global start_time_reached
    if use_start_time and start_time_str:
        now = datetime.now(timezone.utc).strftime("%H:%M")  # Текущее время в формате UTC
        print(f"Текущее время (UTC): {now}. Ожидаем времени старта (UTC): {start_time_str}.")
        
        if now == start_time_str and not start_time_reached:
            print(f"Наступило время старта {start_time_str} (UTC). Нажимаем кнопку...")
            click_button()
            start_time_reached = True  # Устанавливаем флаг, чтобы предотвратить повторное срабатывание
        elif not start_time_reached:
            print("Время старта ещё не наступило.")
    else:
        start_time_reached = True  # Если режим старта отключён, флаг сразу True

# Сохраняем скриншот сразу при запуске
save_energy_screenshot()
print("Скриншот сохранён. Переходим к проверке времени старта...")

# Основной цикл
try:
    print("Входим в основной цикл...")
    while True:
        check_start_time()  # Проверка времени старта
        print("Проверка времени старта завершена...")

        # Проверяем уровень энергии только если время старта уже наступило или режим отключён
        if start_time_reached:
            print("Проверяем уровень энергии...")
            energy = get_energy_value()
            print(f"Текущий уровень энергии: {energy}")

            if energy < energy_min:
                if last_energy_state != "low":  # Проверка, чтобы избежать повторного клика
                    print(f"Энергия ниже минимума ({energy}). Останавливаем майнинг...")
                    click_button()
                    last_energy_state = "low"  # Запоминаем состояние
                else:
                    print("Майнинг уже остановлен. Ожидание...")
            elif energy > energy_max:
                if last_energy_state != "high":  # Проверка, чтобы избежать повторного клика
                    print(f"Энергия выше максимума ({energy}). Запускаем майнинг...")
                    click_button()
                    last_energy_state = "high"  # Запоминаем состояние
                else:
                    print("Майнинг уже запущен. Ожидание...")
            else:
                print(f"Энергия в промежутке ({energy}). Ничего не делаем...")
                last_energy_state = None  # Сбрасываем состояние, если энергия между порогами

        # Ожидаем перед следующей проверкой
        print(f"Ожидание {energy_check_interval * 10} секунд перед следующей проверкой...")
        time.sleep(energy_check_interval * 10)
except KeyboardInterrupt:
    print("\nСкрипт остановлен.")
