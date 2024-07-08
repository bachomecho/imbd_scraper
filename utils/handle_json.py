import sqlite3
import json, os
from utils.utils import log
from datetime import datetime
from pathlib import Path

def view_current_state(cur: sqlite3.Cursor, keys: list[str]):
    exec = cur.execute('SELECT * FROM movies')
    current_db_state = exec.fetchall()
    log(current_db_state)
    data_integrity_check = input('Do you want to update current database state using json? [y/n]')
    if data_integrity_check == 'y':
        json_movies = [dict(zip(keys,list(movie[1:])))for movie in current_db_state]
        with open(f"db_dump_{str(datetime.today().date()).replace('-', '_')}.json", 'w') as out:
            json.dump(json_movies, out)

def insert_json_into_db(con: sqlite3.Connection, cur: sqlite3.Cursor, json_file: Path):
    with open(json_file, 'r') as movies:
        data = json.load(movies)
    print('data: ', type(data[0]))
    keys = list(dict(data[0]).keys())
    log(keys)
    cur.execute(f"PRAGMA table_info(movies);") # extracting column headers from table in db
    columns_info = cur.fetchall()
    db_column_headers = [info[1] for info in columns_info]
    if 'id' in db_column_headers:
        db_column_headers.remove('id')
    log(db_column_headers)

    new_cur = None
    if db_column_headers != keys:
        create_new_db = input('The column headers of the json file and database diverge. Do you want to create a new database with the columns that are present in the json? [y/n]')
        if create_new_db == 'y':
            new_path = input('Please provide a path for the new database: ')
            is_file_name = False if '/' in new_path or '\\' in new_path else True
            if new_path:
                if is_file_name: new_con = sqlite3.connect(new_path)
                else:
                    if os.path.isabs(new_path): new_con = sqlite3.connect(new_path)
                    else: print('[-] Invalid path. Either no path was provided or the given path is not absolute.')
            new_cur = new_con.cursor()
    insert_query = f"""
        INSERT OR IGNORE INTO movies (
            {",".join(keys)}
        ) VALUES ({"".join([f':{name},' for name in keys]).strip(',')})
        """

    if not new_cur:
        cur.executemany(insert_query, data)
    else:
        new_cur.executemany(insert_query, data)
    con.commit()
    con.close()
    print('[+] Json successfully migrated into db.')
