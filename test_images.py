import requests
from bs4 import BeautifulSoup
import urllib.parse

def get_images():
    url = f"https://runescape.wiki/w/Abyssal_demon"
    headers = {"User-Agent": "SlayerDropsApp/1.0"}
    r = requests.get(url, headers=headers)
    soup = BeautifulSoup(r.text, 'html.parser')
    
    tables = soup.find_all('table', class_='wikitable')
    for table in tables:
        headers = [th.text.strip() for th in table.find_all('th')]
        if 'Item' in headers and 'Rarity' in headers:
            for row in table.find_all('tr')[1:3]:
                cols = row.find_all(['td', 'th'])
                if len(cols) >= 5:
                    img_tag = cols[0].find('img')
                    if img_tag and img_tag.has_attr('src'):
                        print("Image src:", img_tag['src'])

get_images()
