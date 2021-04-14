import os
import requests
from bs4 import BeautifulSoup

BASE_URL = 'https://www.gutenberg.org'
POETRY_URL = 'https://www.gutenberg.org/ebooks/bookshelf/60'

def get_poetry_urls(url):
    req = requests.get(url)
    soup = BeautifulSoup(req.text, 'html.parser')
    links = [link.get('href') for link in soup.find_all('a')]
    return [link for link in links if link.startswith('/ebooks/') and len(link) > len('/ebooks') and link[8:].isnumeric()]


def get_text_file_links(urls):
    txt_file_links = []
    for book_page in urls:
        req = requests.get(book_page)
        soup = BeautifulSoup(req.text, 'html.parser')
        links = [link.get('href') for link in soup.find_all('a')]
        txt_files = [link for link in links if link and '.txt' in link and 'readme' not in link]
        print(txt_files)

        if len(txt_files) == 0:
            continue # skips audio books

        txt_file_links.append(BASE_URL + txt_files[0])

    return txt_file_links


def handler():
    poetry_links = []

    urls = [
        'https://www.gutenberg.org/ebooks/bookshelf/60',
        'https://www.gutenberg.org/ebooks/bookshelf/60?start_index=26',
        'https://www.gutenberg.org/ebooks/bookshelf/60?start_index=51',
        'https://www.gutenberg.org/ebooks/bookshelf/60?start_index=76',
        'https://www.gutenberg.org/ebooks/bookshelf/60?start_index=101',
        'https://www.gutenberg.org/ebooks/bookshelf/60?start_index=126',
        'https://www.gutenberg.org/ebooks/bookshelf/60?start_index=151',
        'https://www.gutenberg.org/ebooks/bookshelf/60?start_index=176',
    ]

    for url in urls:
        print(f'Fetching urls from: {url}')
        book_endpoints = get_poetry_urls(url)
        print('And book endpoints: ', book_endpoints)

        poetry_urls = [BASE_URL + endpoint for endpoint in book_endpoints]
        [poetry_links.append(poetry_url) for poetry_url in poetry_urls]

    print('FINAL_RESULT: ', poetry_links)

    txt_file_links = get_text_file_links(poetry_links)
    print('TXT_FILE_LINKS: ', txt_file_links)

    return txt_file_links


if __name__ == '__main__':
    txt_file_links = handler()

    for link in txt_file_links:
        os.system(f'wget --random-wait -P text/ {link}')
