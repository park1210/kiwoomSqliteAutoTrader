from pathlib import Path

APP_NAME = "Kiwoom SQLite Auto Trader"

# 실행 버전
RUN_VERSION = "v6"  # v1 / v2 / v3 / v4 / v5 / v6 / password

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
ENABLE_ORDER = True

# 실전 주문 허용 여부
ALLOW_LIVE_ORDER = False

# 테스트 주문 설정
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
# v5/v6 조건검색 설정
# =========================

CONDITION_INDEX = None
CONDITION_NAME = None

CONDITION_SCREEN_NO = "4000"

# 0: 일반 조건검색
# 1: 실시간 조건검색
CONDITION_SEARCH_TYPE = 1

CONDITION_WATCH_SECONDS = 30
CONDITION_MAX_INITIAL_CODES = 5

# =========================
# v6 조건검색 주문 설정
# =========================

# 매우 중요:
# 처음에는 False로 실행해서 주문 후보 평가만 확인하세요.
ENABLE_CONDITION_ORDER = True

# 조건검색 초기 편입 종목 중 몇 개만 주문 후보로 볼지 제한
CONDITION_ORDER_MAX_CANDIDATES = 1

# 조건검색 기반 주문 수량
CONDITION_ORDER_QTY = 1

# 초기 편입 종목도 주문 후보로 볼지 여부
USE_INITIAL_CONDITION_CODES_FOR_ORDER = True

# 실시간 편입 이벤트도 주문 후보로 볼지 여부
USE_REALTIME_CONDITION_IN_FOR_ORDER = True