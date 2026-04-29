import sys

with open('database_manager.py', 'r', encoding='utf-8') as f:
    content = f.read()

new_method = '''
    def delete_student(self, student_id: int) -> bool:
        """Delete a student and all their payment records (cascade). Returns True on success."""
        self._ensure_connection()
        cursor = self.connection.cursor()
        try:
            cursor.execute("DELETE FROM students WHERE id = %s", (student_id,))
            self.connection.commit()
            return cursor.rowcount > 0
        except Error as e:
            self.connection.rollback()
            raise RuntimeError(f"Failed to delete student: {e}")
        finally:
            cursor.close()
'''

content = content.rstrip() + '\n' + new_method + '\n'
with open('database_manager.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Done')
