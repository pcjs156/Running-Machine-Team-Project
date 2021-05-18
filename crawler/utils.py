# -*- encoding: utf-8 -*-
from math import floor

def getAge(year):
    return floor(year / 10) * 10

def getMonthURLList(year: int, monthStart: int=1, monthEnd: int=12) -> list:
    """
    해당 연도의 monthStart월~monthEnd월까지의 데이터 URL을 리스트로 반환함
    """
    ret = []
    age = getAge(year) # 연대 (1980, 1990, ...)
    BASE_URL_FW = f'https://www.melon.com/chart/search/list.htm?chartType=MO&age={age}&year={year}&mon='
    BASE_URL_BW = '&classCd=DM0000&moved=Y'
    for m in range(monthStart, monthEnd+1):
        ret.append((m, BASE_URL_FW + "%02d" % m + BASE_URL_BW))

    return ret

def getDetailURL(songId: str) -> str:
    DETAIL_URL_FW = 'https://www.melon.com/song/detail.htm?songId='
    return DETAIL_URL_FW + songId

# 파일이 비어 있다면 True, 비어 있지 않다면 False를 반환하는 함수
def isEmptyFile(fullPath):
    with open(fullPath, mode='r', encoding='utf-8') as f:
        lines = f.readlines()
        # 비어 있는 파일이면 True
        if len(lines) == 0:
            return True
        # 비어 있지 않은 파일이면 False
        else:
            return False

def isFrontPartFilename(filename: str) -> bool:
    idx = filename.find('_')
    year = int(filename[:idx])
    # 1984~2002년을 전반부로 봄
    return 1984 <= year <= 2002