import inspect, os
import sqlite3
import requests
from bs4 import BeautifulSoup
from typing import Literal
from datetime import datetime

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


def file_input_prompt(
        operational_argument:Literal["current_state", "fill_missing", "integrate_json"]=None,
        parsing_args=False,
        normal_db_inquiry=False,
        normal_json_inquiry=False
    ) -> str:
    if parsing_args: assert not operational_argument, "Cannot provide ops argument when parsing data."
    if operational_argument: assert not parsing_args, "Cannot provide parsing argument when using operational argument."

    if (parsing_args or normal_db_inquiry or operational_argument == 'current_state'):
        is_current_state_arg_provided = True if operational_argument else False
        dbs = [
            file
            for file in os.listdir()
            if file.endswith(".db") and os.path.isfile(file)
        ]

        if dbs:
            print("\n*** DATABASE FILES AVAILABLE IN THE CURRENT DIRECTORY ***\n")
            if not is_current_state_arg_provided or not normal_db_inquiry:
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
            if not is_current_state_arg_provided and not normal_db_inquiry:
                return f"movies_{str(datetime.today().date()).replace('-', '_')}.db" # creates a default database file to operate on
            else:
                raise FileNotFoundError("There are no database files available in the current directory.")
    elif operational_argument == 'fill_missing' or operational_argument == 'integrate_json' or normal_json_inquiry:
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

