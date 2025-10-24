Alembic setup for the backend

Quick start:

1. Install requirements (in your backend venv):

   pip install -r requirements.txt

2. Run autogenerate to create initial migration:

   alembic revision --autogenerate -m "initial"

3. Apply migrations:

   alembic upgrade head

Notes:
- The Alembic env.py imports `Base` from `src.database` and uses the DATABASE_URL environment variable when present.
- For SQLite, Alembic autogenerate may not detect JSON columns or certain SQLite-specific types; adjust the generated revision manually if needed.
