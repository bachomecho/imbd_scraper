from imdb import Cinemagoer
import argparse, os, sys, sqlite3, shutil, json
import requests, warnings
from utils import log,get_playlist, parse_playlist_for_ids, titles_currently_present, file_input_prompt, bulk_update_with_file, file_prompt
from fill_missing_fields import fill_missing
from typing import Literal
from handle_json import insert_json_into_db, output_current_state_json
from datetime import datetime
from selenium_scraping.imdb_custom_parser_selenium import SeleniumScraper
from translator import DeeplTranslator
from movie import Movie


class Arguments:
    individual: str
    id_list: list[str]
    file: str
    playlist: str  # TODO: some kind of url type
    current_state: 1
    integrate_json: 1
    fill_missing: 1
    download_thumbnails: 1
    tidy_dir: 1
    remove_entry: 1

def group_files_dir(files):
    dir_name = f"1_{str(datetime.today().date()).replace('-', '')}_DATABASE_AND_JSON"
    idx = 1
    while os.path.isdir(dir_name):
        dir_name_split = dir_name.split('_')
        idx += 1
        dir_name = f"{idx}_{'_'.join(dir_name_split[1:])}"
    os.makedirs(dir_name)
    for file in files:
        shutil.copyfile(file, os.path.join(dir_name, file))


def main():
    parser = argparse.ArgumentParser(
        description="Extract information about movies from IMDb"
    )
    parser.add_argument(
        "-path",
        "--path",
        help="Provide path to the sqlite3 database that you want to interact with.",
    )
    parser.add_argument(
        "-i", "--individual", help="Provide the imdb to an individual movie."
    )
    parser.add_argument("-l", "--id_list", help="Provide a list of movie ids")
    parser.add_argument(
        "-f", "--file", help="Provide a file containing a list of movie ids"
    )
    parser.add_argument("-p", "--playlist", help="Provide a list of movie ids")
    parser.add_argument(
        "-CURRENT_STATE",
        "--current_state",
        help="This will dump database into a json file in the current directory.",
        required=False,
    )
    parser.add_argument(
        "-INTEGRATE_JSON",
        "--integrate_json",
        help="Provide a json_file that you want to insert into a current or new database",
        required=False,
    )
    parser.add_argument(
        "-FILL_MISSING",
        "--fill_missing",
        help="Fill missing fields given there is a database dump in json format in current directory",
        required=False,
    )
    parser.add_argument(
        "-DOWNLOAD_THUMBNAILS",
        "--download_thumbnails",
        help="Download thumbnails for the movies in the database. Provide that argument in combination with the parsing arguments: -individual, -id_list, -file, -playlist",
    )
    parser.add_argument(
        "-TIDY_DIR",
        "--tidy_dir",
        help="Get rid of all db and json files in current directory"
    )
    parser.add_argument(
        "-REMOVE_ENTRY",
        "--remove_entry",
        help="Remove database entry"
    )
    args: Arguments = parser.parse_args()

    DB_KEYS = [
        "imdb_id",
        "title",
        "thumbnail_name",
        "video_id",
        "multi_part",
        "duration",
        "release_year",
        "genre",
        "director",
        "plot",
    ]

    assert (
        args.id_list
        or args.playlist
        or args.file
        or args.individual
        or args.current_state
        or args.integrate_json
        or args.fill_missing
        or args.tidy_dir
        or args.remove_entry
    ), "No arguments provided on the command line."

    files_to_be_moved = []

    database_path = None

    if args.individual or args.id_list or args.file or args.playlist:
        database_path = file_input_prompt(parsing_args=True)
    elif args.current_state:
        database_path = file_input_prompt(operational_argument='current_state')

    if database_path:
        files_to_be_moved.append(database_path)
        con = sqlite3.connect(database_path)
        if con:
            print(f"[log] Connection to {database_path} has been established.")
        else:
            raise ConnectionRefusedError(
                f"Connection to {database_path} could not be established."
            )
        cur = con.cursor()

    movie_ids: list[str] = []
    if args.individual:
        movie_ids.append(args.individual.split('tt')[-1].strip('/'))
    elif args.id_list:
        movie_ids = args.id_list.split(',')
    elif args.playlist: # link to playlist https://www.imdb.com/list/ls563851203/
        movie_ids = parse_playlist_for_ids(get_playlist(args.playlist, os.getenv('USER_AGENT')))
    elif args.file:
        if '.txt' not in args.file: args.file = args.file + '.txt'
        with open(args.file, 'r') as file:
            movie_links = list(map(str.strip, file.readlines()))
            movie_ids = [link.split('tt')[-1].strip('/') for link in movie_links]
    elif args.current_state:
        files_to_be_moved.append(f"db_dump_{os.path.basename(database_path).strip('.db')}.json")
        output_current_state_json(cur, DB_KEYS, database_path)
        sys.exit(0)
    elif args.integrate_json:
        json_file = file_input_prompt(operational_argument='integrate_json')
        files_to_be_moved.append(json_file)
        files_to_be_moved.append(database_path = 'REVISED_' + os.path.basename(json_file).strip('.json') + '.db')
        insert_json_into_db(json_file)
        sys.exit(0)

    elif args.fill_missing:
        json_dump_to_revise = file_input_prompt(operational_argument='fill_missing')
        fill_missing(json_dump_to_revise)
        files_to_be_moved.append(json_dump_to_revise)
        sys.exit(0)
    elif args.tidy_dir:
        db_json_files = [file for file in os.listdir() if file.endswith('.db') or file.endswith('.json')]
        if not db_json_files:
            print("No .json or .db files found in the current directory.")
            sys.exit(0)
        for file in db_json_files:
            os.remove(file)
        print(f"[+] Removed {len(db_json_files)} .json or .db files from the current directory.")
        sys.exit(0)
    elif args.remove_entry:
        all_movies = cur.execute("SELECT title FROM movies")
        for idx, movie in enumerate(all_movies):
            print(f"\t[{idx+1}] {movie}")
        select_movie_to_update = input("Please select movie you wish to remove: \n")
        remove_query = f"""
        DELETE FROM movies
        WHERE title = "{all_movies[select_movie_to_update-1]}";
        """
        print('remove query: ', remove_query)
        cur.execute(remove_query)
        con.commit()


    ia = Cinemagoer()
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

    current_database_state = titles_currently_present(cur)
    extracted_movies = []

    selenium_scraper = SeleniumScraper()
    translator = DeeplTranslator.initialize_translator()
    for movie_id in movie_ids:
        try:
            movie = ia.get_movie_main(movie_id)['data']
            movie_obj = Movie(
                imdb_id=movie_id,
                titles=movie['akas'],
                director=movie['director'],
                duration=movie['runtimes'],
                release_year=movie['year'],
                genre=movie['genres'],
                translator=translator
            )
            print('Information from following movies is being extracted: \n')
            print(f'{movie_id}: {repr(movie_obj)}')
            movie_info = movie_obj.get_info()
            if args.download_thumbnails:
                movie_obj.download_thumbnail(movie['cover url'], os.getenv('THUMBNAIL_DIR'))
            log(movie_info)
            (
                extracted_movies.append(movie_info)
                if movie_info["title"] not in current_database_state
                else print(f'{movie_info["title"]} already exists in database.')
            )
        except (KeyError, AttributeError):
            continue

    print(
        f"\nFollowing movies will be added into the database -> {[mov['title'] for mov in extracted_movies]}.\n\nOut of the provided {len(movie_ids)} movie ids, {len(extracted_movies)} are actual new movies."
    )
    add_movies = input("Do you want to add them? [y/n]")
    if add_movies == "y":
        insert_query = f"""
        INSERT OR IGNORE INTO movies (
            {",".join(DB_KEYS)}
        ) VALUES ({"".join([f':{name},' for name in DB_KEYS]).strip(',')})
        """

        cur.executemany(insert_query, extracted_movies)
        con.commit()
        print(f"[+] {len(extracted_movies)} movies have been added to movies table in {database_path}")

    inquire_current_db_state = input("Do you want to see current db state. This will dump database into a json file in the current directory. [y/n]: ")
    if inquire_current_db_state == "y":
        json_dump = f"db_dump_{os.path.basename(database_path).strip('.db')}.json"
        files_to_be_moved.append(json_dump)
        output_current_state_json(cur, DB_KEYS, database_path)

    inquire_missing_fields = input("Do you want to fill missing fields of newly extracted movies e.g. video id and multi_part. [y/n]")
    if inquire_missing_fields == "y":
        revised_json = f"REVISED_movies_{str(datetime.today().date()).replace('-', '')}.json"
        files_to_be_moved.append(revised_json)
        fill_missing(json_dump, len(extracted_movies))

        inquire_insert_into_db = input("Do you want to insert revised fields back into a database?")
        if inquire_insert_into_db == "y":
            files_to_be_moved.append('REVISED_' + os.path.basename(revised_json).strip('.json') + '.db')
            insert_json_into_db(revised_json)

    con.close()

    group_files_dir(files_to_be_moved)

if __name__ == '__main__':
    main()
