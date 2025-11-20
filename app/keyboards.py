from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

start = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Start daemon", callback_data="start_daemon")],
        [InlineKeyboardButton(text="Stop daemon", callback_data="stop_daemon")]
        [InlineKeyboardButton(text="Get last file", callback_data="get_last_file")]
    ]
)
