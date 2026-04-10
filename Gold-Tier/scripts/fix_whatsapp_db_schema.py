"""
Fix Database Schema - Update column sizes for whatsapp_messages table
"""

from db_neon import NeonDatabase

def fix_schema():
    """Fix the recipient_number and sender_number column sizes."""
    db = NeonDatabase()
    
    print("Connecting to Neon database...")
    
    try:
        with db.get_cursor(commit=True) as cursor:
            # Alter existing table columns
            cursor.execute('''
                ALTER TABLE whatsapp_messages 
                ALTER COLUMN sender_number TYPE VARCHAR(50),
                ALTER COLUMN recipient_number TYPE VARCHAR(50)
            ''')
        
        print("✓ Database schema updated successfully!")
        print("  - sender_number: VARCHAR(20) → VARCHAR(50)")
        print("  - recipient_number: VARCHAR(20) → VARCHAR(50)")
        
        # Verify the changes
        with db.get_cursor() as cursor:
            cursor.execute('''
                SELECT column_name, data_type, character_maximum_length 
                FROM information_schema.columns 
                WHERE table_name = 'whatsapp_messages' 
                AND column_name IN ('sender_number', 'recipient_number')
                ORDER BY column_name
            ''')
            columns = cursor.fetchall()
            print("\nCurrent column definitions:")
            for col in columns:
                print(f"  - {col['column_name']}: {col['data_type']}({col['character_maximum_length']})")
        
        return True
        
    except Exception as e:
        print(f"✗ Error updating schema: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("WhatsApp Database Schema Fix")
    print("=" * 60)
    print()
    
    if fix_schema():
        print("\n✓ Schema fix complete! Try sending a message again:")
        print("  python scripts\\whatsapp_responder.py --to \"whatsapp:+923163265423\" --message \"Test\"")
    else:
        print("\n✗ Schema fix failed. Check your database connection.")
