import re
import logging
import asyncio
import sqlite3
from datetime import datetime, timedelta

from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from keyboards import inline_kb, secondary_kb, third_kb, confirmation_kb, my_reports_kb,\
    create_game_stats_kb, create_report_kb
from keyboards import create_proficiency_type_keyboard, create_skills_keyboard, create_change_stats_keyboard,\
    create_habits_keyboard, create_goals_keyboard
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
            goals TEXT
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
    conn.commit()
    conn.close()


create_db()


# Функция для создания клавиатуры выбора даты
def create_date_keyboard():
    today = datetime.now().date()
    keyboard = types.InlineKeyboardMarkup(row_width=7)
    for i in range(7):
        date = today - timedelta(days=i)
        callback_data = date.isoformat()  # Используем ISO-формат для передачи даты
        button_text = date.strftime('%d.%m.%Y')
        keyboard.insert(types.InlineKeyboardButton(button_text, callback_data=callback_data))
    return keyboard


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


@dp.callback_query_handler(lambda c: c.data == 'create_game_stats')
async def process_callback_create_game_stats(callback_query: types.CallbackQuery, state: FSMContext):
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(callback_query.from_user.id, "1)Придумай себе никнейм.(если не получается можешь ввести ФИО")

    # Устанавливаем состояние 'name'
    await UserInfo.name.set()


@dp.message_handler(state=UserInfo.name)
async def user_name(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['name'] = message.text

    await UserInfo.next()
    await bot.send_message(message.chat.id, 'Приятно познакомиться! Никнейм для твоей игровой статистики внесён')
    await asyncio.sleep(2)
    await bot.send_message(message.chat.id, '2)Введи дату своего рождения (требуется для выяснения твоего текущего'
                                            'уровня и количества опыта)')


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
    await bot.send_message(message.chat.id, '3)Какие навыки хочешь прокачать/обрести?\n'
                                            'PS. Также оцени на каком уровне в том или ином навыке ты находишься прямо '
                                            'сейчас. (На каждом ранге разный уровень сложности прокачки, поэтому '
                                            'старайся отвечать максимально точно)👐.\n'
                                            '0-10 Lvl - "Новичок"\n'
                                            '10-20 Lvl - "Ниже-среднего"\n'
                                            '20-30 Lvl - "Средний"\n'
                                            '30-40 Lvl - "Выше среднего"\n'
                                            '40-50 Lvl - "Продвинутый"\n'
                                            '50-60 Lvl - "Эксперт"\n'
                                            '60-70 Lvl - "Профессионал"\n'
                                            '70-80 Lvl - "Мастер"\n'
                                            '80-90 Lvl - "Великий"\n'
                                            '90-100 Lvl - "Лучший"\n'
                           )


@dp.message_handler(state=UserInfo.skills)
async def user_skills(message: types.Message, state: FSMContext):
    skill_pattern = r'^[А-Яа-яёЁA-Za-z ]+ \d{1,2}$'
    skills = message.text.split('\n')

    for skill in skills:
        if not re.match(skill_pattern, skill.strip()):
            await bot.send_message(message.chat.id,
                                   "Ошибка! Введите каждый навык в формате '(какой-то навык) (подходящий Lvl)'")
            return

    async with state.proxy() as data:
        data['skills'] = message.text

    await UserInfo.next()
    await bot.send_message(message.chat.id, 'Интересные навыки, они внесены в твою игровую статистику!')
    await asyncio.sleep(2)
    await bot.send_message(message.chat.id, '4)Какие привычки ты хотел бы привить/избавиться?')


@dp.message_handler(state=UserInfo.habits)
async def user_habits(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['habits'] = message.text

    await UserInfo.next()
    await bot.send_message(message.chat.id, 'Хорошо что ты решил начать это делать!\n'
                                            ' Привычки внесены в игровую статистику')
    await asyncio.sleep(2)
    await bot.send_message(message.chat.id, '5)Каких целей ты хотел бы достичь за ближайшие 12 месяцев?\n'
                                            '(записывай цели в настоящем времени, будто ты их уже достиг и\n'
                                            'подпиши дату, когда та или иная цель должна быть достигнута)')


@dp.message_handler(state=UserInfo.goals)
async def user_goals(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['goals'] = message.text

    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()

    user_id = message.from_user.id

    name = data['name']
    birth = data['birth']
    skills = data['skills']
    habits = data['habits']
    goals = data['goals']

    # Сохранение данных в базу данных

    cursor.execute('''
        INSERT INTO users (user_id, name, birth, skills, habits, goals)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (user_id, name, birth, skills, habits, goals))
    conn.commit()
    conn.close()
    await bot.send_message(message.from_user.id, "Твои данные сохранены в игровую статистику!")
    await bot.send_message(message.chat.id,
                           'Какие амбициозные цели! Теперь они готовы МОТИВИРОВАТЬ ТЕБЯ изо дня в день!')
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
        "birth": "Даты Рождения",
        "skills": "Навыки",
        "habits": "Привычки",
        "goals": "Цели"
    }
    await bot.send_message(callback_query.from_user.id,
                           f"Введите новые данные для {stat_to_change_text[data['stat_to_change']]}:")
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
    cursor.execute('SELECT * FROM reports WHERE user_id = ?', (user_id,))
    reports = cursor.fetchall()
    conn.close()

    if reports:
        await bot.answer_callback_query(callback_query.id)
        await bot.send_message(callback_query.from_user.id, "Тут будут твои отчёты!")
        for report in reports:
            await bot.send_message(callback_query.from_user.id, f"Отчёт {report[0]}: {report[2]}")
    else:
        await bot.answer_callback_query(callback_query.id)
        await bot.send_message(callback_query.from_user.id, "У тебя нет ни одного отчёта! Создай же его!",
                               reply_markup=create_report_kb)


# Обработчик для кнопки "Создать Отчет"
@dp.callback_query_handler(lambda c: c.data == 'create_report')
async def process_callback_create_report(callback_query: types.CallbackQuery, state: FSMContext):
    user_id = callback_query.from_user.id

    # Подключение к базе данных
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()

    # Проверка наличия игровой статистики
    cursor.execute('SELECT 1 FROM users WHERE user_id = ?', (user_id,))
    user_has_game_stats = cursor.fetchone() is not None

    conn.close()

    if user_has_game_stats:
        await bot.answer_callback_query(callback_query.id)
        await bot.send_message(callback_query.from_user.id, "1) Для какого дня ты хочешь создать отчёт? Выбери дату:",
                               reply_markup=create_date_keyboard())

        await state.set_state(Report.choosing_date)
    else:
        await bot.answer_callback_query(callback_query.id)
        await bot.send_message(callback_query.from_user.id, "Без игровой статистики ты не сможешь создать отчет!"
                                                            " Создай игровую статистику.",
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
        await bot.send_message(callback_query.from_user.id, "2) Какие навыки ты сегодня прокачал?",
                               reply_markup=create_skills_keyboard(skills))
        await state.set_state(Report.skills_report)
    else:
        await bot.send_message(callback_query.from_user.id, "У тебя нет сохранённых навыков!")


# Обработчик для выбора навыка из списка
@dp.callback_query_handler(lambda c: c.data.startswith('skill_'), state=Report.skills_report)
async def add_report_data1(callback_query: types.CallbackQuery, state: FSMContext):
    skill = callback_query.data.split('_')[1]

    # Сохраняем выбранный навык в состоянии пользователя
    await state.update_data(skill=skill)

    await bot.send_message(callback_query.from_user.id, "3) Выберите способ прокачки:",
                           reply_markup=create_proficiency_type_keyboard())
    await state.set_state(Report.method)


# Обработчик для выбора способа прокачки
@dp.callback_query_handler(lambda c: c.data in ['practical_proficiency', 'theoretical_proficiency'],
                           state=Report.method)
async def process_proficiency_type_choice(callback_query: types.CallbackQuery, state: FSMContext):
    proficiency_type = "Практическая Прокачка" if callback_query.data == 'practical_proficiency'\
        else "Теоретическая Прокачка"

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
        await bot.send_message(message.chat.id, "3) Поставь галочки к привычкам, которые соблюдал.",
                               reply_markup=create_habits_keyboard(habits))
    else:
        await bot.send_message(message.chat.id, "У тебя нет сохранённых привычек!")
    await state.set_state(Report.habits_report)


# Обработчик для добавления данных в отчет
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

    # Получение целей пользователя из базы данных
    user_id = callback_query.from_user.id
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('SELECT goals FROM users WHERE user_id = ?', (user_id,))
    user_goals = cursor.fetchone()
    conn.close()

    if user_goals and user_goals[0]:
        goals = user_goals[0].split(',')
        await bot.send_message(callback_query.from_user.id, "4) К каким целям ты стал ближе? (можно ничего не выбрать)",
                               reply_markup=create_goals_keyboard(goals))
        await state.set_state(Report.goals_report)
        asyncio.create_task(send_goal_reminder(user_id, state))
    else:
        await bot.send_message(callback_query.from_user.id, "У тебя нет сохранённых целей!")
        await save_report_and_finalize(user_id, state)


# Обработчик для выбора целей из клавиатуры create_goals_keyboard
@dp.callback_query_handler(lambda c: c.data.startswith('goal_'), state=Report.goals_report)
async def process_goals_report(callback_query: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as data:
        if 'goals' not in data:
            data['goals'] = []
        data['goals'].append(callback_query.data.split('_')[1])

    await callback_query.answer("Цель отмечена!")
    await save_report_and_finalize(callback_query.from_user.id, state)


# Функция для сохранения отчета и подведения итогов
async def save_report_and_finalize(user_id, state):
    async with state.proxy() as data:
        chosen_date = data['chosen_date']
        skill = data['skill']
        proficiency_type = data['proficiency_type']
        time_spent = data['time_spent']
        chosen_habits = data['habits']
        all_habits = data['all_habits']
        chosen_goals = data.get('goals', [])

    # Определение соблюденных и несоблюденных привычек
    observed_habits = [habit for habit in chosen_habits]
    not_observed_habits = [habit for habit in all_habits if habit not in chosen_habits]

    # Сохранение данных в базу
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO reports (user_id, report_date, skill, proficiency_type, time_spent, habits_observed, habits_not_observed, goals_achieved)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (user_id, chosen_date, skill, proficiency_type, time_spent, ','.join(observed_habits), ','.join(not_observed_habits), ','.join(chosen_goals)))
    conn.commit()
    conn.close()

    # Формирование итогового сообщения
    final_message = (
        f"Итог\n"
        f"Навык: {skill} + {time_spent} ХР + 1 Lvl\n"
        f"Соблюдены привычки: {', '.join(observed_habits)}\n"
        f"Не соблюдены: {', '.join(not_observed_habits)}\n"
        f"Приближение к цели: {', '.join([goal + ' + 1%' for goal in chosen_goals])}\n"
    )
    await bot.send_message(user_id, final_message)

    # Переход к следующему состоянию или завершение
    await state.finish()


# Таймер для отправки напоминания о целях
async def send_goal_reminder(user_id, state):
    await asyncio.sleep(10)
    async with state.proxy() as data:
        if 'goals' not in data or not data['goals']:
            await bot.send_message(user_id, "Дружок! Цели сами себя не достигнут, вставай с дивана!")
            await save_report_and_finalize(user_id, state)


@dp.callback_query_handler(lambda c: c.data == 'back')
async def process_callback_back(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(callback_query.from_user.id, "Выбор действия:", reply_markup=secondary_kb)
    # Вызов главного меню или другой необходимой логики


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
