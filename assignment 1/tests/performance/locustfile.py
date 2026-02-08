from locust import HttpUser, task, between, LoadTestShape
import random

class BookstoreUser(HttpUser):
    wait_time = between(1, 3)
    user_id = 1

    def on_start(self):
        self.user_id = random.randint(1, 100)

    @task(3)
    def browse_books(self):
        self.client.get("/api/books")

    @task(3)
    def get_book(self):
        # Assuming we have some books in DB, IDs 1-10 widely used
        book_id = random.randint(1, 20) 
        self.client.get(f"/api/books/{book_id}")

    @task(2)
    def search_books(self):
        queries = ["Science", "Fiction", "History", "Cook"]
        q = random.choice(queries)
        self.client.get(f"/api/search?q={q}")

    @task(2)
    def get_recommendations(self):
        self.client.get("/api/recommendations")

    @task(1)
    def add_to_cart(self):
        book_id = random.randint(1, 20)
        self.client.post("/api/cart/add", json={
            "user_id": self.user_id,
            "book_id": book_id,
            "quantity": 1
        })

    @task(1)
    def checkout(self):
        with self.client.post("/api/checkout", json={
            "user_id": self.user_id
        }, catch_response=True) as response:
            if response.status_code == 400 and "Cart is empty" in response.text:
                response.success()
            elif response.status_code != 200:
                response.failure(response.text)

class StepLoadShape(LoadTestShape):
    """
    Step load shape
    Start at 100 users
    Add 50 users every 2 minutes
    """
    step_time = 120 # 2 minutes
    step_users = 50
    spawn_rate = 10 
    initial_users = 100

    def tick(self):
        run_time = self.get_run_time()
        
        # Check for time limit (e.g., stopping after a certain duration)
        # You can set this via environment variable or hardcode
        # For this assignment, let's stop after 30 minutes (1800s) to be safe
        if run_time > 1800:
            return None

        # Calculate current step based on time
        current_step = int(run_time / self.step_time)
        
        # Calculate target user count
        # Initial 100 + (step * 50)
        user_count = self.initial_users + (current_step * self.step_users)
        
        return (user_count, self.spawn_rate)
