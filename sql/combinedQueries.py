from psycopg2.extras import RealDictCursor
from datetime import datetime, timezone
from typing import Optional
from sql.queries import AuthQueries,VocalistQueries

class Queries(AuthQueries,VocalistQueries):
    def __init__(self, conn):
        # Initialize both parent classes
        AuthQueries.__init__(self, conn)
        VocalistQueries.__init__(self, conn)
