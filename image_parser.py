from simple_image_download import simple_image_download as simp
import os
import requests
import json
import urllib.parse
import random
from virtual_tryon import VirtualTryOn

# Предопределенные стили и образы
STYLES = {
    'мужской': {
        'классический': {
            'деловая встреча': [
                'мужской классический пиджак темный',
                'мужская белая рубашка',
                'мужские классические брюки',
                'мужские кожаные туфли оксфорды',
                'мужской кожаный ремень',
                'мужской галстук шелковый'
            ],
            'собеседование': [
                'мужской синий пиджак',
                'мужская светлая рубашка',
                'мужские темные брюки',
                'мужские коричневые туфли дерби',
                'мужской кожаный портфель'
            ],
            'деловой ужин': [
                'мужской темный костюм',
                'мужская голубая рубашка',
                'мужской шелковый галстук',
                'мужские запонки',
                'мужские черные оксфорды'
            ],
            'повседневный офис': [
                'мужской серый блейзер',
                'мужская рубашка поло',
                'мужские бежевые чинос',
                'мужские коричневые лоферы',
                'мужской кожаный ремень'
            ]
        },
        'кэжуал': {
            'свидание': [
                'мужская джинсовая рубашка',
                'мужская белая футболка',
                'мужские темные джинсы',
                'мужские замшевые челси',
                'мужской кожаный ремень'
            ],
            'выходные': [
                'мужской хлопковый свитер',
                'мужские джинсы',
                'мужские белые кроссовки',
                'мужские часы casual',
                'мужской кожаный браслет'
            ],
            'прогулка': [
                'мужская джинсовая куртка',
                'мужская футболка с принтом',
                'мужские светлые джинсы',
                'мужские кеды',
                'мужской городской рюкзак'
            ]
        },
        'спортивный': {
            'тренировка в зале': [
                'мужская спортивная футболка компрессионная',
                'мужские шорты спортивные',
                'мужские кроссовки для зала',
                'мужские спортивные носки',
                'мужской спортивный браслет'
            ],
            'пробежка': [
                'мужская беговая футболка',
                'мужские шорты для бега',
                'мужские беговые кроссовки',
                'мужские спортивные часы',
                'мужская повязка на голову'
            ]
        }
    },
    'женский': {
        'классический': {
            'деловая встреча': [
                'женский классический жакет',
                'женская шелковая блузка',
                'женская юбка-карандаш',
                'женские кожаные туфли-лодочки',
                'женская кожаная сумка'
            ],
            'собеседование': [
                'женский брючный костюм',
                'женская белая блузка',
                'женские классические брюки',
                'женские туфли на среднем каблуке',
                'женский кожаный портфель'
            ],
            'деловой ужин': [
                'женское платье-футляр',
                'женский приталенный жакет',
                'женские туфли на каблуке',
                'женский клатч',
                'женские серьги минималистичные'
            ],
            'повседневный офис': [
                'женская блузка casual',
                'женские брюки прямые',
                'женские балетки кожаные',
                'женская сумка через плечо',
                'женские часы элегантные'
            ]
        },
        'кэжуал': {
            'свидание': [
                'женское платье casual',
                'женская джинсовая куртка',
                'женские босоножки',
                'женская маленькая сумка',
                'женский браслет'
            ],
            'выходные': [
                'женский свитер оверсайз',
                'женские джинсы mom',
                'женские белые кеды',
                'женский рюкзак городской',
                'женские солнцезащитные очки'
            ],
            'прогулка': [
                'женский тренч',
                'женская футболка базовая',
                'женские джинсы скинни',
                'женские кроссовки',
                'женская сумка шоппер'
            ]
        },
        'спортивный': {
            'тренировка в зале': [
                'женский спортивный топ',
                'женские леггинсы спортивные',
                'женские кроссовки для фитнеса',
                'женский спортивный браслет',
                'женская повязка для волос'
            ],
            'пробежка': [
                'женская спортивная футболка',
                'женские шорты для бега',
                'женские беговые кроссовки',
                'женские спортивные часы',
                'женская бутылка для воды'
            ]
        }
    }
}

def get_outfit_items(gender, style, occasion, include_accessories=True):
    """Получает список элементов одежды для выбранного пола, стиля и случая"""
    gender = gender.lower()
    style = style.lower()
    occasion = occasion.lower()
    
    # Создаем словари с ключами в нижнем регистре
    genders_lower = {k.lower(): v for k, v in STYLES.items()}
    
    if gender in genders_lower:
        styles_lower = {k.lower(): v for k, v in genders_lower[gender].items()}
        if style in styles_lower:
            occasions_lower = {k.lower(): v for k, v in styles_lower[style].items()}
            if occasion in occasions_lower:
                items = occasions_lower[occasion]
                if not include_accessories:
                    # Фильтруем аксессуары
                    accessories_keywords = ['часы', 'сумка', 'ремень', 'браслет', 'серьги', 'галстук', 'шарф', 
                                         'клатч', 'портфель', 'запонки', 'повязка', 'очки', 'платок']
                    items = [item for item in items if not any(keyword in item.lower() for keyword in accessories_keywords)]
                return items
    return []

def search_products(query):
    """Поиск товаров на Wildberries"""
    encoded_query = urllib.parse.quote(query)
    url = f"https://search.wb.ru/exactmatch/ru/common/v4/search?appType=1&curr=rub&dest=-1257786&query={encoded_query}&resultset=catalog&sort=popular&suppressSpellcheck=false"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'application/json',
        'Accept-Language': 'ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3',
        'Referer': 'https://www.wildberries.ru/',
        'Origin': 'https://www.wildberries.ru'
    }
    
    try:
        response = requests.get(url, headers=headers)
        data = response.json()
        
        if 'data' in data and 'products' in data['data'] and data['data']['products']:
            # Получаем все найденные товары
            products = data['data']['products']
            # Выбираем случайный товар
            random_product = random.choice(products)
            
            try:
                name = random_product.get('name', 'Название не указано')
                price = f"{random_product.get('salePriceU', 0) / 100} ₽"
                link = f"https://www.wildberries.ru/catalog/{random_product.get('id', '')}/detail.aspx"
                
                return [{
                    'name': name,
                    'price': price,
                    'link': link
                }]
            except:
                return []
        
        return []
    except Exception as e:
        print(f"Ошибка при поиске товаров: {str(e)}")
        return []

def show_available_options():
    """Показывает доступные варианты для выбора"""
    print("\nДоступные варианты:")
    for gender, styles in STYLES.items():
        print(f"\n{gender.upper()}:")
        for style, occasions in styles.items():
            print(f"\n  {style.upper()}:")
            for occasion in occasions:
                print(f"    - {occasion}")
    print("\nПримечание: при вводе пола, стиля и случая регистр не имеет значения")

def perform_virtual_tryon(garment_image_path, human_image_path, garment_description):
    """
    Perform virtual try-on using the IDM-VTON model
    
    Args:
        garment_image_path (str): Path to the garment image
        human_image_path (str): Path to the human image
        garment_description (str): Description of the garment
        
    Returns:
        str: Path to the resulting image, or None if failed
    """
    try:
        vton = VirtualTryOn()
        result_path = vton.try_on(garment_image_path, human_image_path, garment_description)
        return result_path
    except Exception as e:
        print(f"Error during virtual try-on: {str(e)}")
        return None

def parse_images():
    # Показываем доступные варианты
    show_available_options()
    
    # Получаем предпочтения пользователя
    gender = input("\nВыберите пол (мужской/женский): ").lower()
    if gender not in ['мужской', 'женский']:
        print("Некорректный выбор пола. Пожалуйста, выберите 'мужской' или 'женский'.")
        return
    
    style = input("Введите желаемый стиль из списка выше: ").lower()
    occasion = input("Введите случай из списка выше: ").lower()
    
    # Спрашиваем про аксессуары
    accessories_choice = input("\nВключить аксессуары в образ? (да/нет): ").lower()
    include_accessories = accessories_choice in ['да', 'yes', 'y', 'д']
    
    # Получаем элементы образа
    outfit_items = get_outfit_items(gender, style, occasion, include_accessories)
    
    if not outfit_items:
        print("Выбранная комбинация стиля и случая не найдена. Пожалуйста, используйте варианты из списка.")
        return
    
    print("\nСгенерированный образ:")
    for i, item in enumerate(outfit_items, 1):
        print(f"{i}. {item}")
    
    # Создаем папку для изображений
    path = os.path.join(os.getcwd(), "downloaded_images")
    if not os.path.exists(path):
        os.makedirs(path)
    
    # Скачиваем изображения и ищем товары для каждого элемента
    print("\nНачинаю поиск товаров и скачивание изображений...")
    
    for item in outfit_items:
        print(f"\nПоиск товаров для: {item}")
        
        # Скачиваем изображения
        response = simp.simple_image_download()
        response.directory = path
        response.download(item, 1)
        
        # Ищем товары
        products = search_products(item)
        
        if products:
            print(f"\nНайденные товары для {item}:")
            for i, product in enumerate(products, 1):
                print(f"\n{i}. {product['name']}")
                print(f"   Цена: {product['price']}")
                print(f"   Ссылка: {product['link']}")
        else:
            print(f"Товары для {item} не найдены")

if __name__ == "__main__":
    try:
        parse_images()
    except Exception as e:
        print(f"Произошла ошибка: {str(e)}") 