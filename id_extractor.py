import requests
from bs4 import BeautifulSoup

def get_playlist(url: str, user_agent: str):
    res = requests.get(url, headers={'User-Agent': user_agent})
    if res.status_code == 200:
        return res.text
    else:
        raise Exception(f'Failed to fetch the page with following status code: {res.status_code}')

def parse_playlist_for_ids(playlist_html: str):
    soup = BeautifulSoup(playlist_html, 'html.parser')
    links_with_ids = soup.find_all('a', class_ = 'ipc-title-link-wrapper', href=True)
    return [link['href'].split('/')[2].lstrip('tt') for link in links_with_ids]