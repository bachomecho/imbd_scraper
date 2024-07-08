import inspect
import sqlite3

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
