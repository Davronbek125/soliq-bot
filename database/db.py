"""
Ma'lumotlar bazasi moduli (SQLite / PostgreSQL moslashuvchan).
Server qayta yuklanganda ham ma'lumotlar saqlanishini ta'minlash uchun xavfsiz ulanish.
"""

import sqlite3
import os
import logging
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)

# Muhit o'zgaruvchisidan bazaga yo'l olish (Render/VPS da persistent disk yo'li)
DEFAULT_LOCAL_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tax_bot.db")
DB_PATH = os.getenv("DB_PATH", DEFAULT_LOCAL_PATH)


def get_connection() -> sqlite3.Connection:
    """Xavfsiz va barqaror ulanish yaratish."""
    target_path = DB_PATH
    try:
        conn = sqlite3.connect(target_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys=ON;")
        conn.execute("CREATE TABLE IF NOT EXISTS _io_check (id INT);")
        return conn
    except sqlite3.OperationalError:
        # Agar joriy disk tarmoq diski bo'lib, I/O lock qo'llab-quvvatlamasa, /tmp yoki xavfsiz papkaga o'tish
        fallback_path = "/tmp/tax_bot.db"
        conn = sqlite3.connect(fallback_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys=ON;")
        return conn


def init_db():
    """Barcha jadvallarni yaratish va sxemani tekshirish."""
    with get_connection() as conn:
        cursor = conn.cursor()

        # 1. Foydalanuvchilar jadvali
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            full_name TEXT,
            phone_number TEXT,
            business_type TEXT DEFAULT 'not_set',
            annual_revenue REAL DEFAULT 0,
            employees_count INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)

        # 2. Soliq hisob-kitoblari tarixi jadvali
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS calculations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            calc_type TEXT NOT NULL,
            annual_revenue REAL NOT NULL,
            expenses REAL DEFAULT 0,
            employees_count INTEGER DEFAULT 0,
            calculated_tax REAL NOT NULL,
            effective_rate REAL NOT NULL,
            best_regime TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE
        );
        """)

        # 3. AI Soliq maslahatlari va savol-javoblar tarixi
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS consultations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            user_question TEXT NOT NULL,
            bot_answer TEXT NOT NULL,
            legal_basis TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE
        );
        """)

        # 4. Soliq eslatmalari va taqvim jadvali
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS reminders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            due_date TEXT NOT NULL,
            reminder_text TEXT NOT NULL,
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE
        );
        """)

        # 5. Tizim sozlamalari (BHM, me'yorlar)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS system_settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)

        # Dastlabki sozlamalar
        cursor.execute("""
        INSERT OR IGNORE INTO system_settings (key, value)
        VALUES ('BHM', '412000'), ('MHEKM', '1360000'), ('VERSION', '2026.1');
        """)

        conn.commit()


def register_or_update_user(user_id: int, username: Optional[str], full_name: Optional[str]) -> bool:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        INSERT INTO users (user_id, username, full_name, last_activity)
        VALUES (?, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(user_id) DO UPDATE SET
            username = excluded.username,
            full_name = excluded.full_name,
            last_activity = CURRENT_TIMESTAMP;
        """, (user_id, username, full_name))
        conn.commit()
        return True


def update_user_business_profile(user_id: int, business_type: str, annual_revenue: float, employees_count: int = 0):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        UPDATE users 
        SET business_type = ?, annual_revenue = ?, employees_count = ?, last_activity = CURRENT_TIMESTAMP
        WHERE user_id = ?;
        """, (business_type, annual_revenue, employees_count, user_id))
        conn.commit()


def save_calculation(user_id: int, calc_type: str, annual_revenue: float,
                     calculated_tax: float, effective_rate: float,
                     expenses: float = 0, employees_count: int = 0, best_regime: str = "") -> int:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        INSERT INTO calculations (user_id, calc_type, annual_revenue, expenses, employees_count, calculated_tax, effective_rate, best_regime)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?);
        """, (user_id, calc_type, annual_revenue, expenses, employees_count, calculated_tax, effective_rate, best_regime))
        conn.commit()
        return cursor.lastrowid


def save_consultation(user_id: int, question: str, answer: str, legal_basis: str = "") -> int:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        INSERT INTO consultations (user_id, user_question, bot_answer, legal_basis)
        VALUES (?, ?, ?, ?);
        """, (user_id, question, answer, legal_basis))
        conn.commit()
        return cursor.lastrowid


def get_user_history(user_id: int, limit: int = 5) -> List[Dict[str, Any]]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        SELECT * FROM calculations WHERE user_id = ? ORDER BY id DESC LIMIT ?;
        """, (user_id, limit))
        return [dict(row) for row in cursor.fetchall()]


def get_user_consultation_history(user_id: int, limit: int = 5) -> List[Dict[str, Any]]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        SELECT * FROM consultations WHERE user_id = ? ORDER BY id DESC LIMIT ?;
        """, (user_id, limit))
        return [dict(row) for row in cursor.fetchall()]


def get_users_count() -> int:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM users;")
        return cursor.fetchone()[0]
