from aiogram.dispatcher.filters.state import State, StatesGroup

#State для добавления новой книги
class AddBook(StatesGroup):
    Title = State()
    Author = State()
    Description = State()
    Genre = State()
    CustomGenre = State()

#State для поиска по ключевому слову
class SearchKeyword(StatesGroup):
    Keyword = State()