# %%
import os
import requests
from dotenv import load_dotenv
import datetime
import csv

# %%
# .env 파일로 Steam_API, Steam_id 불러옴
load_dotenv()

# %%
# 환경변수 값 불러오기
API_KEY = os.getenv("STEAM_API_KEY")
STEAM_ID = os.getenv("STEAM_USER_ID")
ITAD_API_KEY = os.getenv("ITAD_API_KEY")

# %%
# Steam 매개변수 전달 방식 : URL Query Parameters 이기에, 키값을 파라미터 지정
# Steam 공식 API 문서 참고해 GetAppPriceInfo url을 받아옴.
url = "https://partner.steam-api.com/ISteamUser/GetAppPriceInfo/v1/"
params = {
    'key': API_KEY,
    'steamid':STEAM_ID,
    'appids':{'2358720'},
}

# %%
# 스팀 상점 '가격'관련 API 
#1. Lookup Game : 게임정보, 자체 ID 정보
url_pr1 = "https://api.isthereanydeal.com/games/lookup/v1"

#2. Prices : 게임 가격

#3. Active shops : 해당 국가에서 제공하는 상점

headers = {
    "ITAD-API-Key": ITAD_API_KEY,
}

params_pr = {
    "appid": 2358720,
}


# %%
#  이전 실행결과가 남았을 수도 있으니 값 초기화
response_steam = None
response_pr1 = None
Steam_data = None
price_data = None

#  requests해 API 불러오기
#response_steam = requests.get(url, params=params)
response_pr1 = requests.get(url_pr1, headers=headers,params=params_pr)
print("HTTP 상태:", response_pr1.status_code)
#print("HTTP 상태:", response_steam.status_code)

# %%
if response_pr1 is not None:

    #http 코드가 200~300인경우 (정상)
    if 200 <= response_pr1.status_code <=300:

        #json 파일로 저장
        price_data = response_pr1.json()
        print("Price 데이터 Json 저장")

    # 비정상인 경우
    else:
        print("ITAD 정상 응답이 업습니다.")

# %%
# response가 data안에 제대로 있는지 확인.
if price_data is not None:

    # 제대로 있는 경우, 데이터 출력
    print(price_data)
    print("스팀 데이터 수신 성공")

    #Docker 추가 예정


    # DB 저장
# response가 data안에 없을 경우.
else:
    print("스팀 데이터가 존재하지 않습니다.")


