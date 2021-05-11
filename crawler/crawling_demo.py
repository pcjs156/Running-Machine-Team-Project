# -*- encoding: utf-8 -*-
"""
크롤러 데모 프로그램
가온 주간 차트 순위 데이터를 파싱해 저장함
"""

import os
from datetime import datetime

import requests
from bs4 import BeautifulSoup

def get_url_with_param(base: str, params: dict) -> str:
    if base[-1] != '?':
        base += '?'

    for k, v in params.items():
        base += f'&{k}={v}'

    return base

if __name__ == '__main__':
    # 전역 변수 설정
    GAON_WEEKLY_CHART_URL = 'http://mobile.gaonchart.co.kr/musicStreaming.gaon?'
    HEADER = {
        'User-Agent':
            'ozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.272 Whale/2.9.117.21 Safari/537.36'
    }

    # =========================================================================
    # 크롤링 가능한 연도/주차를 찾음
    pre_request = requests.get(GAON_WEEKLY_CHART_URL, headers=HEADER)
    print(f'응답 코드: {pre_request.status_code}')
    if pre_request.status_code == 200:
        print('크롤링 가능 연도/주차 탐색 시작')
        html = pre_request.text
        parsed = BeautifulSoup(html, 'html.parser')

        # select #chart_week_select 검색
        chart_week_select = parsed.find('select', {'id': 'chart_week_select'})
        # select#chart_week_select > option의 맨 첫번째 자식 태그는 항상 '<option value>기간</option>' 임
        options = chart_week_select.find_all('option')[1:]

        # key: 연도(int), value: 주차(int)
        year_weeks = dict()
        for option in options:
            # '<option value="202110">2021년 10주차</option>'의 형태로 저장되어 있으므로,
            # value attribute로부터 연도와 주차 정보를 정수로 저장함
            raw_year_week: str = option.attrs['value']
            year = int(raw_year_week[:4])
            week = int(raw_year_week[4:])

            if year not in year_weeks.keys():
                year_weeks[year] = [week]
            else:
                year_weeks[year].append(week)

        # 크롤링할 주차별 차트 수 총계
        total_weeks_cnt = 0
        for year, weeks in year_weeks.items():
            total_weeks_cnt += len(weeks)

        print('크롤링 가능 연도/주차 탐색 완료!')
        print(f'크롤링할 주차별 차트 수: {total_weeks_cnt}')
        print('=' * 30)

        # =========================================================================
        print('크롤링 시작!')

        # 에러가 한 번이라도 발생하는 경우, 해당 변수를 True로 전환함
        error_occured = False
        error_logs = list()

        # 가장 오래전부터 크롤링
        sorted_years = sorted(year_weeks.keys())

        # 데이터를 저장할 딕셔너리
        # key: 연도, value: {주차:
        #                       [{rank: 1, title: (1위 곡명), artist: (1위 가수명)},
        #                        {rank: 2, title: (2위 곡명), artist: (2위 가수명)}, ...], ...}
        record = {year: dict() for year in sorted_years}

        # 현재 몇주차까지 크롤링을 완료했는지 확인하기 위한 변수
        week_cnt = 0
        # 연도별 주차를 parameter로 전달해 데이터를 가져옴
        for year in year_weeks.keys():
            print(f'{year}년 크롤링 시작...')
            # 오래된 주차부터 크롤링
            sorted_weeks = sorted(year_weeks[year])

            for week in sorted_weeks:
                CHART_FILE_NAME = f'./data/{year}년 {week}주차 차트.txt'
                # 이미 파일이 존재하는 경우 삭제하고 다시 생성함
                if os.path.isfile(CHART_FILE_NAME):
                    os.remove(CHART_FILE_NAME)
                with open(CHART_FILE_NAME, mode='w', encoding='utf-8') as f:
                    f.write(CHART_FILE_NAME + '\n')

                week_cnt += 1
                print(f'{year}년 {week}주차 [{week}/{len(sorted_weeks)}]')

                print(('#' * int(week_cnt / total_weeks_cnt * 100)) + ('.' * int((total_weeks_cnt-week_cnt) / total_weeks_cnt * 100)) \
                      + f' | TOTAL {week_cnt / total_weeks_cnt * 100}%')

                # nationGbn=T&serviceGbn=S1040&targetTime=37&hitYear=2020&termGbn=week
                param = {
                    'nationGbn': 'T',
                    'serviceGbn': 'S1040',
                    'termGbn': 'week',
                    'targetTime': week,
                    'hitYear': year,
                }
                url = get_url_with_param(GAON_WEEKLY_CHART_URL, param)
                request = requests.get(url, headers = HEADER)
                html = request.text
                parsed = BeautifulSoup(html, 'html.parser')

                # article.musicList > ul
                music_list = parsed.find('article', {'class': 'musicList'})
                music_list_ul = music_list.find('ul')
                li_a_list = music_list_ul.find_all('li')

                # 파싱에 성공한 경우 데이터를 저장
                if li_a_list:
                    record[year][week] = []
                    for li in li_a_list:
                        # 순위
                        rank = int(li.find('strong', {'class': 'rank'}).text)
                        # 제목
                        title = li.find('strong', {'class': 'tit'}).text.rstrip()
                        # 아티스트: '아티스트 | 앨범명' 형태로 되어 있어 아티스트만 따로 떼어냄
                        artist = str(li.find('span', {'class': 'txt'}))

                        START_TAG = '<span class="txt">'
                        START_TAG_LEN = len(START_TAG)
                        FINISH_TAG_IDX = artist.find('<i>')
                        artist = artist[artist.find(START_TAG)+START_TAG_LEN:FINISH_TAG_IDX]
                        artist = artist.strip()

                        # 데이터 저장
                        record[year][week].append({
                            'rank': rank,
                            'title': title,
                            'artist': artist
                        })

                    # 파싱된 데이터가 없는 경우, 생성된 파일을 삭제함
                    if not record[year][week] and os.path.isfile(CHART_FILE_NAME):
                        print(f'{CHART_FILE_NAME}의 내용이 없어 삭제합니다.')
                        os.remove(CHART_FILE_NAME)
                    with open(CHART_FILE_NAME, mode='a', encoding='utf-8') as f:
                        for data in sorted(record[year][week], key=lambda d: d['rank']):
                            f.write(f"{data['rank']}\t{data['artist']}\t{data['title']}\n")
                # 파싱에 실패한 경우 에러 로그를 남김
                else:
                    print(f'{year}년 {week}주차 이상 발생!')
                    print('')
                    error_logs.append(f'{year}년 {week}주차 이상 발생')
                    error_occured = True



        # 에러가 발생했을 경우 에러 로그 파일을 저장함
        if error_occured:
            # 에러 로그를 작성하기 위한 파일 생성
            error_log_filename = datetime.now().strftime('./error_logs/error_log_%Y년_%m월_%d일_%H시_%M분_%S초.txt')
            with open(error_log_filename, mode='w', encoding='utf-8') as f:
                f.write('\n'.join(error_logs))
