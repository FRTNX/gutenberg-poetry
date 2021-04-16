import os
import json
import requests
from bs4 import BeautifulSoup

BASE_URL = 'https://www.gutenberg.org'
POETRY_URL = 'https://www.gutenberg.org/ebooks/bookshelf/60'

def get_poetry_urls(url):
    req = requests.get(url)
    soup = BeautifulSoup(req.text, 'html.parser')
    links = [link.get('href') for link in soup.find_all('a')]
    return [link for link in links if link.startswith('/ebooks/') and len(link) > len('/ebooks') and link[8:].isnumeric()]


# This function takes the book metadata's author/editor/translator value,
# which is usually of the format 'Surname, Name MiddleName, DOB-DOD', or 
# 'Surname, initials (Name MiddleName), DOB-DOD' and turns it into the
# format: 'Name Surname'. This is then combined with the books title
# to form the persisted filename.
def get_filename(book_metadata):
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
    
    author = ' '.join(valid_strings[::-1])

    filename = f"{author} - {book_metadata['Title']}"
    print(f"FILENAME: {filename}")

    return filename


def get_filelinks_and_metadata(poetry_book_links):
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
        table_values = [row.text.replace('\n', '') for row in metadata_table[0].findAll('td')]
        table_dict = {}
        
        for i in range(0, len(table_keys)):
            table_dict[table_keys[i]] = table_values[i]

        table_dict['filename'] = get_filename(table_dict)
        table_dict['file_link'] = BASE_URL + txt_files[0]

        print(table_dict)
        filelinks_and_metadata.append(table_dict)

    return filelinks_and_metadata


def handler():
    poetry_book_links = []

    page_urls = ['https://www.gutenberg.org/ebooks/bookshelf/60']

    # Only 95 books available here but the redundant page requests
    # are non-breaking and could be useful when more books are added
    # this bookshelf.
    for i in range(26, 200, 25):
        page_urls.append(POETRY_URL + f'?start_index={i}')

    for page_url in page_urls:
        print(f'Fetching urls from: {page_url}')
        book_endpoints = get_poetry_urls(page_url)
        print('And book endpoints: ', book_endpoints)

        poetry_urls = [BASE_URL + endpoint for endpoint in book_endpoints]
        [poetry_book_links.append(poetry_url) for poetry_url in poetry_urls]

    print('FINAL_RESULT: ', poetry_book_links)

    filelinks_and_metadata = get_filelinks_and_metadata(poetry_book_links)
    print('FILES_AND_METADATA: ', filelinks_and_metadata)

    return filelinks_and_metadata


if __name__ == '__main__':
    filelinks_and_metadata = handler()

    for metadata in filelinks_and_metadata:
        print('DOWNLOADING: ', metadata['filename'])
        os.system(f"wget --random-wait -O \'text/{metadata['filename']}.txt\' {metadata['file_link']}")

    with open('metadata.json', 'w') as f:
        f.write(json.dumps({ 'metadata': filelinks_and_metadata }))
