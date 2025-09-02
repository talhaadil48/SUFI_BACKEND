from psycopg2.extras import RealDictCursor
from datetime import datetime, timezone
from typing import Optional
from sql.queries import AuthQueries,VocalistQueries,KalamQueries,StudioQueries

class Queries(AuthQueries,VocalistQueries,KalamQueries,StudioQueries):
    def __init__(self, conn):
        # Initialize both parent classes
        AuthQueries.__init__(self, conn)
        VocalistQueries.__init__(self, conn)
        KalamQueries.__init__(self, conn)
        StudioQueries.__init__(self,conn)
        