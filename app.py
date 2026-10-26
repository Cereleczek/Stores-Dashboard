import streamlit as st

import chat
import processing

st.set_page_config(page_title="Bookstore Dashboard", layout="wide")


@st.cache_resource
def load_data():
    data = {store: processing.load_store(store) for store in processing.STORES}
    db = chat.create_database(data)
    return data, db


data, db = load_data()

store = st.sidebar.radio("Store", processing.STORES)
orders, users, books = data[store]
metrics = processing.get_metrics(orders, users, books)

st.title(f"Bookstore Dashboard – {store}")

revenue_tab, users_tab, authors_tab = st.tabs(["Revenue", "Users", "Authors"])

with revenue_tab:
    left, right = st.columns([1, 2])
    with left:
        st.subheader("Top 5 days by revenue")
        top_days = metrics["top_days"].reset_index()
        top_days.columns = ["Date", "Revenue"]
        top_days["Date"] = top_days["Date"].astype(str)  # YYYY-MM-DD
        top_days["Revenue"] = top_days["Revenue"].map("${:,.2f}".format)
        st.dataframe(top_days, hide_index=True)
    with right:
        st.subheader("Daily revenue (USD)")
        st.line_chart(metrics["daily_revenue"])

with users_tab:
    col1, col2 = st.columns(2)
    col1.metric("Unique users", metrics["unique_users"], border=True)
    col2.metric("Best buyer – total spent", f"${metrics['best_buyer_spent']:,.2f}", border=True)
    st.subheader("Best buyer (all user ids)")
    st.code(str(metrics["best_buyer_ids"]))

with authors_tab:
    col1, col2 = st.columns(2)
    col1.metric("Unique sets of authors", metrics["author_sets"], border=True)
    col2.metric("Books sold by the most popular author(s)", metrics["popular_authors_sold"], border=True)
    st.subheader("Most popular author(s)")
    for author in metrics["popular_authors"]:
        st.info(author)

st.divider()
st.subheader("Ask a question about the data")
if "messages" not in st.session_state:
    st.session_state.messages = []

question = st.chat_input("e.g. Which genre sold the most books in STORE2?")
if question:
    st.session_state.messages.append({"role": "user", "content": question})
    with st.spinner("Thinking..."):
        try:
            answer = chat.ask(st.session_state.messages, store, db)
        except Exception as error:
            answer = f"Error: {error}"
    st.session_state.messages.append({"role": "assistant", "content": answer})

for message in st.session_state.messages:
    st.chat_message(message["role"]).write(message["content"])
