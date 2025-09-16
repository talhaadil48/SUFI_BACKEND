from psycopg2.extras import RealDictCursor
from typing import List, Optional


class WriterQueries:
    def __init__(self, conn):
        self.conn = conn

    def get_writer_by_user_id(self, user_id: int):
        query = """
            SELECT 
                w.*, 
                u.country, 
                u.city
            FROM writers w
            JOIN users u ON w.user_id = u.id
            WHERE w.user_id = %s;
        """
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, (user_id,))
            return cur.fetchone()

    def create_writer_profile(self, user_id, writing_styles, languages, sample_title,
                              experience_background, portfolio, availability):
        query = """
        INSERT INTO writers (
            user_id, writing_styles, languages, sample_title,
            experience_background, portfolio, availability
        )
        VALUES (%s,%s,%s,%s,%s,%s,%s)
        RETURNING *;
        """
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, (
                user_id, writing_styles, languages, sample_title,
                experience_background, portfolio, availability
            ))
            self.conn.commit()
            return cur.fetchone()

    def update_writer_profile(self, user_id, writing_styles=None, languages=None,
                              sample_title=None, experience_background=None,
                              portfolio=None, availability=None):
        fields = {
            "writing_styles": writing_styles,
            "languages": languages,
            "sample_title": sample_title,
            "experience_background": experience_background,
            "portfolio": portfolio,
            "availability": availability
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
        values.append(user_id)

        query = f"""
            UPDATE writers
            SET {set_clause_str}
            WHERE user_id = %s
            RETURNING *;
        """

        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, values)
            self.conn.commit()
            return cur.fetchone()

    def is_writer_registered(self, user_id: int):
        query = """
        SELECT w.id
        FROM writers w
        JOIN users u ON u.id = w.user_id
        WHERE w.user_id = %s AND u.role = 'writer';
        """
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, (user_id,))
            return cur.fetchone()
        
        
        
    def fetch_writers(self, skip: int, limit: int) -> List[dict]:
        query = """
            SELECT
                w.*,
                u.name AS user_name,
                u.email AS user_email,
                u.country AS user_country,
                u.city AS user_city,
                u.role AS user_role
            FROM writers w
            JOIN users u ON w.user_id = u.id
            ORDER BY w.created_at DESC
            OFFSET %s
            LIMIT %s;
        """
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, (skip, limit))
                writers = cur.fetchall()
                return writers
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
