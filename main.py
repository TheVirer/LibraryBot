#Импорты для работы с Telegram ботом
from aiogram import Bot, Dispatcher, types, executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.types import InlineKeyboardMarkup,InlineKeyboardButton

#Импорты для работы с базой данных
from sqlalchemy import create_engine, Column, Integer, String, Text
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker

#Импорты из этого же проекта
from config import *
from keyboards import *
from states import *

Base = declarative_base()

# Определение модели для книг
class Book(Base):
    __tablename__ = 'books'

    id = Column(Integer, primary_key=True)
    title = Column(String)
    author = Column(String)
    description = Column(Text)
    genre = Column(String)

# Создание таблицы в базе данных
engine = create_engine('sqlite:///books.db')
Base.metadata.create_all(engine)

Session = sessionmaker(bind=engine)

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())

# Обработчик команды /start
@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    await bot.send_message(text=f"Привет {message.from_user.first_name}! Я бот-библиотекарь. Чем могу быть полезен?", chat_id=message.from_user.id, reply_markup=startkb)

# Обработчик команды "Добавить книгу"
@dp.message_handler(lambda message: message.text == "Добавить книгу")
async def add_book(message: types.Message):
    await bot.send_message(text="Введите название книги:", chat_id=message.from_user.id)
    await AddBook.Title.set()

#Добавление названия книги
@dp.message_handler(state=AddBook.Title)
async def process_book_title(message: types.Message, state: FSMContext):
    session = Session()
    user = Book()

    user.title = message.text
    session.add(user)
    session.commit()

    await bot.send_message(text="Введите автора книги:", chat_id=message.from_user.id)
    await AddBook.Author.set()

#Добавление автора книги
@dp.message_handler(state=AddBook.Author)
async def process_book_author(message: types.Message, state: FSMContext):
    session = Session()
    user = session.query(Book).order_by(Book.id.desc()).first()

    user.author = message.text
    session.commit()

    await bot.send_message(text="Введите описание книги:", chat_id=message.from_user.id)
    await AddBook.Description.set()

#Добавление описания книги
@dp.message_handler(state=AddBook.Description)
async def process_book_description(message: types.Message, state: FSMContext):
    session = Session()
    user = session.query(Book).order_by(Book.id.desc()).first()

    user.description = message.text
    session.commit()

    await bot.send_message(text="Выберите жанр книги или введите свой:", chat_id=message.from_user.id, reply_markup=genrekb)
    await AddBook.Genre.set()

#Добавление жанра книги
@dp.message_handler(state=AddBook.Genre)
async def genre_from_list(message: types.Message, state: FSMContext):
    session = Session()
    user = session.query(Book).order_by(Book.id.desc()).first()

    user.genre = message.text
    session.commit()

    await bot.send_message(text="Книга успешно добавлена в библиотеку!", chat_id=message.from_user.id, reply_markup=startkb)
    await state.finish()

#Обработчик кнопки "Посмотреть список книг"
@dp.message_handler(lambda message: message.text == "Посмотреть список книг")
async def show_books_list(message: types.Message):
    session = Session()

    all_books = session.query(Book).all()

    if all_books:
        keyboard = InlineKeyboardMarkup(row_width=1)
        buttons = [InlineKeyboardButton(text=f"{book.title} - {book.author}",callback_data=f"book_info_{book.id}") for book in all_books]
        keyboard.add(*buttons)

        await bot.send_message(text="Список всех книг:",chat_id=message.from_user.id,reply_markup=keyboard)
    else:
        await bot.send_message(text="На данный момент в библиотеке нет добавленных книг.", chat_id=message.from_user.id)

# Обработчик кнопки "Найти книгу по ключевому слову"
@dp.message_handler(lambda message: message.text == "Найти книгу по ключевому слову")
async def search_book_by_keyword(message: types.Message):
    await bot.send_message(text="Введите ключевое слово для поиска:", chat_id=message.from_user.id)
    await SearchKeyword.Keyword.set()

#Поиск книг по ключевому слову
@dp.message_handler(state=SearchKeyword.Keyword)
async def process_search_keyword(message: types.Message, state: FSMContext):
    keyword = message.text
    session = Session()

    found_books = session.query(Book).filter((Book.title.ilike(f"%{keyword}%")) | (Book.author.ilike(f"%{keyword}%"))).all()

    if found_books:
        keyboard = InlineKeyboardMarkup(row_width=1)
        buttons = [InlineKeyboardButton(text=f"{book.title} - {book.author}",callback_data=f"book_info_{book.id}") for book in found_books]
        keyboard.add(*buttons)

        await bot.send_message(text=f"Найденные книги по ключевому слову '{keyword}':",chat_id=message.from_user.id,reply_markup=keyboard)
    else:
        await bot.send_message(text=f"По запросу '{keyword}' ничего не найдено.", chat_id=message.from_user.id)
    await state.finish()

#Обработчик кнопки "Найти книги по жанру"
@dp.message_handler(lambda message: message.text == "Найти книги по жанру")
async def search_books_by_genre(message: types.Message):
    session = Session()

    genres = session.query(Book.genre).distinct().all()
    genres = [genre[0] for genre in genres if genre[0]]
    if len(genres)>=1:
        keyboard = InlineKeyboardMarkup(row_width=3)
        buttons = [InlineKeyboardButton(text=genre, callback_data=f"genre_{genre}") for genre in genres]
        keyboard.add(*buttons)

        await bot.send_message(text="Выберите жанр:",chat_id=message.from_user.id,reply_markup=keyboard)
    else:
        await bot.send_message(text="К сожалению в библиотеке не нашлось книг с каким либо жанром. Добавьте их, и тогда вы сможете найти что-либо по жанру.",chat_id=message.from_user.id)

#Поиск всех книг по выбранному жанру
@dp.callback_query_handler(lambda callback: callback.data.startswith('genre_'))
async def process_genre_callback(callback: types.CallbackQuery):
    genre = callback.data[len('genre_'):]
    session = Session()

    found_books = session.query(Book).filter(Book.genre.ilike(f"%{genre}%")).all()

    if found_books:
        keyboard = InlineKeyboardMarkup(row_width=1)
        buttons = [InlineKeyboardButton(text=f"{book.title} - {book.author}",callback_data=f"book_info_{book.id}") for book in found_books]
        keyboard.add(*buttons)

        await bot.send_message(text=f"Найденные книги по жанру '{genre}':",chat_id=callback.from_user.id,reply_markup=keyboard)
    else:
        await bot.send_message(text=f"По жанру '{genre}' ничего не найдено.", chat_id=callback.from_user.id)
    await callback.answer()

#Вывод названия,автора,жанра и описания книги, а также inline кнопок
@dp.callback_query_handler(lambda callback: callback.data.startswith('book_info_'))
async def process_book_info_callback(callback: types.CallbackQuery):
    book_id = int(callback.data[len('book_info_'):])
    session = Session()
    book = session.query(Book).filter_by(id=book_id).first()

    if book:
        book_info_message = f"Название: {book.title}\nАвтор: {book.author}\nЖанр: {book.genre}\n\n{book.description}"

        keyboard = InlineKeyboardMarkup(row_width=1)
        delete_button = InlineKeyboardButton(text="Удалить книгу",callback_data=f"delete_book_{book.id}")
        back_to_list_button = InlineKeyboardButton(text="Посмотреть книги с похожим жанром",callback_data=f"back_to_list_{book.genre}")
        keyboard.add(delete_button, back_to_list_button)

        await bot.send_message(text=book_info_message,chat_id=callback.from_user.id,reply_markup=keyboard)
    else:
        await bot.send_message(text="Книга не найдена.", chat_id=callback.from_user.id)
    await callback.answer()

#Удаление книги из базы данных
@dp.callback_query_handler(lambda callback: callback.data.startswith('delete_book_'))
async def process_delete_book_callback(callback: types.CallbackQuery):
    book_id = int(callback.data[len('delete_book_'):])
    session = Session()
    book = session.query(Book).filter_by(id=book_id).first()

    if book:
        session.delete(book)
        session.commit()
        await bot.send_message(text="Книга успешно удалена из библиотеки.", chat_id=callback.from_user.id)
    else:
        await bot.send_message(text="Книга не найдена.", chat_id=callback.from_user.id)
    await callback.answer()

#Переход к списку книг по похожему жанру
@dp.callback_query_handler(lambda callback: callback.data.startswith('back_to_list_'))
async def process_back_to_list_callback(callback: types.CallbackQuery):
    genre = callback.data[len('back_to_list_'):]
    session = Session()

    found_books = session.query(Book).filter(Book.genre.ilike(f"%{genre}%")).all()

    if found_books:
        keyboard = InlineKeyboardMarkup(row_width=1)
        buttons = [InlineKeyboardButton(text=f"{book.title} - {book.author}",callback_data=f"book_info_{book.id}") for book in found_books]
        keyboard.add(*buttons)

        await bot.send_message(text=f"Найденные книги по жанру '{genre}':",chat_id=callback.from_user.id,reply_markup=keyboard)
    else:
        await bot.send_message(text=f"По жанру '{genre}' ничего не найдено.", chat_id=callback.from_user.id)
    await callback.answer()

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)