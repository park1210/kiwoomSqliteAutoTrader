import os
from pathlib import Path

import yaml


BASE_DIR = Path(__file__).resolve().parent
CONFIG_DIR = BASE_DIR / "config"

DEFAULT_SETTINGS_PATH = CONFIG_DIR / "settings.yaml"
LOCAL_SETTINGS_PATH = CONFIG_DIR / "settings.local.yaml"
ENV_PATH = CONFIG_DIR / ".env"


def load_dotenv_simple(path):
    if not path.exists():
        return

    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            text = line.strip()

            if not text or text.startswith("#"):
                continue

            if "=" not in text:
                continue

            key, value = text.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")

            # OS 환경변수가 이미 있으면 OS 환경변수를 우선 사용
            os.environ.setdefault(key, value)


def load_yaml(path):
    if not path.exists():
        return {}

    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def deep_merge(base, override):
    result = dict(base)

    for key, value in override.items():
        if (
            key in result
            and isinstance(result[key], dict)
            and isinstance(value, dict)
        ):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value

    return result


def get_nested(data, path, default=None):
    current = data

    for key in path.split("."):
        if not isinstance(current, dict):
            return default

        if key not in current:
            return default

        current = current[key]

    return current


load_dotenv_simple(ENV_PATH)

_settings = load_yaml(DEFAULT_SETTINGS_PATH)
_local_settings = load_yaml(LOCAL_SETTINGS_PATH)
SETTINGS = deep_merge(_settings, _local_settings)


APP_NAME = get_nested(SETTINGS, "app.name", "Kiwoom SQLite Auto Trader")
RUN_VERSION = get_nested(SETTINGS, "app.run_version", "v8")

MODE = get_nested(SETTINGS, "mode", "paper")

DATA_DIR = BASE_DIR / "data"
LOG_DIR = BASE_DIR / "logs"
DB_PATH = DATA_DIR / "trading.db"

TARGET_CODES = get_nested(SETTINGS, "target_codes", ["005930"])

SHORT_WINDOW = get_nested(SETTINGS, "strategy.short_window", 5)
LONG_WINDOW = get_nested(SETTINGS, "strategy.long_window", 20)
STRATEGY_NAME = get_nested(SETTINGS, "strategy.name", "MovingAverageStrategy")


# =========================
# 주문 안전 설정
# =========================

ENABLE_ORDER = get_nested(SETTINGS, "order.enable_order", False)
ALLOW_LIVE_ORDER = get_nested(SETTINGS, "order.allow_live_order", False)

TEST_ORDER_CODE = get_nested(SETTINGS, "test_order.code", "005930")
TEST_ORDER_QTY = get_nested(SETTINGS, "test_order.qty", 1)
TEST_ORDER_PRICE = get_nested(SETTINGS, "test_order.price", 0)
TEST_HOGA_GB = get_nested(SETTINGS, "test_order.hoga_gb", "03")

MAX_BUY_AMOUNT_PER_STOCK = get_nested(
    SETTINGS,
    "order.max_buy_amount_per_stock",
    300_000,
)
MAX_HOLDING_COUNT = get_nested(SETTINGS, "order.max_holding_count", 3)
MAX_DAILY_LOSS = get_nested(SETTINGS, "order.max_daily_loss", -30_000)

BLOCK_IF_ALREADY_HOLDING = get_nested(
    SETTINGS,
    "order.block_if_already_holding",
    True,
)
BLOCK_IF_UNFILLED_ORDER_EXISTS = get_nested(
    SETTINGS,
    "order.block_if_unfilled_order_exists",
    True,
)


# =========================
# 조건검색 설정
# =========================

CONDITION_INDEX = get_nested(SETTINGS, "condition.condition_index", None)
CONDITION_NAME = get_nested(SETTINGS, "condition.condition_name", None)
CONDITION_SCREEN_NO = get_nested(SETTINGS, "condition.screen_no", "4000")
CONDITION_SEARCH_TYPE = get_nested(SETTINGS, "condition.search_type", 1)
CONDITION_WATCH_SECONDS = get_nested(SETTINGS, "condition.watch_seconds", 20)
CONDITION_MAX_INITIAL_CODES = get_nested(
    SETTINGS,
    "condition.max_initial_codes",
    5,
)

ENABLE_CONDITION_ORDER = get_nested(
    SETTINGS,
    "condition.enable_condition_order",
    False,
)
CONDITION_ORDER_MAX_CANDIDATES = get_nested(
    SETTINGS,
    "condition.order_max_candidates",
    1,
)
CONDITION_ORDER_QTY = get_nested(SETTINGS, "condition.order_qty", 1)
USE_INITIAL_CONDITION_CODES_FOR_ORDER = get_nested(
    SETTINGS,
    "condition.use_initial_codes_for_order",
    True,
)
USE_REALTIME_CONDITION_IN_FOR_ORDER = get_nested(
    SETTINGS,
    "condition.use_realtime_in_for_order",
    True,
)


# =========================
# 매도 설정
# =========================

ENABLE_SELL_ORDER = get_nested(SETTINGS, "sell.enable_sell_order", False)
TAKE_PROFIT_RATE = get_nested(SETTINGS, "sell.take_profit_rate", 3.0)
STOP_LOSS_RATE = get_nested(SETTINGS, "sell.stop_loss_rate", -2.0)
SELL_ONLY_MARKET_ORDER = get_nested(SETTINGS, "sell.only_market_order", True)
SELL_MAX_CANDIDATES = get_nested(SETTINGS, "sell.max_candidates", 3)


# =========================
# 루프 설정
# =========================

ENABLE_TRADING_LOOP = get_nested(SETTINGS, "trading_loop.enable", True)
LOOP_INTERVAL_SECONDS = get_nested(
    SETTINGS,
    "trading_loop.loop_interval_seconds",
    60,
)
MARKET_OPEN_TIME = get_nested(SETTINGS, "trading_loop.market_open_time", "09:00")
MARKET_CLOSE_TIME = get_nested(SETTINGS, "trading_loop.market_close_time", "15:30")
ALLOW_LOOP_OUTSIDE_MARKET = get_nested(
    SETTINGS,
    "trading_loop.allow_loop_outside_market",
    True,
)
MAX_LOOP_COUNT = get_nested(SETTINGS, "trading_loop.max_loop_count", 3)

ENABLE_LOOP_ACCOUNT_SYNC = get_nested(
    SETTINGS,
    "trading_loop.enable_account_sync",
    True,
)
ENABLE_LOOP_SELL_CHECK = get_nested(
    SETTINGS,
    "trading_loop.enable_sell_check",
    True,
)
ENABLE_LOOP_CONDITION_BUY = get_nested(
    SETTINGS,
    "trading_loop.enable_condition_buy",
    True,
)
RUN_CONDITION_EACH_LOOP = get_nested(
    SETTINGS,
    "trading_loop.run_condition_each_loop",
    False,
)
SKIP_ALREADY_EVALUATED_CONDITION_CODES = get_nested(
    SETTINGS,
    "trading_loop.skip_already_evaluated_condition_codes",
    True,
)


# =========================
# 알림 설정
# =========================

ENABLE_CONSOLE_NOTIFICATION = get_nested(
    SETTINGS,
    "notification.console",
    True,
)
ENABLE_EMAIL_NOTIFICATION = get_nested(
    SETTINGS,
    "notification.email",
    False,
)
ENABLE_TELEGRAM_NOTIFICATION = get_nested(
    SETTINGS,
    "notification.telegram",
    False,
)

NOTIFY_ON_INFO = get_nested(SETTINGS, "notification.notify_on_info", True)
NOTIFY_ON_ORDER = get_nested(SETTINGS, "notification.notify_on_order", True)
NOTIFY_ON_ERROR = get_nested(SETTINGS, "notification.notify_on_error", True)
NOTIFY_ON_LOOP_SUMMARY = get_nested(
    SETTINGS,
    "notification.notify_on_loop_summary",
    True,
)


# =========================
# 환경변수 이름
# =========================

EMAIL_SMTP_HOST_ENV = "KSA_EMAIL_SMTP_HOST"
EMAIL_SMTP_PORT_ENV = "KSA_EMAIL_SMTP_PORT"
EMAIL_USERNAME_ENV = "KSA_EMAIL_USERNAME"
EMAIL_PASSWORD_ENV = "KSA_EMAIL_PASSWORD"
EMAIL_FROM_ENV = "KSA_EMAIL_FROM"
EMAIL_TO_ENV = "KSA_EMAIL_TO"

TELEGRAM_BOT_TOKEN_ENV = "KSA_TELEGRAM_BOT_TOKEN"
TELEGRAM_CHAT_ID_ENV = "KSA_TELEGRAM_CHAT_ID"

# =========================
# 코드 기반 조건검색 설정 v5.1
# =========================

CODE_CONDITION_ENABLE = get_nested(
    SETTINGS,
    "code_condition.enable",
    True,
)

CODE_CONDITION_MAX_UNIVERSE_SIZE = get_nested(
    SETTINGS,
    "code_condition.max_universe_size",
    20,
)

CODE_CONDITION_MAX_CANDIDATES = get_nested(
    SETTINGS,
    "code_condition.max_candidates",
    3,
)

CODE_CONDITION_UNIVERSE_TYPE = get_nested(
    SETTINGS,
    "code_condition.universe.type",
    "manual",
)

CODE_CONDITION_UNIVERSE_CODES = get_nested(
    SETTINGS,
    "code_condition.universe.codes",
    ["005930"],
)

CODE_CONDITION_MIN_PRICE = get_nested(
    SETTINGS,
    "code_condition.filters.min_price",
    1000,
)

CODE_CONDITION_MAX_PRICE = get_nested(
    SETTINGS,
    "code_condition.filters.max_price",
    500000,
)

CODE_CONDITION_MIN_VOLUME = get_nested(
    SETTINGS,
    "code_condition.filters.min_volume",
    100000,
)

CODE_CONDITION_EXCLUDE_HOLDING = get_nested(
    SETTINGS,
    "code_condition.filters.exclude_holding",
    True,
)

CODE_CONDITION_EXCLUDE_UNFILLED = get_nested(
    SETTINGS,
    "code_condition.filters.exclude_unfilled",
    True,
)

CODE_CONDITION_REQUEST_DELAY_SECONDS = get_nested(
    SETTINGS,
    "code_condition.request_delay_seconds",
    0.7,
)

CODE_CONDITION_MAX_RETRY = get_nested(
    SETTINGS,
    "code_condition.max_retry",
    2,
)

CODE_CONDITION_ENABLE_ORDER = get_nested(
    SETTINGS,
    "code_condition.order.enable_order",
    False,
)

CODE_CONDITION_ORDER_QTY = get_nested(
    SETTINGS,
    "code_condition.order.qty",
    1,
)

CODE_CONDITION_ORDER_MAX_CANDIDATES = get_nested(
    SETTINGS,
    "code_condition.order.max_candidates",
    1,
)