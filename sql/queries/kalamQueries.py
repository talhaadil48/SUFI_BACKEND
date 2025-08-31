
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from psycopg2.extras import RealDictCursor
from db.connection import DBConnection
from datetime import datetime, timezone

class KalamQueries:
    def __init__(self, conn):
        self.conn = conn

    def create_kalam(self, writer_id: int, data: any):
        query = """
        INSERT INTO kalam_content (
            title, language, theme, kalam_text, description, 
            sufi_influence, musical_preference
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        RETURNING id;
        """
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, (
                data.title, data.language, data.theme, data.kalam_text,
                data.description, data.sufi_influence, data.musical_preference
            ))
            content_id = cur.fetchone()['id']
            
            # Insert into kalams table
            query_kalam = """
            INSERT INTO kalams (content_id, writer_id)
            VALUES (%s, %s)
            RETURNING *;
            """
            cur.execute(query_kalam, (content_id, writer_id))

            # Insert into kalam_submissions
            query_submission = """
            INSERT INTO kalam_submissions (content_id, writer_id, status)
            VALUES (%s, %s, 'draft')
            RETURNING id;
            """
            cur.execute(query_submission, (content_id, writer_id))
            submission_id = cur.fetchone()['id']
            
            # Update kalams with submission_id
            query_update = """
            UPDATE kalams
            SET submission_id = %s
            WHERE content_id = %s;
            """
            cur.execute(query_update, (submission_id, content_id))
            
            self.conn.commit()
            return self.get_kalam(content_id)

    def get_kalam(self, kalam_id: int):
        query = """
        SELECT k.*, kc.title, kc.language, kc.theme, kc.kalam_text,
               kc.description, kc.sufi_influence, kc.musical_preference,
               ks.status as submission_status
        FROM kalams k
        JOIN kalam_content kc ON k.content_id = kc.id
        LEFT JOIN kalam_submissions ks ON k.submission_id = ks.id
        WHERE k.content_id = %s;
        """
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, (kalam_id,))
            return cur.fetchone()

    def update_kalam(self, content_id: int, data: any):
        fields = {
            "title": data.title,
            "language": data.language,
            "theme": data.theme,
            "kalam_text": data.kalam_text,
            "description": data.description,
            "sufi_influence": data.sufi_influence,
            "musical_preference": data.musical_preference
        }
        set_clauses = []
        values = []

        for key, value in fields.items():
            if value is not None:
                set_clauses.append(f"{key} = %s")
                values.append(value)

        if not set_clauses:
            return None

        set_clause_str = ", ".join(set_clauses) + ", updated_at = CURRENT_TIMESTAMP"
        values.append(content_id)

        query = f"""
        UPDATE kalam_content
        SET {set_clause_str}
        WHERE id = %s
        RETURNING *;
        """
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, values)
            self.conn.commit()
            return self.get_kalam(content_id)

    def assign_vocalist(self, content_id: int, vocalist_id: int):
        query = """
        UPDATE kalams
        SET vocalist_id = %s, updated_at = CURRENT_TIMESTAMP
        WHERE content_id = %s
        RETURNING *;
        """
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, (vocalist_id, content_id))
            self.conn.commit()
            return self.get_kalam(content_id)

    def submit_kalam(self, content_id: int, writer_id: int, writer_comments: Optional[str]):
        query = """
        UPDATE kalam_submissions
        SET status = 'submitted',
            user_approval_status = 'pending',
            writer_comments = %s,
            updated_at = CURRENT_TIMESTAMP
        WHERE content_id = %s AND writer_id = %s
        RETURNING *;
        """
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, (writer_comments, content_id, writer_id))
            self.conn.commit()
            return cur.fetchone()

    def get_submission(self, submission_id: int):
        query = """
        SELECT * FROM kalam_submissions
        WHERE id = %s;
        """
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, (submission_id,))
            return cur.fetchone()

    def update_submission_status(self, submission_id: int, new_status: str, comments: Optional[str]):
        query = """
        UPDATE kalam_submissions
        SET status = %s,
            admin_comments = %s,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = %s
        RETURNING *;
        """
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, (new_status, comments, submission_id))
            self.conn.commit()
            return cur.fetchone()

    def writer_response(self, submission_id: int, user_approval_status: str, writer_comments: Optional[str]):
        query = """
        UPDATE kalam_submissions
        SET user_approval_status = %s,
            writer_comments = %s,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = %s
        RETURNING *;
        """
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, (user_approval_status, writer_comments, submission_id))
            self.conn.commit()
            result = cur.fetchone()
            
            # If approved, update kalams table
            if user_approval_status == 'approved':
                query_update = """
                UPDATE kalams
                SET updated_at = CURRENT_TIMESTAMP
                WHERE submission_id = %s;
                """
                cur.execute(query_update, (submission_id,))
                self.conn.commit()
                
            return result
