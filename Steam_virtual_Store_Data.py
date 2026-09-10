import datetime
import csv

# Steam 가상 테이블

## Steam 상점 내 게임 이름과 기본 가격 ('원'화기준)
game_price_table = {
    "Black Myth: Wukong": 64800,
    "Lies of P":64800,
    "ELDEN RING":64000
}

# 시뮬레이션 날짜
## 시뮬레이션은 실제 시간이 아닌, 가상의 시간으로 진행한다.

    #시작일 설정
start_date = datetime.date(2026, 1, 1)
    # 종료일 설정
end_date = datetime.date(2026, 12, 31)

    
# 현재 시간 변수
current_date = start_date

# 게임가격 변화 누적 변수
daily_price_log = []

# 현재 시간이 2026년 12월 31일이 될때까지 반복
while current_date <= end_date:


# ---------- 요일별 가격 적용 -----------------
    # 이벤트 조건 (요일별)
    day_of_week = current_date.weekday()

    # 주말인경우
    if(day_of_week == 5 or day_of_week == 6):
        #주말 할인 (20%)
        discount_rate = 0.8

    #평일인경우
    else:
        #기본 가격
        discount_rate = 1.0

# ------------ 할인율 가격 적용 ----------------

    #게임 이름과 가격을 모두 담을때까지 반복
    for game_name, price in game_price_table.items():

        #최종 가격 = 기본 가격 * 할인 계수
        final_price = price * discount_rate

        #현재 날짜, 게임 이름, 게임 가격을 연결해 daily_price_log에 넣기
        row_data = [current_date, game_name, final_price]
        daily_price_log.append(row_data)

    #현재 시간에 하루씩 더함
    current_date = current_date + datetime.timedelta(days=1)

#csv파일로 열기
with open('steam_discount_sim.csv', 'w', encoding='utf-8',newline='') as file:
    #열린 csv파일에 쓰기
    writer = csv.writer(file)
    #파일 헤더 붙이기
    writer.writerow(['Date', 'Game_Name','Price'])
    #날짜, 게임이름, 가격 데이터 저장
    writer.writerows(daily_price_log)
