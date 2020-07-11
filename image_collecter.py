import os, json, time, sys, argparse, uuid, logging

import requests
import boto3

from bs4 import BeautifulSoup
from PIL import Image
from io import BytesIO

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC

logging.basicConfig(level=logging.DEBUG)

class ImageCollecter(object):
    def __init__(self):
        """Initialize selenium"""
        self.chromedriver = "C:/chromedriver/chromedriver.exe"
        self.options = webdriver.ChromeOptions()
        self.options.add_argument('--no-sandbox')
        self.options.add_argument('--headless')

    def check_root_dir(self):
        """Check root dir exists"""
        if not os.path.exists('images'):
            logging.debug(f'Creating root dir at {os.getcwd()}')
            os.mkdir('images')

    def open_browser(self):
        """Open a headless browser"""
        logging.debug('Initializing browser...')

        try:
            self.browser = webdriver.Chrome(self.chromedriver, options=self.options)
        except Exception as e:
            logging.error(f'No found chromedriver in this environment.')
            logging.error(f'Install on your machine. exception: {e}')
            sys.exit()

    def download_images(self, max_limit, searchword):
        """Downloading images after scroll down the page 50 times"""
        try:
            self.searchurl = 'https://oceanhero.today/images?q=' + '+'.join(searchword.split())

            logging.debug('Creating sub directory...')
            name = '_'.join(searchword.split()).lower()
            dirs = f"images/{name}"

            if not os.path.exists(dirs):
                os.mkdir(dirs)

            self.browser.get(self.searchurl)
            time.sleep(1)

            element = self.browser.find_element_by_tag_name('body')

            # Scroll down
            logging.debug('Start scrolling down...')

            for i in range(50):
                element.send_keys(Keys.PAGE_DOWN)
                time.sleep(0.3)

            logging.debug('Reached at hte bottom...')
            page_source = self.browser.page_source 
            soup = BeautifulSoup(page_source, 'lxml')
            images = soup.find_all('img')

            logging.debug(images)
            urls = [image['src'] for image in images if not image['src'].find('https://')]

            if len(urls) == 0:
                return 0

            if len(urls) > max_limit:
                urls = urls[:max_limit]

            count = 0
            for url in urls:
                logging.debug(f"Saving image #{count} to {name}...")
                try:
                    res = requests.get(url, verify=True, stream=True)
                    rawdata = res.raw.read()
                    file_name = dirs + '/img_' + str(count) + '.jpg'

                    with open(file_name, 'wb') as f:
                        f.write(rawdata)
                        f.close()
                        count += 1
                except Exception as e:
                    logging.error('Failed to write rawdata.')
                    logging.error(e)
                    pass

            return count
        except Exception as e:
            logging.error(str(e))
        finally:
            self.browser.close()

    def run(self, max_limit: int, searchword: str) -> int:
        if isinstance(max_limit, int) and isinstance(searchword, str):
            raise TypeError

        self.check_root_dir()
        self.open_browser()
        count = self.download_images(max_limit, searchword)

        return count

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--limit', required=False, default=500, help='max number of images')
    parser.add_argument('--searchword', required=True, help='Search keywords')
    args = parser.parse_args()

    logging.debug(f"Start searching {args.limit} images of {args.searchword}...")
    start = time.time()

    obj = ImageCollecter()
    count = obj.run(int(args.limit), args.searchword)
    end = time.time()
    total_time = end - start

    logging.debug(f'Download completed. [Successful count = {count}].')
    logging.debug(f'Total time is {str(total_time)} seconds.')
