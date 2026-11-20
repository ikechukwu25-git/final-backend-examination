
from app.database import engine, Base
from app import models

# Create all database tables
Base.metadata.create_all(bind=engine)

print("Database created successfully!")

print("Tables:", Base.metadata.tables.keys())
