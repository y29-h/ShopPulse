import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import json
import os

# Import token from config.py
from config import TOKEN

bot = telebot.TeleBot(TOKEN)

PRODUCTS_FILE = "products.json"
if not os.path.exists(PRODUCTS_FILE):
    with open(PRODUCTS_FILE, "w") as f:
        json.dump({}, f)

with open(PRODUCTS_FILE, "r") as f:
    products = json.load(f)

# Home menu
@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton(
            "Перейти в мини-приложение", 
            url="https://example.com"  
        )
    )
    bot.send_message(
        message.chat.id, 
        "Добро пожаловать в ShopBot! Вы можете перейти в наше мини-приложение, чтобы начать использовать его:", 
        reply_markup=markup
    )

# select category
@bot.callback_query_handler(func=lambda call: call.data.startswith("category"))
def show_products(call):
    category = call.data.split(":")[1]
    if category not in products:
        bot.answer_callback_query(call.id, "Категория не найдена.")
        return

    markup = InlineKeyboardMarkup()
    for product in products[category]:
        markup.add(
            InlineKeyboardButton(
                f"{product['name']} - {product['price']} грн", 
                callback_data=f"buy:{category}:{product['name']}"
            )
        )
    bot.edit_message_text(
        f"Товары в категории {category}:", 
        call.message.chat.id, 
        call.message.id, 
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("buy"))
def buy_product(call):
    _, category, product_name = call.data.split(":")
    product = next((p for p in products[category] if p["name"] == product_name), None)
    if not product:
        bot.answer_callback_query(call.id, "Товар не найден.")
        return

    # "Оплата" и выдача товара
    bot.send_message(
        call.message.chat.id, 
        f"Спасибо за покупку {product_name}! Вот ваш файл: {product['file']}"
    )
    bot.answer_callback_query(call.id, "Ваш заказ обработан.")

# Command for add category
@bot.message_handler(commands=['add_category'])
def add_category(message):
    if message.chat.id != int(os.getenv("ADMIN_ID", message.chat.id)):  # Проверка на администратора
        bot.reply_to(message, "У вас нет прав на выполнение этой команды.")
        return
    msg = bot.reply_to(message, "Введите название новой категории:")
    bot.register_next_step_handler(msg, save_category)

def save_category(message):
    category_name = message.text.strip()
    if category_name in products:
        bot.reply_to(message, "Такая категория уже существует.")
        return
    products[category_name] = []
    with open(PRODUCTS_FILE, "w") as f:
        json.dump(products, f)
    bot.reply_to(message, f"Категория '{category_name}' успешно добавлена!")

# Command for add product
@bot.message_handler(commands=['add_product'])
def add_product(message):
    if message.chat.id != int(os.getenv("ADMIN_ID", message.chat.id)):  # Проверка на администратора
        bot.reply_to(message, "У вас нет прав на выполнение этой команды.")
        return
    msg = bot.reply_to(message, "Введите данные товара в формате: \nКатегория | Название | Цена | Файл")
    bot.register_next_step_handler(msg, save_product)

def save_product(message):
    try:
        category, name, price, file_link = map(str.strip, message.text.split("|"))
        price = int(price)
        if category not in products:
            bot.reply_to(message, "Категория не найдена. Сначала добавьте её через /add_category.")
            return
        products[category].append({"name": name, "price": price, "file": file_link})
        with open(PRODUCTS_FILE, "w") as f:
            json.dump(products, f)
        bot.reply_to(message, f"Товар '{name}' успешно добавлен в категорию '{category}'!")
    except Exception as e:
        bot.reply_to(message, f"Ошибка: {str(e)}. Проверьте формат данных.")

# Запуск бота
bot.polling()
