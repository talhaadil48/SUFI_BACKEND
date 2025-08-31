import psycopg2
from config import DATABASE_CONFIG
from psycopg2.extras import DictCursor
class DBConnection:
    """
    Manages a single global DB connection using psycopg (PostgreSQL).
    """
    _connection = None

    @classmethod
    def get_connection(cls):
        if cls._connection is None or cls._connection.closed:
            try:
                print(DATABASE_CONFIG)
                cls._connection = psycopg2.connect(
                    host=DATABASE_CONFIG["host"],
                    dbname=DATABASE_CONFIG["database"],
                    user=DATABASE_CONFIG["user"],
                    password=DATABASE_CONFIG["password"],
                    port=DATABASE_CONFIG["port"],
                    cursor_factory=DictCursor  # Returns rows as dicts like DictCursor
                )
                print("Database connected.")
            except psycopg2.Error as e:
                print("Error connecting to database:", e)
                raise e
        return cls._connection

    @classmethod
    def get_cursor(cls):
        return cls.get_connection().cursor()

    @classmethod
    def close_connection(cls):
        if cls._connection and not cls._connection.closed:
            cls._connection.close()
            print("Database connection closed.")
            cls._connection = None
