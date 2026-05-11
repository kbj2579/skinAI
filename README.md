# AI 기반 두피·안면피부 분석 서비스

> 본 서비스는 AI 보조 분석 도구입니다. 의학적 진단을 대체하지 않으며, 모든 분석 결과는 참고용으로만 활용하십시오.

---

## 프로젝트 주제 및 목표

스마트폰 카메라로 촬영한 두피·안면피부 이미지를 AI가 분석하여 상태를 분류하고, 쉬운 언어로 관리 방법을 안내하는 건강 보조 서비스입니다.

### 핵심 목표

| 목표 | 설명 |
|------|------|
| **접근성** | 병원 방문 전 간편하게 두피·피부 상태를 1차 확인 |
| **안전성** | AI 분석은 보조 수단임을 명시, 고위험 결과 시 전문의 방문 자동 권장 |
| **연속성** | 분석 이력을 축적하여 시간에 따른 상태 변화 모니터링 |

### 분석 유형

- **안면피부 분석** — 피부염, 아토피, 건선, 주사, 지루성피부염, 정상 (6종)
- **두피 분석** — 미세각질, 피지과다, 비듬, 탈모, 정상 (5종)

---

## 시스템 아키텍처

```
┌──────────────────────────────────────────────────────────────────────────────────┐
│                            Frontend  (React + TypeScript + Vite)                  │
│                                                                                    │
│  • 이미지 선택 후 Canvas API로 1024×1024 리사이즈                                  │
│  • 분석 유형 선택 (안면피부 / 두피)                                                  │
│  • 분석 결과 표시: 위험도 배지, 감지 상태, AI 설명, 병원 방문 권장 배너              │
│  • 분석 이력 목록 및 상세 조회                                                       │
└────────────────────────────┬─────────────────────────────────────────────────────┘
                             │  REST API  (JWT 인증)
                             ▼
┌──────────────────────────────────────────────────────────────────────────────────┐
│                              Backend  (FastAPI · Python)                           │
│                                                                                    │
│   ① 이미지 수신                                                                     │
│      └─ 업로드된 이미지를 멀티파트로 수신, 포맷·확장자 검증                          │
│                                                                                    │
│   ② 병렬 처리  (asyncio.gather)                                                    │
│      ├─ [이미지 저장]  →  Cloudflare R2에 업로드, 저장 경로(key) 반환               │
│      └─ [AI 추론]     →  Model Server에 이미지 전송, 분류 결과 수신                 │
│                                                                                    │
│   ③ 위험도 판정  (룰 기반 · 코드 고정)                                              │
│      └─ suspicious / danger 판정 시 → 병원 방문 권장 플래그 자동 설정               │
│                                                                                    │
│   ④ AI 관리 안내 생성                                                               │
│      └─ Gemini API에 분석 결과 + 과거 이력 전달                                     │
│         → 현재 상태 설명, 즉시 실천 관리법, 병원 방문 안내 텍스트 생성              │
│         → 응답 캐싱으로 동일 결과 중복 호출 방지 / API 실패 시 fallback 메시지 반환  │
│                                                                                    │
│   ⑤ DB 저장 및 응답 반환                                                            │
│      └─ 분석 결과 전체를 Supabase에 저장, 면책 문구 포함하여 클라이언트에 응답       │
│                                                                                    │
└──────┬──────────────────────────┬──────────────────────┬───────────────────────  ┘
       │                          │                      │
       ▼                          ▼                      ▼
┌─────────────────┐   ┌─────────────────────┐   ┌──────────────────────┐
│   Model Server  │   │   Cloudflare R2      │   │   Supabase           │
│   (FastAPI)     │   │   (이미지 저장소)     │   │   (PostgreSQL DB)    │
│                 │   │                     │   │                      │
│ • 안면피부 분류  │   │ • 업로드 이미지 보관  │   │ • users              │
│   6종 클래스    │   │ • S3 호환 API        │   │ • analyses           │
│ • 두피 분류     │   │ • DB엔 경로만 저장   │   │ • lesion_tracks      │
│   5종 클래스    │   │                     │   │ • lesion_analyses    │
│ • 신뢰도 점수   │   │                     │   │                      │
│ • 바운딩 박스   │   │                     │   │                      │
└─────────────────┘   └─────────────────────┘   └──────────────────────┘
```

---

## 기술 스택

| 영역 | 기술 | 역할 |
|------|------|------|
| **Frontend** | React 18, TypeScript, Vite, React Router v6, Axios, Recharts | 모바일 UI (390×844), 라우팅, HTTP 클라이언트, 차트 |
| **Backend** | FastAPI, SQLAlchemy (async), Alembic, Pydantic, python-jose, bcrypt | REST API, ORM, 마이그레이션, 스키마 검증, JWT 인증 |
| **Model Server** | FastAPI, Python | AI 추론 엔드포인트 (현재 Mock → 실 모델 교체 가능) |
| **Database** | Supabase (PostgreSQL), asyncpg | 사용자·분석 결과·이력 데이터 저장 |
| **이미지 저장소** | Cloudflare R2 (S3 호환), boto3 | 분석 이미지 원본 보관, 무료 egress |
| **AI 설명** | Google Gemini API | 분석 결과 기반 관리 안내 텍스트 생성 |
| **인프라** | Docker, Docker Compose | 서비스 컨테이너화 및 로컬 오케스트레이션 |

---

## 로컬 실행 방법

### 사전 요구사항

| 도구 | 버전 | 확인 명령어 |
|------|------|-------------|
| Python | 3.13 | `python --version` |
| Node.js | 18 이상 | `node --version` |
| npm | 8 이상 | `npm --version` |

---

### 1단계 — 환경 변수 설정

프로젝트 루트에 `.env` 파일을 생성합니다.

```env
# DB (로컬 SQLite)
DATABASE_URL=sqlite+aiosqlite:///C:/절대경로/medical_ai_team3_new/backend/skin_ai.db

# DB (Supabase 사용 시 위 줄 주석 처리 후 아래 사용)
# DATABASE_URL=postgresql+asyncpg://postgres:[PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres

# 이미지 저장소 (Cloudflare R2 미설정 시 Mock 동작)
STORAGE_ENDPOINT=https://[ACCOUNT-ID].r2.cloudflarestorage.com
STORAGE_ACCESS_KEY=your-r2-access-key
STORAGE_SECRET_KEY=your-r2-secret-key
STORAGE_BUCKET=skin-ai
STORAGE_REGION=auto

# AI 모델 서버
AI_MODEL_BASE_URL=http://127.0.0.1:8001

# Gemini API (없으면 fallback 메시지 반환)
GEMINI_API_KEY=your-gemini-api-key

# JWT
JWT_SECRET=your-random-secret-string
JWT_EXPIRE_MINUTES=60

# CORS
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

---

### 2단계 — 백엔드 실행 (Terminal 1)

```powershell
cd backend
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

> `alembic upgrade head` — DB 테이블 최초 생성 시 한 번만 실행

---

### 3단계 — 프론트엔드 실행 (Terminal 2)

```powershell
cd frontend
npm install
npm run dev
```

---

### 4단계 — 모델 서버 실행 (Terminal 3, 선택)

```powershell
cd model
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8001
```

> 모델 서버 없이도 동작합니다. 미실행 시 Mock 결과(랜덤 분류)를 반환합니다.

---

### 브라우저 접속

```
http://localhost:3000
```

---

### 서비스 포트 요약

| 서비스 | 포트 | 설명 |
|--------|------|------|
| Frontend | 3000 | React 개발 서버 |
| Backend API | 8000 | FastAPI REST API |
| Model Server | 8001 | AI 추론 서버 (Mock) |

---

### 포트 충돌 해결

```powershell
# 모든 Python 프로세스 종료 후 재시작
taskkill /F /IM python.exe
```

---

## 다른 컴퓨터로 옮길 때 체크리스트

| 항목 | 상태 | 조치 |
|------|------|------|
| `.env` DB 절대경로 | ⚠️ 주의 | `DATABASE_URL` 줄 삭제 또는 주석 처리 → 자동 경로 사용 |
| `node_modules/` | ✅ 불필요 | `npm install` 로 재생성 |
| Python 패키지 | ✅ 불필요 | `pip install -r requirements.txt` 로 재설치 |
| `skin_ai.db` (SQLite) | ⚠️ 선택 | 기존 데이터 이전 시 파일도 함께 복사 |
| `.env` 파일 | ⚠️ 필수 | `.gitignore` 대상이므로 직접 복사 필요 |

> **핵심:** `.env`에서 `DATABASE_URL` 줄을 주석 처리하면 어느 컴퓨터에서든 자동으로 올바른 경로를 찾습니다.

```env
# 이 줄을 주석 처리하면 자동으로 경로 계산
# DATABASE_URL=sqlite+aiosqlite:///C:/절대경로/...
```
