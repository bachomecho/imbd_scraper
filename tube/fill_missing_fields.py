import json, os, sys
from datetime import datetime
from tube.tube import YoutubeSearch
from utils import log # TODO: fix relative import
import warnings
from typing import List, Literal, TypedDict

class JsonMovie(TypedDict):
    title: str
    video_id: str
    multi_part: Literal[0,1]

def main():
    yt_search = YoutubeSearch()

    db_dump = sys.argv[1]
    assert '.json' in db_dump, 'Provide file name with .json extension'

    if os.path.isfile(os.path.join(os.pardir, db_dump)):
        db_dump = os.path.join(os.pardir, db_dump)
        print('[+] File exists in parent directory and will now be handled.')
    elif os.path.isfile(os.path.join(os.curdir, db_dump)):
        db_dump = os.path.join(os.curdir, db_dump)
        print('[+] File exists in current directory and will now be handled.')
    else:
        raise FileNotFoundError('Provided json file does not exist.')

    with open(db_dump, 'r') as input:
        movies: List[JsonMovie] = json.load(input)

    for movie in movies:
        print('title: ', movie['title'].lower())
        correct_video: dict = yt_search.extract_correct_video(movie['title'].lower())
        if not correct_video:
            warnings.warn(f"No correct video has been found for movie {movie['title']}")
        else:
            log(correct_video)
            movie['video_id'] = correct_video['video_id']
            movie['multi_part'] = correct_video['multi_part']

    # outputting revised movies
    with open(f"REVISED_movies_{str(datetime.today().date()).replace('-', '')}.json", 'w') as output:
        json.dump(movies, output)

if __name__ == '__main__':
    main()