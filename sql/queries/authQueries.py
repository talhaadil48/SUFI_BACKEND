from datetime import datetime,timezone
from typing import Optional
import json

class AuthQueries:
    def __init__(self, conn):
        self.conn = conn
        
    def create_user(self, email, name, password_hash, role, country, city):
        query = """
        INSERT INTO users (email, name, password_hash, role, country, city, is_registered)
        VALUES (%s, %s, %s, %s, %s, %s, TRUE)
        RETURNING id, email, name, role, country, city, permissions, is_registered, created_at;
        """
        with self.conn.cursor() as cur:
            cur.execute(query, (email, name, password_hash, role, country, city))
            user = cur.fetchone()
            self.conn.commit()
        return user


    def create_user_with_otp(self, email, name, password_hash, role, country, city, otp, otp_expiry):
        query = """
        INSERT INTO users (email, name, password_hash, role, country, city, otp, otp_expiry, is_registered)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, FALSE)
        RETURNING id, email, name, role, country, city, permissions, is_registered, created_at;
        """
        with self.conn.cursor() as cur:
            cur.execute(query, (email, name, password_hash, role, country, city, otp, otp_expiry))
            user = cur.fetchone()
            self.conn.commit()
            return user

    def get_user_by_email(self, email):
        query = "SELECT id, email, name, role, country, city, permissions, is_registered, password_hash FROM users WHERE email = %s;"
        with self.conn.cursor() as cur:
            cur.execute(query, (email,))
            row = cur.fetchone()
            if not row:
                return None
            keys = ["id", "email", "name", "role", "country", "city", "permissions", "is_registered", "password_hash"]
            return {k: row[i] for i, k in enumerate(keys)}


    def verify_otp_and_register(self, email, otp) -> tuple[Optional[dict], str]:
        query = "SELECT otp, otp_expiry, id, email, name, role, country, city, permissions FROM users WHERE email = %s;"
        with self.conn.cursor() as cur:
            cur.execute(query, (email,))
            row = cur.fetchone()
            if not row:
                return None, "User not found"

            stored_otp, expiry, user_id, email, name, role, country, city, permissions = row
            if not expiry:
                return None, "OTP expiry not found or not set"  


            if datetime.now(timezone.utc) > expiry:
                return None, "OTP expired"
            if stored_otp != otp:
                return None, "Invalid OTP"

            update_query = "UPDATE users SET is_registered = TRUE, otp = NULL, otp_expiry = NULL WHERE email = %s;"
            cur.execute(update_query, (email,))
            self.conn.commit()
            user_info = {
                "id": user_id,
                "email": email,
                "name": name,
                "role": role,
                "country": country,
                "city": city,
                "permissions": permissions,
                "is_registered": True
            }
            return user_info, "OTP verified"

    def resend_otp(self, email, otp, otp_expiry):
        query = "UPDATE users SET otp = %s, otp_expiry = %s WHERE email = %s;"
        with self.conn.cursor() as cur:
            cur.execute(query, (otp, otp_expiry, email))
            self.conn.commit()
    def update_password(self, email: str, new_password_hash: str):
        query = "UPDATE users SET password_hash = %s WHERE email = %s;"
        with self.conn.cursor() as cur:
            cur.execute(query, (new_password_hash, email))
            self.conn.commit()
            
    def get_user_by_id(self, user_id: int) -> dict:
        query = "SELECT * FROM users WHERE id = %s"
        with self.conn.cursor() as cur:
            cur.execute(query, (user_id,))
            return cur.fetchone()
        
        
    def create_subadmin(self, email, name, password_hash, permissions):
        query = """
        INSERT INTO users (email, name, password_hash, role, permissions, is_registered)
        VALUES (%s, %s, %s, 'sub-admin', %s, TRUE)
        RETURNING id, email, name, role, permissions, is_registered, created_at;
        """
        with self.conn.cursor() as cur:
            cur.execute(query, (email, name, password_hash, json.dumps(permissions)))
            user = cur.fetchone()
            self.conn.commit()
            if user:
                keys = ["id", "email", "name", "role", "permissions", "is_registered", "created_at"]
                return dict(zip(keys, user))
            return None 

    def update_subadmin(self, id, name, password_hash, permissions):
        query = """
        UPDATE users
        SET name = %s, password_hash = %s, permissions = %s
        WHERE id = %s AND role = 'sub-admin'
        RETURNING id, email, name, role, permissions, is_registered, updated_at;
        """
        with self.conn.cursor() as cur:
            cur.execute(query, (name, password_hash, json.dumps(permissions), id))
            user = cur.fetchone()
            self.conn.commit()
            if user:
                keys = ["id", "email", "name", "role", "permissions", "is_registered", "updated_at"]
                return dict(zip(keys, user))
            return None

    def delete_user_by_id(self, user_id):
        query = "DELETE FROM users WHERE id = %s;"
        with self.conn.cursor() as cur:
            cur.execute(query, (user_id,))
            self.conn.commit()

    
    def get_all_subadmins(self):
        query = """
        SELECT id, email, name, role, permissions, created_at
        FROM users
        WHERE role = 'sub-admin';
        """
        with self.conn.cursor() as cur:
            cur.execute(query)
            rows = cur.fetchall()
            keys = ["id", "email", "name", "role", "permissions", "created_at"]
            return [dict(zip(keys, row)) for row in rows]

