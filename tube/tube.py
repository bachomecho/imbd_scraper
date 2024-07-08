from pytube import Search, YouTube

class Video:
    title: str
    length: int
    views: int

class YoutubeSearch:
    def _search_movies(self, title) -> list[dict]:
        s = Search(title).results
        res = []
        for result in s:
            yt: Video = YouTube(f'http://youtube.com/watch?v={result.video_id}')
            info = {'video_id': result.video_id, 'title': yt.title, 'duration': yt.length, 'views': yt.views}
            res.append(info)
        return res

    def extract_correct_video(self, movie_title) -> dict:
        multi_part = 0
        for movie in self._search_movies(movie_title):
            if movie['duration'] > 3600 and movie_title in movie['title'].lower() and movie['views'] > 10000:
                if 'част' in movie['title'].lower():
                    multi_part = 1
                movie['multi_part'] = multi_part
                return movie
        return {}


