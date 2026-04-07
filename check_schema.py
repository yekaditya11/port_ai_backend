from database import engine
from sqlalchemy import inspect

inspector = inspect(engine)
for table_name in inspector.get_table_names():
    print(f"Table: {table_name}")
    for column in inspector.get_columns(table_name):
        print(f"  - {column['name']}")
