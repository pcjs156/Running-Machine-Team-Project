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
    done = 0
    for chartFilename in chartFilenames:
        # 2021년 데이터는 대조군으로 사용해야 하므로, 검사하지 않음
        if chartFilename.startswith('2021'):
            continue
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

        plt.title(f"MAX_DATA_CLUSTER_SIZE = {MAX_DATA_CLUSTER_SIZE}")
        scatter = plt.scatter([i for i in range(1, lastIdx+1)], avrPerFrequency[1:lastIdx+1])
        plt.xlabel('Frequency * MAX_DATA_CLUSTER_SIZE')
        plt.ylabel('Average Rank')
        plt.show()

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

    # 데이터 오른쪽 축 잘라낼꺼면 주석 제거
    # xData = xData[:400]
    # yData = yData[:400]

    # 무의미한 값들 삭제
    cnt = 0
    for i in remove_idx:
        del xData[i - cnt], yData[i - cnt]
        cnt += 1

    sum = 0
    avg_y = []
    for i in range(len(yData)):
        if yData[i] == 101:
            x = sum / len(avg_y)
            avg_y.append(x)
            # sum += (x)
        else:
            avg_y.append(yData[i])
            sum += yData[i]

    plt.scatter(xData, avg_y)
    plt.title('MEAN_IMPUTATION')
    plt.xlabel('Frequency * MAX_DATA_CLUSTER_SIZE')
    plt.ylabel('Average Rank')
    plt.show()

    # 대조군 데이터
    # control_target = ['33239419@아이유@Celebrity.txt', '33295747@소정 (레이디스 코드)@함께 했는데 이별은 나 혼자인 거야.txt',
    #                   '33260801@허각@고백 (바른연애 길잡이 X 허각).txt', '33372785@아이유@돌림노래 (Feat. DEAN).txt']
    # control_target_rank = [1, 44, 21, 25]
    # control_target_contains = []
    # for controlFilename in control_target:
    #     with open(os.path.join(CRAWLER_PATH, 'lyricsdata', controlFilename), mode='r',
    #               encoding='utf-8') as lyricsFile:
    #         lines = lyricsFile.readlines()
    #         rawLyrics = ' '.join(lines)
    #         words = rawLyrics.split(' ')
    #         lenTargetContains = len(list(filter(lambda w: contains(targetWords, w), words)))
    #         control_target_contains.append(round((lenTargetContains / len(words)) * MAX_DATA_CLUSTER_SIZE))



    # for i in range(1, 6):
    i = 8
    fp1 = np.polyfit(xData, avg_y, i)
    f1 = np.poly1d(fp1)

    plt.scatter(xData, avg_y, label='Imputation data', color='y')
    plt.plot(xData, f1(xData), lw=2, color='r', label='Polyfit data')
    plt.title('Polyfit {}'.format(i))
    plt.xlabel('Frequency * MAX_DATA_CLUSTER_SIZE')
    plt.ylabel('Average Rank')
    plt.show()



