# Setup Guide

## Prerequisites
- Python 3.9+
- PostgreSQL
- Docker

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd cody
```

2. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
.\venv\Scripts\activate  # Windows
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Start the application:
```bash
uvicorn api.main:app --reload
```

## Docker Setup
TBD - Docker setup instructions will be added
