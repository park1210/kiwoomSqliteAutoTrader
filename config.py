from pathlib import Path

APP_NAME = "Kiwoom SQLite Auto Trader"

# 실행 버전
RUN_VERSION = "v5"  # v1 / v2 / v3 / v4 / v5 / password

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

ENABLE_ORDER = False
ALLOW_LIVE_ORDER = False

TEST_ORDER_CODE = "005930"
TEST_ORDER_QTY = 1
TEST_ORDER_PRICE = 0
TEST_HOGA_GB = "03"

MAX_BUY_AMOUNT_PER_STOCK = 300_000
MAX_HOLDING_COUNT = 3
MAX_DAILY_LOSS = -30_000

BLOCK_IF_ALREADY_HOLDING = True
BLOCK_IF_UNFILLED_ORDER_EXISTS = True

# =========================
# v5 조건검색 설정
# =========================

# None이면 첫 번째 조건식을 자동 선택
CONDITION_INDEX = None
CONDITION_NAME = None

CONDITION_SCREEN_NO = "4000"

# 0: 일반 조건검색, 1: 실시간 조건검색
CONDITION_SEARCH_TYPE = 1

# 조건검색 감시 시간 초 단위
CONDITION_WATCH_SECONDS = 60

# 초기 조건검색 결과 종목을 너무 많이 조회하지 않도록 제한
CONDITION_MAX_INITIAL_CODES = 5

# v5에서는 기본적으로 조건검색으로 주문하지 않음
ENABLE_CONDITION_ORDER = False