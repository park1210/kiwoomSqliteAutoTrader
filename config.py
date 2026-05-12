from pathlib import Path

APP_NAME = "Kiwoom SQLite Auto Trader"

# v1에서는 실제 주문하지 않음
MODE = "simulation"  # simulation / paper / live

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
LOG_DIR = BASE_DIR / "logs"

DB_PATH = DATA_DIR / "trading.db"

TARGET_CODES = ["005930"]

SHORT_WINDOW = 5
LONG_WINDOW = 20

STRATEGY_NAME = "MovingAverageStrategy"

MAX_BUY_AMOUNT_PER_STOCK = 100_000
MAX_HOLDING_COUNT = 3
MAX_DAILY_LOSS = -30_000