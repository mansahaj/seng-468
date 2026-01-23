"""
BookStore API - Flask Application with Intentional Performance Issues
For SENG 468 Assignment 1
"""
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os
import time
import random

app = Flask(__name__)

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv(
    'DATABASE_URL',
    'postgresql://bookstore:password@localhost:5432/bookstore'
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Global cache for recommendations (INTENTIONAL MEMORY LEAK)
recommendation_cache = {}

# ============================================================================
# DATABASE MODELS
# ============================================================================

class Book(db.Model):
    __tablename__ = 'books'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)  # NO INDEX - intentional!
    author = db.Column(db.String(255), nullable=False)  # NO INDEX - intentional!
    isbn = db.Column(db.String(13), unique=True)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    description = db.Column(db.Text)
    stock = db.Column(db.Integer, default=0)
    category = db.Column(db.String(100))
    published_year = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    reviews = db.relationship('Review', backref='book', lazy='dynamic')
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'author': self.author,
            'isbn': self.isbn,
            'price': float(self.price),
            'description': self.description,
            'stock': self.stock,
            'category': self.category,
            'published_year': self.published_year,
            'avg_rating': self.get_average_rating()  # N+1 QUERY!
        }
    
    def get_average_rating(self):
        """INTENTIONAL N+1 QUERY PROBLEM"""
        reviews = self.reviews.all()  # Separate query for each book!
        if not reviews:
            return 0
        return sum(r.rating for r in reviews) / len(reviews)


class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    reviews = db.relationship('Review', backref='user', lazy='dynamic')
    cart_items = db.relationship('CartItem', backref='user', lazy='dynamic')


class Review(db.Model):
    __tablename__ = 'reviews'
    
    id = db.Column(db.Integer, primary_key=True)
    book_id = db.Column(db.Integer, db.ForeignKey('books.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)  # 1-5
    comment = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class CartItem(db.Model):
    __tablename__ = 'cart_items'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey('books.id'), nullable=False)
    quantity = db.Column(db.Integer, default=1)
    added_at = db.Column(db.DateTime, default=datetime.utcnow)


class Order(db.Model):
    __tablename__ = 'orders'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    total = db.Column(db.Numeric(10, 2), nullable=False)
    status = db.Column(db.String(50), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.route('/api/books', methods=['GET'])
def get_books():
    """
    List all books with pagination
    ISSUE: N+1 query problem with avg_rating
    """
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    pagination = Book.query.paginate(page=page, per_page=per_page, error_out=False)
    
    # N+1 PROBLEM: to_dict() calls get_average_rating() for each book
    books = [book.to_dict() for book in pagination.items]
    
    return jsonify({
        'books': books,
        'total': pagination.total,
        'page': page,
        'pages': pagination.pages
    })


@app.route('/api/books/<int:book_id>', methods=['GET'])
def get_book(book_id):
    """Get single book details"""
    book = Book.query.get_or_404(book_id)
    
    # Get reviews (separate query)
    reviews = Review.query.filter_by(book_id=book_id).all()
    review_data = [{
        'user_id': r.user_id,
        'rating': r.rating,
        'comment': r.comment
    } for r in reviews]
    
    result = book.to_dict()
    result['reviews'] = review_data
    
    return jsonify(result)


@app.route('/api/books', methods=['POST'])
def create_book():
    """Create new book (admin only - no auth check for simplicity)"""
    data = request.get_json()
    
    book = Book(
        title=data['title'],
        author=data['author'],
        isbn=data.get('isbn'),
        price=data['price'],
        description=data.get('description'),
        stock=data.get('stock', 0),
        category=data.get('category'),
        published_year=data.get('published_year')
    )
    
    db.session.add(book)
    db.session.commit()
    
    return jsonify(book.to_dict()), 201


@app.route('/api/search', methods=['GET'])
def search_books():
    """
    Search books by title or author
    ISSUES:
    1. NO INDEXES on title/author columns -> slow
    2. Uses LIKE which doesn't use indexes well
    3. N+1 query problem with ratings
    """
    query = request.args.get('q', '')
    
    if not query:
        return jsonify({'books': [], 'total': 0})
    
    # INEFFICIENT QUERY - No indexes!
    books = Book.query.filter(
        db.or_(
            Book.title.ilike(f'%{query}%'),
            Book.author.ilike(f'%{query}%')
        )
    ).all()
    
    # N+1 PROBLEM
    results = [book.to_dict() for book in books]
    
    return jsonify({
        'books': results,
        'total': len(results),
        'query': query
    })


@app.route('/api/recommendations', methods=['GET'])
def get_recommendations():
    """
    Get personalized book recommendations
    ISSUES:
    1. MEMORY LEAK - cache grows unbounded
    2. CPU-INTENSIVE - inefficient algorithm
    3. NO CACHING at HTTP level
    """
    user_id = request.args.get('user_id', 1, type=int)
    
    # Check unbounded cache (MEMORY LEAK!)
    cache_key = f'rec_{user_id}_{datetime.now().minute}'  # Changes every minute
    if cache_key in recommendation_cache:
        return jsonify(recommendation_cache[cache_key])
    
    # INEFFICIENT ALGORITHM - simulate complex computation
    all_books = Book.query.all()
    
    # Simulate expensive recommendation algorithm
    recommendations = []
    for book in all_books:
        # Simulate complex scoring (CPU intensive)
        score = 0
        for _ in range(100):  # Wasteful computation!
            score += random.random() * len(book.title) * len(book.author)
        
        recommendations.append({
            'book': book.to_dict(),  # N+1 with ratings!
            'score': score
        })
    
    # Sort by score (expensive for large datasets)
    recommendations.sort(key=lambda x: x['score'], reverse=True)
    top_10 = recommendations[:10]
    
    # Store in unbounded cache (MEMORY LEAK!)
    recommendation_cache[cache_key] = {
        'recommendations': top_10,
        'generated_at': datetime.now().isoformat()
    }
    
    # Simulate some additional processing time
    time.sleep(0.1)
    
    return jsonify(recommendation_cache[cache_key])


@app.route('/api/cart/add', methods=['POST'])
def add_to_cart():
    """Add item to cart"""
    data = request.get_json()
    user_id = data.get('user_id', 1)
    book_id = data['book_id']
    quantity = data.get('quantity', 1)
    
    # Check if book exists
    book = Book.query.get_or_404(book_id)
    
    # Check if already in cart
    cart_item = CartItem.query.filter_by(
        user_id=user_id,
        book_id=book_id
    ).first()
    
    if cart_item:
        cart_item.quantity += quantity
    else:
        cart_item = CartItem(
            user_id=user_id,
            book_id=book_id,
            quantity=quantity
        )
        db.session.add(cart_item)
    
    db.session.commit()
    
    return jsonify({'message': 'Added to cart', 'quantity': cart_item.quantity})


@app.route('/api/cart', methods=['GET'])
def get_cart():
    """
    View cart contents
    ISSUE: N+1 query for book details
    """
    user_id = request.args.get('user_id', 1, type=int)
    
    cart_items = CartItem.query.filter_by(user_id=user_id).all()
    
    # N+1 PROBLEM - separate query for each book
    items = []
    total = 0
    for item in cart_items:
        book = Book.query.get(item.book_id)  # Separate query!
        item_total = float(book.price) * item.quantity
        total += item_total
        
        items.append({
            'book_id': book.id,
            'title': book.title,
            'price': float(book.price),
            'quantity': item.quantity,
            'subtotal': item_total
        })
    
    return jsonify({
        'items': items,
        'total': total
    })


@app.route('/api/checkout', methods=['POST'])
def checkout():
    """
    Process order
    ISSUE: No transaction handling, inefficient queries
    """
    data = request.get_json()
    user_id = data.get('user_id', 1)
    
    # Get cart items (N+1 problem)
    cart_items = CartItem.query.filter_by(user_id=user_id).all()
    
    if not cart_items:
        return jsonify({'error': 'Cart is empty'}), 400
    
    # Calculate total (N+1 for book prices)
    total = 0
    for item in cart_items:
        book = Book.query.get(item.book_id)
        total += float(book.price) * item.quantity
    
    # Create order
    order = Order(
        user_id=user_id,
        total=total,
        status='completed'
    )
    db.session.add(order)
    
    # Clear cart
    for item in cart_items:
        db.session.delete(item)
    
    db.session.commit()
    
    # Simulate payment processing
    time.sleep(0.2)
    
    return jsonify({
        'order_id': order.id,
        'total': float(order.total),
        'status': order.status
    })


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()})


# ============================================================================
# DATABASE INITIALIZATION
# ============================================================================

@app.cli.command()
def init_db():
    """Initialize the database"""
    db.create_all()
    print('Database initialized!')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
