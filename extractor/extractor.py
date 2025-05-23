from selenium_scraping.imdb_custom_parser_selenium import SeleniumScraper
import requests, os
from extractor.translator import DeeplTranslator
from bs4 import BeautifulSoup
from abc import ABC, abstractmethod
from extractor.movie import Movie

class ExtractorMeta(ABC):
    def __init__(self, selenium_scraper: SeleniumScraper, translator: DeeplTranslator, imdb, extract_sole_field=None):
        self.selenium_scraper = selenium_scraper
        self.imdb = imdb
        self.translator = translator.initialize_translator()
        self.extract_sole_field = extract_sole_field

    @abstractmethod
    def get_movie_ids(self) -> list[str]:
        pass

    def extract(self) -> list[dict]:
        extracted_movies = []
        movie_ids = self.get_movie_ids()
        if self.selenium_scraper:
            plots_map = self.selenium_scraper.extract_multiple_summaries(self.get_movie_ids()) if len(movie_ids) > 1 else self.selenium_scraper.extract_summary(movie_ids[0])
            for movie_id in movie_ids:
                if self.extract_sole_field:
                    print(f'extracting {self.extract_sole_field} for {movie_id}..')
                try:
                    movie = self.imdb.get_movie_main(movie_id)['data']
                    movie_obj = Movie(
                        imdb_id=movie_id,
                        titles=(movie['akas'], movie['localized title']),
                        director=movie['director'],
                        duration=movie['runtimes'],
                        release_year=movie['year'],
                        genre=movie['genres'],
                        rating=movie['rating'],
                        plot=plots_map[movie_id],
                        translator=self.translator
                    )
                    extracted_movies.append(movie_obj.get_info())
                except (KeyError, AttributeError) as e:
                    print('error: ', e)
                    continue
        else:
            for movie_id in movie_ids:
                if self.extract_sole_field:
                    print(f'extracting {self.extract_sole_field} for {movie_id}..')
                try:
                    movie = self.imdb.get_movie_main(movie_id)['data']
                    movie_obj = Movie(
                        imdb_id=movie_id,
                        titles=(movie['akas'], movie['localized title']),
                        director=movie['director'],
                        duration=movie['runtimes'],
                        release_year=movie['year'],
                        genre=movie['genres'],
                        rating=movie['rating'],
                        plot=None,
                        translator=self.translator
                    )
                    extracted_movies.append(movie_obj.get_info())
                except (KeyError, AttributeError) as e:
                    print('error: ', e)
                    continue
        return extracted_movies


class FileExtractor(ExtractorMeta):
    def __init__(self, selenium_scraper: SeleniumScraper, translator: DeeplTranslator, imdb, file):
        super().__init__(selenium_scraper, translator, imdb)
        self.file = file

    def get_movie_ids(self):
        if '.txt' not in self.file: self.file = self.file + '.txt'
        with open(self.file, 'r') as file:
            movie_links = list(map(str.strip, file.readlines()))
        return [link.split('tt')[-1].strip('/') for link in movie_links]

    def extract(self):
        return super().extract()

class PlaylistExtractor(ExtractorMeta):
    def __init__(self, selenium_scraper, translator, imdb, playlist_url):
        super().__init__(selenium_scraper, translator, imdb)
        self.playlist_url = playlist_url
    """
    Extracts movie ids from movies packed in a playlist from imdb
    """
    def get_playlist_html(self):
        assert 'imdb.com' in self.playlist_url, "A full url is required"
        user_agent = os.getenv('USER_AGENT')
        res = requests.get(self.playlist_url, headers={'User-Agent': user_agent})
        return res.text if res.status_code == 200 else None

    def get_movie_ids(self):
        p_html = self.get_playlist_html()
        soup = BeautifulSoup(p_html, 'html.parser')
        links_with_ids = soup.find_all('a', class_ = 'ipc-title-link-wrapper', href=True)
        return [link['href'].split('/')[2].lstrip('tt') for link in links_with_ids]

    def extract(self):
        return super().extract()

class IndividualExtractor(ExtractorMeta):
    def __init__(self, selenium_scraper, translator, imdb, movie_id):
        super().__init__(selenium_scraper, translator, imdb)
        self.movie_id = movie_id.strip('tt')

    def get_movie_ids(self):
        return [self.movie_id]

    def extract(self):
        return super().extract()

class IDListExtractor(ExtractorMeta):
    def __init__(self, selenium_scraper, translator, imdb, extract_sole_field, id_list):
        super().__init__(selenium_scraper, translator, imdb, extract_sole_field)
        self.id_list = id_list
    def get_movie_ids(self):
        assert isinstance(self.id_list, list), 'Argument id_list is not a list'
        return self.id_list
    def extract(self):
        return super().extract()

class SetExtractStrategy:
    def __init__(self, strategy: ExtractorMeta | None = None):
        self.strategy = strategy

    def set_extract_method(self, strategy):
        self.strategy = strategy

    def extract(self) -> list[dict]:
        return self.strategy.extract()
