import configparser
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.contrib.fsm_storage.memory import MemoryStorage

config = configparser.ConfigParser()
config.read('config.ini')

API_TOKEN = config['telegram']['Token']
ADMIN_ID = int(config['DEFAULT']['AdminID'])

bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)
dp.middleware.setup(LoggingMiddleware())

user_tickets = {}

class SupportStates(StatesGroup):
    waiting_for_message = State()
    reply = State()

def main_keyboard(is_admin):
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    if is_admin:
        keyboard.add(KeyboardButton("Просмотреть тикеты"))
    else:
        keyboard.add(KeyboardButton("Создать новый тикет"), KeyboardButton("Просмотреть тикеты"))
    return keyboard

@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    await message.answer("Lorena lorem lorem", reply_markup=InlineKeyboardMarkup().add(
        InlineKeyboardButton(text="Open WebApp", url="https://www.google.com")
    ))
    await message.answer("Добро пожаловать!", reply_markup=main_keyboard(message.from_user.id == ADMIN_ID))

@dp.message_handler(lambda message: message.text == "Создать новый тикет")
async def create_ticket(message: types.Message):
    await message.answer("Опишите проблему:", reply_markup=ReplyKeyboardMarkup(resize_keyboard=True).add(KeyboardButton("Отмена")))
    await SupportStates.waiting_for_message.set()

@dp.message_handler(lambda message: message.text == "Отмена", state=SupportStates.waiting_for_message)
async def cancel_ticket(message: types.Message, state: FSMContext):
    await state.finish()
    await message.answer("Действие отменено", reply_markup=main_keyboard(message.from_user.id == ADMIN_ID))

@dp.message_handler(state=SupportStates.waiting_for_message)
async def handle_ticket(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    ticket_number = len(user_tickets.get(user_id, [])) + 1
    user_tickets.setdefault(user_id, []).append({"number": ticket_number, "text": [message.text], "is_closed": False})
    
    await bot.send_message(ADMIN_ID, f"Новое сообщение от {user_id}:\n\n{message.text}")
    await message.answer(f"Тикет #{ticket_number} создан.")
    await state.finish()
    await message.answer("Что будем делать дальше?", reply_markup=main_keyboard(message.from_user.id == ADMIN_ID))

@dp.message_handler(lambda message: message.text == "Просмотреть тикеты")
async def view_tickets(message: types.Message):
    user_id = message.from_user.id
    tickets = user_tickets.get(user_id, [])
    if not tickets:
        await message.answer("Тикетов нет.")
        return
    
    for ticket in sorted(tickets, key=lambda t: t["is_closed"]):
        status = "Закрыт" if ticket["is_closed"] else "Открыт"
        text_messages = "\n".join(ticket["text"])
        keyboard = InlineKeyboardMarkup().add(
            InlineKeyboardButton(text="Ответить", callback_data=f"reply|{ticket['number']}")) if not ticket["is_closed"] else None
        await message.answer(f"Тикет #{ticket['number']} ({status}):\n{text_messages}", reply_markup=keyboard)

@dp.callback_query_handler(lambda c: c.data.startswith('reply|'))
async def reply_ticket(callback_query: types.CallbackQuery, state: FSMContext):
    ticket_number = int(callback_query.data.split('|')[1])
    user_id = callback_query.from_user.id

    await state.update_data(ticket_info=(user_id, ticket_number))
    await bot.send_message(user_id, "Напишите сообщение для тикета:")
    await SupportStates.reply.set()
    await bot.answer_callback_query(callback_query.id)

@dp.message_handler(state=SupportStates.reply)
async def send_reply(message: types.Message, state: FSMContext):
    data = await state.get_data()
    user_id, ticket_number = data['ticket_info']
    
    for ticket in user_tickets[user_id]:
        if ticket["number"] == ticket_number and not ticket["is_closed"]:
            ticket["text"].append(message.text)
            await bot.send_message(user_id if user_id == message.from_user.id else ADMIN_ID, f"Сообщение в тикете #{ticket_number}:\n{message.text}")
            break
    await state.finish()

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
