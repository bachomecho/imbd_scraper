from typing import Literal
from extractor.translator import DeeplTranslator
import os, shutil, requests

class Movie:
    def __init__(
        self,
        imdb_id: str,
        titles: list[str],
        director: list[str],
        duration: list[int],
        release_year: int,
        genre: list[str],
        rating: float,
        plot: str,
        translator: DeeplTranslator,
    ) -> None:
        self.imdb_id = imdb_id
        self.titles = titles
        self.director = director[0]['name']
        if len(self.director.split()) > 2:
            self.director = " ".join(self.director.split()[1:])
        self.duration = int(duration[0])
        self.release_year = release_year
        self.genre = genre
        self.rating = rating
        self.plot = plot
        self.translator = translator

    def __repr__(self) -> str:
        return f"""Movie: (
            imdb_id={self.imdb_id},
            titles={self.titles},
            director={self.director},
            duration={self.duration},
            release_year={self.release_year},
            genre={self.genre},
            rating={self.rating},
            plot={self.plot},
        )"""

    def _parse_title(self, lang: Literal['bulgarian', 'english']) -> str:
        akas, localized_title = self.titles
        for title in akas:
            if lang in title.lower():
                return title.split('(')[0].strip()
        return localized_title

    def _generate_thumbnail_name(self):
        english_title = self._parse_title('english')
        thumb_chars_to_replace = ('*', '#', '!', ',')
        for char in thumb_chars_to_replace:
            english_title = english_title.replace(char, '')
        return f"{english_title.replace(' ', '_').replace('-', '_').lower()}_{self.duration}_{self.release_year}"

    def download_thumbnail(self, url: str, thumbnail_dir: str):
        thumbnail_path = os.path.join(thumbnail_dir, f'{self._generate_thumbnail_name()}.jpg')
        if os.path.exists(thumbnail_path):
            return
        res = requests.get(url, headers={'User-Agent': os.getenv('USER_AGENT')}, stream=True)
        if res.status_code == 200:
            if not os.path.exists(thumbnail_dir):
                os.makedirs(thumbnail_dir)
            with open(thumbnail_path, 'wb') as file:
                shutil.copyfileobj(res.raw, file)
            del res

    def get_info(self) -> dict:
        obj = {
            'imdb_id': self.imdb_id,
            'title': self._parse_title('bulgarian'),
            'thumbnail_name': self._generate_thumbnail_name(),
            'video_id': None,
            'site': None,
            'video_id_1': None,
            'site_1': None,
            'gledambg_video_id': None,
            'multi_part': 0,
            'duration': self.duration,
            'release_year': self.release_year,
            'genre': self.translator.translate_text(','.join(self.genre), target_lang="BG").text,
            'rating': self.rating,
            'director': self.translator.translate_text(self.director, target_lang="BG").text,
        }
        if self.plot:
            obj.update({'plot': self.translator.translate_text(self.plot, target_lang="BG").text})
        else: obj.update({'plot': None})
        return obj
