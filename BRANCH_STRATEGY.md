# Branch Strategy

이 문서는 현재 프로젝트를 `기능별 브랜치 -> main 통합` 방식으로 운영하기 위한 기준을 정리합니다.

## 1. Current Scenario File Split

버전별 실행 로직은 이제 `app/scenarios/` 아래로 분리되었습니다.

| Version | Scenario File | Responsibility |
| --- | --- | --- |
| `v1` | `app/scenarios/simulation.py` | 이동평균 시뮬레이션 |
| `v2` | `app/scenarios/snapshot.py` | 현재가 스냅샷 조회 |
| `v3` | `app/scenarios/paper_order_test.py` | 모의 매수 주문 테스트 |
| `v4` | `app/scenarios/position_tracking.py` | 주문/잔고 추적 테스트 |
| `v5` | `app/scenarios/kiwoom_condition_scan.py` | 키움 조건검색 감시 |
| `v5.1` | `app/scenarios/code_condition_scan.py` | 코드 기반 조건검색 |
| `v6` | `app/scenarios/kiwoom_condition_order.py` | 키움 조건검색 기반 주문 평가 |
| `v6.1` | `app/scenarios/code_condition_order.py` | 코드 조건검색 기반 주문 평가 |
| `v7` | `app/scenarios/sell_exit_test.py` | 익절/손절 판단 및 매도 테스트 |
| `v8` | `app/scenarios/trading_loop.py` | 자동 운용 루프 |
| `v10` | `app/scenarios/trading_report.py` | 거래 리포트 생성 |
| `v11` | `app/scenarios/safety_guard_test.py` | 안전장치 테스트 |
| `v12` | `app/scenarios/strategy_plugin_test.py` | 전략 플러그인 테스트 |
| `password` | `app/scenarios/password_window.py` | 계좌 비밀번호 창 호출 |

공통 로직은 아래 파일에 둡니다.

- `app/scenarios/base.py`
- `app/trading/order_manager.py`
- `app/trading/position_manager.py`
- `app/trading/sell_manager.py`
- `app/trading/safety_guard.py`
- `app/kiwoom/kiwoom_api.py`
- `app/database/repository.py`

## 2. Recommended Branch Layout

앞으로는 브랜치를 `기능 추가 단위`로 운영하는 것을 권장합니다.

| Branch Name | Main Files |
| --- | --- |
| `feature/v1-simulation` | `app/scenarios/simulation.py` |
| `feature/v2-snapshot` | `app/scenarios/snapshot.py` |
| `feature/v3-paper-order-test` | `app/scenarios/paper_order_test.py`, `app/trading/order_manager.py` |
| `feature/v4-position-tracking` | `app/scenarios/position_tracking.py`, `app/trading/position_manager.py` |
| `feature/v5-kiwoom-condition-scan` | `app/scenarios/kiwoom_condition_scan.py`, `app/kiwoom/condition_manager.py` |
| `feature/v5-1-code-condition-scan` | `app/scenarios/code_condition_scan.py`, `app/strategy/code_condition_engine.py`, `app/strategy/filters.py`, `app/strategy/universe_provider.py` |
| `feature/v6-kiwoom-condition-order` | `app/scenarios/kiwoom_condition_order.py`, `app/kiwoom/condition_manager.py`, `app/trading/order_manager.py` |
| `feature/v6-1-code-condition-order` | `app/scenarios/code_condition_order.py`, `app/trading/code_condition_order_service.py`, `app/trading/order_manager.py` |
| `feature/v7-sell-exit` | `app/scenarios/sell_exit_test.py`, `app/trading/sell_manager.py`, `app/trading/order_manager.py` |
| `feature/v8-trading-loop` | `app/scenarios/trading_loop.py`, `app/trading/trading_loop.py`, `app/trading/market_time.py` |
| `feature/v10-report` | `app/scenarios/trading_report.py`, `app/report/*` |
| `feature/v11-safety-guard` | `app/scenarios/safety_guard_test.py`, `app/trading/safety_guard.py` |
| `feature/v12-strategy-plugin` | `app/scenarios/strategy_plugin_test.py`, `app/strategy/strategy_runner.py`, `app/strategy/strategy_loader.py`, `app/strategy/plugins/*` |

주의할 점:

- `main.py`
- `app/trading/trading_engine.py`
- `app/scenarios/registry.py`

이 세 파일은 거의 모든 브랜치에서 함께 바뀔 수 있습니다. 따라서 이 파일들은 `공통 라우팅 파일`로 보고, 각 브랜치가 자기 기능을 추가할 때만 최소 범위로 수정하는 것이 좋습니다.

## 3. How To Rebuild Clean Branches

현재 브랜치들이 여러 기능이 섞여 있다면, 기존 브랜치를 억지로 정리하기보다 `main`에서 새 브랜치를 다시 만드는 방식을 추천합니다.

### Recommended

1. 현재 상태 백업
2. `main` 최신화
3. 기능별 새 브랜치 생성
4. 필요한 파일만 가져오기
5. 테스트 후 커밋

예시:

```bash
git checkout main
git pull origin main

git branch backup/all-in-one-current

git checkout -b feature/v5-kiwoom-condition-scan
```

이후 `v5` 관련 파일만 남기고 커밋합니다.

## 4. Upload To GitHub

### A. New Clean Branch Push

기능별 브랜치를 새로 만들었다면 아래 순서가 가장 안전합니다.

```bash
git checkout feature/v5-kiwoom-condition-scan
git status
git add .
git commit -m "Split v5 scenario into dedicated files"
git push -u origin feature/v5-kiwoom-condition-scan
```

### B. Main Merge Later

검토 후 `main`에 병합합니다.

```bash
git checkout main
git pull origin main
git merge feature/v5-kiwoom-condition-scan
git push origin main
```

## 5. Existing Branches: Keep Or Delete?

추천은 `일단 살리고`, 정리된 새 브랜치가 안정화된 뒤 삭제하는 것입니다.

### Why keeping old branches first is better

- 기존 작업 이력을 잃지 않음
- 빠뜨린 코드가 있을 때 복구 가능
- 새 기능 브랜치를 만들 때 참고 자료로 사용 가능

### Recommended lifecycle

1. 기존 브랜치 이름 유지
2. 새 정리 브랜치 생성
3. 새 브랜치가 정상 동작하면 PR 또는 merge
4. 병합 완료 후 기존 브랜치 삭제 여부 결정

## 6. Branch Deletion

### Delete local branch

```bash
git branch -d feature/v5-kiwoom-condition-scan
```

강제 삭제가 필요할 때만:

```bash
git branch -D feature/v5-kiwoom-condition-scan
```

### Delete remote branch

```bash
git push origin --delete feature/v5-kiwoom-condition-scan
```

## 7. If You Want To Start Over Completely

가장 안전한 순서는 아래입니다.

1. `main`을 기준 브랜치로 확정
2. 현재 브랜치 전체를 `backup/*` 이름으로 보존
3. 기능별 새 브랜치를 `main`에서 다시 생성
4. `app/scenarios/` 기준으로 필요한 파일만 가져오기
5. 각 브랜치가 한 기능만 담도록 유지

예시:

```bash
git checkout main
git pull origin main

git branch backup/legacy-v-branches

git checkout -b feature/v8-trading-loop
```

이후 `v8` 관련 파일만 정리해서 커밋합니다.

## 8. Recommended Decision

현 상태에서는 아래 방식을 권장합니다.

- 기존 브랜치: 삭제하지 말고 백업/참고용으로 유지
- 새 브랜치: `main`에서 기능별로 다시 생성
- 기능 분리 기준: `app/scenarios/*.py` 단위
- `main` 반영 방식: 기능 브랜치별로 검증 후 순차 병합
