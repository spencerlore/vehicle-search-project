1. Start API Server
uvicorn app.main:app --reload --port 8000

2. Open in browser
http://127.0.0.1:8000/docs

3. Send request to test functionality through browser. Example:

[
  {
    "length": 10,
    "quantity": 1
  },
  {
    "length": 20,
    "quantity": 2
  },
  {
    "length": 25,
    "quantity": 1
  }
]

