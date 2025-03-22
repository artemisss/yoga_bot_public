import os
from dotenv import load_dotenv
import telebot
from telebot import types
import requests

load_dotenv()

API_URL = os.environ.get('API_URL')
API_KEY = os.environ.get('API_KEY')
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')

bot = telebot.TeleBot(TELEGRAM_TOKEN)

headers = {'X-API-KEY': API_KEY}

# Функция регистрации пользователя
def register_user(telegram_id, name, employee_id=None):
    data = {
        'name': name,
        'telegram_id': telegram_id,
        'employee_id': employee_id,
        'role': 'user',
        'info': {}
    }
    response = requests.post(f'{API_URL}/users', json=data, headers=headers)
    if response.status_code == 201:
        return True, "Вы успешно зарегистрированы!"
    elif response.status_code == 409:
        return False, "Пользователь уже зарегистрирован."
    else:
        return False, "Произошла ошибка при регистрации."

# Функция получения доступных событий
def get_available_events(telegram_id):
    response = requests.get(f'{API_URL}/available_events', params={'telegram_id': telegram_id}, headers=headers)
    if response.ok:
        return response.json()
    return []

# Функция регистрации на событие
def register_for_event(telegram_id, event_id):
    data = {'telegram_id': telegram_id, 'event_id': event_id}
    response = requests.post(f'{API_URL}/event_registrations', json=data, headers=headers)
    return response.ok

# Функция получения событий, на которые зарегистрирован пользователь
def get_user_events(telegram_id):
    response = requests.get(f'{API_URL}/user_events', params={'telegram_id': telegram_id}, headers=headers)
    if response.ok:
        return response.json()
    return []

def update_user_data(telegram_id, employee_id=None, name=None, role=None, info=None):
    data = {
        'telegram_id': telegram_id,
        'employee_id': employee_id,
        'name': name,
        'role': role,
        'info': info
    }
    data = {k: v for k, v in data.items() if v is not None}

    response = requests.put(f'{API_URL}/users/update_by_telegram_id', json=data, headers=headers)
    return response.ok, response.text

# Функция удаления регистрации с события
def delete_event_registration(telegram_id, event_id):
    data = {'telegram_id': telegram_id, 'event_id': event_id}
    response = requests.post(f'{API_URL}/event_registrations/delete', json=data, headers=headers)
    return response.ok

@bot.message_handler(commands=['start'])
def handle_start(message):
    telegram_id = message.from_user.id
    name = message.from_user.first_name + (" " + message.from_user.last_name if message.from_user.last_name else "")
    # Регистрируем пользователя без employee_id, предполагая, что функция register_user обрабатывает None значения для employee_id
    success, response_message = register_user(telegram_id, name)
    if success:
        bot.send_message(message.chat.id, "Вы успешно зарегистрированы! Пожалуйста, введите ваш employee_id для завершения регистрации или обновления данных.")
    else:
        bot.send_message(message.chat.id, response_message + " Пожалуйста, введите ваш employee_id для обновления данных.")
    show_main_menu(message.chat.id)

@bot.message_handler(func=lambda message: message.text.isdigit())
def handle_employee_id(message):
    telegram_id = message.from_user.id
    name = message.from_user.first_name + (" " + message.from_user.last_name if message.from_user.last_name else "")
    employee_id = message.text
    success, response_message = update_user_data(telegram_id, employee_id=employee_id, name=name)
    if success:
        bot.send_message(message.chat.id, "Ваши данные успешно обновлены.")
    else:
        bot.send_message(message.chat.id, f"Произошла ошибка при обновлении вашего employee_id: {response_message}")
    show_main_menu_first(message.chat.id)


@bot.message_handler(commands=['status_yoga'])
def status_yoga(message):
    telegram_id = message.from_user.id
    events = get_available_events(telegram_id)
    if events:
        # Сортируем события по office_name и datetime
        events.sort(key=lambda x: (x['office_name'], x['datetime']))
        response_message = ""
        current_office = ""
        for event in events:
            office_name = event['office_name']
            # Проверяем, изменилось ли название офиса, чтобы добавить заголовок
            if current_office != office_name:
                if current_office != "":  # Добавляем разделитель между офисами, если это не первый офис
                    response_message += "\n"
                response_message += f"События в {office_name}\n"
                current_office = office_name
            # Формируем строку с информацией о событии
            datetime_str = format_event_datetime(event['datetime'])
            registered = event['registered_participants']
            max_participants = event['max_participants']
            response_message += f"На событие {datetime_str} записалось {registered} человек из {max_participants}\n"
        bot.send_message(message.chat.id, response_message.strip())  # .strip() удаляет лишние пробелы и переводы строки в начале и конце строки
    else:
        bot.send_message(message.chat.id, "На данный момент нет доступных событий.")

@bot.message_handler(commands=['status_yoga_users'])
def handle_status_yoga_users(message):
    telegram_id = message.from_user.id
    send_registered_users(message.chat.id, telegram_id)


def send_registered_users(chat_id, telegram_id):
    # Здесь мы предполагаем, что у вас есть endpoint /upcoming_event_registrations, который возвращает необходимую информацию
    response = requests.get(f'{API_URL}/upcoming_event_registrations', headers=headers)
    if response.ok:
        events_users = response.json()
        if not events_users:
            bot.send_message(chat_id, "На данный момент нет записавшихся пользователей на ближайшие события.")
            return

        message_text = ""
        current_event_id = None
        for item in events_users:
            if current_event_id != item['event_id']:
                # Начало нового события
                message_text += f"\n{item['office_name']} {item['event_date']} в {item['event_time']}\n"
                current_event_id = item['event_id']
            message_text += f"{item['user_name']}\n"

        bot.send_message(chat_id, message_text.strip())
    else:
        bot.send_message(chat_id, "Не удалось получить список зарегистрированных пользователей.")


@bot.message_handler(func=lambda message: True)
def main_menu(message):
    if message.text == 'Записаться на йогу':
        show_available_events(message)
    elif message.text == 'Мои записи на йогу':
        show_user_events(message)
    elif message.text == 'Выбрать любимый офис':
        choose_favorite_office(message)
    elif message.text == 'Романов двор':
        update_user_office(message, 1, "Романов двор")
    elif message.text == 'Динамо':
        update_user_office(message, 2, "Динамо")
    elif message.text == 'Белорусская':
        update_user_office(message, 6, "Белорусская")
    elif message.text == 'Щербинка':
        update_user_office(message, 5, "Щербинка")
    elif message.text == 'Парк Культуры':
        update_user_office(message, 4, "Парк Культуры")
    elif message.text == 'Парк Кузьминки':
        update_user_office(message, 7, "Парк Кузьминки")
    elif message.text == 'Чертаново':
        update_user_office(message, 8, "Чертаново")


from datetime import datetime
def get_weekday_name(date_str):
    # Преобразуем строку даты в объект datetime
    date = datetime.strptime(date_str, "%Y-%m-%d")
    # Словарь для перевода названий дней недели
    weekdays = {
        "Monday": "ПН",
        "Tuesday": "ВТ",
        "Wednesday": "СР",
        "Thursday": "ЧТ",
        "Friday": "ПТ",
        "Saturday": "СБ",
        "Sunday": "ВС"
    }
    # Получаем день недели на английском и переводим на русский
    weekday_name = date.strftime("%A")
    return weekdays.get(weekday_name, "Неизвестный день")

def format_event_datetime(datetime_str):
    # Преобразуем строку даты и времени в объект datetime
    event_datetime = datetime.strptime(datetime_str, "%Y-%m-%d %H:%M:%S")  # Предполагаем, что это формат входной строки
    # Форматируем дату и время согласно заданию
    formatted_datetime = event_datetime.strftime("%d %B %H:%M")
    # Словарь для перевода названий месяцев
    months = {
        "January": "января", "February": "февраля", "March": "марта",
        "April": "апреля", "May": "мая", "June": "июня",
        "July": "июля", "August": "августа", "September": "сентября",
        "October": "октября", "November": "ноября", "December": "декабря"
    }
    # Извлекаем день, месяц и время
    day = event_datetime.strftime("%d")
    month_en = event_datetime.strftime("%B")
    time = event_datetime.strftime("%H:%M")
    # Переводим месяц
    month_ru = months.get(month_en, "неизвестно")
    # Собираем итоговую строку
    return f"{day} {month_ru} {time}"


def show_available_events(message):
    telegram_id = message.from_user.id
    events = get_available_events(telegram_id)
    sorted_events = sorted(events, key=lambda x: x['office_name'])
    if sorted_events:
        markup = types.InlineKeyboardMarkup()
        for event in sorted_events:
            free_places_percentage = (1 - (event['registered_participants'] / event['max_participants'])) * 100
            # Форматируем дату и время события для отображения
            formatted_datetime = format_event_datetime(event['datetime'])
            weekday_name = get_weekday_name(event['datetime'].split(" ")[0])
            # Теперь включаем описание тренера в текст сообщения
            coach_description = event.get('coach_description', 'Информация о тренере недоступна')  # Предполагаем, что API возвращает 'coach_description'
            button_text = f"{coach_description} {weekday_name}, {formatted_datetime} {event['office_name']}"  # Добавляем описание тренера в текст кнопки
            if free_places_percentage < 20:
                button_text += " ⚠️"  # Добавляем эмодзи, если мест меньше 20%
            markup.add(types.InlineKeyboardButton(text=button_text, callback_data=f"reg_{event['event_id']}"))
        bot.send_message(message.chat.id, "Выберите событие для записи:", reply_markup=markup)
    else:
        bot.send_message(message.chat.id, "На данный момент нет доступных событий.")


def show_available_events_by_id(telegram_id, chat_id):
    events = get_available_events(telegram_id)
    sorted_events = sorted(events, key=lambda x: x['office_name'])
    if sorted_events:
        markup = types.InlineKeyboardMarkup()
        for event in sorted_events:
            free_places_percentage = (1 - (event['registered_participants'] / event['max_participants'])) * 100
            # Форматируем дату и время события для отображения
            formatted_datetime = format_event_datetime(event['datetime'])
            weekday_name = get_weekday_name(event['datetime'].split(" ")[0])
            # Включаем описание тренера в текст сообщения
            coach_description = event.get('coach_description', 'Информация о тренере недоступна')
            button_text = f"{coach_description} {weekday_name}, {formatted_datetime} {event['office_name']}"
            if free_places_percentage < 20:
                button_text += " ⚠️"  # Добавляем эмодзи, если мест меньше 20%
            markup.add(types.InlineKeyboardButton(text=button_text, callback_data=f"reg_{event['event_id']}"))
        # Отправляем описания тренеров перед кнопками
        bot.send_message(chat_id, "Информация о тренерах и доступные события:", parse_mode='Markdown')
        bot.send_message(chat_id, "Выберите событие для записи:", reply_markup=markup)
    else:
        bot.send_message(chat_id, "На данный момент нет доступных событий.")


def show_user_events(message):
    telegram_id = message.from_user.id
    events = get_user_events(telegram_id)
    if events:
        markup = types.InlineKeyboardMarkup()
        for event in events:
            markup.add(types.InlineKeyboardButton(text=f"{event['event_date']} {event['event_time']} {event['office_name']}", callback_data=f"unreg_{event['event_id']}"))
        bot.send_message(message.chat.id, "Ваши записи на йогу.\nЧтобы отменить запись - нажмите на неё:", reply_markup=markup)
    else:
        bot.send_message(message.chat.id, "Если вы захотите посетить йогу - то вы можете снова записаться на занятие!")


@bot.callback_query_handler(func=lambda call: True)
def handle_callback_query(call):
    telegram_id = call.from_user.id
    chat_id = call.message.chat.id
    if call.data.startswith("reg_"):
        event_id = call.data.split("_")[1]
        if register_for_event(telegram_id, event_id):

            bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
            show_available_events_by_id(telegram_id, chat_id)
            bot.send_message(chat_id, "**Вы успешно записались на событие!**", parse_mode='Markdown')
            show_main_menu(call.message.chat.id)
        else:
            bot.answer_callback_query(call.id, "Произошла ошибка при записи на событие или места на занятие закончились.", show_alert=True)
    elif call.data.startswith("unreg_"):
        event_id = call.data.split("_")[1]
        if delete_event_registration(telegram_id, event_id):
            # Изменено здесь: замена на send_message для отправки сообщения пользователю
            bot.send_message(chat_id, "Вы успешно отменили запись на событие.") # todo - добавить логирование отписок от событий с датами отписки
            bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
            show_main_menu(call.message.chat.id)
        else:
            bot.answer_callback_query(call.id, "Произошла ошибка при отмене записи на событие.", show_alert=True)

from telebot import types
def show_main_menu(chat_id):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False)
    markup.row('Записаться на йогу', 'Мои записи на йогу')
    markup.row('Выбрать любимый офис')
    bot.send_message(chat_id, "Выберите действие:", reply_markup=markup)



def show_main_menu_first(chat_id):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False)
    markup.add('Записаться на йогу', 'Мои записи на йогу', 'Выбрать любимый офис')
    bot.send_message(chat_id, "Теперь вы можете записаться на йогу!", reply_markup=markup)

def choose_favorite_office(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add('Динамо', 'Чертаново', 'Парк Кузьминки')
    bot.send_message(message.chat.id, "Выберите ваш любимый офис:", reply_markup=markup)

def send_office_preference_to_api(telegram_id, office_id):
    endpoint = f"{API_URL}/users/office/{telegram_id}"
    headers = {
        'Content-Type': 'application/json',
        'X-API-KEY': API_KEY
    }
    data = {
        'office_id': office_id
    }
    try:
        response = requests.put(endpoint, json=data, headers=headers)
        return response.ok  # Возвращает True, если статус ответа в диапазоне 200-299
    except requests.RequestException as e:
        print(f"Ошибка при отправке запроса к API: {e}")
        return False

def update_user_office(message, office_id, office_name):
    telegram_id = message.from_user.id
    # Здесь предполагается, что функция отправляет запрос к API для обновления предпочтения пользователя
    success = send_office_preference_to_api(telegram_id, office_id)

    if success:
        bot.send_message(message.chat.id,
                         f"Вы выбрали любимым офис {office_name}. Теперь вам будут предлагаться только события в этом офисе.")
    else:
        bot.send_message(message.chat.id, "Произошла ошибка при обновлении вашего любимого офиса.")

    show_main_menu(message.chat.id)  # Показываем главное меню снова


if __name__ == '__main__':
    bot.polling(none_stop=True)