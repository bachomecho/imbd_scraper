from imdb import Cinemagoer
import json
import argparse
import os

# TODO: set up testing
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
        self.duration = duration[0]
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

    def _parse_bulgarian_title(self, titles: list[str]) -> str:
        for title in titles:
            if 'bulgaria' in title.lower():
                return title.split('(')[0].strip()

    def get_info(self) -> dict:
        return {
            'title': self._parse_bulgarian_title(self.titles),
            'director': self.director,
            'duration': self.duration,
            'release_year': self.release_year,
            'genre': self.genre,
            'plot': self.plot,
        }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-l', '--list', help='Provide a list of movie ids')
    parser.add_argument('-f', '--file', help='Provide a file containing a list of movie ids')
    parser.add_argument('-p', '--playlist', help='Provide a list of movie ids')
    parser.add_argument('-o', '--output', help='Provide an absolute path to an output directory', required=False)
    args = parser.parse_args()

    assert (args.list or args.playlist or args.file), 'No arguments provided on the command line.'

    movie_ids = []
    if args.list:
        movie_ids: list[int] = args.list.split(',')
    elif args.playlist:
        # link to playlist https://www.imdb.com/list/ls563851203/
        from id_extractor import get_playlist, parse_playlist_for_ids
        import os
        from dotenv import load_dotenv

        load_dotenv('.env')
        movie_ids = parse_playlist_for_ids(get_playlist(args.playlist, os.getenv('USER_AGENT')))
    elif args.file:
        if '.txt' not in args.file: args.file = args.file + '.txt'
        with open(args.file, 'r') as file:
            movie_ids = list(map(str.strip, file.readlines()))


    ia = Cinemagoer()

    extracted_movies = []
    count = 0

    for movie_id in movie_ids:
        if count <= 2:
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
                count += 1
            except KeyError:
                continue

    output_path = 'res.json'
    if args.output:
        assert os.path.isabs(args.output) and os.path.isdir(args.output), 'Provided destination path is not absolute or does not exist.'
        output_path = os.path.join(args.output, output_path)

    with open(output_path, 'w') as output_file:
        json.dump(extracted_movies, output_file)

if __name__ == '__main__':
    main()
