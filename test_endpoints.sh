#!/bin/bash
# Quick test script to verify BookStore API endpoints

BASE_URL="http://localhost:5000"

echo "========================================="
echo "BookStore API - Quick Test Script"
echo "========================================="
echo ""

# Test health endpoint
echo "1. Testing health endpoint..."
curl -s $BASE_URL/health | jq '.'
echo ""

# Test list books
echo "2. Testing list books..."
curl -s "$BASE_URL/api/books?page=1&per_page=5" | jq '.books | length'
echo " books returned"
echo ""

# Test get single book
echo "3. Testing get single book..."
curl -s $BASE_URL/api/books/1 | jq '.title'
echo ""

# Test search
echo "4. Testing search..."
curl -s "$BASE_URL/api/search?q=book" | jq '.total'
echo " results found"
echo ""

# Test recommendations
echo "5. Testing recommendations..."
curl -s "$BASE_URL/api/recommendations?user_id=1" | jq '.recommendations | length'
echo " recommendations"
echo ""

# Test add to cart
echo "6. Testing add to cart..."
curl -s -X POST $BASE_URL/api/cart/add \
  -H "Content-Type: application/json" \
  -d '{"user_id": 1, "book_id": 1, "quantity": 2}' | jq '.message'
echo ""

# Test view cart
echo "7. Testing view cart..."
curl -s "$BASE_URL/api/cart?user_id=1" | jq '.total'
echo ""

echo "========================================="
echo "✓ All endpoints tested!"
echo "========================================="
