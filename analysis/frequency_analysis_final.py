# -*- encoding: utf-8 -*-
"""
빈도수 분석
"""
import os
from matplotlib import pyplot as plt
import numpy as np

# token이 words에 있는 단어를 하나라도 가지고 있는지 검사하는 함수
def contains(words, token):
    for word in words:
        word = word.strip()
        if word in token:
            return True
        if word.lower() in token:
            return True
        if word.upper() in token:
            return True
    return False

if __name__ == '__main__':
    # crawler 디렉토리의 경로를 저장
    CRAWLER_PATH = os.path.join('..', 'crawler')

    # 곡 정보가 담긴 파일명의 모음
    lyricsFilenames = os.listdir(os.path.join(CRAWLER_PATH, 'lyricsdata'))

    # 각 차트 파일별로 곡 정보를 받아옴
    chartFilenames = os.listdir(os.path.join(CRAWLER_PATH, 'melon_chartdata'))

    # 빈도수 분석을 수행할 단어
    # targetWords = input('빈도수 분석을 수행할 단어들을 공백을 기준으로 나누어 입력하세요: ').split()
    targetWords = ['사랑', '좋', 'love', 'loves', 'loved', 'loving']

    # 차트에 해당 songId가 몇번 등장했는지 계산
    songIdFreq = dict()

    # 이론상 가능한 클러스터의 최대 개수
    MAX_DATA_CLUSTER_SIZES = [10000]
    sumChartScorePairs = list(dict() for _ in range(len(MAX_DATA_CLUSTER_SIZES)))
    frequencyPerSongIdPairs = list(dict() for _ in range(len(MAX_DATA_CLUSTER_SIZES)))
    songIdCounter = {}
    songIdRank = {}
    done = 0

    for chartFilename in chartFilenames:
        done += 1
        print(f'분석 시작: {chartFilename} / {done / len(chartFilenames) * 100}%')
        with open(os.path.join(CRAWLER_PATH, 'melon_chartdata', chartFilename), mode='r',
                  encoding='utf-8') as chartFile:
            for line in chartFile.readlines():
                try:
                    rank, songId, artist, title = line.rstrip().split('\t')
                    rank = int(rank)
                # 하나라도 누락된 경우 건너뜀
                except (ValueError, TypeError):
                    continue

                # 해당 songId를 가지는 파일을 검색
                try:
                    lyricsFilename = list(filter(lambda fn: fn.startswith(songId), lyricsFilenames))[0]
                # 해당 songId를 가지는 파일이 없다면 건너뜀
                except IndexError:
                    continue

                if songId not in songIdRank.keys():
                    songIdCounter[songId] = 1
                    songIdRank[songId] = 0
                else:
                    songIdCounter[songId] += 1
                    songIdRank[songId] += rank

                for i in range(len(MAX_DATA_CLUSTER_SIZES)):
                    MAX_DATA_CLUSTER_SIZE = MAX_DATA_CLUSTER_SIZES[i]

                    # {songId: 음원 차트 최대 성적(가장 작은 순위값)}
                    sumChartScore = sumChartScorePairs[i]
                    # {songId: 빈도값}
                    frequencyPerSongId = frequencyPerSongIdPairs[i]
                    # 만약 해당 songId를 가지는 곡의 빈도수 분석을 이미 마쳤다면 다시 수행하지 않음
                    if songId not in frequencyPerSongId.keys():
                        # 가사 파일 열기
                        with open(os.path.join(CRAWLER_PATH, 'lyricsdata', lyricsFilename), mode='r',
                                  encoding='utf-8') as lyricsFile:
                            lines = lyricsFile.readlines()
                            rawLyrics = ' '.join(lines)
                            words = rawLyrics.split(' ')
                            lenTargetContains = len(list(filter(lambda w: contains(targetWords, w), words)))
                            frequencyPerSongId[songId] = round((lenTargetContains / len(words)) * MAX_DATA_CLUSTER_SIZE)

                    # 차트 최고 성적 갱신
                    if songId in sumChartScore.keys():
                        sumChartScore[songId] += rank
                        songIdFreq[songId] += 1
                    else:
                        sumChartScore[songId] = rank
                        songIdFreq[songId] = 1

    print(f'Data Cluster size별 데이터 분포 분석 완료(Cluster size: {MAX_DATA_CLUSTER_SIZES})')
    for i in range(len(MAX_DATA_CLUSTER_SIZES)):
        MAX_DATA_CLUSTER_SIZE = MAX_DATA_CLUSTER_SIZES[i]

        # {frequency: chartSum}
        totalChartPerFrequency = [0 for _ in range(MAX_DATA_CLUSTER_SIZE)]
        frequencyPerSongId = frequencyPerSongIdPairs[i]
        sumChartScore = sumChartScorePairs[i]
        sumChartScore = {songId: sumChartScore[songId]/songIdFreq[songId] for songId in songIdFreq.keys()}

        print(f'\n{i+1}. Size {MAX_DATA_CLUSTER_SIZE}: ')

        print(f'{len(set(frequencyPerSongId.values()))}개의 클러스터 생성 완료')
        print(f'가장 Frequency Value가 높은 차트 데이터의 Frequency Value: {max(set(frequencyPerSongId.values()))}')

        # counter의 각 요소는 해당 frequency를 가지는 차트 데이터가 들어 있음
        # {idx}의 위치에는 frequency가 counter[idx]인 차트 데이터의 개수가 있음
        # 단, 차트 최고 성적만 데이터로 취급하므로 전체 데이터보다는 적음
        counter = [0 for _ in range(MAX_DATA_CLUSTER_SIZE)]
        for freq in frequencyPerSongId.values():
            counter[freq] += 1
        maxFrequency = max(counter[1:])
        print(f'가장 많은 차트 데이터가 속해 있는 Cluster: {counter.index(maxFrequency)}')

        for songId in frequencyPerSongId.keys():
            freq = frequencyPerSongId[songId]
            rank = sumChartScore[songId]
            totalChartPerFrequency[freq] += rank
        avrPerFrequency = totalChartPerFrequency[:]

        for i in range(len(counter)):
            cnt = counter[i]
            try:
                avrPerFrequency[i] /= cnt
            except ZeroDivisionError:
                avrPerFrequency[i] = 101

        # 가장 마지막 0이 아닌 값의 뒤에 있는 모든 Frequency가 0인 값들을 잘라냄
        lastIdx = MAX_DATA_CLUSTER_SIZE-1
        while counter[lastIdx] == 0:
            lastIdx -= 1

        # 데이터 분포 확
        # plt.title(f"MAX_DATA_CLUSTER_SIZE = {MAX_DATA_CLUSTER_SIZE}")
        # scatter = plt.scatter([i for i in range(1, lastIdx+1)], avrPerFrequency[1:lastIdx+1])
        # plt.xlabel('Frequency * MAX_DATA_CLUSTER_SIZE')
        # plt.ylabel('Average Rank')
        # plt.show()

        xData = [str(i) for i in range(lastIdx+1)]
        yData = list(map(lambda s: str(s), avrPerFrequency[:lastIdx+1]))

    xData = [int(x) for x in xData]
    yData = [float(x) for x in yData]
    remove_idx = []
    for i in range(len(yData)):
        yData[i] = float(yData[i])
        if yData[i] >= 80.0:
            yData[i] = 101.0
            remove_idx.append(i)

    # 무의미한 값들 제거
    cnt = 0
    for i in remove_idx:
        del xData[i - cnt], yData[i - cnt]
        cnt += 1


    # 대조군 생성
    count_x = []
    count_y = []
    for chartFilename in chartFilenames:
        # 대조군 데이터는 년이 0으로 끝날 경우 6월, 이 5로 끝날 경우 12월
        year = int(chartFilename[:4])
        month = int(chartFilename[5:7])
        if((year % 10 == 0 and month % 12 == 6) or (year % 10 == 5 and month % 12 == 0)):
            pass
        else:
            continue
        with open(os.path.join(CRAWLER_PATH, 'melon_chartdata', chartFilename), mode='r',
                  encoding='utf-8') as chartFile:
            for line in chartFile.readlines():
                try:
                    rank, songId, artist, title = line.rstrip().split('\t')
                    rank = int(rank)
                # 하나라도 누락된 경우 건너뜀
                except (ValueError, TypeError):
                    continue

                # 해당 songId를 가지는 파일을 검색
                try:
                    lyricsFilename = list(filter(lambda fn: fn.startswith(songId), lyricsFilenames))[0]
                # 해당 songId를 가지는 파일이 없다면 건너뜀
                except IndexError:
                    continue
                if frequencyPerSongId[songId] != 0:
                    count_x.append(frequencyPerSongId[songId])
                    count_y.append(songIdRank[songId] / songIdCounter[songId])


    # MSE 및 근사 확인 / MAE로 대체
    # degree = [1, 2, 3, 5, 10, 30, 50, 86]
    # for i in degree:
    #     fp1 = np.polyfit(xData, yData, i)
    #     f1 = np.poly1d(fp1)
    #     mse = 0
    #     for j in range(len(xData[1:])):
    #         mse += (f1(xData[j]) - yData[j]) ** 2
    #     mse /= len(xData[1:])
    #     plt.scatter(xData[1:], yData[1:], label='Imputation data', color='y', alpha=0.3)
    #     plt.plot(xData[1:], f1(xData[1:]), color='r', label='Polyfit data')
    #     plt.title('Polyfit {}, MSE {}'.format(i, mse))
    #     plt.xlabel('Frequency * MAX_DATA_CLUSTER_SIZE')
    #     plt.ylabel('Average Rank')
    #     plt.show()

    # MAE 및 근사 확인
    degree = [1, 2, 3, 5, 10, 30, 50, 86]
    for i in degree:
        fp1 = np.polyfit(xData, yData, i)
        f1 = np.poly1d(fp1)
        mae = 0
        for j in range(len(xData[1:])):
            mae += abs(f1(xData[j]) - yData[j])
        mae /= len(xData[1:])
        # MAE 및 근사 확인
        # plt.scatter(xData[1:], yData[1:], label='Imputation data', color='y', alpha=0.3)
        # plt.plot(xData[1:], f1(xData[1:]), color='r', label='Polyfit data')
        # plt.title('Polyfit {}, MAE {}'.format(i, mse))
        # plt.xlabel('Frequency * MAX_DATA_CLUSTER_SIZE')
        # plt.ylabel('Average Rank')
        # plt.show()

    # 모델링 검증 및 대조군 MAE 계산
    fp1 = np.polyfit(xData, yData, 86)
    f1 = np.poly1d(fp1)
    mae = 0
    for j in range(len(count_x)):
        mae += abs(f1(count_x[j]) - count_y[j])
    mae /= len(count_x)

    plt.scatter(count_x, count_y, label='correct', color='g', alpha=0.5)
    plt.scatter(count_x, f1(count_x), label='count', color='b', alpha=0.3)
    plt.plot(xData[1:], f1(xData[1:]), color='r', label='Polyfit data')
    plt.title('Data verification')
    plt.xlabel('Frequency * MAX_DATA_CLUSTER_SIZE')
    plt.ylabel('Average Rank')
    plt.show()
