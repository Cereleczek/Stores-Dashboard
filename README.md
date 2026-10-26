# Bookstore Dashboard (Task 4)

Dashboard for the data of 5 bookstores with an AI chat.

- `processing.py` - loads and cleans the data (prices -> USD, €1 = $1.2, timestamps, missing values, duplicates),
  finds real unique users and computes the metrics
- `app.py` - the dashboard: Revenue, Users and Authors tabs + a chat area below them
- `chat.py` - the chat: Gemini (`gemini-3.8-flash`) gets a `run_sql` tool and answers by running SQL queries
  on the cleaned tables (SQLite), so all numbers come from the data, not from the model

**Real unique users:** a person can register again with one changed field (name, address, phone or email),
so records with the same values in 3 of the 4 fields are the same person (connected groups in a graph).

## Results

| Store  | Top 5 days by revenue                                      | Unique users | Author sets | Most popular author(s)                   | Best buyer            |
|--------|------------------------------------------------------------|--------------|-------------|------------------------------------------|-----------------------|
| STORE1 | 2025-08-20, 2025-09-22, 2026-01-15, 2025-09-03, 2025-10-17 | 3221         | 324         | Darron Ernser, Miss Lorina Kertzmann     | [48403, 48904, 50056] |
| STORE2 | 2025-11-16, 2025-12-12, 2025-12-10, 2025-09-19, 2025-11-19 | 3166         | 281         | Kenneth Hamill, Marcus McKenzie          | [51014]               |
| STORE3 | 2025-10-09, 2025-09-21, 2025-09-04, 2025-09-30, 2025-09-01 | 2955         | 307         | Loreta Metz                              | [52881, 53869, 54846] |
| STORE4 | 2025-11-24, 2025-11-17, 2025-11-28, 2025-11-13, 2025-09-21 | 2850         | 299         | Emil Rempel, Heriberto Kutch, Merle Rice | [53347, 54809]        |
| STORE5 | 2025-10-20, 2025-11-28, 2025-09-27, 2025-10-17, 2025-12-05 | 2987         | 311         | Dulcie Bode                              | [52895, 53969]        |


## Run

```bash
pip install -r requirements.txt
export GEMINI_API_KEY=your-key
streamlit run app.py
```
