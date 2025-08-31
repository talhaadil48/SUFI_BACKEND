from dotenv import load_dotenv
import os
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env.local'))


host = os.getenv('HOST')
database = os.getenv('DATABASE')
user = os.getenv('USER')
password = os.getenv('PASSWORD')
port = os.getenv('PORT')
DATABASE_CONFIG = {
    "host" : host,
    "database": database,
    "user": user,
    "password": password,
    "port" : int(port),
    
}
