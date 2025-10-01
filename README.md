<!-- About the project -->
## :star2: About the Project

<a>A search algorithm that allows renters to find locations to store multiple vehicles.</a>
<div align="center"> 
  <img src="assets/Screenshot1.png" alt="screenshot1" />
  <img src="assets/Screenshot2.png" alt="screenshot2" />
</div>


<!-- TechStack -->
### :space_invader: Tech Stack

  <ul>
    <li><a href="https://www.python.org/">Python</a></li>
    <li><a href="https://fastapi.tiangolo.com/">FastAPI</a></li>
    <li><a href="https://uvicorn.dev/">Uvicorn</a></li>
    <li><a href="https://docs.pydantic.dev/latest/">Pydantic</a></li>
    <li><a href="https://docs.pytest.org/en/stable/">Pytest</a></li>
  </ul>

<!-- Features -->
### :dart: Features

- Includes every possible location that could store all requested vehicles.
- Includes the chapest possible combination of listings per location.
- Includes only one result per location_id.
- Sorted by the total price in cents, ascending.

<!-- Run Locally -->
### :running: Run Locally

Clone the project

```bash
  git clone https://github.com/spencerlore/vehicle-search-project
```

Go to the project directory

```bash
  cd vehicle-search-project
```

Create a virtual environment and install dependencies

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Start the API server

```bash
python -m uvicorn app.main:app --reload --port 8000
```

Open in browser
```bash
http://127.0.0.1:8000/docs
```

Click the "try it out" button and send a request. Example:
```bash
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
```
