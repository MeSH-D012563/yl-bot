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
        """Update a specific item in an outfit"""
        outfit = self.get_outfit(outfit_id, user_id)
        if not outfit:
            return False
            
        items = outfit['items']
        products = outfit['products']
        
        if 0 <= item_index < len(items):
            items[item_index] = new_item
            products[item_index] = new_product
            
            conn = sqlite3.connect(self.db_name)
            c = conn.cursor()
            
            c.execute('''
                UPDATE outfits 
                SET items = ?, products = ?
                WHERE id = ? AND user_id = ?
            ''', (json.dumps(items), json.dumps(products), outfit_id, user_id))
            
            conn.commit()
            conn.close()
            return True
            
        return False 