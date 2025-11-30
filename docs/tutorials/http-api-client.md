# Tutorial: Your First API Client

Learn to use the API Client in 15 minutes.

## What You'll Build

A simple client that fetches user data and creates resources via REST API.

## Prerequisites

- Python 3.8+
- Basic Python knowledge

## Step 1: Your First Request

Start simple - fetch data from an API:

```python
from api_client import APIClient

# Create a client
client = APIClient("https://jsonplaceholder.typicode.com")

# Make a GET request
response = client.get("/users/1")

# Get the data
user = response.json()
print(f"User: {user['name']}")
print(f"Email: {user['email']}")
```

**Output:**
```
User: Leanne Graham
Email: Sincere@april.biz
```

That's it! You've made your first API request.

## Step 2: Working with JSON

Most APIs return JSON data. The client makes this easy:

```python
# Fetch a post
response = client.get("/posts/1")

# The .json() method parses the response
post = response.json()

print(f"Title: {post['title']}")
print(f"Body: {post['body'][:50]}...")  # First 50 chars
```

## Step 3: Creating Resources

Use POST to create new resources:

```python
# Create a new post
new_post = {
    "title": "My First Post",
    "body": "This is the content of my post.",
    "userId": 1
}

response = client.post("/posts", json_data=new_post)

# Check it was created (201 status)
if response.status_code == 201:
    created = response.json()
    print(f"Created post with ID: {created['id']}")
```

## Step 4: Error Handling

APIs can fail. Handle errors gracefully:

```python
from api_client import HTTPError

try:
    # Try to get a non-existent user
    response = client.get("/users/999999")
    user = response.json()
except HTTPError as e:
    print(f"Error {e.status_code}: User not found")
```

## Step 5: Using Authentication

Many APIs require authentication:

```python
# Create client with API key
client = APIClient(
    "https://api.example.com",
    api_key="your-secret-key"
)

# The API key is automatically added to requests
response = client.get("/protected/data")
```

## Step 6: Updating Resources

Use PUT to update existing resources:

```python
# Update a post
updates = {
    "id": 1,
    "title": "Updated Title",
    "body": "Updated content",
    "userId": 1
}

response = client.put("/posts/1", json_data=updates)

if response.ok:  # True for 2xx status codes
    print("Post updated successfully")
```

## Step 7: Deleting Resources

Use DELETE to remove resources:

```python
response = client.delete("/posts/1")

if response.ok:
    print("Post deleted")
```

## Complete Example: TODO Client

Let's build a simple TODO client:

```python
from api_client import APIClient, HTTPError

class TodoClient:
    """Simple client for TODO API."""

    def __init__(self, base_url):
        self.client = APIClient(base_url)

    def list_todos(self, user_id=None):
        """Get todos, optionally filtered by user."""
        params = {"userId": user_id} if user_id else {}
        response = self.client.get("/todos", params=params)
        return response.json()

    def create_todo(self, title, user_id, completed=False):
        """Create a new todo."""
        todo_data = {
            "title": title,
            "userId": user_id,
            "completed": completed
        }
        response = self.client.post("/todos", json_data=todo_data)
        return response.json()

    def mark_complete(self, todo_id):
        """Mark a todo as completed."""
        response = self.client.patch(
            f"/todos/{todo_id}",
            json_data={"completed": True}
        )
        return response.ok

# Use the client
todos = TodoClient("https://jsonplaceholder.typicode.com")

# List todos for user 1
user_todos = todos.list_todos(user_id=1)
print(f"User 1 has {len(user_todos)} todos")

# Create a new todo
new_todo = todos.create_todo(
    title="Learn API Client",
    user_id=1
)
print(f"Created: {new_todo['title']}")

# Mark it complete
if todos.mark_complete(new_todo['id']):
    print("Marked as complete!")
```

## Key Concepts

### 1. Simple by Default

```python
# Simplest possible usage
client = APIClient("https://api.example.com")
data = client.get("/endpoint").json()
```

### 2. Only Two Exceptions

```python
try:
    response = client.get("/data")
except HTTPError as e:
    # HTTP errors (4xx, 5xx)
    print(f"HTTP {e.status_code}")
except APIError as e:
    # Network errors, timeouts
    print(f"Request failed: {e}")
```

### 3. Automatic Retries

The client automatically retries 5xx errors with exponential backoff. You don't need to implement retry logic.

### 4. Clear Configuration

```python
from api_client import ClientConfig

config = ClientConfig(
    base_url="https://api.example.com",
    api_key="secret",
    timeout=60,
    max_retries=5
)
client = APIClient(config=config)
```

## What You've Learned

✅ Making GET, POST, PUT, DELETE requests
✅ Working with JSON responses
✅ Handling errors with HTTPError
✅ Using authentication (API key or bearer token)
✅ Building a simple API client class

## Next Steps

- [How-To Guide](../howto/http-api-client.md) - Common patterns and tasks
- [API Reference](../reference/http-api-client.md) - Complete API documentation

## Tips

1. **Start simple** - Use the basic constructor first
2. **Check response.ok** - Simple way to check for success
3. **Use .json()** - Automatically parses JSON responses
4. **Let it retry** - Don't implement your own retry logic
5. **Two exceptions** - HTTPError and APIError cover everything

Happy coding!