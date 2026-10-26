import re

import networkx as nx
import pandas as pd
import yaml
from dateutil import parser

STORES = ["STORE1", "STORE2", "STORE3", "STORE4", "STORE5"]
EUR_TO_USD = 1.2


def parse_price(text):

    numbers = re.findall(r"\d+", text)
    price = float(".".join(numbers))
    if "€" in text or "EUR" in text:
        price = price * EUR_TO_USD
    return round(price, 2)


def parse_timestamp(text):
    text = text.replace("A.M.", "AM").replace("P.M.", "PM").replace(";", " ").replace(",", " ")
    day_first = re.search(r"\d+\.\d+\.\d{4}", text) is not None
    return parser.parse(text, dayfirst=day_first)


def load_orders(store):
    orders = pd.read_parquet(f"data/{store}/orders.parquet").drop_duplicates()
    orders["unit_price"] = orders["unit_price"].map(parse_price)
    orders["paid_price"] = (orders["quantity"] * orders["unit_price"]).round(2)
    orders["timestamp"] = pd.to_datetime(orders["timestamp"].map(parse_timestamp))
    orders["date"] = orders["timestamp"].dt.date
    orders["shipping"] = orders["shipping"].str.strip().replace(["", "NULL", "None"], pd.NA)
    return orders


def load_users(store):
    users = pd.read_csv(f"data/{store}/users.csv").drop_duplicates()
    users["name"] = users["name"].str.strip()
    users["address"] = users["address"].str.strip().replace("", pd.NA)
    users["phone"] = users["phone"].str.replace(r"\D", "", regex=True)
    users["email"] = users["email"].str.strip().str.lower()
    return users


def load_books(store):
    with open(f"data/{store}/books.yaml") as file:
        books = pd.DataFrame(yaml.safe_load(file))
    books.columns = [column.lstrip(":") for column in books.columns]

    books["author"] = books["author"].map(lambda text: ", ".join(sorted({a.strip() for a in text.split(",")})))
    books["year"] = pd.to_numeric(books["year"], errors="coerce")
    books["year"] = books["year"].where(books["year"] > 0)
    return books.drop_duplicates(subset="id")


def add_real_user_id(users):
    fields = ["name", "address", "phone", "email"]
    graph = nx.Graph()
    graph.add_nodes_from(users["id"])
    for skipped_field in fields:
        other_fields = [field for field in fields if field != skipped_field]
        for _, group in users.dropna(subset=other_fields).groupby(other_fields):
            nx.add_path(graph, group["id"])

    real_id = {}
    for group in nx.connected_components(graph):
        for user_id in group:
            real_id[user_id] = min(group)
    users["real_user_id"] = users["id"].map(real_id)
    return users


def load_store(store):
    orders = load_orders(store)
    users = add_real_user_id(load_users(store))
    books = load_books(store)
    orders = orders.merge(users[["id", "real_user_id"]].rename(columns={"id": "user_id"}), on="user_id")
    return orders, users, books


def get_metrics(orders, users, books):
    daily_revenue = orders.groupby("date")["paid_price"].sum().round(2)

    sold_by_author = orders.merge(books, left_on="book_id", right_on="id").groupby("author")["quantity"].sum()

    spent_by_user = orders.groupby("real_user_id")["paid_price"].sum()
    best_buyer = spent_by_user.idxmax()

    return {
        "daily_revenue": daily_revenue,
        "top_days": daily_revenue.sort_values(ascending=False).head(5),
        "unique_users": users["real_user_id"].nunique(),
        "author_sets": books["author"].nunique(),
        "popular_authors": sold_by_author[sold_by_author == sold_by_author.max()].index.tolist(),
        "popular_authors_sold": sold_by_author.max(),
        "best_buyer_ids": sorted(users.loc[users["real_user_id"] == best_buyer, "id"].tolist()),
        "best_buyer_spent": round(spent_by_user.max(), 2),
    }
