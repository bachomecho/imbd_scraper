import inspect, os
import sqlite3
import requests
from bs4 import BeautifulSoup
from typing import Literal
from datetime import datetime
from pathlib import Path


def log(var):
    frame = inspect.currentframe()
    try:
        local_vars = frame.f_back.f_locals
        var_names = [name for name, value in local_vars.items() if value is var]
        if var_names:
            var_name = var_names[0]
            print(f"{var_name} = {var}")
        else:
            print(f"Variable not found in the local scope.")
    finally:
        del frame


def titles_currently_present(cur: sqlite3.Cursor) -> list[str]:
    res = cur.execute('SELECT title FROM movies')
    movie_titles = res.fetchall()
    return [title[0] for title in movie_titles]


def get_playlist(url: str, user_agent: str):
    res = requests.get(url, headers={'User-Agent': user_agent})
    if res.status_code == 200:
        return res.text
    else:
        raise Exception(f'Failed to fetch the page with following status code: {res.status_code}')


def parse_playlist_for_ids(playlist_html: str):
    soup = BeautifulSoup(playlist_html, 'html.parser')
    links_with_ids = soup.find_all('a', class_ = 'ipc-title-link-wrapper', href=True)
    return [link['href'].split('/')[2].lstrip('tt') for link in links_with_ids]


def file_prompt(file_type: Literal['json', 'db']) -> str:
    assert file_type == 'db' or file_type == 'json', 'File type is neither .db nor .json'
    files = None
    if file_type == 'db':
        files = [
            os.path.join(root, file) for root, _, files in os.walk(os.curdir) for file in files
            if file.endswith('.db')
            and 'movies' in file
            and os.path.exists(os.path.join(root, file))
        ]
    else:
        files = [
            os.path.join(root, file) for root, _, files in os.walk(os.curdir) for file in files
            if file.endswith('.json')
            and 'movies' in file
            and 'db_dump' in file
            and os.path.exists(os.path.join(root, file))
        ]

    while True:
        for idx, file in enumerate(files):
            print(f"\t[{idx + 1}] {Path(file).as_posix()}")
        file_path_idx = input("Please choose which database file to operate on: \n")

        if not file_path_idx.isnumeric() or len(files) < int(file_path_idx) or int(file_path_idx) < 1:
            print("This option is not available. Please choose an option from the list.\n")
            continue
        else:
            break
    return os.path.abspath(files[int(file_path_idx) - 1])


def file_input_prompt(
        operational_argument:Literal["current_state", "fill_missing", "integrate_json"]=None,
        parsing_args=False
    ) -> str: # TODO: pass in a list of db and json files, differentiate based on code logic
    if parsing_args: assert not operational_argument, "Cannot provide ops argument when parsing data."
    if operational_argument: assert not parsing_args, "Cannot provide parsing argument when using operational argument."

    if (parsing_args or operational_argument == 'current_state'):
        is_current_state_arg_provided = True if operational_argument else False
        # TODO: os.walk current dir and find folders containing db and json files
        dbs = [
            file
            for file in os.listdir()
            if file.endswith(".db") and os.path.isfile(file)
        ]

        if dbs:
            print("\n*** DATABASE FILES AVAILABLE IN THE CURRENT DIRECTORY ***\n")
            if not is_current_state_arg_provided:
                print("\t[0] Create a new database.")

            for idx, file in enumerate(dbs):
                print(f"\t[{idx+1}] {file}")
            database_select = input("Select one of the following database options: \n")
            database_select = int(database_select)
            while not isinstance(database_select, int) and database_select < len(dbs) and database_select >= 0:
                print("Please input the number of the database option you want to use.")
                database_select = input("Select one of following databases present in the current directory: \n")
            if not is_current_state_arg_provided and database_select == 0:
                return (f"movies_{str(datetime.today().date()).replace('-', '_')}.db")
            else:
                return dbs[database_select - 1]
        else:
            if not is_current_state_arg_provided:
                return f"movies_{str(datetime.today().date()).replace('-', '_')}.db" # creates a default database file to operate on
            else:
                raise FileNotFoundError("There are no database files available in the current directory.")
    elif operational_argument == 'fill_missing' or operational_argument == 'integrate_json':
        json_files = [
            file
            for file in os.listdir()
            if file.endswith(".json") and os.path.isfile(file)
        ]

        if json_files:
            print("\n*** JSON FILES AVAILABLE IN THE CURRENT DIRECTORY ***\n")
            for idx, file in enumerate(json_files):
                print(f"\t[{idx+1}] {file}")
            json_files_select = input("Select one of following json files present in the current directory: \n")
            json_files_select = int(json_files_select)
            while not isinstance(json_files_select, int) and json_files_select < len(json_files) and json_files_select >= 0:
                print("Please input the number of the json file  you want to use.")
                json_files_select = input("Select one of following json files present in the current directory: \n")
            return json_files[json_files_select - 1]
        else:
            raise FileNotFoundError("There are no json files available in the current directory that can be integrated into a database.")

import json
def bulk_update_with_file(file: str, indicator_update_field: str, field_to_update: str) -> str:
    print('exists: ', Path(file).exists())

    with open(file, 'r') as input:
        data = json.load(input)
    when_statements = [f"WHEN '{key}' THEN '{value}'" for key, value in data.items()]
    log(when_statements)
    update_query = f"""
        UPDATE  movies
        SET     {field_to_update} = CASE {indicator_update_field} {chr(10)}{f'{chr(10)}'.join(when_statements)}
        END
        WHERE   title IN ({','.join([f"'{key}'" for key in data.keys()])})
    """
    return update_query