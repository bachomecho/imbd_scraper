import inspect
import sqlite3
import requests
from bs4 import BeautifulSoup

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