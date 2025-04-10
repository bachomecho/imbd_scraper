from selenium_scraping.imdb_custom_parser_selenium import SeleniumScraper
from imdb import Cinemagoer
from extractor.translator import DeeplTranslator
from extractor.extractor import FileExtractor, IndividualExtractor

def file_extractor():
    imdb = Cinemagoer()
    selenium_scraper = SeleniumScraper()
    translator = DeeplTranslator()
    f = FileExtractor(
        selenium_scraper=selenium_scraper,
        translator=translator,
        imdb=imdb,
        file='test_movies.txt')
    return f.extract()


def individual_extractor():
    imdb = Cinemagoer()
    selenium_scraper = SeleniumScraper()
    translator = DeeplTranslator()
    i = IndividualExtractor(
        selenium_scraper=selenium_scraper,
        translator=translator,
        imdb=imdb,
        movie_id='tt0238363')
    return i.extract()


def test_extract_movies():
    assert file_extractor() == [{'imdb_id': '0238363', 'title': 'Куче в чекмедже', 'thumbnail_name': 'a_dog_in_a_drawer_80_1982', 'video_id': None, 'multi_part': 0, 'duration': 80, 'release_year': 1982, 'genre': 'Семейство', 'director': 'Г-н Димитър Петров', 'plot': 'Петгодишно момче с разведени родители седи по цял ден вкъщи и гледа телевизия. Майка му е на пълен работен ден, а бащата го посещава само от време на време. Единствената мечта на момчето е да има кученце. Затова той и трима негови приятели решават да си купят кученце. Не след дълго това се случва. Децата са готови да направят всичко за своя домашен любимец, но бездушието и липсата на разбиране от страна на техните роднини и съседи ги лишава от такава на радост. Кученцето е предназначено за село, а хлапетата отново са съвсем сами вкъщи и гледат телевизия." -Георги Дюлгеров <georgidjul1943@gmail.com>'}, {'imdb_id': '0235952', 'title': 'Trinadesetata godenitsa na printsa', 'thumbnail_name': 'the_thirteenth_bride_of_the_prince_89_1987', 'video_id': None, 'multi_part': 0, 'duration': 89, 'release_year': 1987, 'genre': 'Фентъзи, Комедия, Фантастика, Романтика, Научна фантастика, Семейни, Приключения', 'director': 'Иванка Грибчева', 'plot': 'Един глупав принц иска да се ожени за красива селянка. Стражите му я отвличат, но момичето успява да избяга и се връща при любимия си. Междувременно в кралството каца НЛО и извънземните стават свидетели на неприятности, дворцови интриги и лъжи. На тях не им е позволено да се месят в чуждите дела, но въпреки това те оказват влияние върху щастливия край. -Георги Дюлгеров <georgidjul1943@gmail.com>'}]
    assert individual_extractor() == [{'imdb_id': '0238363', 'title': 'Куче в чекмедже', 'thumbnail_name': 'a_dog_in_a_drawer_80_1982', 'video_id': None, 'multi_part': 0, 'duration': 80, 'release_year': 1982, 'genre': 'Семейство', 'director': 'Г-н Димитър Петров', 'plot': 'Петгодишно момче с разведени родители седи по цял ден вкъщи и гледа телевизия. Майка му е на пълен работен ден, а бащата го посещава само от време на време. Единствената мечта на момчето е да има кученце. Затова той и трима негови приятели решават да си купят кученце. Не след дълго това се случва. Децата са готови да направят всичко за своя домашен любимец, но бездушието и липсата на разбиране от страна на техните роднини и съседи ги лишава от такава на радост. Кученцето е предназначено за село, а хлапетата отново са съвсем сами вкъщи и гледат телевизия." -Георги Дюлгеров <georgidjul1943@gmail.com>'}]