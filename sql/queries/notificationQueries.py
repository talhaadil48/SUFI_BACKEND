from typing import List
from psycopg2.extras import RealDictCursor
from pydantic import BaseModel
class SpecialRecognitionCreate(BaseModel):
    title: str
    subtitle: str | None = None
    description: str | None = None
    achievement: str | None = None

class NotificationQueries:
    def __init__(self, conn):
        self.conn = conn

    def create_notification(self, title, message, target_type, target_user_ids=None):
        query = """
        INSERT INTO notifications (title, message, target_type, target_user_ids)
        VALUES (%s, %s, %s, %s)
        RETURNING id, title, message, target_type, target_user_ids, created_at;
        """
        with self.conn.cursor() as cur:
            cur.execute(query, (title, message, target_type, target_user_ids))
            notification = cur.fetchone()
            self.conn.commit()
        return notification

    def get_user_notifications(self, user_id):
        user = self.get_user_by_id(user_id)
        if not user or user["role"] == "admin":
            return []

        user_role = user["role"]+'s'  # Convert 'writer' to 'writers', 'vocalist' to 'vocalists'

        query = """
        SELECT n.id, n.title, n.message, n.target_type, n.target_user_ids, n.created_at,
            CASE WHEN nr.id IS NULL THEN FALSE ELSE TRUE END AS is_read
        FROM notifications n
        LEFT JOIN notification_reads nr
            ON nr.notification_id = n.id AND nr.user_id = %s
        WHERE n.target_type = 'all'
        OR n.target_type = %s
        OR (n.target_type = 'specific' AND %s = ANY(n.target_user_ids))
        ORDER BY n.created_at DESC;
        """
        with self.conn.cursor() as cur:
            cur.execute(query, (user_id, user_role, user_id))
            notifications = cur.fetchall()
        return notifications

    def mark_as_read(self, notification_id, user_id):
        query = """
        INSERT INTO notification_reads (notification_id, user_id)
        VALUES (%s, %s)
        ON CONFLICT (notification_id, user_id) DO NOTHING
        RETURNING id;
        """
        with self.conn.cursor() as cur:
            cur.execute(query, (notification_id, user_id))
            read_entry = cur.fetchone()
            self.conn.commit()
        return read_entry



    def create_guest_post(
        self,
        user_id: str,
        title: str,
        role: str,
        city: str,
        country: str,
        date: str,
        category: str,
        excerpt: str,
        content: str,
        tags: List[str]
    ) -> int:
        query = """
            INSERT INTO guest_posts (
                user_id, title, role, city, country, date, 
                category, excerpt, content, tags, status
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'pending')
            RETURNING id;
        """
        try:
            with self.conn.cursor() as cur:
                cur.execute(query, (
                    user_id, title, role, city, country, date,
                    category, excerpt, content, tags
                ))
                post_id = cur.fetchone()[0]
                self.conn.commit()
                return post_id
        except Exception as e:
            self.conn.rollback()
            raise e
        
        
    def update_guest_post_status(self, post_id: int, status: str):
        query = """
            UPDATE guest_posts 
            SET status = %s 
            WHERE id = %s;
        """
        try:
            with self.conn.cursor() as cur:
                cur.execute(query, (status, post_id))
                self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            raise e
        
        
    
    def fetch_all_guest_posts(self) -> List[dict]:
        query = """
            SELECT 
                gp.*,
                u.name AS author
            FROM guest_posts gp
            JOIN users u ON gp.user_id = u.id
            ORDER BY gp.date DESC;
        """
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query)
                return cur.fetchall()
        except Exception as e:
            raise e

    def fetch_user_guest_posts(self, user_id: str) -> List[dict]:
        query = """
            SELECT 
                gp.*,
                u.name AS author
            FROM guest_posts gp
            JOIN users u ON gp.user_id = u.id
            WHERE gp.user_id = %s
            ORDER BY gp.date DESC;
        """
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, (user_id,))
                return cur.fetchall()
        except Exception as e:
            raise e

    def fetch_paginated_guest_posts(self, skip: int, limit: int) -> List[dict]:
        query = """
            SELECT 
                gp.*,
                u.name AS author
            FROM guest_posts gp
            JOIN users u ON gp.user_id = u.id
            WHERE gp.status = 'approved'
            ORDER BY gp.date DESC
            OFFSET %s
            LIMIT %s;
        """
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, (skip, limit))
                return cur.fetchall()
        except Exception as e:
            raise e
        
        
        
    def create_special_recognition(self, recognition: SpecialRecognitionCreate) -> dict:
        query = """
            INSERT INTO special_recognitions (title, subtitle, description, achievement)
            VALUES (%s, %s, %s, %s)
            RETURNING *;
        """
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, (
                    recognition.title,
                    recognition.subtitle,
                    recognition.description,
                    recognition.achievement
                ))
                self.conn.commit()
                return cur.fetchone()
        except Exception as e:
            self.conn.rollback()
            raise e

    
    def fetch_all_special_recognitions(self) -> List[dict]:
        query = """
            SELECT *
            FROM special_recognitions
            ORDER BY id DESC;
        """
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query)
                return cur.fetchall()
        except Exception as e:
            raise e
        
        
    def delete_special_recognition(self, recognition_id: int) -> dict:
        query = """
            DELETE FROM special_recognitions
            WHERE id = %s
            RETURNING *;
        """
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, (recognition_id,))
                result = cur.fetchone()
                self.conn.commit()
                if not result:
                    raise HTTPException(status_code=404, detail="Recognition not found")
                return result
        except Exception as e:
            self.conn.rollback()
            raise e


        
  
