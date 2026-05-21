from pathlib import Path

APP_NAME = "Kiwoom SQLite Auto Trader"

# 실행 버전
RUN_VERSION = "v8"  # v1 / v2 / v3 / v4 / v5 / v6 / v7 / v8 / password

# simulation: 주문 없음
# paper: 모의투자
# live: 실전투자
MODE = "paper"

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
LOG_DIR = BASE_DIR / "logs"

DB_PATH = DATA_DIR / "trading.db"

TARGET_CODES = ["005930"]

SHORT_WINDOW = 5
LONG_WINDOW = 20

STRATEGY_NAME = "MovingAverageStrategy"

# =========================
# 주문 안전 설정
# =========================

# 일반 주문 허용 여부
ENABLE_ORDER = False

# 실전 주문 허용 여부
ALLOW_LIVE_ORDER = False

TEST_ORDER_CODE = "005930"
TEST_ORDER_QTY = 1
TEST_ORDER_PRICE = 0
TEST_HOGA_GB = "03"

# =========================
# 리스크 설정
# =========================

MAX_BUY_AMOUNT_PER_STOCK = 300_000
MAX_HOLDING_COUNT = 3
MAX_DAILY_LOSS = -30_000

BLOCK_IF_ALREADY_HOLDING = True
BLOCK_IF_UNFILLED_ORDER_EXISTS = True

# =========================
# 조건검색 설정
# =========================

CONDITION_INDEX = None
CONDITION_NAME = None
CONDITION_SCREEN_NO = "4000"
CONDITION_SEARCH_TYPE = 1
CONDITION_WATCH_SECONDS = 20
CONDITION_MAX_INITIAL_CODES = 5

# 조건검색 기반 주문
ENABLE_CONDITION_ORDER = False
CONDITION_ORDER_MAX_CANDIDATES = 1
CONDITION_ORDER_QTY = 1
USE_INITIAL_CONDITION_CODES_FOR_ORDER = True
USE_REALTIME_CONDITION_IN_FOR_ORDER = True

# =========================
# 매도/청산 설정
# =========================

ENABLE_SELL_ORDER = False

TAKE_PROFIT_RATE = 3.0
STOP_LOSS_RATE = -2.0

SELL_ONLY_MARKET_ORDER = True
SELL_MAX_CANDIDATES = 3

# =========================
# v8 자동 운영 루프 설정
# =========================

ENABLE_TRADING_LOOP = True

# 루프 간격, 초 단위
LOOP_INTERVAL_SECONDS = 60

# 정규장 기준
MARKET_OPEN_TIME = "09:00"
MARKET_CLOSE_TIME = "15:30"

# 개발/테스트용:
# True면 장 시간이 아니어도 루프를 실행한다.
ALLOW_LOOP_OUTSIDE_MARKET = True

# 테스트용 반복 횟수
# None이면 시간 조건에 따라 계속 실행
MAX_LOOP_COUNT = 3

# 루프 안에서 실행할 기능
ENABLE_LOOP_ACCOUNT_SYNC = True
ENABLE_LOOP_SELL_CHECK = True
ENABLE_LOOP_CONDITION_BUY = True

# v8.1 변경:
# 조건식 목록은 매 루프마다 다시 불러오지 않고 최초 1회만 불러온다.
RUN_CONDITION_EACH_LOOP = False

# v8.1 추가:
# 같은 프로그램 실행 세션에서 이미 평가한 조건검색 후보 종목은 다시 평가하지 않는다.
SKIP_ALREADY_EVALUATED_CONDITION_CODES = True