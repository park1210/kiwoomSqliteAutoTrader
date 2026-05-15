CREATE TABLE IF NOT EXISTS stocks (
    code TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    market TEXT,
    is_active INTEGER DEFAULT 1,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS price_minute (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT NOT NULL,
    datetime TEXT NOT NULL,
    open INTEGER,
    high INTEGER,
    low INTEGER,
    close INTEGER,
    volume INTEGER,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(code, datetime)
);

CREATE TABLE IF NOT EXISTS price_snapshot (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT NOT NULL,
    name TEXT,
    current_price INTEGER,
    volume INTEGER,
    raw_current_price TEXT,
    raw_volume TEXT,
    captured_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS signals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT NOT NULL,
    signal_type TEXT NOT NULL,
    strategy_name TEXT NOT NULL,
    price INTEGER,
    reason TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT NOT NULL,
    name TEXT,
    account_no TEXT,
    order_type TEXT NOT NULL,
    quantity INTEGER NOT NULL,
    price INTEGER DEFAULT 0,
    hoga_gb TEXT,
    status TEXT DEFAULT 'REQUESTED',
    kiwoom_order_no TEXT,
    reason TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS executions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER,
    code TEXT,
    name TEXT,
    kiwoom_order_no TEXT,
    order_status TEXT,
    order_type_raw TEXT,
    quantity INTEGER,
    price INTEGER,
    unfilled_quantity INTEGER,
    execution_price INTEGER,
    execution_quantity INTEGER,
    execution_time TEXT,
    raw_data TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(order_id) REFERENCES orders(id)
);

CREATE TABLE IF NOT EXISTS positions (
    code TEXT PRIMARY KEY,
    name TEXT,
    quantity INTEGER DEFAULT 0,
    avg_price INTEGER DEFAULT 0,
    current_price INTEGER,
    eval_amount INTEGER,
    profit_loss INTEGER,
    profit_rate REAL,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS unfilled_orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    account_no TEXT,
    code TEXT,
    name TEXT,
    kiwoom_order_no TEXT,
    order_type TEXT,
    order_price INTEGER,
    order_quantity INTEGER,
    unfilled_quantity INTEGER,
    current_price INTEGER,
    raw_data TEXT,
    captured_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS account_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    account_no TEXT,
    cash INTEGER,
    total_buy_amount INTEGER,
    total_eval_amount INTEGER,
    total_profit_loss INTEGER,
    total_profit_rate REAL,
    raw_data TEXT,
    captured_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS notifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    channel TEXT NOT NULL,
    title TEXT,
    message TEXT NOT NULL,
    status TEXT DEFAULT 'PENDING',
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    sent_at TEXT
);

CREATE TABLE IF NOT EXISTS system_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    level TEXT NOT NULL,
    message TEXT NOT NULL,
    detail TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);