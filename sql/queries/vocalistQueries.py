from psycopg2.extras import RealDictCursor

class VocalistQueries:
    def __init__(self, conn):
        self.conn = conn


    def get_vocalist_by_user_id(self, user_id: int):
        query = "SELECT * FROM vocalists WHERE user_id = %s;"
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, (user_id,))
            return cur.fetchone()

    def create_vocalist_profile(self, user_id, vocal_range, languages, sample_title, audio_sample_url,
                                sample_description, experience_background, portfolio, availability):
        query = """
        INSERT INTO vocalists (
            user_id, vocal_range, languages, sample_title, audio_sample_url,
            sample_description, experience_background, portfolio, availability
        )
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
        RETURNING *;
        """
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, (user_id, vocal_range, languages, sample_title,
                                audio_sample_url, sample_description,
                                experience_background, portfolio, availability))
            self.conn.commit()
            return cur.fetchone()

    def update_vocalist_profile(self, user_id, vocal_range=None, languages=None, sample_title=None,
                            audio_sample_url=None, sample_description=None, experience_background=None,
                            portfolio=None, availability=None):
        fields = {
            "vocal_range": vocal_range,
            "languages": languages,
            "sample_title": sample_title,
            "audio_sample_url": audio_sample_url,
            "sample_description": sample_description,
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
            UPDATE vocalists
            SET {set_clause_str}
            WHERE user_id = %s
            RETURNING *;
        """

        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, values)
            self.conn.commit()
            return cur.fetchone()