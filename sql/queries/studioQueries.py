from psycopg2.extras import RealDictCursor
from typing import Optional
from datetime import datetime, timezone
from fastapi import HTTPException
from datetime import date

class StudioQueries:
    def __init__(self, conn):
        self.conn = conn

    def check_studio_visit_conflict(self, vocalist_id: int, kalam_id: int, preferred_date: date, preferred_time: str) -> bool:
        query = """
            SELECT EXISTS (
                SELECT 1 FROM studio_visit_requests 
                WHERE vocalist_id = %s AND kalam_id = %s 
                AND preferred_date = %s AND preferred_time = %s
            ) as conflict;
        """
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, (vocalist_id, kalam_id, preferred_date, preferred_time))
            result = cur.fetchone()
            printr(result)
            return result['conflict']

    def check_remote_recording_conflict(self, vocalist_id: int, kalam_id: int, preferred_date: date, preferred_time: str) -> bool:
        query = """
            SELECT EXISTS (
                SELECT 1 FROM remote_recording_requests 
                WHERE vocalist_id = %s AND kalam_id = %s 
                AND preferred_date = %s AND preferred_time = %s
            ) as conflict;
        """
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, (vocalist_id, kalam_id, preferred_date, preferred_time))
            
            result = cur.fetchone()
            print(result)
            return result['conflict']
        
    def check_studio_visit_conflict_datetime(self, preferred_date: date, preferred_time: str) -> bool:
        query = """
            SELECT EXISTS (
                SELECT 1 FROM studio_visit_requests 
                WHERE preferred_date = %s AND preferred_time = %s
            ) as conflict;
        """
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, (preferred_date, preferred_time))
            result = cur.fetchone()
            print(result)
            return result['conflict']

    def check_remote_recording_conflict_datetime(self, preferred_date: date, preferred_time: str) -> bool:
        query = """
            SELECT EXISTS (
                SELECT 1 FROM remote_recording_requests 
                WHERE preferred_date = %s AND preferred_time = %s
            ) as conflict;
        """
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, (preferred_date, preferred_time))
            result = cur.fetchone()
            print(result)
            return result['conflict']


    def create_studio_visit_request(self, data: dict) -> dict:
        if data.get('preferred_date'):
            preferred_date_obj = data['preferred_date']
            if isinstance(preferred_date_obj, str):
                preferred_date_obj = datetime.strptime(preferred_date_obj, "%Y-%m-%d").date()
            if preferred_date_obj < date.today():
                raise HTTPException(
                    status_code=400,
                    detail="The preferred date cannot be in the past."
                )
        # Check for scheduling conflict
        if data.get('preferred_date') and data.get('preferred_time'):
            if self.check_studio_visit_conflict_datetime(
                data['preferred_date'], 
                data['preferred_time']
            ):
                raise HTTPException(
                    status_code=400, 
                    detail="The selected time slot is already taken. Please choose another time."
                )

        query = """
            INSERT INTO studio_visit_requests (
                vocalist_id, kalam_id, name, email, organization, contact_number,
                preferred_date, preferred_time, purpose, number_of_visitors,
                additional_details, special_requests, status, created_at, updated_at
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING *;
        """
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, (
                data['vocalist_id'],
                data['kalam_id'],
                data['name'], data['email'],
                data['organization'], data['contact_number'],
                data['preferred_date'], data['preferred_time'],
                data['purpose'], data['number_of_visitors'],
                data['additional_details'], data['special_requests'],
                'pending', datetime.now(timezone.utc),
                datetime.now(timezone.utc)
            ))
            self.conn.commit()
            return cur.fetchone()

    def get_all_studio_visit_requests(self) -> list:
        query = "SELECT * FROM studio_visit_requests ORDER BY created_at DESC;"
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query)
            return cur.fetchall()

    def get_studio_visit_requests_by_vocalist(self, vocalist_user_id: int) -> list:
        query = "SELECT * FROM studio_visit_requests WHERE vocalist_id = %s ORDER BY created_at DESC;"
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, (vocalist_user_id,))
            return cur.fetchall()

    def create_remote_recording_request(self, data: dict) -> dict:
        # Check for scheduling conflict
        if data.get('preferred_date'):
            preferred_date_obj = data['preferred_date']
            if isinstance(preferred_date_obj, str):
                preferred_date_obj = datetime.strptime(preferred_date_obj, "%Y-%m-%d").date()
            if preferred_date_obj < date.today():
                raise HTTPException(
                    status_code=400,
                    detail="The preferred date cannot be in the past."
                )
        if data.get('preferred_date') and data.get('preferred_time'):
            if self.check_remote_recording_conflict_datetime(
                
                data['preferred_date'], 
                data['preferred_time']
            ):
                raise HTTPException(
                    status_code=400, 
                    detail="The selected time slot is already taken. Please choose another time."
                )

        query = """
            INSERT INTO remote_recording_requests (
                vocalist_id, kalam_id, name, email, city, country, time_zone, role,
                project_type, recording_equipment, internet_speed, preferred_software,
                availability, recording_experience, technical_setup, additional_details,
                status, created_at, updated_at
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING *;
        """
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, (
                data['vocalist_id'],
                data['kalam_id'],
                data['name'], data['email'],
                data['city'], data['country'], data['time_zone'], data['role'],
                data['project_type'], data['recording_equipment'], data['internet_speed'],
                data['preferred_software'], data['availability'],
                data['recording_experience'], data['technical_setup'],
                data['additional_details'], 'pending',
                datetime.now(timezone.utc), datetime.now(timezone.utc)
            ))
            self.conn.commit()
            return cur.fetchone()

    def get_all_remote_recording_requests(self) -> list:
        query = "SELECT * FROM remote_recording_requests ORDER BY created_at DESC;"
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query)
            return cur.fetchall()

    def get_remote_recording_requests_by_vocalist(self, vocalist_user_id: int) -> list:
        query = "SELECT * FROM remote_recording_requests WHERE vocalist_id = %s ORDER BY created_at DESC;"
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, (vocalist_user_id,))
            return cur.fetchall()
    def studio_request_exists(self, vocalist_id: int, kalam_id: int) -> bool:
        query = """
        SELECT 1
        FROM studio_visit_requests
        WHERE vocalist_id = %s AND kalam_id = %s
        LIMIT 1;
        """
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, (vocalist_id, kalam_id))
            return cur.fetchone() is not None

    def remote_request_exists(self, vocalist_id: int, kalam_id: int) -> bool:
        query = """
        SELECT 1
        FROM remote_recording_requests
        WHERE vocalist_id = %s AND kalam_id = %s
        LIMIT 1;
        """
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, (vocalist_id, kalam_id))
            return cur.fetchone() is not None
