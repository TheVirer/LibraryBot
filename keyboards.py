from aiogram.types import ReplyKeyboardMarkup,KeyboardButton,ReplyKeyboardRemove

#Стартовая клавиатура
startkb = ReplyKeyboardMarkup(resize_keyboard=True,row_width=2)
startkb1 = KeyboardButton(text="Добавить книгу")
startkb2 = KeyboardButton(text="Посмотреть список книг")
startkb3 = KeyboardButton(text="Найти книгу по ключевому слову")
startkb4 = KeyboardButton(text="Найти книги по жанру")
startkb.add(startkb1,startkb2).add(startkb3).add(startkb4)

genres = ["Фантастика", "Детектив", "Роман", "Комедия", "История"]

#Клавиатура для подсказки пользователю в выборе жанра
genrekb = ReplyKeyboardMarkup(resize_keyboard=True)
genrebuttons = [KeyboardButton(text=genre) for genre in genres]
genrekb.add(*genrebuttons)
