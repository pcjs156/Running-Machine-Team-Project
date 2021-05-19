# -*- encoding: utf-8 -*-
"""
크롤러 데모 프로그램
멜론 월별 차트 순위 데이터를 파싱해 저장함
"""

import os
import sys
from datetime import datetime
from time import sleep
from math import floor

import requests
from bs4 import BeautifulSoup

from utils import *

def removeInvalidCharacters(string):
    invalidCharacters = ["\\", "/", ":", "*", "?", "\"", "<", ">", "|"]
    while True:
        hasInvalidCharacter = False
        for c in invalidCharacters:
            if c in string:
                string = c.replace(c, '')
                hasInvalidCharacter = True
        if not hasInvalidCharacter:
            break
    return string

if __name__ == '__main__':
    # https://www.melon.com/chart/search/list.htm?chartType=MO&age=2020&year=2021&mon=04&classCd=DM0000&moved=Y
    # 전역 변수 설정
    # 쿠키는 임의로 넣어줘야 함 ㅠ
    HEADER = {
        'User-Agent':
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.272 Whale/2.9.117.21 Safari/537.36',
        'Cookie':
            'PCID=16201318686845976249684; PC_PCID=16201318686845976249684; melonlogging=1000002502; mainPop=2021%3A05%3A18%2023%3A59%3A59; POC=WP10'
    }

    # 현재 파싱되어 있으며, 비어 있지 않은 정상 처리된 차트 데이터는 크롤링하지 않음
    parsedFilenames = list(filter(lambda p: p.endswith('.txt'), os.listdir(os.path.join('.', 'melon_chartdata'))))
    parsedFilenames = list(filter(lambda p: not isEmptyFile(os.path.join('.', 'melon_chartdata', p)), parsedFilenames))

    for year in range(1984, 2021+1):
        # 2021년인 경우 차트 데이터가 4월까지밖에 없으므로 범위를 수정함
        if year == 2021:
            monthUrlList = getMonthURLList(2021, 1, 4)
        # 1984년인 경우 차트 데이터가 3월부터 있으므로 범위를 수정함
        elif year == 1984:
            monthUrlList = getMonthURLList(1984, 3, 12)
        else:
            monthUrlList = getMonthURLList(year)

        for month, url in monthUrlList:
            # 차트 데이터를 파일명 "yyyy_mm_dd_mellon_chart.txt"로 저장한다.
            chartFileName = f"%4d_%02d_mellon_chart.txt" % (year, month)
            # 이미 파싱된 파일인 경우, 따로 크롤링하지 않고 다음 차트로 넘어간다.
            if chartFileName in parsedFilenames:
                continue

            req = requests.get(url, headers=HEADER)
            if req.status_code != 200:
                print(f'WARNING) 다음 URL에서 status code가 {req.status_code}입니다.')
                print(f'>>> {url}')
                continue
            else:
                parsed = BeautifulSoup(req.text, 'html.parser')
                # 1위~50위 데이터와 51위~100위 데이터를 합침
                chartDatas1_50 = parsed.find_all('tr', {'class':'lst50'})
                chartDatas51_100 = parsed.find_all('tr', {'class':'lst100'})
                chartDatas = chartDatas1_50 + chartDatas51_100
                # 만약 100위/50위 파싱에 실패하는 경우 HTML 데이터가 정상적으로 응답되지 않은 것이므로 알림
                if not chartDatas:
                    print(f'ERROR) {year}년 {month}월 HTML Response에서 차트 순위를 파싱할 수 없습니다.')
                    print(f'>>> {url}')
                    continue
                # 파싱에 성공한 경우 차트 데이터의 개수를 보여줌
                else:
                    print(f'>>> {year}년 {month}월: {len(chartDatas)}건')

                fullPath = os.path.join('.', 'melon_chartdata', chartFileName)
                with open(fullPath, mode='w', encoding='utf-8') as chartFile:
                    # 데이터의 각 행은 "{랭킹}\t{songId}\t{아티스트}\t{곡 제목}\n"으로 한다.
                    # 이때 파일명으로 사용 불가능한 문자는 모두 삭제한다. (\ / : * ? " < > |)
                    lines = []
                    # 해당 연 월의 차트 목록 파싱
                    for i in range(len(chartDatas)):
                        chartData = chartDatas[i]
                        rank = i+1
                        songId = chartData.find('input', {'type': 'checkbox'}).attrs['value']
                        rawTitle = chartData.find('input', {'type': 'checkbox'}).attrs['title']
                        trashIdx = rawTitle.find(' 곡 선택')
                        # 윈도우에서 파일명으로 사용할 수 없는 모든 문자들은 삭제함
                        title = removeInvalidCharacters(rawTitle[:trashIdx])
                        artist = removeInvalidCharacters(chartData.find('a', {'class': 'fc_mgray'}).text)
                        lines.append(f'{rank}\t{songId}\t{artist}\t{title}')
                    if lines:
                        chartFile.write('\n'.join(lines))
                    else:
                        print(f'ERROR) {year}년 {month}월 차트 데이터에서 곡 정보를 파싱할 수 없습니다.')
                        print(f'>>> {url}')

                print(f'{year}년 {month}월 차트 데이트 파싱 완료')
                sleep(7)
