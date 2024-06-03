from imdb import Cinemagoer
import json


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
    ia = Cinemagoer()

    movie_ids: list[int] = ['0297689', '0326098']
    for movie_id in movie_ids:
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

    with open('imdb_res.json', 'w') as output_file:
        json.dump(movie_obj.get_info(), output_file)

if __name__ == '__main__':
    main()
