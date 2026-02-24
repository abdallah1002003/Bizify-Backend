from sqlalchemy import create_engine
import os
from dotenv import load_dotenv

load_dotenv()
db_url = os.getenv("DATABASE_URL")
if not db_url:
    print("NO DB URL")
    exit(1)
    
engine = create_engine(db_url)
with engine.connect() as conn:
    print("Connected")
