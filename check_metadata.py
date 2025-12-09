import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.database import Base
from app import models

print("=" * 50)
print("Base metadata info:")
print(f"Number of tables: {len(Base.metadata.tables)}")
print("Tables in metadata:")

for table_name, table in Base.metadata.tables.items():
    print(f"\nTable: {table_name}")
    print(f"  Columns: {[col.name for col in table.columns]}")
    print(f"  Constraints: {[c for c in table.constraints]}")
    
print("\n" + "=" * 50)
print("Checking if models are properly imported...")
try:
    from app.models.users import User
    from app.models.categories import Category
    from app.models.products import Product
    from app.models.reviews import Review
    print("✓ All models imported successfully")
except ImportError as e:
    print(f"✗ Import error: {e}")
