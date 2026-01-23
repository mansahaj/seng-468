"""
Load sample data into BookStore API database
Generates 10,000 books, 1,000 users, and sample reviews
FIXED VERSION - Guarantees unique emails, better error handling
"""
import sys
import os
import time

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db, Book, User, Review
from faker import Faker
import random

# Use timestamp as seed for uniqueness
fake = Faker()
Faker.seed(int(time.time()))

CATEGORIES = [
    'Fiction', 'Non-Fiction', 'Science Fiction', 'Fantasy', 
    'Mystery', 'Thriller', 'Romance', 'Biography',
    'History', 'Science', 'Technology', 'Business',
    'Self-Help', 'Poetry', 'Drama', 'Horror'
]

def load_users(count=1000):
    """Generate unique users - FIXED to prevent duplicates"""
    print(f"Loading {count} users...")
    users = []
    
    for i in range(count):
        # Generate unique email with index prefix to guarantee uniqueness
        email = f"user{i}@example{random.randint(1,999)}.com"
        username = f"user_{i}_{random.randint(1000,9999)}"
        
        user = User(
            username=username,
            email=email,
            created_at=fake.date_time_this_year()
        )
        users.append(user)
        
        if (i + 1) % 100 == 0:
            print(f"  Generated {i + 1} users...")
    
    try:
        db.session.bulk_save_objects(users)
        db.session.commit()
        print(f"✓ Successfully loaded {count} users")
        return users
    except Exception as e:
        print(f"✗ Error loading users: {e}")
        db.session.rollback()
        raise

def load_books(count=10000):
    """Generate sample books"""
    print(f"Loading {count} books...")
    books = []
    
    for i in range(count):
        book = Book(
            title=fake.catch_phrase() + " " + fake.word().title(),
            author=fake.name(),
            isbn=fake.isbn13().replace('-', ''),
            price=round(random.uniform(9.99, 99.99), 2),
            description=fake.text(max_nb_chars=200),
            stock=random.randint(0, 100),
            category=random.choice(CATEGORIES),
            published_year=random.randint(1950, 2024),
            created_at=fake.date_time_this_year()
        )
        books.append(book)
        
        if (i + 1) % 1000 == 0:
            print(f"  Generated {i + 1} books...")
    
    try:
        db.session.bulk_save_objects(books)
        db.session.commit()
        print(f"✓ Successfully loaded {count} books")
        return books
    except Exception as e:
        print(f"✗ Error loading books: {e}")
        db.session.rollback()
        raise

def load_reviews(count=5000):
    """Generate sample reviews"""
    print(f"Loading {count} reviews...")
    
    # Get IDs from database
    book_ids = [b.id for b in Book.query.limit(1000).all()]
    user_ids = [u.id for u in User.query.limit(500).all()]
    
    if not book_ids or not user_ids:
        print("✗ No books or users found. Load books and users first.")
        return []
    
    reviews = []
    for i in range(count):
        review = Review(
            book_id=random.choice(book_ids),
            user_id=random.choice(user_ids),
            rating=random.randint(1, 5),
            comment=fake.paragraph(nb_sentences=3),
            created_at=fake.date_time_this_year()
        )
        reviews.append(review)
        
        if (i + 1) % 500 == 0:
            print(f"  Generated {i + 1} reviews...")
    
    try:
        db.session.bulk_save_objects(reviews)
        db.session.commit()
        print(f"✓ Successfully loaded {count} reviews")
        return reviews
    except Exception as e:
        print(f"✗ Error loading reviews: {e}")
        db.session.rollback()
        raise

def main():
    print("=" * 60)
    print("BookStore API - Data Loader (FIXED VERSION)")
    print("=" * 60)
    print()
    
    with app.app_context():
        # Initialize database
        print("Initializing database...")
        try:
            db.create_all()
            print("✓ Database initialized")
            print()
        except Exception as e:
            print(f"✗ Database initialization failed: {e}")
            return
        
        # Check if data already exists
        existing_users = User.query.count()
        existing_books = Book.query.count()
        
        if existing_users > 0 or existing_books > 0:
            print(f"⚠ Database already contains data:")
            print(f"  - {existing_users} users")
            print(f"  - {existing_books} books")
            print("Clearing existing data...")
            Review.query.delete()
            Book.query.delete()
            User.query.delete()
            db.session.commit()
            print("✓ Existing data cleared")
            print()
        
        print("Loading sample data...")
        print("-" * 60)
        
        try:
            # Load data
            users = load_users(1000)
            print()
            
            books = load_books(10000)
            print()
            
            reviews = load_reviews(5000)
            print()
            
            print("=" * 60)
            print("✓ DATA LOADING COMPLETE!")
            print("=" * 60)
            print()
            print("Summary:")
            print(f"  - {len(users)} users")
            print(f"  - {len(books)} books")
            print(f"  - {len(reviews)} reviews")
            print()
            print("Test the API: curl http://localhost:5000/api/books")
            
        except Exception as e:
            print()
            print("=" * 60)
            print(f"✗ Data loading failed: {e}")
            print("=" * 60)
            sys.exit(1)

if __name__ == '__main__':
    main()
