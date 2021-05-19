# -*- encoding: utf-8 -*-
import os
import time
from datetime import datetime as dt

import requests
from bs4 import BeautifulSoup

from utils import *

if __name__ == '__main__':
    # WARNING!!!!!!! Cookie Value 무조건 바꿔줘야 됨 !!!!!!!!!!!!!
    HEADER = {
        'User-Agent':
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.272 Whale/2.9.117.21 Safari/537.36',
        'Cookie':
            'PCID=16201318686845976249684; PC_PCID=16201318686845976249684; melonlogging=1000002502; mainPop=2021%3A05%3A18%2023%3A59%3A59; POC=WP10'
    }

    # 가사 데이터 파일 목록을 불러옴
    # 프로그램 실행 도중 크롤링이 완료되는 대로 파일명을 추가할 것이므로, list로 선언함(계속해서 파일 목록을 확인하지 않기 위해)
    lyricsFilenameList = os.listdir(os.path.join('.', 'lyricsdata'))

    # 가사 파싱중 발생하는 에러 로그를 파일에 씀
    now = dt.now()
    ERROR_LOG_FULLPATH = os.path.join('.', 'error_logs', f'{now.year}년 {now.month}월 {now.day}일 {now.hour}시 {now.minute}분 {now.second}초.txt')
    with open(ERROR_LOG_FULLPATH, mode='w', encoding='utf-8') as errorLogFile:
        pass

    # .txt로 끝나는 차트 데이터를 불러옴
    chartDataFilenames = list(filter(lambda fn: fn.endswith('.txt'), os.listdir(os.path.join('.', 'melon_chartdata'))))

    # 유빈: 전반부
    chartDataFilenames = list(filter(lambda fn: isFrontPartFilename(fn), chartDataFilenames))
    # 윤석: 후반부
    # chartDataFilenames = list(filter(lambda fn: not isFrontPartFilename(fn), chartDataFilenames))

    for i in range(len(chartDataFilenames)):
        filename = chartDataFilenames[i]
        print(f'>>> {filename} 크롤링 시작... ({(i+1)/len(chartDataFilenames)* 100}%)')
        with open(os.path.join('.', 'melon_chartdata', filename), mode='r', encoding='utf-8') as f:
            chartLines = list(map(lambda s: s.strip(), f.readlines()))
            for line in chartLines:
                # 순위, 아티스트, 제목이 탭 문자로 구분되어 있음
                chartInfo = line.strip().split('\t')
                try:
                    rank, songId, artist, title = chartInfo
                except ValueError:
                    rank, songId, artist, title = chartInfo + ['UNKNOWN' for _ in range(4-len(chartInfo))]
                    with open(ERROR_LOG_FULLPATH, mode='a', encoding='utf-8') as errorLogFile:
                        print(f'{dt.now()}) {rank}위 {artist}-{title}에서 ValueError 발생 -> UNKNOWN으로 대체')
                        errorLogFile.write(f'{dt.now()}) {rank}위 {artist}-{title}에서 ValueError 발생 -> UNKNOWN으로 대체\n')


                # 저장될 파일 이름은 "songId@아티스트명@곡명.txt"로 함
                lyricsFilename = songId + '@' + artist + '@' + title + '.txt'
                # 만약 해당 가사가 이미 크롤링되어 있다면, 다음 차트 목록으로 넘어감
                if lyricsFilename in lyricsFilenameList:
                    # 단, 크롤링에 실패해 파일이 비어 있을 수 있으므로 이 경우 다시 크롤링을 시도함
                    with open(os.path.join('.', 'lyricsdata', lyricsFilename), mode='r', encoding='utf-8') as lyricsFile:
                        if not lyricsFile.readlines():
                            print(f'{lyricsFilename}이 비어 있어 다시 크롤링을 시도합니다.')
                        else:
                            continue

                detailPageURL = getDetailURL(songId)
                # 응답 코드가 200일 때까지 총 5번 요청함
                for req_try in range(1, 6):
                    req = requests.get(detailPageURL, headers=HEADER)
                    if req.status_code != 200:
                        print(f'{dt.now()}) {rank}위 {artist}-{title}에서 가사 정보 status code != 200 발생({req.status_code})')
                        print('10초간 대기...')
                        print(f'>>>{detailPageURL}')
                        time.sleep(10)
                    else:
                        break

                # 요청을 5회 이상 보냈다면, 그냥 다음 파일로 건너뜀
                if req_try >= 5:
                    print(f'!!!!!!{dt.now()}) {rank}위 {artist}-{title}에서 가사 정보 크롤링 실패!!!!!!')
                    print(f'URL: {detailPageURL}')
                    with open(ERROR_LOG_FULLPATH, mode='a', encoding='utf-8') as errorLogFile:
                        errorLogFile.write(f'{dt.now()}) {rank}위 {artist}-{title}에서 가사 크롤링 실패(status code != 200)\n')
                    continue

                # 크롤링에 성공한 경우
                html = req.text.replace('<br>', ' ')
                parsed = BeautifulSoup(html, 'html.parser')
                try:
                    lyricsText = parsed.find('div', {'class': 'lyric'})
                # 위의 규칙으로
                except AttributeError:
                    print(f'파싱 실패(CODE {req.status_code}): {dt.now()}) {rank}위 {artist}-{title}')
                    print(f'URL: {detailPageURL}')
                    with open(ERROR_LOG_FULLPATH, mode='a', encoding='utf-8') as errorLogFile:
                        errorLogFile.write(f'{dt.now()}) {rank}위 {artist}-{title}에서 현재 규칙 기반 크롤링 실패\n')
                else:
                    # 가사가 비어 있는 경우 다음 파일로 넘어감
                    if not lyricsText:
                        print(f'######{dt.now()}) {rank}위 {artist}-{title}에서 가사 파싱 실패######')
                        with open(ERROR_LOG_FULLPATH, mode='a', encoding='utf-8') as errorLogFile:
                            errorLogFile.write(f'{dt.now()}) {rank}위 {artist}-{title}에서 가사 파싱 실패(성인인증 필요, 또는  없음)\n')

                    else:
                        with open('./lyricsdata/' + lyricsFilename, mode='w', encoding='utf-8') as lyricsFile:
                            pass
                        with open('./lyricsdata/' + lyricsFilename, mode='w', encoding='utf-8') as lyricsFile:
                            lyricsFile.write(lyricsText.get_text().strip())
                            lyricsFilenameList.append(lyricsFilename)
                    time.sleep(6)
