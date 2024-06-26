from datetime import datetime, timedelta
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


inline_kb = InlineKeyboardMarkup().add(
    InlineKeyboardButton('Перейти в Главное Меню', callback_data='main_menu')
)


secondary_kb = InlineKeyboardMarkup().add(
    InlineKeyboardButton('Игровая Статистика', callback_data='game_stats')
).add(
    InlineKeyboardButton('Отчеты', callback_data='reports')
).add(
    InlineKeyboardButton('Служба Поддержки', callback_data='support_services')
)


third_kb = InlineKeyboardMarkup().add(
    InlineKeyboardButton('Посмотреть Статистику', callback_data='view_stats')
).add(
    InlineKeyboardButton('Изменить Статистику', callback_data='change_stats')
).add(
    InlineKeyboardButton('Очистить Статистику', callback_data='clear_stats')
).add(
    InlineKeyboardButton('Назад', callback_data='back')
)

# Создание клавиатуры с кнопками "Принять" и "Отменить"
confirmation_kb = InlineKeyboardMarkup()
confirmation_kb.add(InlineKeyboardButton('Принять', callback_data='accept'))
confirmation_kb.add(InlineKeyboardButton('Отменить', callback_data='cancel'))

# Создание клавиатуры с кнопками "Принять" и "Отменить"
confirmation_kb2 = InlineKeyboardMarkup()
confirmation_kb2.add(InlineKeyboardButton('Принять статистику', callback_data='accept_stat'))
confirmation_kb2.add(InlineKeyboardButton('Отменить сохранение', callback_data='cancel_stat'))


my_reports_kb = InlineKeyboardMarkup().add(
    InlineKeyboardButton('Мои Отчёты', callback_data='my_reports')
)
my_reports_kb.add(
    InlineKeyboardButton('Создать Отчет', callback_data='create_report')
)
my_reports_kb.add(
    InlineKeyboardButton('Назад', callback_data='back_from_reports')
)

create_game_stats_kb = InlineKeyboardMarkup()
create_game_stats_kb.add(InlineKeyboardButton('Создать Игровую Статистику', callback_data='create_game_stats'))
create_game_stats_kb.add(InlineKeyboardButton('Назад', callback_data='back'))

# Создание клавиатуры для кнопки "Создать Отчет" и "Назад"
create_report_kb = InlineKeyboardMarkup()
create_report_kb.add(InlineKeyboardButton('Создать Отчет', callback_data='create_report'))
create_report_kb.add(InlineKeyboardButton('Назад', callback_data='back_from_reports'))


# Функция для создания клавиатуры способа прокачки
def create_proficiency_type_keyboard():
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("Практическая Прокачка", callback_data='practical_proficiency'))
    keyboard.add(InlineKeyboardButton("Теоретическая Прокачка", callback_data='theoretical_proficiency'))
    return keyboard


def create_skills_keyboard(skills):
    keyboard = InlineKeyboardMarkup(row_width=1)
    for skill in skills:
        keyboard.add(InlineKeyboardButton(skill, callback_data=f'skill_{skill}'))
    keyboard.add(InlineKeyboardButton("Ни одного", callback_data='skill_none'))
    return keyboard


# Функция для создания клавиатуры изменения статистики
def create_change_stats_keyboard():
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("Никнейм", callback_data='change_name'))
    keyboard.add(InlineKeyboardButton("Дата Рождения", callback_data='change_birth'))
    keyboard.add(InlineKeyboardButton("Навыки", callback_data='change_skills'))
    keyboard.add(InlineKeyboardButton("Привычки", callback_data='change_habits'))
    keyboard.add(InlineKeyboardButton("Цели", callback_data='change_goals'))
    return keyboard


# Функция для создания клавиатуры выбора привычек
def create_habits_keyboard(habits):
    keyboard = InlineKeyboardMarkup(row_width=1)
    for habit in habits:
        keyboard.add(InlineKeyboardButton(habit, callback_data=f'habit_{habit}'))
    keyboard.add(InlineKeyboardButton("Пропустить", callback_data="habit_skip"))  # Добавляем кнопку "Пропустить"
    return keyboard


# Функция для создания клавиатуры выбора целей
def create_goals_keyboard(goals):
    keyboard = InlineKeyboardMarkup(row_width=1)
    for goal in goals:
        keyboard.add(InlineKeyboardButton(goal, callback_data=f'goal_{goal}'))
    keyboard.add(InlineKeyboardButton("Пропустить", callback_data="goal_skip"))  # Добавляем кнопку "Пропустить"
    return keyboard


# Функция для создания клавиатуры выбора даты
def create_date_keyboard():
    today = datetime.now().date()
    keyboard = InlineKeyboardMarkup(row_width=7)
    for i in range(7):
        date = today - timedelta(days=i)
        callback_data = date.isoformat()  # Используем ISO-формат для передачи даты
        button_text = date.strftime('%d.%m.%Y')
        keyboard.insert(InlineKeyboardButton(button_text, callback_data=callback_data))
    return keyboard
