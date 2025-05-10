from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException
import time, os
from selenium.webdriver.common.by import By
from dotenv import load_dotenv
load_dotenv('.env')

DEBUG = False

class SeleniumScraper:
    def __init__(self):
        if not DEBUG:
            self.chrome_options = Options()
            self.chrome_options.add_argument("--headless=new")
            self.chrome_options.add_argument("--window-size=1920,1080")
            self.chrome_options.add_argument('--ignore-certificate-errors')
            self.chrome_options.add_argument(f'user-agent={os.getenv("USER-AGENT")}')
            self.driver = webdriver.Chrome(options=self.chrome_options)
        else:
            self.driver = webdriver.Chrome() # does not run driver in headless mode so one can do "visual" debugging, if that's even a thing

    def extract_summary(self, id: str, single_summary=True):
        time.sleep(2)
        url = f'https://www.imdb.com/title/tt{id}'
        print(url)
        self.driver.get(url)
        scroll_pause_time = 1
        element_found = False
        text = ''

        while not element_found:
            try:
                element = self.driver.find_element(
                    By.CSS_SELECTOR, "div[data-testid='storyline-plot-summary'][class*='ipc-overflowText']"
                )
                print(element.text)
                text = element.text
                element_found = True
            except NoSuchElementException:
                time.sleep(scroll_pause_time)
                self.driver.execute_script("window.scrollBy(0, 1000);")
                time.sleep(scroll_pause_time)
                reachedBottom: bool = self.driver.execute_script('return window.innerHeight + Math.round(window.scrollY) >= document.body.offsetHeight')
                print(reachedBottom)
                if reachedBottom:
                    print('No summary element found.')
                    break
        if single_summary:
            self.driver.quit()
            print('[INFO] Selenium driver was terminated.')
        return {id: text}

    def extract_multiple_summaries(self, ids: list[str]):
        summaries = dict()
        for id in ids:
            summaries.update(self.extract_summary(id, single_summary=False))
            self.driver.delete_all_cookies()
        self.driver.quit()
        print('[INFO] Selenium driver was terminated.')
        return summaries

