import os
import sys

# Ensure we can import from the current directory
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from database_manager import DatabaseManager

if __name__ == "__main__":
    print("Connecting to database...")
    db = DatabaseManager()
    
    print("Clearing all student data...")
    try:
        count = db.clear_all_student_data()
        print(f"SUCCESS: {count} student records and all related data have been cleared from the database.")
    except Exception as e:
        print(f"ERROR: Failed to clear database. {e}")
