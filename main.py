import asyncio

from aiogram import Bot, Dispatcher, types
from aiogram.filters.command import Command
from aiogram.filters.state import StatesGroup, State, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
import sqlite3
import requests

#  Создание экземпляра бота
bot = Bot(token='7603118234:AAEQwEVKpLgiAucQzmICfN9YLtFkGLrEWn8')

storage = MemoryStorage()

#  Создание экземпляра диспетчера
dp = Dispatcher(storage=storage)


class CheckStockStates(StatesGroup):
    StockID = State()
    StockPrice = State()
    StockQuantity = State()


class User:
    def __init__(self, telegram_id):
        self.telegram_id = telegram_id

    def write_data(self):
        conn = sqlite3.connect('./app_data/database.db')
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS users (telegram_id INTEGER PRIMARY KEY)''')
        cursor.execute('INSERT INTO users (telegram_id) VALUES (?)', (self.telegram_id,))
        inserted_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return inserted_id

    def read_data(self):
        conn = sqlite3.connect('./app_data/database.db')
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS users (telegram_id INTEGER PRIMARY KEY AUTOINCREMENT)''')
        cursor.execute('SELECT * FROM users WHERE telegram_id = ?', (self.telegram_id,))
        result = cursor.fetchone()
        if result is None:
            return None
        conn.close()
        return result


#  Обработчик команды /start
@dp.message(Command('start'))
async def start_command(message: types.Message):
    await message.reply('Привет! Я бот! Для регистрации /reg')


#  Обработчик команды /reg
@dp.message(Command('reg'))
async def reg_command(message: types.Message):
    user_tg_id = message.from_user.id
    new_user = User(user_tg_id)
    if new_user.read_data() is None:
        new_user.write_data()
        await message.reply('Регистрация прошла успешно')
    else:
        await message.reply(f'Вы зарегистрированы, ваш id: {str(user_tg_id)}')


# Проверка существования тикера
def check_stock_existence(stock_id):
    url = f'https://iss.moex.com/iss/securities/{stock_id}.json'
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        exist = data.get('boards', {}).get('data', [])
        return bool(exist) if exist != [] else False
    else:
        return False


#  Получение стоимости запрошенного тикера
def get_stock_price(stock_id: str) -> (float, str):
    url = f'https://iss.moex.com/iss/engines/stock/markets/shares/boards/TQBR/securities/{stock_id}.json?iss.only=securities&securities.columns=PREVPRICE,CURRENCYID'
    response = requests.get(url)
    stock_price = ''
    stock_currency = ''
    if response.status_code == 200:
        data = response.json()
        data = data.get('securities').get('data')
        stock_price = data[0][0]
        stock_currency = data[0][1]
        if stock_currency == 'SUR':
            stock_currency = 'RUB'

    return stock_price, stock_currency


#  Обработчик команды /checkStock
@dp.message(Command('checkStock'))
async def check_stock_start(message: types.Message, state: FSMContext):
    await message.reply('Хорошо! Введи тикер ценной бумаги')
    await state.set_state(CheckStockStates.StockID)


@dp.message(StateFilter(CheckStockStates.StockID))
async def check_stock_id(message: types.Message, state: FSMContext):
    stock_id = message.text.upper()
    stock_existence = check_stock_existence(stock_id)
    if stock_existence:
        stock_price, stock_currency = get_stock_price(stock_id)
        await message.reply(f'Стоимость {stock_price} {stock_currency}')
    else:
        await message.reply('Ценная бумага не существует. Попробуй ввести другой тикер /checkStock')
    await state.clear()


async def main():
    await dp.start_polling(bot)


#  Запуск бота
if __name__ == '__main__':
    asyncio.run(main())

# Материалы с первого занятия https://drive.google.com/drive/folders/1ceEmfDI8JSJip_3gQnyWgY5f-YFbH7T5?usp=share_link
# Материалы второго урока https://drive.google.com/drive/folders/1j1CTWkn4gdCuysjCVEPWHO06ZVn8upZc?usp=share_link
