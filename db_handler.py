import sqlite3
import json
from pathlib import Path

def titles_currently_present(cur: sqlite3.Cursor) -> list[str]:
    res = cur.execute('SELECT title FROM movies')
    movie_titles = res.fetchall()
    return [title[0] for title in movie_titles]

def insert_into_db(cur: sqlite3.Cursor, data: dict, keys: list[str]) -> None:
    insert_query = f"""
    INSERT OR IGNORE INTO movies (
        {",".join(keys)}
    ) VALUES ({"".join(['?,' for _ in range(len(keys))]).strip(',')})
    """
    print('testing insert query: ', insert_query)

    cur.executemany(insert_query, data)

def current_db_state(cur: sqlite3.Cursor) -> list[tuple]:
    exec = cur.execute('SELECT * FROM movies')
    return exec.fetchall()

def reintegrate_json_into_sqlite(cur: sqlite3.Cursor, json_file: str):
    with open(json_file, 'r') as movies:
        data = json.load(movies)
    insert_into_db(cur, data)

def fetch_titles_from_existing_database(db_path: Path, table_name: str):
    with sqlite3.connect(db_path) as conn:
        cur = conn.cursor()
        return cur.execute(f'SELECT title from {table_name}').fetchall()
