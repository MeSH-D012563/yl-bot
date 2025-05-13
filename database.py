import sqlite3
import json
from datetime import datetime
import os

class OutfitDatabase:
    def __init__(self, db_name='outfits.db'):
        self.db_name = db_name
        self.init_db()

    def init_db(self):
        """Initialize the database with required tables"""
        # Проверяем существование базы данных
        db_exists = os.path.exists(self.db_name)
        
        conn = sqlite3.connect(self.db_name)
        c = conn.cursor()
        
        if db_exists:
            # Проверяем наличие колонки name
            c.execute("PRAGMA table_info(outfits)")
            columns = [column[1] for column in c.fetchall()]
            
            if 'name' not in columns:
                # Добавляем колонку name
                c.execute('ALTER TABLE outfits ADD COLUMN name TEXT')
                conn.commit()
        
        # Create outfits table if it doesn't exist
        c.execute('''
            CREATE TABLE IF NOT EXISTS outfits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                name TEXT,
                gender TEXT NOT NULL,
                style TEXT NOT NULL,
                occasion TEXT NOT NULL,
                items TEXT NOT NULL,
                products TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create ratings table if it doesn't exist
        c.execute('''
            CREATE TABLE IF NOT EXISTS ratings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                outfit_id INTEGER NOT NULL,
                rating INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (outfit_id) REFERENCES outfits(id) ON DELETE CASCADE
            )
        ''')
        
        conn.commit()
        conn.close()

    def save_outfit(self, user_id, name, gender, style, occasion, items, products):
        """Save a new outfit to the database"""
        conn = sqlite3.connect(self.db_name)
        c = conn.cursor()
        
        c.execute('''
            INSERT INTO outfits (user_id, name, gender, style, occasion, items, products)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, name, gender, style, occasion, json.dumps(items), json.dumps(products)))
        
        conn.commit()
        conn.close()

    def get_user_outfits(self, user_id):
        """Get all outfits for a specific user"""
        conn = sqlite3.connect(self.db_name)
        c = conn.cursor()
        
        c.execute('''
            SELECT * FROM outfits 
            WHERE user_id = ? 
            ORDER BY created_at DESC
        ''', (user_id,))
        
        outfits = c.fetchall()
        conn.close()
        
        return [{
            'id': outfit[0],
            'name': outfit[2],
            'gender': outfit[3],
            'style': outfit[4],
            'occasion': outfit[5],
            'items': json.loads(outfit[6]),
            'products': json.loads(outfit[7]),
            'created_at': outfit[8]
        } for outfit in outfits]

    def delete_outfit(self, outfit_id, user_id):
        """Delete a specific outfit"""
        conn = sqlite3.connect(self.db_name)
        c = conn.cursor()
        
        c.execute('''
            DELETE FROM outfits 
            WHERE id = ? AND user_id = ?
        ''', (outfit_id, user_id))
        
        conn.commit()
        conn.close()

    def get_outfit(self, outfit_id, user_id):
        """Get a specific outfit"""
        conn = sqlite3.connect(self.db_name)
        c = conn.cursor()
        
        c.execute('''
            SELECT * FROM outfits 
            WHERE id = ? AND user_id = ?
        ''', (outfit_id, user_id))
        
        outfit = c.fetchone()
        conn.close()
        
        if outfit:
            return {
                'id': outfit[0],
                'name': outfit[2],
                'gender': outfit[3],
                'style': outfit[4],
                'occasion': outfit[5],
                'items': json.loads(outfit[6]),
                'products': json.loads(outfit[7]),
                'created_at': outfit[8]
            }
        return None

    def update_outfit_item(self, outfit_id, user_id, item_index, new_item, new_product):
        """Обновить элемент в образе"""
        try:
            # Получаем текущий образ
            outfit = self.get_outfit(outfit_id, user_id)
            if not outfit:
                return False

            # Получаем текущие списки (они уже в нужном формате)
            items = outfit['items']
            products = outfit['products']

            # Проверяем индекс
            if item_index >= len(items):
                return False

            # Обновляем элемент и товар
            items[item_index] = new_item
            products[item_index] = new_product

            # Обновляем в базе данных
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE outfits SET items = ?, products = ? WHERE id = ? AND user_id = ?",
                    (json.dumps(items), json.dumps(products), outfit_id, user_id)
                )
                conn.commit()
                return True
        except Exception as e:
            print(f"Debug - Error in update_outfit_item: {str(e)}")
            return False

    def add_rating(self, user_id, outfit_id, rating):
        """Add or update a rating for an outfit"""
        conn = sqlite3.connect(self.db_name)
        c = conn.cursor()
        
        # Проверяем, существует ли уже рейтинг от этого пользователя
        c.execute('''
            SELECT id FROM ratings 
            WHERE user_id = ? AND outfit_id = ?
        ''', (user_id, outfit_id))
        
        existing_rating = c.fetchone()
        
        if existing_rating:
            # Обновляем существующий рейтинг
            c.execute('''
                UPDATE ratings 
                SET rating = ?, created_at = CURRENT_TIMESTAMP 
                WHERE user_id = ? AND outfit_id = ?
            ''', (rating, user_id, outfit_id))
        else:
            # Добавляем новый рейтинг
            c.execute('''
                INSERT INTO ratings (user_id, outfit_id, rating)
                VALUES (?, ?, ?)
            ''', (user_id, outfit_id, rating))
        
        conn.commit()
        conn.close()

    def get_average_rating(self, outfit_id):
        """Get the average rating for an outfit"""
        conn = sqlite3.connect(self.db_name)
        c = conn.cursor()
        
        c.execute('''
            SELECT ROUND(AVG(rating), 1) 
            FROM ratings 
            WHERE outfit_id = ?
        ''', (outfit_id,))
        
        result = c.fetchone()[0]
        conn.close()
        
        return result if result is not None else 0.0

