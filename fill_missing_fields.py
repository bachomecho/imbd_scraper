import json, os
from datetime import datetime
from tube import YoutubeSearch
import warnings
from typing import Literal, TypedDict

class JsonMovie(TypedDict):
    title: str
    video_id: str
    multi_part: Literal[0,1]

def fill_missing(db_dump_json: str):
    yt_search = YoutubeSearch()

    assert '.json' in db_dump_json, 'Provide file name with .json extension'

    if os.path.isfile(os.path.join(os.curdir, db_dump_json)):
        db_dump_json = os.path.join(os.curdir, db_dump_json)
        print('[+] File exists in current directory and will now be handled.')
    else:
        raise FileNotFoundError('Provided json file does not exist.')

    with open(db_dump_json, 'r') as input:
        movies: list[JsonMovie] = json.load(input)

    for movie in movies:
        correct_video: dict = yt_search.extract_correct_video(movie['title'].lower())
        if not correct_video:
            warnings.warn(f"No correct video has been found for movie {movie['title']}")
        else:
            print('correct video: ', correct_video)
            movie['video_id'] = correct_video['video_id']
            movie['multi_part'] = correct_video['multi_part']

    # outputting revised movies
    with open(f"REVISED_movies_{str(datetime.today().date()).replace('-', '')}.json", 'w') as output:
        json.dump(movies, output)
