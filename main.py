from imdb import Cinemagoer
import argparse, os, sys, json, sqlite3, shutil
from id_extractor import get_playlist, parse_playlist_for_ids
from dotenv import load_dotenv
import deepl
from datetime import datetime
from typing import Literal
from db_handler import *

load_dotenv('.env')
translator = deepl.Translator(os.getenv("DEEPL_API_KEY"))

class Movie:
    def __init__(
        self,
        titles: list[str],
        director: list[str],
        duration: list[int],
        release_year: int,
        genre: list[str],
        plot: str,
    ) -> None:
        self.titles = titles
        self.director = director[0]['name']
        if len(self.director.split()) > 2:
            self.director = " ".join(self.director.split()[1:])
        self.duration = int(duration[0])
        self.release_year = release_year
        self.genre = genre
        self.plot = plot

    def __repr__(self) -> str:
        return f"""Movie: (
            titles={self.titles},
            director={self.director},
            duration={self.duration},
            release_year={self.release_year},
            genre={self.genre},
            plot={self.plot},
        )"""

    def _parse_title(self, lang: Literal['bulgarian', 'english']) -> str:
        for title in self.titles:
            if lang in title.lower():
                return title.split('(')[0].strip()


    def _generate_thumbnail_name(self):
        return f"{self._parse_title('english').replace(' ', '_').lower()}_{self.duration}_{self.release_year}"

    def get_info(self) -> dict:
        return {
            'title': self._parse_title('bulgarian'),
            'thumbnail_name': self._generate_thumbnail_name(),
            'video_id': None,
            'multi_part': 0,
            'duration': self.duration,
            'release_year': self.release_year,
            'genre': translator.translate_text(','.join(self.genre), target_lang="BG").text,
            'director': translator.translate_text(self.director, target_lang="BG").text,
            'plot': translator.translate_text(self.plot, target_lang="BG").text,
        }


def view_current_state(cur: sqlite3.Cursor, keys: list[str]):
        exec = cur.execute('SELECT * FROM movies')
        current_db_state = exec.fetchall()
        print('current db state: \n', current_db_state)
        data_integrity_check = input('Do you want to update current database state using json? [y/n]')
        if data_integrity_check == 'y':
            json_movies = [dict(zip(keys,list(movie[1:])))for movie in current_db_state]
            with open(f"db_dump_{str(datetime.today().date()).replace('-', '_')}.json", 'w') as out:
                json.dump(json_movies, out)

def main():
    parser = argparse.ArgumentParser(description='Extract information about movies from IMDb')
    parser.add_argument('-path', '--path', help='Provide path to the sqlite3 database that you want to interact with.')
    parser.add_argument('-i', '--individual', help='Provide the imdb to an individual movie.')
    parser.add_argument('-l', '--list', help='Provide a list of movie ids')
    parser.add_argument('-f', '--file', help='Provide a file containing a list of movie ids')
    parser.add_argument('-p', '--playlist', help='Provide a list of movie ids')
    parser.add_argument('-o', '--output', help='Provide an absolute path to an output directory', required=False)
    parser.add_argument('-cs', '--current_state', help='When provided shows the current state of the specified database.', required=False)
    args = parser.parse_args()

    DB_KEYS = ['title', 'thumbnail_name', 'video_id', 'multi_part', 'duration', 'release_year', 'genre', 'director', 'plot']


    assert (args.list or args.playlist or args.file or args.individual or args.current_state), 'No arguments provided on the command line.'
    if not args.current_state:
        assert args.path, 'No path to/for a database has been provided.'
        assert os.path.isabs(args.path), 'The path to the database is not absolute.'

        if os.path.isfile(args.path):
            print('Specified path points to a file that already exists.') # this is done in order for parsed movies to not be unnecessarily appended to an existing db
            append_to_existing_database = input('Do you want to append to already existing database? [y/n]')
            if append_to_existing_database == 'n':
                create_new_db = input('Do you want to create a new database? If yes, a backup will be created in case you want to revert to previous state. [y/n]')
                if create_new_db == 'y':
                    shutil.copyfile(args.path, args.path.split('.')[0] + '_backup' + '.db')
                    os.unlink(args.path)
        con = sqlite3.connect(args.path)
    else:
        assert os.path.isabs(args.current_state), 'Argument provided for current state should be an absolute file to a .db file.'
        con = sqlite3.connect(args.current_state)

    database_path = args.current_state if args.current_state else args.path
    if con: print(f'[log] Connection to {database_path} has been established.')
    else: raise ConnectionRefusedError(f'Connection to {database_path} could not be established.')
    cur = con.cursor()

    movie_ids: list[int] = []
    if args.individual:
        movie_ids.append(args.individual.split('tt')[-1].strip('/'))
    elif args.list:
        movie_ids = args.list.split(',')
    elif args.playlist: # link to playlist https://www.imdb.com/list/ls563851203/
        movie_ids = parse_playlist_for_ids(get_playlist(args.playlist, os.getenv('USER_AGENT')))
    elif args.file:
        if '.txt' not in args.file: args.file = args.file + '.txt'
        with open(args.file, 'r') as file:
            movie_ids = list(map(str.strip, file.readlines()))
    elif args.current_state:
        view_current_state(cur, DB_KEYS)
        sys.exit(0)


    ia = Cinemagoer()
    create_table_query = """
    CREATE TABLE IF NOT EXISTS movies (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
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

    current_database_state = titles_currently_present(cur)
    extracted_movies = []

    for movie_id in movie_ids:
            try:
                movie = ia.get_movie_main(movie_id)['data']
                movie_obj = Movie(
                    titles=movie['akas'],
                    director=movie['director'],
                    duration=movie['runtimes'],
                    release_year=movie['year'],
                    genre=movie['genres'],
                    plot=movie['plot outline'],
                )
                print('Information from following movies is being extracted: \n')
                print(f'{movie_id}: {repr(movie_obj)}')

                movie_info = movie_obj.get_info()
                print('Movie info: ', movie_info)
                extracted_movies.append(movie_info) if movie_info['title'] not in current_database_state else print(f'{movie_info["title"]} already exists in database.')
            except (KeyError, AttributeError):
                continue

    print('Movies that will be added into the database.', extracted_movies)
    add_movies = input('Do you want to add them? [y/n]')
    if add_movies == 'y':
        insert_query = f"""
        INSERT OR IGNORE INTO movies (
            {",".join(DB_KEYS)}
        ) VALUES ({"".join([f':{name},' for name in DB_KEYS]).strip(',')})
        """

        cur.executemany(insert_query, extracted_movies)
        con.commit()
        print(f'[+] {len(extracted_movies)} movies have been added to movies table in {args.path}')

    inquire_current_db_state = input('Do you want to see current db state [y/n]: ')
    if inquire_current_db_state == 'y':
        view_current_state(cur, DB_KEYS)

    con.close()

if __name__ == '__main__':
    main()
