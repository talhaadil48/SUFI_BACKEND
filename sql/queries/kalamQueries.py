from psycopg2.extras import RealDictCursor
from typing import Optional,List
from fastapi import HTTPException

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
        
        
    def get_kalams_by_writer_id(self, writer_id: int) -> List[dict]:
        query = "SELECT * FROM kalams WHERE writer_id = %s ORDER BY created_at DESC;"
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, (writer_id,))
            return cur.fetchall()

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
        query_submission = """
        UPDATE kalam_submissions
        SET vocalist_approval_status = 'pending', status = 'final_approved', updated_at = CURRENT_TIMESTAMP
        WHERE kalam_id = %s
        RETURNING *;
        """
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Check if this user_id exists in vocalists table
            cur.execute("SELECT 1 FROM vocalists WHERE user_id = %s", (user_id,))
            if not cur.fetchone():
                raise ValueError("No vocalist found for this user_id")
            
            # Assign user_id to kalams.vocalist_id
            cur.execute(query_update, (user_id, kalam_id))
            kalam = cur.fetchone()
            
            # Update submission status
            cur.execute(query_submission, (kalam_id,))
            submission = cur.fetchone()
            
            self.conn.commit()
            return kalam, submission

    def update_youtube_link(self, kalam_id: int, youtube_link: str):
        query_kalam = """
        UPDATE kalams
        SET youtube_link = %s, updated_at = CURRENT_TIMESTAMP, published_at = CURRENT_TIMESTAMP
        WHERE id = %s
        RETURNING *;
        """
        query_submission = """
        UPDATE kalam_submissions
        SET status = 'posted', updated_at = CURRENT_TIMESTAMP
        WHERE kalam_id = %s
        RETURNING *;
        """
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query_kalam, (youtube_link, kalam_id))
            kalam = cur.fetchone()
            
            cur.execute(query_submission, (kalam_id,))
            submission = cur.fetchone()
            
            self.conn.commit()
            return kalam, submission

    def vocalist_response(self, kalam_id: int, vocalist_approval_status: str, vocalist_comments: Optional[str] = None):
        if vocalist_approval_status not in ["approved", "rejected"]:
            raise ValueError("Invalid vocalist approval status")

        if vocalist_approval_status == "rejected":
            query_kalam = """
            UPDATE kalams
            SET vocalist_id = NULL, updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
            RETURNING *;
            """
            query_submission = """
            UPDATE kalam_submissions
            SET status = 'pending', vocalist_approval_status = %s, writer_comments = %s, updated_at = CURRENT_TIMESTAMP
            WHERE kalam_id = %s
            RETURNING *;
            """
        else:  # approved
            query_kalam = """
            UPDATE kalams
            SET updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
            RETURNING *;
            """
            query_submission = """
            UPDATE kalam_submissions
            SET status = 'complete_approved', vocalist_approval_status = %s, writer_comments = %s, 
                updated_at = CURRENT_TIMESTAMP
            WHERE kalam_id = %s
            RETURNING *;
            """

        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query_kalam, (kalam_id,))
            kalam = cur.fetchone()
            
            cur.execute(query_submission, (vocalist_approval_status, vocalist_comments, kalam_id))
            submission = cur.fetchone()
            
            self.conn.commit()
            return kalam, submission

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
        if new_status == "changes_requested":
            user_approval_status = "pending"
        elif new_status == "final_approved":
            user_approval_status = "approved"
        else:
            user_approval_status = None

        if user_approval_status:
            query = """
            UPDATE kalam_submissions
            SET status = %s, admin_comments = %s, user_approval_status = %s, updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
            RETURNING *;
            """
            params = (new_status, admin_comments, user_approval_status, submission_id)
        else:
            query = """
            UPDATE kalam_submissions
            SET status = %s, admin_comments = %s, updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
            RETURNING *;
            """
            params = (new_status, admin_comments, submission_id)

        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, params)
            self.conn.commit()
            return cur.fetchone()


    def writer_response(self, submission_id: int, user_approval_status: str, writer_comments: Optional[str] = None):
    # Only update status if user_approval_status is 'rejected'
        update_status = "submitted" if user_approval_status.lower() == "rejected" else None

        if update_status:
            query = """
            UPDATE kalam_submissions
            SET user_approval_status = %s, writer_comments = %s, status = %s, updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
            RETURNING *;
            """
            params = (user_approval_status, writer_comments, update_status, submission_id)
        else:
            query = """
            UPDATE kalam_submissions
            SET user_approval_status = %s, writer_comments = %s, updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
            RETURNING *;
            """
            params = (user_approval_status, writer_comments, submission_id)

        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, params)
            self.conn.commit()
            return cur.fetchone()


    def fetch_posted_kalams(self, skip: int, limit: int) -> List[dict]:
        query = """
            SELECT
                k.*,
                u.name AS writer_name,
                u.email AS writer_email,
                u.country AS writer_country,
                u.city AS writer_city,
                v.name AS vocalist_name,
                v.email AS vocalist_email,
                v.country AS vocalist_country,
                v.city AS vocalist_city
            FROM kalams k
            JOIN users u ON k.writer_id = u.id
            LEFT JOIN users v ON k.vocalist_id = v.id
            JOIN kalam_submissions ks ON ks.kalam_id = k.id
            WHERE ks.status = 'posted'
            ORDER BY k.created_at DESC, k.id DESC
            OFFSET %s
            LIMIT %s;
        """
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, (skip, limit))
                kalams = cur.fetchall()
                return kalams
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
