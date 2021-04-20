import os
import sys
import json

import requests
from bs4 import BeautifulSoup

BASE_URL = 'https://www.gutenberg.org'
POETRY_URL = 'https://www.gutenberg.org/ebooks/bookshelf/60'

# This function takes the book metadata's author/editor/translator value,
# which is usually of the format 'Surname, Name MiddleName, DOB-DOD', or 
# 'Surname, initials (Name MiddleName), DOB-DOD' and turns it into the
# format: 'Name Surname'. This is then combined with the books title
# to form the persisted filename.
def find_and_normalize_author(book_metadata):
    author = ''
    if 'Author' not in book_metadata.keys():
        if 'Translator' in book_metadata.keys():   
            author = book_metadata['Translator']
        if 'Editor' in book_metadata.keys():               
            author = book_metadata['Editor']
    else:
        author = book_metadata['Author']

    if not author:
        raise Exception(f'Could not find author using supported schemas: {book_metadata}')        
            
    if author.count(',') > 1:           
        reversed_val = author[::-1]        
        author = reversed_val[reversed_val.find(',') + 1:][::-1]

    split_names = author.split(',')
    valid_strings = []
    for name in split_names:
        if not any(map(str.isdigit, name)):
            if '(' in name:
                valid_strings.append(name[name.find('(') + 1: len(name) - 1].strip())
            else:
                valid_strings.append(name.strip())
    
    return ' '.join(valid_strings[::-1])


def get_filelinks_and_metadata(poetry_book_links, search_term=None):
    filelinks_and_metadata = []
    for book_url in poetry_book_links:
        req = requests.get(book_url)
        soup = BeautifulSoup(req.text, 'html.parser')
        links = [link.get('href') for link in soup.find_all('a')]
        txt_files = [link for link in links if link and '.txt' in link and 'readme' not in link]
        print(txt_files)

        if len(txt_files) == 0:
            continue # skips audio books

        metadata_table = soup.find_all('table', class_='bibrec')
        table_keys = [row.text for row in metadata_table[0].findAll('th')]
        table_values = [row.text.replace('\n', '').replace('\r', '') for row in \
            metadata_table[0].findAll('td')]
    
        table_dict = {}
        
        for i in range(0, len(table_keys)):
            table_dict[table_keys[i]] = table_values[i]

        author = find_and_normalize_author(table_dict)
        print('AUTHOR: ', author)

        table_dict['file_link'] = BASE_URL + txt_files[0]
        table_dict['filename'] = f"{author} - {table_dict['Title']}".replace("'", '').replace('"', '')

        if search_term and search_term.lower() not in author.lower():
            print(f'{table_dict["filename"]} does not match search term. Skipping.')
            continue # skips irrelevant search results
    
        if table_dict['Language'].lower() != 'english':
            print(f'{table_dict["filename"]} is not written in English. Skipping')
            continue # skips non english books

        print(f"FILENAME: {table_dict['filename']}")

        print(table_dict)
        filelinks_and_metadata.append(table_dict)

    return filelinks_and_metadata


def get_poetry_urls(url):
    req = requests.get(url)
    soup = BeautifulSoup(req.text, 'html.parser')
    links = [link.get('href') for link in soup.find_all('a')]
    return [link for link in links if link.startswith('/ebooks/') and \
        len(link) > len('/ebooks') and link[8:].isnumeric()]


def handler(search_term=None):
    poetry_book_links = []

    if not search_term:
        page_urls = ['https://www.gutenberg.org/ebooks/bookshelf/60']

        # Only 95 books available here but the redundant page requests
        # are non-breaking and could be useful when more books are added to
        # this bookshelf.
        for i in range(26, 200, 25):
            page_urls.append(POETRY_URL + f'?start_index={i}')
    else:
        search_url = f"https://www.gutenberg.org/ebooks/search/?query={search_term.replace(' ', '+')}&submit_search=Go%21"
        page_urls = [search_url]
        for i in range(26, 300, 25):
            page_urls.append(search_url + f'&start_index={i}')

    for page_url in page_urls:
        print(f'Fetching urls from: {page_url}')
        book_endpoints = get_poetry_urls(page_url)
        print('And book endpoints: ', book_endpoints)
        poetry_urls = [BASE_URL + endpoint for endpoint in book_endpoints]
        [poetry_book_links.append(poetry_url) for poetry_url in poetry_urls]

    print('FINAL_RESULT: ', poetry_book_links)

    filelinks_and_metadata = get_filelinks_and_metadata(poetry_book_links, search_term)
    print('FILES_AND_METADATA: ', filelinks_and_metadata)

    return filelinks_and_metadata


if __name__ == '__main__':
    has_search_term = len(sys.argv) == 3 and (sys.argv[1] == '--author' or sys.argv[1] == '-a') 
    search_term = sys.argv[2] if has_search_term else None
    print(f'Beginning extraction. Search term: {search_term}')

    filelinks_and_metadata = handler(search_term)

    for metadata in filelinks_and_metadata:
        print('DOWNLOADING: ', metadata['filename'])
        os.system(f"wget --random-wait -O \'text/{metadata['filename']}.txt\' {metadata['file_link']}")

    with open('metadata.json', 'w') as f:
        f.write(json.dumps({ 'metadata': filelinks_and_metadata }))
