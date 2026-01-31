import sqlite3
from typing import Optional, Tuple, List


class Database:
    """Handles SQLite database operations"""
    
    def __init__(self, db_path: str = "ir_remotes.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize the database with required tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create Remote table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Remote (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                comment TEXT
            )
        """)
        
        # Create Key table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Key (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                remote_id INTEGER NOT NULL,
                protocol TEXT NOT NULL,
                address TEXT NOT NULL,
                command TEXT NOT NULL,
                key_name TEXT NOT NULL,
                comment TEXT,
                FOREIGN KEY (remote_id) REFERENCES Remote (id),
                UNIQUE(remote_id, key_name)
            )
        """)
        
        conn.commit()
        conn.close()
    
    def create_remote(self, name: str, comment: str = None) -> int:
        """Create a new remote and return its ID"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("INSERT INTO Remote (name, comment) VALUES (?, ?)", (name, comment))
            remote_id = cursor.lastrowid
            conn.commit()
            return remote_id
        except sqlite3.IntegrityError:
            raise ValueError(f"Remote with name '{name}' already exists")
        finally:
            conn.close()
    
    def list_remotes(self) -> List[Tuple]:
        """List all remotes"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT id, name, comment FROM Remote ORDER BY name COLLATE NOCASE ASC")
        remotes = cursor.fetchall()
        conn.close()
        
        return remotes
    
    def get_remote(self, remote_id: int) -> Optional[Tuple]:
        """Get remote by ID"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT id, name, comment FROM Remote WHERE id = ?", (remote_id,))
        remote = cursor.fetchone()
        conn.close()
        
        return remote
    
    def add_key(self, remote_id: int, protocol: str, address: str, command: str, 
                key_name: str, comment: str = None):
        """Add a new key to a remote"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT OR REPLACE INTO Key (remote_id, protocol, address, command, key_name, comment)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (remote_id, protocol, address, command, key_name, comment))
            conn.commit()
        finally:
            conn.close()
    
    def get_keys_for_remote(self, remote_id: int) -> List[Tuple]:
        """Get all keys for a specific remote"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT key_name, protocol, address, command, comment 
            FROM Key 
            WHERE remote_id = ? 
            ORDER BY key_name
        """, (remote_id,))
        keys = cursor.fetchall()
        conn.close()
        
        return keys