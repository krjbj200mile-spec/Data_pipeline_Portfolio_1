# %%
import os
import requests
import pandas as pd
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
# 내가 불러올 게임 List (csv파일로 200개 게임 id목록 불러옴)
game_list = pd.read_csv(
    "steam_game_list_200_utf8.csv",
    encoding="utf-8-sig",
)

#전체 수집 개수
print(f"수집 대상 : {len(game_list)}개", flush=True)


for game_id in game_list["app_id"]:
    game_id = int(game_id)
    print(f"수집 대상 게임 ID : {game_id}", flush=True)

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
    #1. Lookup Game : ITAD의 게임정보 (자체 ID 정보)
    url_lookup = "https://api.isthereanydeal.com/games/lookup/v1"

    headers = {
        "ITAD-API-Key": ITAD_API_KEY,
    }

    params_lookup = {
        "appid": game_id,
    }

    #2. Prices : 게임 가격
    url_prices = "https://api.isthereanydeal.com/games/prices/v3"

    params_prices = {
        "country":"KR",
        "deals":False,
        "vouchers":False,
        "capacity":"0",
        "shops":"61",
    }

    #3. Active shops : 해당 국가에서 제공하는 상점
    url_active_shops = "https://api.isthereanydeal.com/service/shops/v1"

    params_active_shops = {
    }

    # %%
    #  이전 실행결과가 남았을 수도 있으니 값 초기화
    response_game_list = None
    response_game_review = None
    response_lookup = None

    Steam_app_data = None
    Steam_review_data = None
    lookup_data = None
    prices_data = None
    active_data =None

    #수집된 시각
    collected_at = None
    #데이터 기준 날짜
    snapshot_date = None
    #게임 아이디
    collected_game_id = game_id


    # API 요청 > 상태 확인 > JSON으로 받기
    requests_stage = "Steam 게임 목록"

    try:
        #requests해 API 불러오기
        response_game_list = requests.get(Steam_app_url, params=params_Steam,timeout=20)
        # response는 HTTP 응답이기에 200~300 사이인경우를 먼저 확인.
        if 200 <= response_game_list.status_code <300:
            # 정상인경우 json파일로 data 변수에 저장.
            Steam_app_data = response_game_list.json()
            apps = Steam_app_data["response"]["apps"]
            #대상 ID가 목록에 없으면 다음 게임이 반환될 수 있어, 일치 여부를 확인.
            if not apps or apps[0]["appid"] != game_id:
                raise ValueError("요청한 game_id를 Steam 게임 목록에서 찾기 못했습니다.")
        else:
            raise RuntimeError (f"Steam 게임 list HTTP 오류: {response_game_list.status_code}")

        # 리뷰 HTTP도 똑같이 검사.
        requests_stage = "Steam 리뷰"
        response_game_review = requests.get(Steam_review_url, params=params_review,timeout=20)
        if 200 <= response_game_review.status_code < 300:
            Steam_review_data = response_game_review.json()
        else:
            raise RuntimeError(f"Steam 리뷰 HTTP 오류: {response_game_review.status_code}")

        # ITAD의 lookup 데이터 HTTP 검사.
        requests_stage = "ITAD Lookup"
        response_lookup = requests.get(url_lookup, headers=headers,params=params_lookup,timeout=20)
        if 200 <= response_lookup.status_code < 300:
            lookup_data = response_lookup.json()
            if lookup_data.get("found") is not True:
                raise ValueError("ITAD에서 해당 Steam 게임을 찾지 못했습니다.")
            #lookupdata에 게임 ID 저장
            itad_game_id = lookup_data["game"]["id"]
        else:
            raise RuntimeError(f"ITAD lookup 데이터 HTTP 오류:{response_lookup.status_code}")

        # ITAD의 prices 데이터 HTTP 검사.
        requests_stage = "ITAD Prices"
        #JSON 파일로 게임 ID 받아옴 (해당 ID의 가격만 받기 위해) (price는 get이 아닌 post로 받기)
        response_prices = requests.post(url_prices, headers=headers, params=params_prices,json=[itad_game_id],timeout=20)
        if 200 <= response_prices.status_code < 300:
            prices_data = response_prices.json()
        else:
            raise RuntimeError(f"ITAD price 데이터 HTTP 오류:{response_prices.status_code}")

        # ITAD의 active 데이터 HTTP 검사.
        response_active = requests.get(url_active_shops, params=params_active_shops,timeout=20)
        if 200 <= response_active.status_code < 300:
            active_data = response_active.json()
        else:
            raise RuntimeError(f"ITAD active 데이터 HTTP 오류: {response_active.status_code}")

    except requests.Timeout:
        raise RuntimeError(f"{requests_stage}: 요청 시간이 초과됐습니다. 잠시 뒤 다시 실행하세요") from None
    except requests.ConnectionError:
        raise RuntimeError(
            f"{requests_stage}: 서버 연결에 실패했습니다. 인터넷 연결과 도메인의 DNS 조회를 확인하세요."
        ) from None
    except requests.RequestException:
        raise RuntimeError(f"{requests_stage}:HTTP 요청에 실패했습니다.") from None

    #수집한 시각을 현재로 설정
    collected_at = datetime.datetime.now(datetime.timezone.utc)
    kst = datetime.timezone(datetime.timedelta(hours=9))
    snapshot_date = collected_at.astimezone(kst).date()
    print("5개 API 응답 수신 완료.")


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


    if prices_data is not None:

            # 제대로 있는 경우, 데이터 출력
            print(prices_data)
            print("prices 데이터 수신 성공")

        # response가 data안에 없을 경우.
    else:
        print(" prices 데이터가 존재하지 않습니다.")

        
    if active_data is not None:

            # 제대로 있는 경우, 데이터 출력
            print(active_data)
            print("active 데이터 수신 성공")

        # response가 data안에 없을 경우.
    else:
        print(" active 데이터가 존재하지 않습니다.")

    # %%
    #Json 응답을 DataFrame으로 변경하기.
    # raw 데이터 프레임을 담을곳
    raw_df = None

    #받은 데이터 파일들을 하나로 묶기
    api_rows = [
        ["steam_app",json.loads(params_Steam["input_json"]), Steam_app_data],
        ["steam_reviews",params_review,Steam_review_data],
        ['itad_lookup',params_lookup,lookup_data],
        ['itad_prices',{"query":params_prices,'body':[itad_game_id]},prices_data],
        ['itad_acitve_shops',params_active_shops, active_data],
    ]

    raw_df = pd.DataFrame(api_rows, columns=["source","request_params","payload"])
    raw_df["game_id"] = collected_game_id
    raw_df["collected_at"] = collected_at
    raw_df["snapshot_date"] = snapshot_date

    print("DataFrame 행 수 :", len(raw_df))
    #값이 빈 목록인 가격 응답도 raw 원본이므로, 우선은 가격 0원으로 대체하지 않음.
    raw_df


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

        print("DB 연결 확인:", database, user)

    except psycopg2.Error:
        raise RuntimeError(
            "DB 연결 검사 실패: 컨테이너 실행 상태·포트·DB 환경변수 재확인 필요"
        ) from None
    except psycopg2.Error:
        raise RuntimeError("DB 연결 실패 : PostgreSQL 실행 상태, 포트, DB 환경변수를 확인하세요.") from None

    finally:
        if conn is not None:
            conn.close()

    # %%
    from psycopg2.extras import Json

    #DF로 만든 데이터 PG raw에 저장하기.
    conn = None
    inserted_count = 0
    db_step = "연결"

    try:
        conn = psycopg2.connect(**settings)
        # 자동 커밋 비활성화 (정상 확인 후 커밋)
        conn.set_session(readonly=False, autocommit=False)

        # 1. DB 연결 및 환경 설정
        # cur 라는 임시 테이블을 만듬
        with conn.cursor() as cur:
            db_step = "raw 테이블 준비"
            
            # 2. raw 스키마가 없는 경우 생성
            cur.execute("CREATE SCHEMA IF NOT EXISTS raw;")
            cur.execute(
                """CREATE TABLE IF NOT EXISTS raw.steam_api_response (
                raw_id BIGSERIAL PRIMARY KEY,
                game_id INTEGER NOT NULL,
                source TEXT NOT NULL,
                collected_at TIMESTAMPTZ NOT NULL,
                snapshot_date DATE NOT NULL,
                request_params JSONB NOT NULL,
                payload JSONB NOT NULL,
                UNIQUE (game_id, source, collected_at));
                """
                )

            # 3. DataFrame을 DB에 넣기
            db_step = "Data Frame 저장"
            # raw_df DataFrame을 딕셔너리로 저장 (for문으로 쓰기위함)
            for row in raw_df.to_dict("records"):
                # raw스키마 내 steam_api_response 데이터 넣기
                # 단, 똑같은 데이터가 있어도 에러 발생 없음. 
                cur.execute("""
                    INSERT INTO raw.steam_api_response (
                    game_id, source, collected_at, snapshot_date, request_params, payload)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (game_id, source, collected_at) DO NOTHING;
                """, (
                    int(row["game_id"]),
                    row["source"],
                    row["collected_at"].to_pydatetime(),
                    row["snapshot_date"],
                    Json(row["request_params"]),
                    Json(row["payload"]),))
                inserted_count = inserted_count + cur.rowcount

            db_step = "저장 확인"

            # 4. 방금 넣은 데이터 샘플 확인
            cur.execute("""
                SELECT source, payload
                FROM raw.steam_api_response
                WHERE game_id = %s AND collected_at = %s
                ORDER BY source;
            """, (collected_game_id, collected_at))
            save_rows = cur.fetchall()

        db_step = "저장 완료"

        #모든 작업 저장
        conn.commit()
        print("저장 완료.추가한 행 수 : ",inserted_count)

    # try 에러 시 이전으로 되돌림.
    except (psycopg2.Error, UnicodeDecodeError, ValueError, TypeError) as error:
        if conn is not None:
            conn.rollback()

        raise RuntimeError(
            f"DB {db_step} 실패 ({type(error).__name__})."
        ) from None

    # DB 연결 종료
    finally:
        if conn is not None:
            conn.close()




