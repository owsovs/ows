from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

def admin_keyboard():
    keyboard = InlineKeyboardMarkup(row_width=2)
    view_tickets_button = InlineKeyboardButton(text="Просмотреть тикеты", callback_data="view_tickets_admin")
    keyboard.add(view_tickets_button)
    return keyboard

def support_keyboard():
    keyboard = InlineKeyboardMarkup(row_width=2)
    create_ticket_button = InlineKeyboardButton(text="Создать тикет", callback_data="create_ticket")
    view_tickets_button = InlineKeyboardButton(text="Просмотреть тикеты", callback_data="view_tickets")
    keyboard.add(create_ticket_button, view_tickets_button)
    return keyboard
