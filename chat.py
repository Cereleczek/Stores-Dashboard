import sqlite3

import pandas as pd
from google import genai
from google.genai import types

SYSTEM_PROMPT = """You answer questions about the data of 5 online bookstores (STORE1 - STORE5).
You don't know the data. Use the run_sql tool to get every number, never guess or calculate it yourself.

Tables in the SQLite database (X = store number 1-5):
storeX_orders(id, user_id, real_user_id, book_id, quantity, unit_price, paid_price, timestamp, date, shipping)
  - unit_price and paid_price are in USD, paid_price = quantity * unit_price (revenue of the order)
  - date is text 'YYYY-MM-DD'
storeX_users(id, real_user_id, name, address, phone, email)
  - one person can have several user records (alias, other address, phone or email);
    real_user_id is the same for all records of one person, so unique users = COUNT(DISTINCT real_user_id)
storeX_books(id, title, author, genre, publisher, year)
  - author = all authors of the book sorted and joined with ', ' (a set of authors)

Rules:
- books sold = SUM(quantity), revenue = SUM(paid_price)
- the most popular author = author with the highest number of books sold
- the best buyer = real_user_id with the highest SUM(paid_price), show all user ids of that person
- if no store is mentioned, use {store}; always say which store the answer is about
- write money like $1,234.56 and dates like YYYY-MM-DD, answer shortly in the language of the question"""


def create_database(data):
    db = sqlite3.connect(":memory:", check_same_thread=False)
    for store, (orders, users, books) in data.items():
        orders.to_sql(f"{store.lower()}_orders", db, index=False)
        users.to_sql(f"{store.lower()}_users", db, index=False)
        books.to_sql(f"{store.lower()}_books", db, index=False)
    db.execute("PRAGMA query_only = ON")  # the model can only read the data, not change it
    return db


def ask(messages, store, db):
    def run_sql(query: str) -> str:
        """Run a SQL SELECT query on the bookstore database and return the result as CSV.

        Args:
            query: one SQLite SELECT query, e.g. SELECT COUNT(*) FROM store1_orders
        """
        if not query.strip().lower().startswith(("select", "with")):
            return "Error: only SELECT queries are allowed"
        result = pd.read_sql_query(query, db)
        return f"{len(result)} rows (max 100 shown)\n" + result.head(100).to_csv(index=False)


    contents = [
        {"role": "model" if m["role"] == "assistant" else "user", "parts": [{"text": m["content"]}]}
        for m in messages
    ]

    client = genai.Client()
    response = client.models.generate_content(
        model="gemini-3.5-flash-lite",
        contents=contents,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT.format(store=store),
            tools=[run_sql],
        ),
    )
    return response.text or "Sorry, I can't answer this question."
