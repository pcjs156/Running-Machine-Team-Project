# -*- encoding: utf-8 -*-
import os
import time

import requests
from bs4 import BeautifulSoup

if __name__ == '__main__':
    # q parameter 뒤쪽에 검색어를 넣으면 됨
    # https://www.melon.com/search/song/index.htm?q=%EB%B9%84+%28Rain%29+%EB%84%90+%EB%B6%99%EC%9E%A1%EC%9D%84+%EB%85%B8%EB%9E%98&section=&searchGnbYn=Y&kkoSpl=N&kkoDpType=&ipath=srch_form
    MELON_SEARCH_URL_FW = 'https://www.melon.com/search/total/index.htm?q='
    MELON_SEARCH_URL_BW ='&section=&searchGnbYn=Y&kkoSpl=Y&kkoDpType=&linkOrText=T&ipath=srch_form'

    HEADER = {
        'User-Agent':
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.272 Whale/2.9.117.21 Safari/537.36'
    }

    # 가사 데이터 파일 목록을 불러옴
    # 프로그램 실행 도중 크롤링이 완료되는 대로 파일명을 추가할 것이므로, list로 선언함(계속해서 파일 목록을 확인하지 않기 위해)
    lyricsFilenameList = os.listdir('./lyricsdata/')

    # .txt로 끝나는 차트 데이터를 불러옴
    chart_data_files = tuple(filter(lambda fn: fn.endswith('.txt'), os.listdir('./chartdata/')))
    for filename in chart_data_files:
        with open('./chartdata/' + filename, mode='r', encoding='utf-8') as f:
            lines = list(map(lambda s: s.strip(), f.readlines()))
            # 맨 윗줄만 있는 경우, 파일이 비어 있는 것이므로 건너뜀
            if len(lines) == 1:
                continue
            # 정상적으로 차트 정보가 크롤링된 경우
            else:
                # 맨 윗줄은 파일명, 나머지 줄은 차트 정보
                dt, chartLines = lines[0], lines[1:]

                for line in chartLines:
                    # 순위, 아티스트, 제목이 탭 문자로 구분되어 있음
                    # 저장될 파일 이름은 "아티스트명@곡명.txt"로 함
                    chartInfo = line.strip().split('\t')
                    rank, artist, title = chartInfo
                    lyricsFilename = artist + '@' + title + '.txt'
                    # 만약 해당 가사가 이미 크롤링되어 있다면, 다음 차트 목록으로 넘어감
                    if lyricsFilename in lyricsFilenameList:
                        # 단, 크롤링에 실패해 파일이 비어 있을 수 있으므로 이 경우 다시 크롤링을 시도함
                        with open('./lyricsdata/' + lyricsFilename, mode='r', encoding='utf-8') as lyricsFile:
                            if not lyricsFile.readlines():
                                print(f'{lyricsFilename}이 비어 있어 다시 크롤링을 시도합니다.')
                            else:
                                continue

                    # 검색어는 [아티스트 + " " + 제목]으로 함
                    query = title.replace(' ', '%20')
                    query = title.replace('\t', '%20')
                    # 요청 보내기
                    URL = MELON_SEARCH_URL_FW + query + MELON_SEARCH_URL_BW
                    # 응답 코드가 200일 때까지 총 5번 요청함
                    for req_try in range(1, 6):
                        req = requests.get(URL, headers=HEADER)
                        if req.status_code != 200:
                            print(f'{dt}) {rank}위 {artist}-{title}에서 곡 검색 정보 status code != 200 발생({req.status_code})')
                            print('5초간 대기...')
                            print(URL)
                            time.sleep(5)
                        else:
                            break

                    # 요청을 5회 이상 보냈다면, 그냥 다음 파일로 건너뜀
                    if req_try >= 5:
                        print(f'!!!!!!{dt}) {rank}위 {artist}-{title}에서 곡 검색 정보 크롤링 실패!!!!!!')
                        continue

                    # 멜론 곡 검색 페이지에서 노래의 고유 번호를 크롤링함
                    html = req.text
                    parsed = BeautifulSoup(html, 'html.parser')
                    try:
                        trList = parsed.find('div', {'class':'tb_list d_song_list songTypeOne'}).\
                                    find('table').find('tbody').find('tr')
                    except AttributeError:
                        print(f'검색어 {title}에서 가사 검색 건수가 0입니다.')
                        continue

                    else:
                        hrefText = trList.find('a', {'class':'btn btn_icon_detail'}).attrs['href']
                        startIdx = hrefText.find("melon.link.goSongDetail('") + len("melon.link.goSongDetail('")
                        hrefText = hrefText[startIdx:]
                        finishIdx = hrefText.find("');")
                        songId = hrefText[:finishIdx]

                    DETAIL_URL_FW = 'https://www.melon.com/song/detail.htm?songId='
                    # 응답 코드가 200일 때까지 총 5번 요청함
                    for req_try in range(1, 6):
                        DETAIL_URL = DETAIL_URL_FW + songId
                        req = requests.get(DETAIL_URL, headers=HEADER)
                        if req.status_code != 200:
                            print(f'{dt}) {rank}위 {artist}-{title}에서 가사 정보 status code != 200 발생({req.status_code})')
                            print('5초간 대기...')
                            print(DETAIL_URL)
                            time.sleep(5)
                        else:
                            break

                    # 요청을 5회 이상 보냈다면, 그냥 다음 파일로 건너뜀
                    if req_try >= 5:
                        print(f'!!!!!!{dt}) {rank}위 {artist}-{title}에서 가사 정보 크롤링 실패!!!!!!')
                        continue

                    # 크롤링에 성공한 경우
                    html = req.text
                    parsed = BeautifulSoup(html, 'html.parser')
                    try:
                        lyricsText = parsed.find('div', {'class': 'lyric'}).text
                    # 위의 규칙으로
                    except AttributeError:
                        print(f'파싱 실패(CODE {req.status_code}): {dt}) {rank}위 {artist}-{title}')
                        print(f'URL: {DETAIL_URL}')
                    else:
                        # 가사가 비어 있는 경우 다음 파일로 넘어감
                        if not lyricsText:
                            print(f'######{dt}) {rank}위 {artist}-{title}에서 가사 파싱 실패######')
                        else:
                            with open('./lyricsdata/' + lyricsFilename, mode='w', encoding='utf-8') as lyricsFile:
                                lyricsFile.write(lyricsText)
                                time.sleep(5)