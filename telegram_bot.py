import os
import telebot
from telebot import types
from image_parser import STYLES, get_outfit_items, search_products
from simple_image_download import simple_image_download as simp
from dotenv import load_dotenv
from database import OutfitDatabase
import json

# Загружаем переменные окружения
load_dotenv()

# Получаем токен из переменных окружения
BOT_TOKEN = os.getenv('BOT_TOKEN')
if not BOT_TOKEN:
    raise ValueError("Не найден токен бота. Пожалуйста, создайте файл .env и добавьте в него BOT_TOKEN=ваш_токен")

# Инициализация бота и базы данных
bot = telebot.TeleBot(BOT_TOKEN)
db = OutfitDatabase()

# Словарь для хранения состояния пользователей
user_states = {}

class UserState:
    def __init__(self):
        self.gender = None
        self.style = None
        self.occasion = None
        self.include_accessories = None
        self.current_step = 'start'
        self.current_outfit = None
        self.waiting_for_name = False
        self.waiting_for_item_replace = None

@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton("Мужской")
    btn2 = types.KeyboardButton("Женский")
    markup.add(btn1, btn2)
    
    bot.send_message(message.chat.id, 
                     "Добро пожаловать! Я помогу вам подобрать образ.\n"
                     "Выберите пол:", 
                     reply_markup=markup)
    
    user_states[message.chat.id] = UserState()
    user_states[message.chat.id].current_step = 'gender'

@bot.message_handler(commands=['favorites'])
def show_favorites(message):
    """Показать сохраненные образы"""
    outfits = db.get_user_outfits(message.chat.id)
    
    if not outfits:
        bot.send_message(message.chat.id, "У вас пока нет сохраненных образов.")
        return
    
    for outfit in outfits:
        response = f"Образ #{outfit['id']}"
        if outfit['name']:
            response += f" - {outfit['name']}"
        response += f"\nСтиль: {outfit['style'].capitalize()}\n"
        response += f"Случай: {outfit['occasion'].capitalize()}\n"
        response += f"Создан: {outfit['created_at']}\n\n"
        response += "Элементы образа:\n"
        
        for i, (item, product) in enumerate(zip(outfit['items'], outfit['products'])):
            response += f"{i+1}. {item}\n"
            if product:
                response += f"   Цена: {product['price']}\n"
                response += f"   Ссылка: {product['link']}\n"
        
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("Удалить", callback_data=f"delete_{outfit['id']}"))
        markup.add(types.InlineKeyboardButton("Поделиться", callback_data=f"share_{outfit['id']}"))
        markup.add(types.InlineKeyboardButton("Заменить элемент", callback_data=f"replace_{outfit['id']}"))
        
        bot.send_message(message.chat.id, response, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('replace_'))
def handle_replace_request(call):
    """Начать процесс замены элемента образа"""
    try:
        outfit_id = int(call.data.split('_')[1])
        outfit = db.get_outfit(outfit_id, call.message.chat.id)
        
        if not outfit:
            bot.answer_callback_query(call.id, "Образ не найден!")
            return
        
        # Получаем данные из словаря
        items = outfit['items']  # items уже в нужном формате
        products = outfit['products']  # products уже в нужном формате
        
        # Проверяем структуру данных
        print(f"Debug - Items: {items}")
        print(f"Debug - Products: {products}")
        
        markup = types.InlineKeyboardMarkup(row_width=1)
        for i, (item, product) in enumerate(zip(items, products)):
            # Проверяем структуру product
            if isinstance(product, dict):
                product_name = product.get('name', 'Товар не найден')
            else:
                product_name = 'Товар не найден'
                
            markup.add(types.InlineKeyboardButton(
                f"{i+1}. {item} - {product_name}",
                callback_data=f"select_item_{outfit_id}_{i}"
            ))
        markup.add(types.InlineKeyboardButton("Отмена", callback_data="cancel"))
        
        bot.edit_message_text(
            "Выберите элемент для замены:",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=markup
        )
    except Exception as e:
        print(f"Debug - Error in handle_replace_request: {str(e)}")
        bot.answer_callback_query(call.id, f"Произошла ошибка: {str(e)}")

@bot.callback_query_handler(func=lambda call: call.data.startswith('select_item_'))
def handle_item_selection(call):
    """Обработка выбора элемента для замены"""
    try:
        _, _, outfit_id, item_index = call.data.split('_')
        outfit_id = int(outfit_id)
        item_index = int(item_index)
        
        # Создаем или обновляем состояние пользователя
        if call.message.chat.id not in user_states:
            user_states[call.message.chat.id] = UserState()
        
        state = user_states[call.message.chat.id]
        state.waiting_for_item_replace = (outfit_id, item_index)
        
        bot.edit_message_text(
            "Введите новый поисковый запрос для этого элемента:",
            call.message.chat.id,
            call.message.message_id
        )
    except Exception as e:
        bot.answer_callback_query(call.id, f"Произошла ошибка: {str(e)}")

@bot.message_handler(func=lambda message: user_states.get(message.chat.id, UserState()).waiting_for_item_replace is not None)
def handle_new_item_search(message):
    """Обработка нового поискового запроса для элемента"""
    try:
        state = user_states[message.chat.id]
        outfit_id, item_index = state.waiting_for_item_replace
        
        # Ищем новый товар
        products = search_products(message.text)
        
        if not products:
            bot.send_message(message.chat.id, "Товар не найден. Попробуйте другой запрос.")
            return
        
        product = products[0]
        
        # Проверяем структуру product перед обновлением
        print(f"Debug - New product: {product}")
        
        # Обновляем элемент в образе
        if db.update_outfit_item(outfit_id, message.chat.id, item_index, message.text, product):
            bot.send_message(
                message.chat.id,
                f"Элемент успешно обновлен!\n"
                f"Название: {product['name']}\n"
                f"Цена: {product['price']}\n"
                f"Ссылка: {product['link']}"
            )
        else:
            bot.send_message(message.chat.id, "Не удалось обновить элемент.")
        
        # Сбрасываем состояние
        state.waiting_for_item_replace = None
        
        # Показываем обновленный образ
        show_favorites(message)
    except Exception as e:
        print(f"Debug - Error in handle_new_item_search: {str(e)}")
        bot.send_message(message.chat.id, f"Произошла ошибка: {str(e)}")
        state.waiting_for_item_replace = None

@bot.callback_query_handler(func=lambda call: call.data.startswith('delete_'))
def delete_outfit(call):
    """Удалить сохраненный образ"""
    outfit_id = int(call.data.split('_')[1])
    db.delete_outfit(outfit_id, call.message.chat.id)
    bot.answer_callback_query(call.id, "Образ удален!")
    bot.delete_message(call.message.chat.id, call.message.message_id)

@bot.callback_query_handler(func=lambda call: call.data.startswith('share_'))
def share_outfit(call):
    """Поделиться образом"""
    outfit_id = int(call.data.split('_')[1])
    outfit = db.get_outfit(outfit_id, call.message.chat.id)
    
    if outfit:
        share_text = f"Поделиться этим образом:\n"
        if outfit['name']:
            share_text += f"Название: {outfit['name']}\n"
        share_text += f"Стиль: {outfit['style'].capitalize()}\n"
        share_text += f"Случай: {outfit['occasion'].capitalize()}\n\n"
        share_text += "Элементы образа:\n"
        
        for item, product in zip(outfit['items'], outfit['products']):
            share_text += f"- {item}\n"
            if product:
                share_text += f"  Цена: {product['price']}\n"
                share_text += f"  Ссылка: {product['link']}\n"
        
        bot.answer_callback_query(call.id, "Скопируйте этот текст, чтобы поделиться образом")
        bot.send_message(call.message.chat.id, share_text)

@bot.message_handler(commands=['save'])
def save_current_outfit(message):
    """Сохранить текущий образ"""
    if message.chat.id not in user_states or not user_states[message.chat.id].current_outfit:
        bot.send_message(message.chat.id, "У вас нет активного образа для сохранения.")
        return
    
    state = user_states[message.chat.id]
    state.waiting_for_name = True
    
    bot.send_message(message.chat.id, "Введите название для этого образа:")

@bot.message_handler(func=lambda message: user_states.get(message.chat.id, UserState()).waiting_for_name)
def handle_outfit_name(message):
    """Обработка названия образа"""
    state = user_states[message.chat.id]
    outfit = state.current_outfit
    
    db.save_outfit(
        message.chat.id,
        message.text,
        state.gender,
        state.style,
        state.occasion,
        outfit['items'],
        outfit['products']
    )
    
    state.waiting_for_name = False
    bot.send_message(message.chat.id, 
                     f"Образ '{message.text}' успешно сохранен! "
                     "Используйте /favorites для просмотра сохраненных образов.")

@bot.message_handler(func=lambda message: user_states.get(message.chat.id, UserState()).current_step == 'gender')
def handle_gender(message):
    if message.text not in ['Мужской', 'Женский']:
        bot.send_message(message.chat.id, "Пожалуйста, выберите 'Мужской' или 'Женский'")
        return

    user_states[message.chat.id].gender = message.text.lower()
    
    # Создаем клавиатуру для выбора стиля
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    styles = list(STYLES[message.text.lower()].keys())
    for style in styles:
        markup.add(types.KeyboardButton(style.capitalize()))
    
    bot.send_message(message.chat.id, 
                     "Выберите стиль:", 
                     reply_markup=markup)
    
    user_states[message.chat.id].current_step = 'style'

@bot.message_handler(func=lambda message: user_states.get(message.chat.id, UserState()).current_step == 'style')
def handle_style(message):
    gender = user_states[message.chat.id].gender
    if message.text.lower() not in STYLES[gender].keys():
        bot.send_message(message.chat.id, "Пожалуйста, выберите стиль из предложенных вариантов")
        return

    user_states[message.chat.id].style = message.text.lower()
    
    # Создаем клавиатуру для выбора случая
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    occasions = list(STYLES[gender][message.text.lower()].keys())
    for occasion in occasions:
        markup.add(types.KeyboardButton(occasion.capitalize()))
    
    bot.send_message(message.chat.id, 
                     "Выберите случай:", 
                     reply_markup=markup)
    
    user_states[message.chat.id].current_step = 'occasion'

@bot.message_handler(func=lambda message: user_states.get(message.chat.id, UserState()).current_step == 'occasion')
def handle_occasion(message):
    gender = user_states[message.chat.id].gender
    style = user_states[message.chat.id].style
    
    if message.text.lower() not in STYLES[gender][style].keys():
        bot.send_message(message.chat.id, "Пожалуйста, выберите случай из предложенных вариантов")
        return

    user_states[message.chat.id].occasion = message.text.lower()
    
    # Создаем клавиатуру для выбора аксессуаров
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("Да"), types.KeyboardButton("Нет"))
    
    bot.send_message(message.chat.id, 
                     "Включить аксессуары в образ?", 
                     reply_markup=markup)
    
    user_states[message.chat.id].current_step = 'accessories'

@bot.message_handler(func=lambda message: user_states.get(message.chat.id, UserState()).current_step == 'accessories')
def handle_accessories(message):
    if message.text.lower() not in ['да', 'нет']:
        bot.send_message(message.chat.id, "Пожалуйста, выберите 'Да' или 'Нет'")
        return

    user_states[message.chat.id].include_accessories = message.text.lower() == 'да'
    
    # Получаем элементы образа
    outfit_items = get_outfit_items(
        user_states[message.chat.id].gender,
        user_states[message.chat.id].style,
        user_states[message.chat.id].occasion,
        user_states[message.chat.id].include_accessories
    )
    
    if not outfit_items:
        bot.send_message(message.chat.id, "Не удалось сгенерировать образ. Попробуйте другие параметры.")
        return
    
    # Отправляем список элементов образа
    response = "Сгенерированный образ:\n\n"
    for i, item in enumerate(outfit_items, 1):
        response += f"{i}. {item}\n"
    
    bot.send_message(message.chat.id, response)
    
    # Создаем папку для изображений
    path = os.path.join(os.getcwd(), "downloaded_images")
    if not os.path.exists(path):
        os.makedirs(path)
    
    # Скачиваем изображения и ищем товары для каждого элемента
    bot.send_message(message.chat.id, "Начинаю поиск товаров и скачивание изображений...")
    
    products = []
    for item in outfit_items:
        bot.send_message(message.chat.id, f"Поиск товара для: {item}")
        
        # Скачиваем изображения
        response = simp.simple_image_download()
        response.directory = path
        response.download(item, 1)
        
        # Ищем товар
        product = search_products(item)
        
        if product:
            products.append(product[0])
            response = f"Найденный товар для {item}:\n\n"
            response += f"Название: {product[0]['name']}\n"
            response += f"Цена: {product[0]['price']}\n"
            response += f"Ссылка: {product[0]['link']}\n"
            bot.send_message(message.chat.id, response)
        else:
            products.append(None)
            bot.send_message(message.chat.id, f"Товар для {item} не найден")
    
    # Сохраняем текущий образ
    user_states[message.chat.id].current_outfit = {
        'items': outfit_items,
        'products': products
    }
    
    # Предлагаем сохранить образ
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("/save"), types.KeyboardButton("/start"))
    bot.send_message(message.chat.id, 
                     "Хотите сохранить этот образ? Используйте /save\n"
                     "Или начните заново с /start", 
                     reply_markup=markup)
    
    # Сбрасываем состояние пользователя
    user_states[message.chat.id].current_step = 'start'

@bot.message_handler(commands=['help'])
def help_command(message):
    """Показать справку по командам"""
    help_text = """
Доступные команды:
/start - Начать подбор образа
/favorites - Показать сохраненные образы
/save - Сохранить текущий образ
/help - Показать эту справку
/cancel - Отменить текущий диалог
    """
    bot.send_message(message.chat.id, help_text)

@bot.message_handler(commands=['cancel'])
def cancel(message):
    """Отмена разговора."""
    if message.chat.id in user_states:
        del user_states[message.chat.id]
    bot.send_message(message.chat.id, 
                     'Разговор отменен.',
                     reply_markup=types.ReplyKeyboardRemove())

def main():
    """Запуск бота."""
    print("Бот запущен...")
    bot.polling(none_stop=True)

if __name__ == '__main__':
    main() 