import sqlite3
import json, os

def output_current_state_json(cur: sqlite3.Cursor, keys: list[str], db_name: str):
    exec = cur.execute('SELECT * FROM movies')
    current_db_state = exec.fetchall()
    json_movies = [dict(zip(keys,list(movie[1:])))for movie in current_db_state]

    dump_name = f"db_dump_{os.path.basename(db_name).strip('.db')}.json"
    with open(dump_name, 'w') as out:
        json.dump(json_movies, out)
        print(f'[log] Current state of the database has been dumped to {dump_name}.')


def insert_json_into_db(json_file: str):
    database_path = 'REVISED_' + os.path.basename(json_file).strip('.json') + '.db'
    con = sqlite3.connect(database_path)
    if con: print(f'[log] Connection to {database_path} has been established.')
    else: raise ConnectionRefusedError(f'Connection to {database_path} could not be established.')
    cur = con.cursor()

    create_table_query = """
    CREATE TABLE IF NOT EXISTS movies (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        imdb_id TEXT UNIQUE,
        title TEXT,
        thumbnail_name TEXT,
        video_id TEXT,
        multi_part INTEGER,
        duration INTEGER,
        release_year INTEGER,
        genre TEXT,
        director TEXT,
        plot TEXT
    )
    """
    cur.execute(create_table_query)
    with open(json_file, 'r') as movies:
        data = json.load(movies)
    keys = list(dict(data[0]).keys())
    insert_query = f"""
        INSERT OR IGNORE INTO movies (
            {",".join(keys)}
        ) VALUES ({"".join([f':{name},' for name in keys]).strip(',')})
        """

    cur.executemany(insert_query, data)
    con.commit()
    del cur; del con
