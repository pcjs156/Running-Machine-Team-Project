# -*- encoding: utf-8 -*-
import requests
from bs4 import BeautifulSoup

if __name__ == '__main__':
    # q parameter 뒤쪽에 검색어를 넣으면 됨
    MELON_SEARCH_URL_FW = 'https://www.melon.com/search/total/index.htm?q='
    MELON_SEARCH_URL_BW ='&section=&searchGnbYn=Y&kkoSpl=Y&kkoDpType=&linkOrText=T&ipath=srch_form'

    HEADER = {
        'User-Agent':
            'ozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.272 Whale/2.9.117.21 Safari/537.36'
    }

    query = '가인	돌이킬 수 없는'
    URL = MELON_SEARCH_URL_FW + query + MELON_SEARCH_URL_BW
    req = requests.get(URL, headers=HEADER)
    html = req.text
    parsed = BeautifulSoup(html, 'html.parser')
    songId = parsed.find('tbody').find('input', {'class': 'input_check'}).attrs['value']

    DETAIL_URL_FW = 'https://www.melon.com/song/detail.htm?songId='
    DETAIL_URL = DETAIL_URL_FW + songId
    req = requests.get(DETAIL_URL, headers=HEADER)
    html = req.text
    parsed = BeautifulSoup(html, 'html.parser')
    print(parsed.find('div', {'class': 'lyric'}).text)