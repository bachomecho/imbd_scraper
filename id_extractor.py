import requests
from bs4 import BeautifulSoup

urls = ['https://www.imdb.com/list/ls563851203/']

def get_playlist(urls: list[str], user_agent: str):
    res = requests.get(urls[0], headers={'User-Agent': user_agent})
    if res.status_code == 200:
        return res.text
    else:
        raise Exception(f'Failed to fetch the page with following status code: {res.status_code}')

def parse_playlist_for_ids(playlist_html: str):
    soup = BeautifulSoup(playlist_html, 'html.parser')
    links_with_ids = soup.find_all('a', class_ = 'ipc-title-link-wrapper', href=True)
    return [link['href'].split('/')[2].lstrip('tt') for link in links_with_ids]