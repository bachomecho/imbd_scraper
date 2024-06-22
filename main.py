from imdb import Cinemagoer
import argparse, os, sys, json, sqlite3
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
            'multi_part': False,
            'duration': self.duration,
            'release_year': self.release_year,
            'genre': translator.translate_text(','.join(self.genre), target_lang="BG").text,
            'director': translator.translate_text(self.director, target_lang="BG").text,
            'plot': translator.translate_text(self.plot, target_lang="BG").text,
        }


def main():
    parser = argparse.ArgumentParser(description='Extract information about movies from IMDb')
    parser.add_argument('-i', '--individual', help='Provide the imdb to an individual movie.')
    parser.add_argument('-l', '--list', help='Provide a list of movie ids')
    parser.add_argument('-f', '--file', help='Provide a file containing a list of movie ids')
    parser.add_argument('-p', '--playlist', help='Provide a list of movie ids')
    parser.add_argument('-o', '--output', help='Provide an absolute path to an output directory', required=False)
    args = parser.parse_args()

    DB_KEYS = ['title', 'thumbnail_name', 'video_id', 'multi_part', 'duration', 'release_year', 'genre', 'director', 'plot']


    assert (args.list or args.playlist or args.file or args.individual), 'No arguments provided on the command line.'

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


    ia = Cinemagoer()

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
                extracted_movies.append(movie_obj.get_info())
            except KeyError:
                continue

    output_path = 'movies.json'
    if args.output:
        assert os.path.isabs(args.output) and os.path.isdir(args.output), 'Provided destination path is not absolute or does not exist.'
        output_path = os.path.join(args.output, output_path)

    with open(output_path, 'w') as output_file:
        json.dump(extracted_movies, output_file)

if __name__ == '__main__':
    main()
