# %%
import os
import requests
from dotenv import load_dotenv
import datetime
import csv
import json
from pathlib import Path

# %%
#작업 파일 폴더 지정
project_file = Path.cwd()

#해당 폴더의 env 파일 조인
env_file = project_file / ".env"

#파일을 변수에 담기 (True/False 반환)
env_loaded = load_dotenv(env_file)

if env_loaded is False:
    raise FileNotFoundError(f".env파일을 찾을 수 없습니다 : {env_file}")

# %%
# 환경변수 값 불러오기
API_KEY = os.getenv("STEAM_API_KEY")
STEAM_ID = os.getenv("STEAM_USER_ID")
ITAD_API_KEY = os.getenv("ITAD_API_KEY")

# %%
# 내가 불러올 게임 List (스팀 http 주소 내 게임 넘버링) - 리뷰 불러오는 데 사용.
game_id = 2358720

# %%
# Steam 게임 정보 API 
    # 매개변수 전달 방식 : URL Query Parameters 이기에, 키값을 파라미터 지정
Steam_app_url = "https://api.steampowered.com/IStoreService/GetAppList/v1/"

# Steam 앱 List 파라미터 ( 참고문서 링크 :https://partner.steamgames.com/doc/webapi/IStoreService)
params_Steam = {
    'key':API_KEY,
    #key 외의 정보는 json.dumps에 담기.
    'input_json':json.dumps({
        'include_games':True,
        'include_dlc':False,
        # ID 순서로 반환되므로, game_id 1개 전부터.
        'last_appid':game_id -1,
        'max_results':1,
    })
}

# %%
#Steam 게임 리뷰 API
if game_id is not None:
    Steam_review_url = f"https://store.steampowered.com/appreviews/{game_id}"


# 스팀 리뷰 파라미터 형식에 맞게 적용. (참고문서 링크 : https://partner.steamgames.com/doc/store/getreviews)
params_review = {

    #json 형식으로 요청,
    "json" : 1,
    "filter":"all",
    # 전체 언어
    "language":"all",
    #n일 전까지 리뷰 범위 (최대값인 1년으로 지정.)
    "day_range":365,
    # 리뷰 커서 값 (20개씩 반환됨.)
    "cursor":"*",
    # 리뷰 긍정/부정 모두
    "review_type":"all",
    #게임 구매 유형 (스팀에서 구매한 이용자들만)
    "purchase_type":"steam",
    #페이지당 개수 (20개)
    "num_per_page":20,
    #필터 (주제와 관련없는 리뷰) 0 : 포함 1 : 미포함
    "filter_offtopic_activity":1,
}

# %%
# 스팀 상점 '가격'관련 API 
#1. Lookup Game : 게임정보, 자체 ID 정보
url_lookup = "https://api.isthereanydeal.com/games/lookup/v1"

#2. Prices : 게임 가격

#3. Active shops : 해당 국가에서 제공하는 상점

headers = {
    "ITAD-API-Key": ITAD_API_KEY,
}

params_lookup = {
    "appid": game_id,
}

# %%
#  이전 실행결과가 남았을 수도 있으니 값 초기화
response_game_list = None
response_game_review = None
response_lookup = None

Steam_app_data = None
Steam_review_data = None
lookup_data = None

#  requests해 API 불러오기
response_game_list = requests.get(Steam_app_url, params=params_Steam,timeout=20)
response_game_review = requests.get(Steam_review_url, params=params_review,timeout=20)
response_lookup = requests.get(url_lookup, headers=headers,params=params_lookup,timeout=20)


#requests해 API 불러오기
# response는 HTTP 응답이기에 200~300 사이인경우를 먼저 확인.
if 200 <= response_game_list.status_code <300:
    # 정상인경우 json파일로 data 변수에 저장.
    Steam_app_data = response_game_list.json()

    
    apps = Steam_app_data["response"]["apps"]
    #대상 ID가 목록에 없으면 다음 게임이 반환될 수 있어, 일치 여부를 확인.
    if not apps or apps[0]["appid"] != game_id:
        Steam_app_data = None
        print("요청한 game_id를 Steam 게임 목록에서 찾기 못했습니다.")
else:
    print("Steam 게임 list HTTP 오류", response_game_list.status_code)



# 리뷰 HTTP도 똑같이 검사.
if 200 <= response_game_review.status_code < 300:
    Steam_review_data = response_game_review.json()
else:
    print("Steam 리뷰 HTTP 오류:", response_game_review.status_code)

# ITAD의 lookup 데이터 HTTP 검사.
if 200 <= response_lookup.status_code < 300:
    lookup_data = response_lookup.json()
else:
    print("ITAD lookup 데이터 HTTP 오류:", response_lookup.status_code)


# %%
# 데이터들이 제대로 들어갔는지 확인하기.

if Steam_app_data is not None:

        # 제대로 있는 경우, 데이터 출력
        print(Steam_app_data)
        print("Steam_app 데이터 수신 성공")


    # response가 data안에 없을 경우.
else:
    print("Steam_app 데이터가 존재하지 않습니다.")

if  Steam_review_data is not None:

        # 제대로 있는 경우, 데이터 출력
        print(Steam_review_data)
        print(" 스팀 리뷰 데이터 수신 성공")

    # response가 data안에 없을 경우.
else:
    print("스팀 리뷰 데이터가 존재하지 않습니다.")


if lookup_data is not None:

        # 제대로 있는 경우, 데이터 출력
        print(lookup_data)
        print("lookup 데이터 수신 성공")

    # response가 data안에 없을 경우.
else:
    print(" lookup 데이터가 존재하지 않습니다.")

# %%
#Docker 연결 코드

# psycopg2 임포트
import psycopg2

# Docker에 넣을 db_password 값 불러옴
db_password = os.getenv("DB_PASSWORD")
if not db_password:
    raise ValueError("DB_PASSWORD 환경변수를 확인해주세요.")

# env 파일 세팅
settings = {
    "host": os.getenv("DB_HOST", "127.0.0.1"),
    "port":os.getenv("DB_PORT", "5432"),
    "dbname":os.getenv("DB_NAME","steam_data"),
    "user":os.getenv("DB_USER","postgres"),
    "password":db_password,
    "connect_timeout":10, #10초 후 타임아웃
}

conn = None
#Docker 연결 실행

try:
    #env로 연결
    conn = psycopg2.connect(**settings)
    conn.set_session(readonly=True, autocommit=True)
    
    with conn.cursor() as cur:
        #현재 데이터베이스, 유저 정보 확인
        cur.execute("SELECT current_database(), current_user;")
        database, user = cur.fetchone()

    print(database, user)

except psycopg2.Error:
    raise RuntimeError(
        "DB 연결 검사 실패: 컨테이너 실행 상태·포트·DB 환경변수 재확인 필요"
    )

finally:
    if conn is not None:
        conn.close()


