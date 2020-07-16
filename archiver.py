import os
import time
import csv
import requests
from dateutil import parser as du_parser
from dotenv import load_dotenv
from bs4 import BeautifulSoup

# Get environment variables from .env file to securely load BB credentials
load_dotenv()

BASE_URL = 'http://wtfdadxbb.vci.net'
POST_URL = BASE_URL + '/login.php'
URL = BASE_URL + '/archives.php'
PAYLOAD = {
    'username': os.environ['WBB_USERNAME'],
    'passcode': os.environ['WBB_PASSWORD']
}

def get_archive_links(archive_dir_html):
    """
    Parse archive "directory" page and build list of URLs to hit for individual archives.
    Args:
    - archive_dir_html: html response from Requests module
    """
    bdoc = BeautifulSoup(archive_dir_html, 'html.parser')
    bdoc_href = bdoc.find_all('a')
    href_list = [BASE_URL + link.get('href') for link in bdoc_href][1:-1]
    return href_list

def parse_archive(archive_html, year):
    """
    Parse individual archive page, grab key data for archival
    Args:
    - archive_dir_html: html response from Requests module
    - year: available from URL path, to add year to timestamps, type string
    Returns:
    - list of lists
        > each list contains 3 strings: timestamp, post text, and poster name
    """
    archive_bdoc = BeautifulSoup(archive_html, 'html.parser')
    entries = archive_bdoc.find_all('tr')[1:]
    return [
        [du_parser.parse(year + ' ' + entry.b.text).isoformat()] + entry.font.text.split('  de ')
        for entry in entries
    ]

def write_to_csv(parsed_archive):
    """
    Write parsed archive list content to CSV
    Args:
    - parsed_archive: list of lists, as output by func parse_archive
    Returns:
    - string confirmation of successful CSV write, filename
    """
    with open('wbb_archive.csv', 'w', newline='') as csvfile:
        archive_writer = csv.writer(csvfile, delimiter=',')
        for entry in parsed_archive:
            archive_writer.writerow(entry)
        return csvfile

def load_wbb_html():
    """
    Main function for script. Gets all archive links, loads monthly archive
    pages one-by-one, parses text and dumps to CSV.
    Returns:
    - string, confirmation of file count parsed, file output information
    """
    with requests.Session() as session:
        post = session.post(POST_URL, data=PAYLOAD)
        pages = get_archive_links(session.get(URL).text)
        archive_list = []
        for page_url in pages:
            print(f'Getting: {page_url[-7:]}')
            parsed_list = parse_archive(session.get(page_url).text, page_url[-7:-3])
            print(f'Parsing: {page_url[-7:]}')
            archive_list.extend(parsed_list)
            print('Waiting 1 second to reduce server load')
            time.sleep(1)
        write_to_csv(archive_list)

if __name__ == '__main__':
    load_wbb_html()