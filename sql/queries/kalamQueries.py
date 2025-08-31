from psycopg2.extras import RealDictCursor
from typing import Optional

class KalamQueries:
    def __init__(self, conn):
        self.conn = conn

    def create_kalam(self, title: str, language: str, theme: str, kalam_text: str, description: str, 
                     sufi_influence: str, musical_preference: str, writer_id: int):
        query = """
        INSERT INTO kalams (
            title, language, theme, kalam_text, description, sufi_influence, musical_preference, writer_id
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING *;
        """
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, (title, language, theme, kalam_text, description, sufi_influence, 
                                musical_preference, writer_id))
            self.conn.commit()
            return cur.fetchone()

    def get_kalam_by_id(self, kalam_id: int):
        query = "SELECT * FROM kalams WHERE id = %s;"
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, (kalam_id,))
            return cur.fetchone()

    def update_kalam(self, kalam_id: int, title: Optional[str] = None, language: Optional[str] = None, 
                     theme: Optional[str] = None, kalam_text: Optional[str] = None, 
                     description: Optional[str] = None, sufi_influence: Optional[str] = None, 
                     musical_preference: Optional[str] = None):
        fields = {
            "title": title,
            "language": language,
            "theme": theme,
            "kalam_text": kalam_text,
            "description": description,
            "sufi_influence": sufi_influence,
            "musical_preference": musical_preference
        }

        set_clauses = []
        values = []

        for key, value in fields.items():
            if value is not None:
                set_clauses.append(f"{key} = %s")
                values.append(value)

        if not set_clauses:
            return None  # Nothing to update

        set_clause_str = ", ".join(set_clauses) + ", updated_at = CURRENT_TIMESTAMP"
        values.append(kalam_id)

        query = f"""
            UPDATE kalams
            SET {set_clause_str}
            WHERE id = %s
            RETURNING *;
        """

        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, values)
            self.conn.commit()
            return cur.fetchone()

    def assign_vocalist(self, kalam_id: int, user_id: int):
        query_update = """
        UPDATE kalams
        SET vocalist_id = %s, updated_at = CURRENT_TIMESTAMP
        WHERE id = %s
        RETURNING *;
        """
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Check if this user_id exists in vocalists table
            cur.execute("SELECT 1 FROM vocalists WHERE user_id = %s", (user_id,))
            if not cur.fetchone():
                raise ValueError("No vocalist found for this user_id")
            
            # Assign user_id to kalams.vocalist_id
            cur.execute(query_update, (user_id, kalam_id))
            self.conn.commit()
            return cur.fetchone()


    def update_youtube_link(self, kalam_id: int, youtube_link: str):
        query = """
        UPDATE kalams
        SET youtube_link = %s, updated_at = CURRENT_TIMESTAMP
        WHERE id = %s
        RETURNING *;
        """
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, (youtube_link, kalam_id))
            self.conn.commit()
            return cur.fetchone()

    def get_kalam_submission_by_kalam_id(self, kalam_id: int):
        query = "SELECT * FROM kalam_submissions WHERE kalam_id = %s;"
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, (kalam_id,))
            return cur.fetchone()

    def get_kalam_submission_by_id(self, submission_id: int):
        query = "SELECT * FROM kalam_submissions WHERE id = %s;"
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, (submission_id,))
            return cur.fetchone()

    def submit_kalam(self, kalam_id: int, writer_comments: Optional[str] = None):
        existing = self.get_kalam_submission_by_kalam_id(kalam_id)
        if existing:
            query = """
            UPDATE kalam_submissions
            SET status = 'submitted', user_approval_status = 'pending', 
                writer_comments = %s, updated_at = CURRENT_TIMESTAMP
            WHERE kalam_id = %s
            RETURNING *;
            """
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, (writer_comments, kalam_id))
                self.conn.commit()
                return cur.fetchone()
        else:
            query = """
            INSERT INTO kalam_submissions (kalam_id, status, user_approval_status, writer_comments)
            VALUES (%s, 'submitted', 'pending', %s)
            RETURNING *;
            """
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, (kalam_id, writer_comments))
                self.conn.commit()
                return cur.fetchone()

    def update_submission_status(self, submission_id: int, new_status: str, admin_comments: Optional[str] = None):
        query = """
        UPDATE kalam_submissions
        SET status = %s, admin_comments = %s, updated_at = CURRENT_TIMESTAMP
        WHERE id = %s
        RETURNING *;
        """
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, (new_status, admin_comments, submission_id))
            self.conn.commit()
            return cur.fetchone()

    def writer_response(self, submission_id: int, user_approval_status: str, writer_comments: Optional[str] = None):
        query = """
        UPDATE kalam_submissions
        SET user_approval_status = %s, writer_comments = %s, updated_at = CURRENT_TIMESTAMP
        WHERE id = %s
        RETURNING *;
        """
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, (user_approval_status, writer_comments, submission_id))
            self.conn.commit()
            return cur.fetchone()
