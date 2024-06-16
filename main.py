import re
import logging
import asyncio
import sqlite3
from datetime import datetime

from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from keyboards import inline_kb, secondary_kb, third_kb, confirmation_kb, my_reports_kb,\
    create_game_stats_kb, create_report_kb
from keyboards import create_proficiency_type_keyboard, create_skills_keyboard, create_change_stats_keyboard,\
    create_habits_keyboard, create_goals_keyboard, create_date_keyboard
from state import UserInfo, Report, ChangeStats


API_TOKEN = '5614902466:AAG5AcR0rd5Yrl-myulxQKQLJvR1n0O6ydI'

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Инициализация бота и диспетчера
bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)


# Функция для создания базы данных и таблицы пользователей
def create_db():
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            name TEXT,
            birth TEXT,
            skills TEXT,
            habits TEXT,
            goals TEXT,
            creation_date TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reports (
            report_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            report_date TEXT,
            skill TEXT,
            proficiency_type TEXT,
            time_spent INTEGER,
            habits_observed TEXT,
            habits_not_observed TEXT,
            goals_achieved TEXT,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
    ''')
    # Создание таблицы skills, если она не существует
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS skills (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            skill_name TEXT,
            xp INTEGER,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
        ''')

    # Создание таблицы habits, если она не существует
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS habits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            habit_name TEXT,
            progress INTEGER,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
        ''')

    # Создание таблицы goals, если она не существует
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS goals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            goal_name TEXT,
            progress INTEGER,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
    ''')
    conn.commit()
    conn.close()


create_db()


# Обработчик команды /start
@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    user_name = message.from_user.first_name
    await message.answer(f"👋Здарова {user_name}! Это Life=Game_bot. ✅Он поможет тебе чётко отслеживать свой"
                         f" прогресс, "
                         f"благодаря чему ты будешь получать мотивацию и эффективнее развиваться в жизненных сферах")

    # Пауза в 3 секунды
    await asyncio.sleep(3)

    await message.answer("🎮 Этот приём широко распространён в видео играх! Именно поэтому тебе хочется возвращаться"
                         " снова и выходить на новый уровень. 🔥Я же предлагаю перенести эту методику"
                         " в самую главную игру"
                         " под названием 'Real Life'. Чтобы с удовольствием прокачивать не игрового персонажа,"
                         " а самого себя! ", reply_markup=inline_kb)


# Обработчик нажатий на кнопки inline клавиатуры
@dp.callback_query_handler(lambda c: c.data == 'main_menu')
async def process_callback_main_menu(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(callback_query.from_user.id, "Главное Меню")
    await bot.send_message(callback_query.from_user.id, "Выбор действия:", reply_markup=secondary_kb)


# Обработчик для проверки наличия игровой статистики и выбора действий
@dp.callback_query_handler(lambda c: c.data == 'game_stats')
async def process_callback_game_stats(callback_query: types.CallbackQuery):
    # Подключение к базе данных
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()

    # Проверка наличия игровой статистики
    cursor.execute('SELECT 1 FROM users WHERE user_id = ?', (callback_query.from_user.id,))
    user_has_game_stats = cursor.fetchone() is not None

    conn.close()

    if user_has_game_stats:
        await bot.answer_callback_query(callback_query.id)
        await bot.send_message(callback_query.from_user.id, "Игровая Статистика")
        await bot.send_message(callback_query.from_user.id, "Выбор действия:", reply_markup=third_kb)
    else:
        await bot.answer_callback_query(callback_query.id)
        await bot.send_message(callback_query.from_user.id, "У тебя нет игровой статистики! Создай её прямо сейчас!",
                               reply_markup=create_game_stats_kb)


# Обработчик для просмотра игровой статистики
@dp.callback_query_handler(lambda c: c.data == 'view_stats')
async def process_callback_view_stats(callback_query: types.CallbackQuery, state: FSMContext):
    # Подключение к базе данных для получения информации о пользователе
    user_id = callback_query.from_user.id
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('SELECT name, birth, habits, goals FROM users WHERE user_id = ?', (user_id,))
    user_data = cursor.fetchone()
    conn.close()

    if user_data:
        name = user_data[0]
        birth_date_str = user_data[1]
        habits_str = user_data[2]
        goals_str = user_data[3]

        # Вычисление возраста пользователя в годах
        birth_date = datetime.strptime(birth_date_str, '%d.%m.%Y')
        today = datetime.now()
        age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))

        # Нахождение последнего дня рождения пользователя
        last_birthday = birth_date.replace(year=today.year)
        if last_birthday > today:
            last_birthday = last_birthday.replace(year=today.year - 1)

        # Рассчет количества дней, прошедших с последнего дня рождения
        days_after_birthday = (today - last_birthday).days

        # Форматирование привычек
        habits = habits_str.split(',') if habits_str else []
        formatted_habits = "\n".join([f"{idx + 1}. {habit.strip()}" for idx, habit in enumerate(habits)])

        # Форматирование целей
        goals = goals_str.split('\n') if goals_str else []
        formatted_goals = "\n".join([f"{idx + 1}. {goal.strip()}" for idx, goal in enumerate(goals)])

        # Определение количества дней в текущем месяце
        days_in_month = (datetime(today.year, today.month % 12 + 1, 1) - datetime(today.year, today.month, 1)).days

        # Определение количества дней в текущем году
        days_in_year = 366 if today.year % 4 == 0 and (today.year % 100 != 0 or today.year % 400 == 0) else 365

        # Формирование сообщения пользователю
        message_text = f"Игрок: {name}\n"
        message_text += f"Возраст: {age} Lvl\n"
        message_text += f"День после дня рождения: {days_after_birthday}/{days_in_year} ХР\n"
        message_text += f"Привычки:\n{formatted_habits if formatted_habits else 'Нет сохраненных привычек'}\n"
        message_text += f"Привычки:\n{formatted_habits if formatted_habits else 'Нет сохраненных привычек'}\n"
        message_text += f"Прогресс выполнения привычек: 0/{days_in_month} дней\n"
        message_text += f"Цели:\n{formatted_goals if formatted_goals else 'Нет сохраненных целей'}"

        await bot.answer_callback_query(callback_query.id)
        await bot.send_message(callback_query.from_user.id, message_text)


# Обработчик создания игровой статистики
@dp.callback_query_handler(lambda c: c.data == 'create_game_stats')
async def process_callback_create_game_stats(callback_query: types.CallbackQuery, state: FSMContext):
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(callback_query.from_user.id, "1) Придумай себе никнейм. (если не получается, можешь ввести ФИО)")
    await UserInfo.name.set()

@dp.message_handler(state=UserInfo.name)
async def user_name(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['name'] = message.text
    await UserInfo.next()
    await bot.send_message(message.chat.id, 'Приятно познакомиться! Никнейм для твоей игровой статистики внесён')
    await asyncio.sleep(2)
    await bot.send_message(message.chat.id, '2) Введи дату своего рождения (требуется для выяснения твоего текущего уровня и количества опыта)')

@dp.message_handler(state=UserInfo.birth)
async def user_birth_date(message: types.Message, state: FSMContext):
    date_pattern = r'^\d{2}\.\d{2}\.\d{4}$'
    if not re.match(date_pattern, message.text):
        await bot.send_message(message.chat.id, "Ошибка! Введите данные в формате '01.01.2000'")
        return

    async with state.proxy() as data:
        data['birth'] = message.text
    await UserInfo.next()
    await bot.send_message(message.chat.id, 'Класс! Твой текущий Lvl зафиксирован!')
    await asyncio.sleep(2)
    await bot.send_message(message.chat.id, '3) Какие навыки хочешь прокачать/обрести? (вводите навыки через запятую, без Lvl)\n'
                                            'PS. Также оцени на каком уровне в том или ином навыке ты находишься прямо сейчас. (На каждом ранге разный уровень сложности прокачки, поэтому старайся отвечать максимально точно)👐.\n'
                                            '0-10 Lvl - "Новичок"\n'
                                            '10-20 Lvl - "Ниже-среднего"\n'
                                            '20-30 Lvl - "Средний"\n'
                                            '30-40 Lvl - "Выше среднего"\n'
                                            '40-50 Lvl - "Продвинутый"\n'
                                            '50-60 Lvl - "Эксперт"\n'
                                            '60-70 Lvl - "Профессионал"\n'
                                            '70-80 Lvl - "Мастер"\n'
                                            '80-90 Lvl - "Великий"\n'
                                            '90-100 Lvl - "Лучший"\n')

@dp.message_handler(state=UserInfo.skills)
async def user_skills(message: types.Message, state: FSMContext):
    skill_pattern = r'^[А-Яа-яёЁA-Za-z ]+ \d{1,2}$'
    skills = message.text.split(',')

    for skill in skills:
        if not re.match(skill_pattern, skill.strip()):
            await bot.send_message(message.chat.id, "Ошибка! Введите каждый навык в формате '(какой-то навык) (подходящий Lvl)'")
            return

    async with state.proxy() as data:
        data['skills'] = ', '.join([skill.strip() for skill in skills])
    await UserInfo.next()
    await bot.send_message(message.chat.id, 'Интересные навыки, они внесены в твою игровую статистику!')
    await asyncio.sleep(2)
    await bot.send_message(message.chat.id, '4) Какие привычки ты хотел бы привить/избавиться? (вводите привычки через запятую)')

@dp.message_handler(state=UserInfo.habits)
async def user_habits(message: types.Message, state: FSMContext):
    habits = message.text.split(',')

    async with state.proxy() as data:
        data['habits'] = ', '.join([habit.strip() for habit in habits])

    await UserInfo.next()
    await bot.send_message(message.chat.id, 'Хорошо что ты решил начать это делать! Привычки внесены в игровую статистику')
    await asyncio.sleep(2)
    await bot.send_message(message.chat.id, '5) Каких целей ты хотел бы достичь за ближайшие 12 месяцев? (записывай цели в настоящем времени, будто ты их уже достиг и подпиши дату, когда та или иная цель должна быть достигнута)')

@dp.message_handler(state=UserInfo.goals)
async def user_goals(message: types.Message, state: FSMContext):
    goals_text = message.text
    goals = goals_text.split('\n')
    valid_goals = []

    for goal in goals:
        match = re.search(r'\d{2}\.\d{2}\.\d{4}', goal)
        if match:
            date_str = match.group()
            try:
                datetime.strptime(date_str, '%d.%m.%Y')
                valid_goals.append(goal)
            except ValueError:
                await bot.send_message(message.chat.id, f"Некорректная дата в цели: {goal}")
                return
        else:
            await bot.send_message(message.chat.id, f"Отсутствует дата в цели: {goal}")
            return

    async with state.proxy() as data:
        data['goals'] = '\n'.join(valid_goals)

    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()

    user_id = message.from_user.id
    name = data['name']
    birth = data['birth']
    skills = data['skills']
    habits = data['habits']
    goals = data['goals']
    creation_date = datetime.now().strftime('%Y-%m-%d')

    cursor.execute('''
        INSERT INTO users (user_id, name, birth, skills, habits, goals, creation_date)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (user_id, name, birth, skills, habits, goals, creation_date))

    for habit in habits.split(','):
        cursor.execute('''
            INSERT INTO habits (user_id, habit_name, progress)
            VALUES (?, ?, ?)
        ''', (user_id, habit.strip(), 0))

    conn.commit()
    conn.close()

    await bot.send_message(message.from_user.id, "Твои данные сохранены в игровую статистику!")
    await bot.send_message(message.chat.id, 'Какие амбициозные цели! Теперь они готовы МОТИВИРОВАТЬ ТЕБЯ изо дня в день!')
    await state.finish()


@dp.callback_query_handler(lambda c: c.data == 'accept_stats')
async def accept_stats(callback_query: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as data:
        user_id = callback_query.from_user.id
        name = data['name']
        birth = data['birth']
        skills = data['skills']
        habits = data['habits']
        goals = data['goals']
        print(data)

        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO users (user_id, name, birth, skills, habits, goals)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_id, name, birth, skills, habits, goals))
        conn.commit()
        conn.close()

    await bot.answer_callback_query(callback_query.id, text="Статистика сохранена!")
    await bot.send_message(callback_query.from_user.id, "Твои данные сохранены в игровую статистику!")
    await bot.send_message(callback_query.from_user.id, 'Какие амбициозные цели! Теперь они готовы МОТИВИРОВАТЬ ТЕБЯ изо дня в день!')
    await state.finish()

@dp.callback_query_handler(lambda c: c.data == 'cancel_stats')
async def cancel_stats(callback_query: types.CallbackQuery, state: FSMContext):
    await bot.answer_callback_query(callback_query.id, text="Сохранение отменено!")
    await bot.send_message(callback_query.from_user.id, "Сохранение статистики отменено.")
    await state.finish()


# Обработчик для кнопки "Изменить Статистику"
@dp.callback_query_handler(lambda c: c.data == 'change_stats')
async def process_callback_change_stats(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(callback_query.from_user.id, "Что ты хочешь изменить?",
                           reply_markup=create_change_stats_keyboard())
    await ChangeStats.waiting_for_stat_choice.set()


# Обработчик для выбора параметра изменения
@dp.callback_query_handler(lambda c: c.data.startswith('change_'), state=ChangeStats.waiting_for_stat_choice)
async def process_stat_choice(callback_query: types.CallbackQuery, state: FSMContext):
    await bot.answer_callback_query(callback_query.id)
    async with state.proxy() as data:
        data['stat_to_change'] = callback_query.data.split('_')[1]
    stat_to_change_text = {
        "name": "Никнейм",
        "birth": "Дата Рождения",
        "skills": "Навыки",
        "habits": "Привычки",
        "goals": "Цели"
    }

    stat_to_change = data['stat_to_change']
    message_text = f"Введите новые данные для {stat_to_change_text[stat_to_change]}:\n"

    # Добавляем дополнительное пояснение для всех, кроме "name" и "birth"
    if stat_to_change not in ["name", "birth"]:
        message_text += "(если несколько значений введите данные через запятую)"

    await bot.send_message(callback_query.from_user.id, message_text)
    await ChangeStats.waiting_for_new_value.set()


# Обработчик для ввода новых данных
@dp.message_handler(state=ChangeStats.waiting_for_new_value)
async def process_new_value(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        stat_to_change = data['stat_to_change']
        new_value = message.text
        user_id = message.from_user.id

    # Подключение к базе данных
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()

    if stat_to_change == 'birth':
        # Проверка правильности формата даты
        date_pattern = r'^\d{2}\.\d{2}\.\d{4}$'
        if not re.match(date_pattern, new_value):
            await bot.send_message(message.chat.id, "Ошибка! Введите данные в формате '01.01.2000'")
            return

    # Формирование запроса для обновления данных
    query = f'UPDATE users SET {stat_to_change} = ? WHERE user_id = ?'
    cursor.execute(query, (new_value, user_id))
    conn.commit()
    conn.close()

    await bot.send_message(message.chat.id, f"Твои данные для {stat_to_change} успешно обновлены на '{new_value}'!")
    await state.finish()


# Обработчик нажатий на кнопку "Очистить Статистику"
@dp.callback_query_handler(lambda c: c.data == 'clear_stats')
async def process_callback_clear_stats(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(callback_query.from_user.id, "Вы уверены? Статистика полностью очиститься!",
                           reply_markup=confirmation_kb)


# Обработчик нажатий на кнопки "Принять" и "Отменить"
@dp.callback_query_handler(lambda c: c.data in ['accept', 'cancel'])
async def process_callback_confirmation(callback_query: types.CallbackQuery):
    if callback_query.data == 'accept':
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        cursor.execute('DELETE FROM users WHERE user_id = ?', (callback_query.from_user.id,))
        conn.commit()
        conn.close()
        await bot.answer_callback_query(callback_query.id, text="Ваша статистика была успешно удалена.")
        await bot.send_message(callback_query.from_user.id, "Статистика успешно удалена.")
    elif callback_query.data == 'cancel':
        await bot.answer_callback_query(callback_query.id, text="Удаление статистики отменено.")
        await bot.send_message(callback_query.from_user.id, "Удаление статистики отменено.")

    await bot.send_message(callback_query.from_user.id, "Выбор действия:", reply_markup=secondary_kb)


@dp.callback_query_handler(lambda c: c.data == 'back')
async def process_callback_back(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(callback_query.from_user.id, "Главное Меню")
    await bot.send_message(callback_query.from_user.id, "Выбор действия:", reply_markup=secondary_kb)


# Обработчик для кнопки "Отчёты"
@dp.callback_query_handler(lambda c: c.data == 'reports')
async def process_callback_reports(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(callback_query.from_user.id, "Выберите опцию:", reply_markup=my_reports_kb)


# Обработчик для кнопки "Мои Отчёты"
@dp.callback_query_handler(lambda c: c.data == 'my_reports')
async def process_callback_my_reports(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id

    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('SELECT report_id, report_date FROM reports WHERE user_id = ?', (user_id,))
    reports = cursor.fetchall()
    conn.close()

    if reports:
        await bot.answer_callback_query(callback_query.id)
        await bot.send_message(callback_query.from_user.id, "Твои отчёты:")

        report_kb = InlineKeyboardMarkup(row_width=1)
        for report_id, report_date in reports:
            button_text = f"Отчёт от {report_date}"
            report_kb.add(InlineKeyboardButton(button_text, callback_data=f'report_{report_id}'))

        await bot.send_message(callback_query.from_user.id, "Выбери отчёт для просмотра деталей:",
                               reply_markup=report_kb)
    else:
        await bot.answer_callback_query(callback_query.id)
        await bot.send_message(callback_query.from_user.id, "У тебя нет ни одного отчёта! Создай же его!",
                               reply_markup=create_report_kb)


# Обработчик для выбора отчета
@dp.callback_query_handler(lambda c: c.data.startswith('report_'))
async def process_callback_view_report(callback_query: types.CallbackQuery):
    report_id = int(callback_query.data.split('_')[1])
    user_id = callback_query.from_user.id

    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()

    # Получение отчета из базы данных
    cursor.execute('''
        SELECT report_date, skill, proficiency_type, time_spent, habits_observed, habits_not_observed, goals_achieved 
        FROM reports WHERE report_id = ? AND user_id = ?
    ''', (report_id, user_id))
    report = cursor.fetchone()

    # Получение даты создания пользователя
    cursor.execute('''
        SELECT creation_date FROM users WHERE user_id = ?
    ''', (user_id,))
    creation_date_str = cursor.fetchone()

    conn.close()

    if report and creation_date_str:
        creation_date = datetime.strptime(creation_date_str[0], '%Y-%m-%d')
        report_date = datetime.strptime(report[0], '%Y-%m-%d')
        days_passed = (report_date - creation_date).days

        report_date, skill, proficiency_type, time_spent, habits_observed, habits_not_observed, goals_achieved = report
        goals_list = goals_achieved.split(', ')

        # Формирование строки с прогрессом выполнения целей
        goals_progress = [f"{goal} выполнена на {days_passed}%" for goal in goals_list]
        # дописать формирование прогресса привычек
        final_message = (
            f"Отчёт от {report_date}\n"
            f"Навык: {skill} (+ {time_spent} ХР, {proficiency_type})\n"
            f"Соблюдены привычки: {habits_observed}\n"
            f"Не соблюдены: {habits_not_observed}\n"
            f"Цели: {'; '.join(goals_progress)}\n"
        )
        await bot.answer_callback_query(callback_query.id)
        await bot.send_message(callback_query.from_user.id, final_message)
    else:
        await bot.answer_callback_query(callback_query.id)
        await bot.send_message(callback_query.from_user.id, "Отчет не найден.")


# Функция для вычисления уровня и опыта
def calculate_level_and_xp(birth_date_str):
    birth_date = datetime.strptime(birth_date_str, '%d.%m.%Y')
    today = datetime.now()
    age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
    next_birthday = birth_date.replace(year=today.year)
    if next_birthday < today:
        next_birthday = next_birthday.replace(year=today.year + 1)
    days_until_birthday = (next_birthday - today).days
    total_days_in_year = 366 if next_birthday.year % 4 == 0 else 365
    xp = total_days_in_year - days_until_birthday
    return age, xp, total_days_in_year


# Обработчик для кнопки "Создать Отчет"
@dp.callback_query_handler(lambda c: c.data == 'create_report')
async def process_callback_create_report(callback_query: types.CallbackQuery, state: FSMContext):
    user_id = callback_query.from_user.id

    # Подключение к базе данных
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()

    # Проверка наличия игровой статистики
    cursor.execute('SELECT name, birth, skills, habits, goals FROM users WHERE user_id = ?', (user_id,))
    user_data = cursor.fetchone()
    conn.close()

    if user_data:
        await bot.answer_callback_query(callback_query.id)
        await bot.send_message(callback_query.from_user.id, "1) Для какого дня ты хочешь создать отчёт? Выбери дату:",
                               reply_markup=create_date_keyboard())

        await state.set_state(Report.choosing_date)
    else:
        await bot.answer_callback_query(callback_query.id)
        await bot.send_message(callback_query.from_user.id, "Без игровой статистики ты не сможешь создать отчет! Создай игровую статистику.",
                               reply_markup=create_game_stats_kb)


# Обработчик для выбора даты отчета
@dp.callback_query_handler(state=Report.choosing_date)
async def process_callback_choose_date(callback_query: types.CallbackQuery, state: FSMContext):
    # Получаем выбранную пользователем дату из callback_data
    chosen_date = datetime.fromisoformat(callback_query.data).date()

    # Сохраняем выбранную дату в состоянии пользователя
    await state.update_data(chosen_date=chosen_date)

    # Выводим сообщение о сохранении даты
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(callback_query.from_user.id,
                           f"выбранная дата: {chosen_date.strftime('%d.%m.%Y')} - день для отчёта")

    # Подключение к базе данных для получения навыков пользователя
    user_id = callback_query.from_user.id
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('SELECT skills FROM users WHERE user_id = ?', (user_id,))
    user_skills = cursor.fetchone()
    conn.close()

    if user_skills:
        skills = user_skills[0].split(',')
        await bot.send_message(callback_query.from_user.id, "2) Какие навыки ты сегодня прокачал, "
                                                            "и что для этого сделал? (можно ничего не выбирать)",
                               reply_markup=create_skills_keyboard(skills))
        await state.set_state(Report.skills_report)
    else:
        await bot.send_message(callback_query.from_user.id, "У тебя нет сохранённых навыков!")


# Обработчик для выбора навыка из списка
@dp.callback_query_handler(lambda c: c.data.startswith('skill_'), state=Report.skills_report)
async def add_report_data1(callback_query: types.CallbackQuery, state: FSMContext):
    skill = callback_query.data.split('_')[1]

    async with state.proxy() as data:
        if 'skills' not in data:
            data['skills'] = []
        data['skills'].append(skill)

    await bot.answer_callback_query(callback_query.id, f"Навык '{skill}' добавлен. Выберите другие навыки или нажмите 'Дальше'.")


# Обработчик для кнопки "Дальше" после выбора навыков
@dp.callback_query_handler(lambda c: c.data == 'next_skill', state=Report.skills_report)
async def next_step(callback_query: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as data:
        if 'skills' not in data or not data['skills']:
            data['skills'] = []

    await bot.send_message(callback_query.from_user.id, "3) Выберите способ прокачки:",
                           reply_markup=create_proficiency_type_keyboard())
    await state.set_state(Report.method)


# Обработчик для пропуска выбора навыка
@dp.callback_query_handler(lambda c: c.data == 'none_skill', state=Report.skills_report)
async def skip_skill_selection(callback_query: types.CallbackQuery, state: FSMContext):
    await state.update_data(skills=[], proficiency_type=None, time_spent=0)  # Обновляем состояние

    # Получение привычек пользователя из базы данных
    user_id = callback_query.from_user.id
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('SELECT habits FROM users WHERE user_id = ?', (user_id,))
    user_habits = cursor.fetchone()
    conn.close()

    if user_habits and user_habits[0]:
        habits = user_habits[0].split(',')
        async with state.proxy() as data:
            data['all_habits'] = habits
        await bot.send_message(callback_query.from_user.id, "3) Поставь галочки к привычкам, которые соблюдал. (можно "
                                                           "ничего не выбрать)"
                                                           "По окончании выбора нажми кнопку Дальше",
                               reply_markup=create_habits_keyboard(habits))
    else:
        await bot.send_message(callback_query.from_user.id, "У тебя нет сохранённых привычек!")
    await state.set_state(Report.habits_report)


# Обработчик для выбора способа прокачки
@dp.callback_query_handler(lambda c: c.data in ['practical_proficiency', 'theoretical_proficiency'], state=Report.method)
async def process_proficiency_type_choice(callback_query: types.CallbackQuery, state: FSMContext):
    proficiency_type = "Практическая Прокачка" if callback_query.data == 'practical_proficiency' else "Теоретическая Прокачка"

    await state.update_data(proficiency_type=proficiency_type)

    await bot.send_message(callback_query.from_user.id, "Сколько времени ты это делал (1 минута = 1 ХР)?")
    await state.set_state(Report.input_time)


# Обработчик для ввода времени
@dp.message_handler(state=Report.input_time)
async def process_input_time(message: types.Message, state: FSMContext):
    time_spent = int(message.text)

    async with state.proxy() as data:
        data['time_spent'] = time_spent

    # Проверка количества прокачанных минут
    if time_spent >= 100:
        await bot.send_message(message.chat.id, "Молодец! Продолжай в том же духе.")
    else:
        await bot.send_message(message.chat.id, "Завтра постарайся получше, прокачка навыков повышает компетенцию!")

    # Получение привычек пользователя из базы данных
    user_id = message.from_user.id
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('SELECT habits FROM users WHERE user_id = ?', (user_id,))
    user_habits = cursor.fetchone()
    conn.close()

    if user_habits and user_habits[0]:
        habits = user_habits[0].split(',')
        async with state.proxy() as data:
            data['all_habits'] = habits
        await bot.send_message(message.chat.id, "3) Поставь галочки к привычкам, которые соблюдал. (можно "
                                                "ничего не выбрать). По окончании выбора нажми кнопку Дальше",
                               reply_markup=create_habits_keyboard(habits))
    else:
        await bot.send_message(message.chat.id, "У тебя нет сохранённых привычек!")
    await state.set_state(Report.habits_report)


# Обработчик для добавления привычек в отчет
@dp.callback_query_handler(lambda c: c.data.startswith('habit_'), state=Report.habits_report)
async def add_report_data3(callback_query: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as data:
        if 'habits' not in data:
            data['habits'] = []
        data['habits'].append(callback_query.data.split('_')[1])

    await callback_query.answer("Привычка отмечена!")

    # Получение всех привычек пользователя из состояния
    async with state.proxy() as data:
        chosen_habits = data.get('habits', [])
        all_habits = data.get('all_habits', [])

    total_habits = len(all_habits)
    chosen_habits_count = len(chosen_habits)
    if total_habits > 0 and chosen_habits_count / total_habits >= 0.5:
        await bot.send_message(callback_query.from_user.id, "Так держать! Не сдавайся!")
    else:
        await bot.send_message(callback_query.from_user.id, "Привычка формируется около 30 дней, не обнуляй прогресс")

    await asyncio.sleep(2)


# Обработчик для нажатия кнопки "Дальше" в выборе привычек
@dp.callback_query_handler(lambda c: c.data == 'next_habit', state=Report.habits_report)
async def process_habits_next(callback_query: types.CallbackQuery, state: FSMContext):
    user_id = callback_query.from_user.id
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('SELECT goals FROM users WHERE user_id = ?', (user_id,))
    user_goals = cursor.fetchone()
    conn.close()

    if user_goals and user_goals[0]:
        goals = user_goals[0].split(',')
        await bot.send_message(callback_query.from_user.id, "4) К каким целям ты стал ближе? (можно ничего не выбрать)"
                                                            "По окончании выбора нажми кнопку Дальше",
                               reply_markup=create_goals_keyboard(goals))
    else:
        await bot.send_message(callback_query.from_user.id, "У тебя нет сохранённых целей!")

    await state.set_state(Report.goals_report)


# Обработчик для пропуска выбора привычек
@dp.callback_query_handler(lambda c: c.data == 'skip_habit', state=Report.habits_report)
async def skip_habits_selection(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.answer("Выбор привычек пропущен.")
    user_id = callback_query.from_user.id
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('SELECT goals FROM users WHERE user_id = ?', (user_id,))
    user_goals = cursor.fetchone()
    conn.close()

    if user_goals and user_goals[0]:
        goals = user_goals[0].split(',')
        await bot.send_message(callback_query.from_user.id, "4) К каким целям ты стал ближе? (можно ничего не выбрать)"
                                                            "По окончании выбора нажми кнопку Дальше",
                               reply_markup=create_goals_keyboard(goals))
    else:
        await bot.send_message(callback_query.from_user.id, "У тебя нет сохранённых целей!")
    await state.set_state(Report.goals_report)


# Обработчик для выбора целей
@dp.callback_query_handler(lambda c: c.data.startswith('goal_'), state=Report.goals_report)
async def process_goals_report(callback_query: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as data:
        if 'goals' not in data:
            data['goals'] = []

        goal = callback_query.data.split('_')[1]
        data['goals'].append(goal)

    await callback_query.answer("Цель отмечена!")


# Обработчик для кнопки "Дальше"
@dp.callback_query_handler(lambda c: c.data == 'next_goal', state=Report.goals_report)
async def next_goal_selection(callback_query: types.CallbackQuery, state: FSMContext):
    await save_report_and_finalize(callback_query.from_user.id, state)


# Обработчик для кнопки "Пропустить"
@dp.callback_query_handler(lambda c: c.data == 'skip_goal', state=Report.goals_report)
async def skip_goal_selection(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.answer("Пропущен выбор целей.")
    await save_report_and_finalize(callback_query.from_user.id, state)


# Функция для сохранения отчета и завершения процесса
async def save_report_and_finalize(user_id, state):
    async with state.proxy() as data:
        skills = data.get('skills', [])
        time_spent = data.get('time_spent', 0)
        chosen_habits = data.get('habits', [])
        all_habits = data.get('all_habits', [])
        chosen_goals = data.get('goals', [])
        chosen_date = data.get('chosen_date')

    # Подключение к базе данных
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()

    # Получение данных пользователя
    cursor.execute('SELECT birth FROM users WHERE user_id = ?', (user_id,))
    birth_date_str = cursor.fetchone()[0]
    lvl, xp, total_days_in_year = calculate_level_and_xp(birth_date_str)

    # Обновление навыков
    if skills:
        for skill in skills:
            cursor.execute('SELECT xp FROM skills WHERE user_id = ? AND skill_name = ?', (user_id, skill))
            skill_xp = cursor.fetchone()
            if skill_xp:
                new_skill_xp = skill_xp[0] + time_spent
                cursor.execute('UPDATE skills SET xp = ? WHERE user_id = ? AND skill_name = ?', (new_skill_xp, user_id, skill))
            else:
                cursor.execute('INSERT INTO skills (user_id, skill_name, xp) VALUES (?, ?, ?)', (user_id, skill, time_spent))
        conn.commit()

    # Обновление привычек
    new_habit_progresses = {}
    if chosen_habits:
        for habit in chosen_habits:
            cursor.execute('SELECT progress FROM habits WHERE user_id = ? AND habit_name = ?', (user_id, habit))
            habit_progress = cursor.fetchone()
            if habit_progress:
                new_habit_progress = habit_progress[0] + 1
                new_habit_progresses[habit] = new_habit_progress
                cursor.execute('UPDATE habits SET progress = ? WHERE user_id = ? AND habit_name = ?', (new_habit_progress, user_id, habit))
            else:
                new_habit_progresses[habit] = 1
                cursor.execute('INSERT INTO habits (user_id, habit_name, progress) VALUES (?, ?, ?)', (user_id, habit, 1))
        conn.commit()

    if all_habits:
        for habit in all_habits:
            if habit not in chosen_habits:
                cursor.execute('SELECT progress FROM habits WHERE user_id = ? AND habit_name = ?', (user_id, habit))
                habit_progress = cursor.fetchone()
                if habit_progress:
                    new_habit_progress = habit_progress[0] - 2
                    new_habit_progresses[habit] = new_habit_progress
                    cursor.execute('UPDATE habits SET progress = ? WHERE user_id = ? AND habit_name = ?', (new_habit_progress, user_id, habit))
                else:
                    new_habit_progresses[habit] = -2
                    cursor.execute('INSERT INTO habits (user_id, habit_name, progress) VALUES (?, ?, ?)', (user_id, habit, -2))
        conn.commit()

    # Обновление целей
    if chosen_goals:
        for goal in chosen_goals:
            cursor.execute('SELECT progress FROM goals WHERE user_id = ? AND goal_name = ?', (user_id, goal))
            goal_progress = cursor.fetchone()
            if goal_progress:
                new_goal_progress = goal_progress[0] + 1
                if new_goal_progress >= 100:
                    # Если цель достигнута, задать вопрос пользователю
                    await bot.send_message(user_id, f"Ты достиг своей цели: {goal}? (да/нет)")
                    async with state.proxy() as data:
                        data['goal_to_check'] = goal
                    await state.set_state(Report.check_goal)
                else:
                    cursor.execute('UPDATE goals SET progress = ? WHERE user_id = ? AND goal_name = ?', (new_goal_progress, user_id, goal))
            else:
                cursor.execute('INSERT INTO goals (user_id, goal_name, progress) VALUES (?, ?, ?)', (user_id, goal, 1))
        conn.commit()

    # Формирование итогового сообщения
    final_message = f"Итог:\n"
    if skills:
        final_message += f"Навыки: {', '.join([f'{skill} + {time_spent} ХР + 1 Lvl' for skill in skills])}\n"
    else:
        final_message += "Навыки: не выбраны\n"

    observed_habits = [habit for habit in chosen_habits]
    not_observed_habits = [habit for habit in all_habits if habit not in chosen_habits]

    if observed_habits:
        final_message += f"Соблюдены привычки: {', '.join([f'{habit} {new_habit_progresses[habit]}/{30}' for habit in observed_habits])}\n"
    if not_observed_habits:
        final_message += f"Не соблюдены привычки: {', '.join([f'{habit} {new_habit_progresses[habit]}/{30}' for habit in not_observed_habits])}\n"

    final_message += f"Приближение к целям: {', '.join([f'{goal} +1%' for goal in chosen_goals])}\n"

    # Создание клавиатуры подтверждения
    keyboard = InlineKeyboardMarkup(row_width=2)
    accept_button = InlineKeyboardButton("Принять", callback_data="report_accept")
    cancel_button = InlineKeyboardButton("Отменить", callback_data="report_cancel")
    keyboard.add(accept_button, cancel_button)

    await bot.send_message(user_id, final_message, reply_markup=keyboard)



# Обработчик для проверки достижения цели
@dp.message_handler(state=Report.check_goal)
async def check_goal(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        goal = data['goal_to_check']

    if message.text.lower() == 'да':
        await bot.send_message(message.chat.id, f"Поздравляем! Цель '{goal}' достигнута и будет добавлена в раздел достигнутых целей.")
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        cursor.execute('DELETE FROM goals WHERE user_id = ? AND goal_name = ?', (message.from_user.id, goal))
        conn.commit()
        conn.close()
    else:
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        cursor.execute('UPDATE goals SET progress = 50 WHERE user_id = ? AND goal_name = ?', (message.from_user.id, goal))
        conn.commit()
        conn.close()
        await bot.send_message(message.chat.id, f"Цель '{goal}' возвращена на 50%.")

    await state.finish()


@dp.callback_query_handler(lambda c: c.data == 'report_accept', state='*')
async def process_report_accept(callback_query: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as data:
        user_id = callback_query.from_user.id
        chosen_date = data['chosen_date']
        skills = data['skills']
        proficiency_type = data['proficiency_type']
        time_spent = data['time_spent']
        chosen_habits = data['habits']
        all_habits = data['all_habits']
        chosen_goals = data.get('goals', [])

    # Преобразование списков в строки
    skills_str = ','.join(skills)
    chosen_habits_str = ','.join(chosen_habits)
    all_habits_str = ','.join([habit for habit in all_habits if habit not in chosen_habits])
    chosen_goals_str = ','.join(chosen_goals)

    # Сохранение данных в базу
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO reports (user_id, report_date, skill, proficiency_type, time_spent,
         habits_observed, habits_not_observed, goals_achieved)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (user_id, chosen_date, skills_str, proficiency_type,
          time_spent, chosen_habits_str, all_habits_str, chosen_goals_str))
    conn.commit()
    conn.close()

    await bot.send_message(callback_query.from_user.id, "Отчёт сохранён.")
    await state.finish()


@dp.callback_query_handler(lambda c: c.data == 'report_cancel', state='*')
async def process_report_cancel(callback_query: types.CallbackQuery, state: FSMContext):
    await bot.send_message(callback_query.from_user.id, "Отчёт отменён.")
    await state.finish()


@dp.callback_query_handler(lambda c: c.data == 'back')
async def process_callback_back(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(callback_query.from_user.id, "Выбор действия:", reply_markup=secondary_kb)


# Обработчик для кнопки "Назад" при просмотре отчетов
@dp.callback_query_handler(lambda c: c.data == 'back_from_reports')
async def process_callback_back_from_reports(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(callback_query.from_user.id, "Главное Меню", reply_markup=secondary_kb)


# Обработчик для кнопки "Служба Поддержки"
@dp.callback_query_handler(lambda c: c.data == 'support_services')
async def process_callback_support_services(callback_query: types.CallbackQuery):
    support_text = "Обратитесь сюда, если вам что-то непонятно:"
    support_link = "https://example.com/support"

    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(callback_query.from_user.id, f"{support_text}\n{support_link}")


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
