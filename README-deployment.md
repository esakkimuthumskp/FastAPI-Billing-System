# FastAPI Billing System

Simple production-minded Billing System built with FastAPI.

Features:
- Product & Denomination models (seeded)
- Billing page to add products, provide denominations and paid amount
- Calculates subtotal, tax, total, change and denomination breakdown
- Saves purchases and shows purchase history per customer
- Generates PDF invoice and sends it via email in background

Quick start

1. Create a virtualenv and install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. Set SMTP environment variables (or see `.env.example`):

```bash
export SMTP_HOST=smtp.example.com
export SMTP_PORT=587
export SMTP_USERNAME=you@example.com
export SMTP_PASSWORD=yourpassword
export SMTP_FROM=you@example.com
```

3. Run the app:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

4. Open http://localhost:8000 in your browser.


Docker & Docker Compose (optional)

You can run the app using Docker Compose for easy setup:

```bash
docker compose up --build
```

This will build and start the app, exposing it on port 8000. The SQLite database file will be persisted in your project directory.

To stop the app:

```bash
docker compose down
```

You can also run with plain Docker:

```bash
docker build -t billing-app .
docker run -p 8000:8000 --env-file .env.example billing-app
```


Assumptions
- Uses SQLite for simplicity (file-based DB). Swap to Postgres by changing `DATABASE_URL` and engine creation.
- Uses `reportlab` to generate a simple PDF invoice.
- Email is sent using SMTP; you'll need valid SMTP credentials.
- Docker Compose maps `billing.db` to your local folder for persistence.
