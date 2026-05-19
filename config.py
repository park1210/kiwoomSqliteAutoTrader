from pathlib import Path

APP_NAME = "Kiwoom SQLite Auto Trader"

# 실행 버전
RUN_VERSION = "v7"  # v1 / v2 / v3 / v4 / v5 / v6 / v7 / password

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
CONDITION_WATCH_SECONDS = 30
CONDITION_MAX_INITIAL_CODES = 5

ENABLE_CONDITION_ORDER = False
CONDITION_ORDER_MAX_CANDIDATES = 1
CONDITION_ORDER_QTY = 1
USE_INITIAL_CONDITION_CODES_FOR_ORDER = True
USE_REALTIME_CONDITION_IN_FOR_ORDER = True

# =========================
# v7 매도/청산 설정
# =========================

# 처음에는 False로 실행해서 매도 판단만 확인하세요.
ENABLE_SELL_ORDER = False

# 익절/손절 기준
TAKE_PROFIT_RATE = 3.0     # +3% 이상이면 익절 후보
STOP_LOSS_RATE = -2.0      # -2% 이하이면 손절 후보

# 수익률이 위 조건에 걸리지 않으면 보유
SELL_ONLY_MARKET_ORDER = True

# 매도 후보 최대 개수
SELL_MAX_CANDIDATES = 3