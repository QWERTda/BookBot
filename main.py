import asyncio
from aiogram import Bot, Dispatcher
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.fsm.storage.memory import MemoryStorage
from config import API_TOKEN

import requests

bot = Bot(token=API_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# Храним языковые настройки пользователей
user_languages = {}

# Сообщения на двух языках
messages = {
    "start": {
        "kk": "Сәлем! Қолайлы тілді таңдаңыз: қазақша немесе орысша.",
        "ru": "Привет! Выберите удобный язык: казахский или русский.",
    },
    "language_set": {
        "kk": "Тіл таңдалды: қазақша. Енді кітапты іздеңіз.",
        "ru": "Язык установлен: русский. Теперь введите название книги для поиска.",
    },
    "book_not_found": {
        "kk": "Кітап табылмады. Автор бойынша іздеу басталды...",
        "ru": "Книга не найдена. Начинаем поиск по автору...",
    },
    "author_not_found": {
        "kk": "Автор бойынша да ештеңе табылмады.",
        "ru": "По автору тоже ничего не найдено.",
    },
    "book_info": {
        "kk": "📚 {title}\nАвтор(лар): {author}\n[Кітап жайлы толығырақ]({link})",
        "ru": "📚 {title}\nАвтор(ы): {author}\n[Подробнее о книге]({link})",
    },
}


# Команда /start
@dp.message(Command("start"))
async def send_welcome(message: Message):
    user_id = message.from_user.id
    # Устанавливаем язык по умолчанию, если не выбран
    if user_id not in user_languages:
        user_languages[user_id] = "ru"

    await message.answer(messages["start"]["ru"], reply_markup=get_language_keyboard())


# Обработка выбора языка
@dp.message(lambda message: message.text in {"Қазақша", "Русский"})
async def set_language(message: Message):
    user_id = message.from_user.id
    if message.text == "Қазақша":
        user_languages[user_id] = "kk"
        await message.answer(messages["language_set"]["kk"])
    else:
        user_languages[user_id] = "ru"
        await message.answer(messages["language_set"]["ru"])


# Поиск книги через Open Library API
@dp.message()
async def search_books(message: Message):
    user_id = message.from_user.id
    language = user_languages.get(user_id, "ru")  # Язык по умолчанию

    query = message.text
    url = f"https://openlibrary.org/search.json?title={query}"
    response = requests.get(url)
    data = response.json()

    if data["numFound"] > 0:
        for book in data["docs"][:5]:  # Ограничиваем до 5 результатов
            title = book.get("title", "Без названия")
            author = ", ".join(book.get("author_name", ["Неизвестные авторы"]))
            olid = book.get("key")  # Получаем уникальный ключ книги
            book_url = f"https://openlibrary.org{olid}"  # Ссылка на страницу книги

            await message.answer(
                messages["book_info"][language].format(title=title, author=author, link=book_url),
                disable_web_page_preview=True,
            )
    else:
        await message.answer(messages["book_not_found"][language])
        await search_by_author(query, message, language)  # Поиск по автору


# Поиск книг по автору
async def search_by_author(author_name, message, language):
    url = f"https://openlibrary.org/search.json?author={author_name}"
    response = requests.get(url)
    data = response.json()

    if data["numFound"] > 0:
        for book in data["docs"][:5]:  # Ограничиваем до 5 результатов
            title = book.get("title", "Без названия")
            author = ", ".join(book.get("author_name", ["Неизвестные авторы"]))
            olid = book.get("key")  # Получаем уникальный ключ книги
            book_url = f"https://openlibrary.org{olid}"  # Ссылка на страницу книги

            await message.answer(
                messages["book_info"][language].format(title=title, author=author, link=book_url),
                disable_web_page_preview=True,
            )
    else:
        await message.answer(messages["author_not_found"][language])


# Клавиатура для выбора языка
def get_language_keyboard():
    from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Қазақша"), KeyboardButton(text="Русский")],
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


# Запуск бота
async def main():
    await bot.delete_webhook(drop_pending_updates=True)  # Удаляем вебхуки (если были)
    await dp.start_polling(bot)  # Запускаем поллинг


if __name__ == "__main__":
    asyncio.run(main())
