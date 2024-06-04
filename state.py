from aiogram.dispatcher.filters.state import State, StatesGroup


class UserInfo(StatesGroup):
    name = State()  # Состояние для имени
    birth = State()  # Состояние для даты рождения
    skills = State()  # Состояние для навыков
    habits = State()  # Состояние для привычек
    goals = State()  # Состояние для целей


class Report(StatesGroup):
    choosing_date = State()
    skills_report = State()
    method = State()
    input_time = State()
    habits_report = State()
    goals_report = State()


class ChangeStats(StatesGroup):
    waiting_for_stat_choice = State()
    waiting_for_new_value = State()
