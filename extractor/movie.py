from extractor.translator import DeeplTranslator
import os, shutil, requests

class Movie:
    def __init__(
        self,
        imdb_id: str,
        title: str,
        director: str,
        duration: str,
        release_year: int,
        genre: str,
        rating: float,
        plot: str,
        translator: DeeplTranslator,
    ) -> None:
        self.imdb_id = imdb_id
        self.title = title
        self.director = director
        if len(self.director.split()) > 2:
            self.director = " ".join(self.director.split()[1:])
        self.duration = int(duration.split()[0]) if duration else 0
        self.release_year = int(release_year)
        self.genre = genre
        self.rating = rating
        self.plot = plot
        self.translator = translator

    def __repr__(self) -> str:
        return f"""Movie: (
            imdb_id={self.imdb_id},
            title={self.title},
            director={self.director},
            duration={self.duration},
            release_year={self.release_year},
            genre={self.genre},
            rating={self.rating},
            plot={self.plot},
        )"""

    def _generate_thumbnail_name(self):
        thumb_chars_to_replace = ('*', '#', '!', ',')
        for char in thumb_chars_to_replace:
            self.title = self.title.replace(char, '')
        return f"{self.title.replace(' ', '_').replace('-', '_').lower()}_{self.duration}_{self.release_year}"

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

    def _translate_fields(self):
        translate_fields = ['title', 'director', 'genre', 'plot']
        for field in translate_fields:
            self_field_value = getattr(self, field)
            if self_field_value:
                translated_value = self.translator.translate_text(self_field_value, target_lang="BG").text
                setattr(self, field, translated_value)

    def get_info(self) -> dict:
        self._translate_fields()
        return {
            'imdb_id': self.imdb_id,
            'title': self.title,
            'thumbnail_name': self._generate_thumbnail_name(),
            'video_id': None,
            'site': None,
            'video_id_1': None,
            'site_1': None,
            'gledambg_video_id': None,
            'multi_part': 0,
            'duration': self.duration,
            'release_year': self.release_year,
            'genre': self.genre,
            'rating': self.rating,
            'director': self.director,
            'plot': self.plot
        }
