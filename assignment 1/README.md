# BookStore API - SENG 468 Assignment 1

A simple e-commerce REST API with intentional performance issues for learning performance measurement and profiling.

## Overview

This is a Python Flask application that provides a REST API for an online bookstore. The application has several **intentional performance issues** that you will need to discover through systematic profiling and load testing.

## Technology Stack

- **Backend:** Python 3.10 with Flask
- **Database:** PostgreSQL 15
- **ORM:** SQLAlchemy
- **Deployment:** Docker Compose

## Architecture

```
┌─────────┐      ┌──────────────┐      ┌────────────┐
│ Client  │─────▶│  Flask App   │─────▶│ PostgreSQL │
│ (wrk)   │      │  (Port 5000) │      │ (Port 5432)│
└─────────┘      └──────────────┘      └────────────┘
```

## Prerequisites

- Docker and Docker Compose
- curl (for testing)
- Load testing tool: wrk, Apache Bench, or Locust

## Quick Start

### 1. Clone the Repository
```bash
git clone https://github.com/uvic-seng468/assignment1-bookstore.git
cd assignment1-bookstore
```

### 2. Start the Application
```bash
docker compose up -d
```

### 3. Wait for Services to Start
```bash
sleep 15
```

### 4. Load Sample Data
```bash
docker compose exec app python scripts/load_data.py
```

This generates:
- **10,000 books** with titles, authors, prices, and descriptions
- **1,000 users** with unique usernames and emails
- **5,000 reviews** with ratings and comments

### 5. Test the API

**Quick test with automated script:**
```bash
chmod +x test_endpoints.sh
./test_endpoints.sh
```

**Or test manually:**
```bash
# Check health
curl http://localhost:5000/health

# List books
curl http://localhost:5000/api/books | jq '.total'
# Should return: 10000
```

---

## Windows WSL2 Users - Troubleshooting

If you get **"connection timeout"** or **"could not translate host name"** errors when loading data:

**Edit `docker-compose.yml` line 25:**

**Change FROM:**
```yaml
DATABASE_URL: postgresql://bookstore:password@db:5432/bookstore
```

**Change TO:**
```yaml
DATABASE_URL: postgresql://bookstore:password@172.18.0.1:5432/bookstore
```

Then restart:
```bash
docker compose restart app
sleep 5
docker compose exec app python scripts/load_data.py
```

---

## API Endpoints

### Books

**List all books (paginated)**
```bash
GET /api/books?page=1&per_page=20

curl http://localhost:5000/api/books?page=1&per_page=20
```

**Get single book**
```bash
GET /api/books/:id

curl http://localhost:5000/api/books/1
```

**Create book**
```bash
POST /api/books

curl -X POST http://localhost:5000/api/books \
  -H "Content-Type: application/json" \
  -d '{
    "title": "The Great Book",
    "author": "John Doe",
    "price": 29.99,
    "stock": 50,
    "category": "Fiction"
  }'
```

### Search

**Search books by title or author**
```bash
GET /api/search?q=query

curl http://localhost:5000/api/search?q=great
```

### Recommendations

**Get personalized recommendations**
```bash
GET /api/recommendations?user_id=1

curl http://localhost:5000/api/recommendations?user_id=1
```

### Cart

**Add to cart**
```bash
POST /api/cart/add

curl -X POST http://localhost:5000/api/cart/add \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 1,
    "book_id": 5,
    "quantity": 2
  }'
```

**View cart**
```bash
GET /api/cart?user_id=1

curl http://localhost:5000/api/cart?user_id=1
```

### Checkout

**Process order**
```bash
POST /api/checkout

curl -X POST http://localhost:5000/api/checkout \
  -H "Content-Type: application/json" \
  -d '{"user_id": 1}'
```

## Load Testing

### Using wrk

**Baseline test** (100 concurrent users, 60 seconds)
```bash
wrk -t4 -c100 -d60s http://localhost:5000/api/books
```

**Test search endpoint**
```bash
wrk -t4 -c100 -d60s "http://localhost:5000/api/search?q=great"
```

**Test recommendations endpoint**
```bash
wrk -t4 -c50 -d60s http://localhost:5000/api/recommendations?user_id=1
```

### Using Apache Bench

```bash
ab -n 1000 -c 50 http://localhost:5000/api/books
```

### Using Locust

Create `locustfile.py`:
```python
from locust import HttpUser, task, between

class BookStoreUser(HttpUser):
    wait_time = between(1, 3)
    
    @task(3)
    def list_books(self):
        self.client.get("/api/books?page=1")
    
    @task(2)
    def search_books(self):
        self.client.get("/api/search?q=book")
    
    @task(1)
    def get_recommendations(self):
        self.client.get("/api/recommendations?user_id=1")
```

Run:
```bash
locust -f locustfile.py --host=http://localhost:5000
```

## Profiling

### CPU Profiling with cProfile

```bash
# Profile the application
docker compose exec app python -m cProfile -o profile.stats app.py

# Analyze results
docker compose exec app python -c "
import pstats
p = pstats.Stats('profile.stats')
p.sort_stats('cumulative').print_stats(20)
"
```

### Memory Profiling

Add `@profile` decorator to functions in `app.py`, then:

```bash
docker compose exec app python -m memory_profiler app.py
```

### Database Query Logging

View PostgreSQL slow query logs:

```bash
docker compose logs db | grep "duration"
```

### SQLAlchemy Query Logging

Add to `app.py`:
```python
import logging
logging.basicConfig()
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
```

## Known Performance Issues

The application has several **intentional** performance problems for you to discover:

1. **N+1 Query Problems**
   - Book listing fetches reviews separately for each book
   - Cart viewing fetches book details one by one
   - Search results calculate ratings with separate queries

2. **Missing Database Indexes**
   - No index on `books.title` (used in search)
   - No index on `books.author` (used in search)
   - Full table scans on search queries

3. **Inefficient Algorithms**
   - Recommendation engine uses CPU-intensive scoring
   - Wasteful loop iterations (100 iterations per book!)
   - In-memory sorting of all books

4. **Memory Leak**
   - Recommendation cache grows unbounded
   - New cache entry every minute
   - Never cleaned up

5. **No Caching**
   - No Redis cache configured
   - No HTTP caching headers
   - Every request hits database

6. **Other Issues**
   - Synchronous I/O (no async)
   - No connection pooling optimization
   - No query result caching

## Your Task

Use load testing and profiling to:

1. **Measure** baseline performance
2. **Identify** bottlenecks systematically
3. **Profile** to find exact locations in code
4. **Recommend** specific fixes with expected impact

**Don't guess!** Use profiling data to prove where the problems are.

## Troubleshooting

### Port Already in Use
```bash
# Stop existing containers
docker compose down

# Or change ports in docker-compose.yml
ports:
  - "5001:5000"  # Use port 5001 instead
  - "5433:5432"  # Use port 5433 instead
```

### Database Connection Issues (WSL2)

If you see `connection timeout` errors:

1. Edit `docker-compose.yml` line 25
2. Change `@db:5432` to `@172.18.0.1:5432`
3. Restart: `docker compose restart app`

### Data Loading Fails

```bash
# Clean restart
docker compose down -v
docker compose up -d
sleep 15
docker compose exec app python scripts/load_data.py
```

### View Logs

```bash
# Application logs
docker compose logs -f app

# Database logs
docker compose logs -f db
```

### Clean Restart

```bash
# Remove all containers and data
docker compose down -v

# Start fresh
docker compose up -d
sleep 15
docker compose exec app python scripts/load_data.py
```

## Stopping the Application

```bash
# Stop containers (keeps data)
docker compose down

# Stop and remove all data
docker compose down -v
```

## Tips for Success

1. **Warm up the system** - Run 5-10 minutes of load before measuring
2. **Test from separate machine** - Don't run load tests on same server as app
3. **Monitor resources** - Use `docker stats` to watch CPU, memory, disk I/O
4. **Profile under load** - Idle profiling won't show real bottlenecks
5. **Read the code** - Look for obvious issues in `app/app.py`
6. **Verify with data** - Use profiling to prove where problems are

## Database Schema

```sql
-- books table
CREATE TABLE books (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    author VARCHAR(255) NOT NULL,
    isbn VARCHAR(13) UNIQUE,
    price NUMERIC(10,2) NOT NULL,
    description TEXT,
    stock INTEGER DEFAULT 0,
    category VARCHAR(100),
    published_year INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);
-- NOTE: No indexes on title/author!

-- users table
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(80) UNIQUE NOT NULL,
    email VARCHAR(120) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- reviews table
CREATE TABLE reviews (
    id SERIAL PRIMARY KEY,
    book_id INTEGER REFERENCES books(id),
    user_id INTEGER REFERENCES users(id),
    rating INTEGER NOT NULL CHECK (rating BETWEEN 1 AND 5),
    comment TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- cart_items table
CREATE TABLE cart_items (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    book_id INTEGER REFERENCES books(id),
    quantity INTEGER DEFAULT 1,
    added_at TIMESTAMP DEFAULT NOW()
);

-- orders table
CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    total NUMERIC(10,2) NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT NOW()
);
```

## Project Structure

```
bookstore-api/
├── app/
│   └── app.py              # Main Flask application
├── scripts/
│   └── load_data.py        # Data generation script
├── docker-compose.yml      # Docker orchestration
├── Dockerfile              # Container definition
├── requirements.txt        # Python dependencies
├── test_endpoints.sh       # Automated API testing script
└── README.md              # This file
```

## Resources

- [Flask Documentation](https://flask.palletsprojects.com/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [wrk Load Testing Tool](https://github.com/wg/wrk)
- [Python cProfile](https://docs.python.org/3/library/profile.html)
- [SENG 468 Course Materials](https://bright.uvic.ca/d2l/home/467415)

## Support

For assignment questions:
- Office hours: Tuesday/Thursday 2:00-4:00 PM
- Discussion forum on Brightspace

## License

This code is provided for educational purposes only as part of SENG 468 and is made with the help of AI!

---

**Good luck!**
