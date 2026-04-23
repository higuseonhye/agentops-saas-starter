# AgentOps SaaS Starter

FastAPI + Next.js 기반의 LLM AgentOps MVP입니다.  
이 저장소는 아래 흐름을 한 번에 확인할 수 있도록 구성되어 있습니다.

- API key 인증
- Agent 요청 실행 (`/query`)
- usage 로그 적재 및 과금 계산
- 실패 케이스 replay / 성능 optimize
- 조직(org) 단위 대시보드 조회
- Slack alert 체크 스크립트

## 1) 빠른 시작 (Windows)

### 사전 요구사항

- Python 3.11+ 권장
- Node.js 20+ 권장
- npm
- (선택) Stripe 키, Slack webhook

### 백엔드 실행

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python scripts_seed.py
uvicorn app.main:app --reload
```

`python scripts_seed.py` 실행 시 demo API key가 출력됩니다.  
이 값을 프론트 `.env.local`의 `NEXT_PUBLIC_API_KEY`에 넣어주세요.

### 프론트 실행

```bash
cd frontend
npm install
copy .env.local.example .env.local
npm run dev
```

프론트 접속: `http://localhost:3000`  
백엔드 기본 주소: `http://localhost:8000`

## 2) 환경변수

### 백엔드 (`backend/.env`)

- `DATABASE_URL` (기본: `sqlite:///./agentops.db`)
- `STRIPE_SECRET_KEY`
- `STRIPE_WEBHOOK_SECRET`
- `SLACK_WEBHOOK_URL`
- `ALERT_ACCURACY_THRESHOLD` (기본: `0.7`)
- `ALERT_DAILY_COST_THRESHOLD` (기본: `50`)
- `DEFAULT_CREDIT_ON_PAYMENT` (기본: `10`)

### 프론트 (`frontend/.env.local`)

- `NEXT_PUBLIC_API_BASE` (기본: `http://localhost:8000`)
- `NEXT_PUBLIC_API_KEY` (`scripts_seed.py` 출력값)

## 3) 주요 API

### Agent / Usage

- `POST /query` - agent 실행 + usage 측정
- `GET /usage` - org usage 요약 (`days` 또는 `start_date`+`end_date`, `org_id` 지원)
- `GET /usage/compare` - 접근 가능한 org 간 비용 비교

### Performance / Failures

- `GET /performance` - 최신 성능 스냅샷
- `GET /performance/history` - 기간별 성능 시계열
- `GET /failures` - 실패 케이스 조회
- `POST /replay` - 실패 케이스 재실행
- `POST /optimize` - 성능 스냅샷 개선 시뮬레이션

### Billing / Org

- `POST /billing/checkout` - Stripe checkout 생성
- `POST /billing/webhook` - Stripe 결제 완료 처리
- `GET /org/usage` - 선택 org 과금 합계
- `GET /orgs` - 현재 API key 사용자 접근 가능한 org 목록

## 4) 대시보드 페이지

- `/usage` - 기간 필터, 일별/누적 토글, org 비교 차트
- `/performance` - 최신 지표 + 히스토리 차트
- `/failures` - 실패 케이스 탐색 및 replay
- `/system` - config 조회, optimize/replay-all 액션

상단 Org 선택기를 통해 `org_id` 컨텍스트를 전 페이지 동기화합니다.

## Alert system

주기 실행으로 성능/비용 임계치 알림을 보낼 수 있습니다.

```bash
python scripts/alert_check.py
```

필수 환경변수:
- `AGENTOPS_API_KEY`
- `AGENTOPS_API_BASE` (default `http://localhost:8000`)
- `SLACK_WEBHOOK_URL` (optional; if absent, prints mock alert)

예시 cron:

```cron
*/10 * * * * python /path/to/agentops/scripts/alert_check.py
```

## 5) 빠른 동작 확인 (Smoke Test)

1. 백엔드 실행 후 `GET /health` 응답 확인
2. 프론트에서 Usage/Performance 페이지 로딩 확인
3. `POST /query` 호출 후 Usage 값 증가 확인
4. Failures 페이지에서 Replay 버튼 동작 확인
5. System 페이지에서 Optimize 실행 후 Performance 변화 확인

## 6) 프로덕션 적용 전 체크리스트

- 실제 LLM provider 연동 (`run_agent` placeholder 교체)
- Stripe webhook 서명 검증/재시도 전략 강화
- CORS/인증키 저장 정책 강화
- DB를 SQLite에서 managed DB로 전환
- 에러 추적/로그 집계/모니터링 연동
