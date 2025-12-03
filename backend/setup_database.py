#!/usr/bin/env python3
"""
Database setup script for Potato Backend
This script helps you set up the PostgreSQL database
"""

import os
import sys
import subprocess

def check_postgres_installed():
    """Check if PostgreSQL is installed and accessible"""
    try:
        result = subprocess.run(['psql', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ PostgreSQL found: {result.stdout.strip()}")
            return True
        else:
            print("❌ PostgreSQL not found or not accessible")
            return False
    except FileNotFoundError:
        print("❌ PostgreSQL not installed or not in PATH")
        return False

def create_database():
    """Create the potato_db database"""
    print("🔍 Creating database 'potato_db'...")
    
    try:
        # Try to create the database
        result = subprocess.run([
            'createdb', '-U', 'postgres', 'potato_db'
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Database 'potato_db' created successfully")
            return True
        elif "already exists" in result.stderr:
            print("✅ Database 'potato_db' already exists")
            return True
        else:
            print(f"❌ Failed to create database: {result.stderr}")
            return False
            
    except FileNotFoundError:
        print("❌ 'createdb' command not found. Please install PostgreSQL client tools.")
        return False

def test_connection():
    """Test connection to the database"""
    print("🔍 Testing database connection...")
    
    try:
        result = subprocess.run([
            'psql', '-U', 'postgres', '-d', 'potato_db', '-c', 'SELECT 1 as test;'
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Database connection test successful")
            return True
        else:
            print(f"❌ Database connection test failed: {result.stderr}")
            return False
            
    except FileNotFoundError:
        print("❌ 'psql' command not found. Please install PostgreSQL client tools.")
        return False

def setup_database():
    """Set up the database with tables and sample data"""
    print("🔍 Setting up database tables and sample data...")
    
    try:
        # Add the app directory to the path
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))
        
        from app.db.database import engine
        from app.db.postgres_models import Base
        
        # Create tables
        Base.metadata.create_all(bind=engine)
        print("✅ Database tables created successfully")
        
        # Try to seed the database
        try:
            from app.main import seed_database
            seed_database()
            print("✅ Sample data seeded successfully")
        except Exception as e:
            print(f"⚠️ Sample data seeding failed: {e}")
            print("This is not critical, continuing...")
        
        return True
        
    except Exception as e:
        print(f"❌ Database setup failed: {e}")
        return False

def main():
    """Main setup function"""
    print("🥔 Potato Database Setup Script")
    print("=" * 40)
    
    # Check PostgreSQL installation
    if not check_postgres_installed():
        print("\n💡 Please install PostgreSQL first:")
        print("   - Windows: Download from https://www.postgresql.org/download/windows/")
        print("   - macOS: brew install postgresql")
        print("   - Ubuntu: sudo apt-get install postgresql postgresql-contrib")
        return
    
    print()
    
    # Create database
    if not create_database():
        print("\n💡 Please create the database manually:")
        print("   createdb -U postgres potato_db")
        return
    
    print()
    
    # Test connection
    if not test_connection():
        print("\n💡 Please check your PostgreSQL configuration:")
        print("   1. Make sure PostgreSQL service is running")
        print("   2. Check if user 'postgres' has the right permissions")
        print("   3. Verify your password")
        return
    
    print()
    
    # Setup database
    if not setup_database():
        print("\n❌ Database setup failed. Please check the errors above.")
        return
    
    print("\n🎉 Database setup completed successfully!")
    print("You can now start the backend server.")

if __name__ == "__main__":
    main()



