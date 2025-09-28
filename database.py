import sqlite3
import hashlib
from datetime import datetime

class Database:
    def __init__(self, db_name='users.db'):
        self.db_name = db_name
        self.init_db()

    def init_db(self):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                created_at TEXT NOT NULL,
                login_attempts INTEGER DEFAULT 0,
                last_attempt TEXT
            )
        ''')
        
        conn.commit()
        conn.close()

    def hash_password(self, password):
        """Хеширование пароля"""
        return hashlib.sha256(password.encode()).hexdigest()

    def register_user(self, name, email, password):
        """Регистрация нового пользователя"""
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            
            hashed_password = self.hash_password(password)
            created_at = datetime.now().isoformat()
            
            cursor.execute('''
                INSERT INTO users (name, email, password, created_at)
                VALUES (?, ?, ?, ?)
            ''', (name, email, hashed_password, created_at))
            
            conn.commit()
            conn.close()
            return True
        except sqlite3.IntegrityError:
            # Пользователь с таким email уже существует
            return False
        except Exception as e:
            print(f"Ошибка при регистрации: {e}")
            return False

    def check_user(self, email, password):
        """Проверка учетных данных пользователя"""
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            
            hashed_password = self.hash_password(password)
            
            cursor.execute('''
                SELECT id, name, login_attempts FROM users 
                WHERE email = ? AND password = ?
            ''', (email, hashed_password))
            
            user = cursor.fetchone()
            conn.close()
            
            return user
        except Exception as e:
            print(f"Ошибка при проверке пользователя: {e}")
            return None

    def user_exists(self, email):
        """Проверка существования пользователя по email"""
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            
            cursor.execute('SELECT id FROM users WHERE email = ?', (email,))
            user = cursor.fetchone()
            conn.close()
            
            return user is not None
        except Exception as e:
            print(f"Ошибка при проверке существования пользователя: {e}")
            return False

    def update_login_attempts(self, email, success):
        """Обновление счетчика попыток входа"""
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            
            if success:
                # Сброс счетчика при успешном входе
                cursor.execute('''
                    UPDATE users SET login_attempts = 0, last_attempt = ?
                    WHERE email = ?
                ''', (datetime.now().isoformat(), email))
            else:
                # Увеличение счетчика при неудачной попытке
                cursor.execute('''
                    UPDATE users 
                    SET login_attempts = login_attempts + 1, last_attempt = ?
                    WHERE email = ?
                ''', (datetime.now().isoformat(), email))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Ошибка при обновлении попыток входа: {e}")
            return False

    def get_login_attempts(self, email):
        """Получение количества неудачных попыток входа"""
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            
            cursor.execute('SELECT login_attempts FROM users WHERE email = ?', (email,))
            result = cursor.fetchone()
            conn.close()
            
            return result[0] if result else 0
        except Exception as e:
            print(f"Ошибка при получении попыток входа: {e}")
            return 0
        
Database()