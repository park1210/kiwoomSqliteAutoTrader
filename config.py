from pathlib import Path

APP_NAME = "Kiwoom SQLite Auto Trader"

# 실행 버전
RUN_VERSION = "v3"  # v1 / v2 / v3

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

# v3에서 실제 SendOrder를 호출하려면 True로 바꿔야 함
# 처음 실행할 때는 False로 두고 계좌/서버 확인부터 하는 것을 추천
ENABLE_ORDER = True

# 실전 주문 허용 여부
# 절대 실수 방지를 위해 기본값 False
ALLOW_LIVE_ORDER = False

# 테스트 주문 설정
TEST_ORDER_CODE = "005930"   # 삼성전자
TEST_ORDER_QTY = 1           # 1주
TEST_ORDER_PRICE = 0         # 시장가일 때 0
TEST_HOGA_GB = "03"          # 03: 시장가

# =========================
# 리스크 설정
# =========================

MAX_BUY_AMOUNT_PER_STOCK = 300_000
MAX_HOLDING_COUNT = 3
MAX_DAILY_LOSS = -30_000