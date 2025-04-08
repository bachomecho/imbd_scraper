from imdb_custom_parser_selenium import SeleniumScraper
import requests
from translator import DeeplTranslator
from bs4 import BeautifulSoup
from abc import abstractmethod
from movie import Movie


class ExtractorMeta:
    def __init__(self, selenium_scraper: SeleniumScraper, translator: DeeplTranslator, imdb):
        self.selenium_scraper = selenium_scraper
        self.imdb = imdb
        self.translator = translator.initialize_translator()

    @abstractmethod
    def get_movie_ids(self) -> list[str]:
        pass

    def extract(self):
        extracted_movies = []
        plots_map = self.selenium_scraper.extract_multiple_summaries(self.get_movie_ids())
        for movie_id in self.get_movie_ids():
            try:
                movie = self.imdb.get_movie_main(movie_id)['data']
                movie_obj = Movie(
                    imdb_id=movie_id,
                    titles=movie['akas'],
                    director=movie['director'],
                    duration=movie['runtimes'],
                    release_year=movie['year'],
                    genre=movie['genres'],
                    plot=plots_map[movie_id],
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
    def get_playlist(self, user_agent: str):
        res = requests.get(self.playlist_url, headers={'User-Agent': user_agent})
        if res.status_code == 200:
            return res.text
        else:
            raise Exception(f'Failed to fetch the page with following status code: {res.status_code}')

    def get_ids_from_playlist(playlist_html: str):
        soup = BeautifulSoup(playlist_html, 'html.parser')
        links_with_ids = soup.find_all('a', class_ = 'ipc-title-link-wrapper', href=True)
        return [link['href'].split('/')[2].lstrip('tt') for link in links_with_ids]

class SetExtractStrategy(ExtractorMeta):
    def __init__(self, strategy: ExtractorMeta):
        self.strategy = strategy

    def set_extract_method(self, strategy):
        self.strategy = strategy

    def extract_imdb_info(self):
        self.strategy.extract()
