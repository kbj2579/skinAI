# AI 기반 안면피부·병변 분석 서비스

> 본 서비스는 AI 보조 분석 도구입니다. 의학적 진단을 대체하지 않으며, 모든 분석 결과는 참고용으로만 활용하십시오.

---

## 프로젝트 주제 및 목표

스마트폰 카메라로 촬영한 안면피부·병변 이미지를 AI가 분석하여 상태를 분류하고, 쉬운 언어로 관리 방법을 안내하는 건강 보조 서비스입니다.

### 핵심 목표

| 목표 | 설명 |
|------|------|
| **접근성** | 병원 방문 전 간편하게 피부 상태를 1차 확인 |
| **안전성** | AI 분석은 보조 수단임을 명시, 고위험 결과 시 전문의 방문 자동 권장 |
| **연속성** | 분석 이력을 축적하여 시간에 따른 상태 변화 모니터링 |

### 분석 유형

- **안면피부 분석** — 여드름, 민감성, 건조, 홍조, 색소침착, 정상
- **병변 분석** — 병변 경계·형태·색상 분석, 위험도 분류

---

## 시스템 아키텍처

```
┌──────────────────────────────────────────────────────────────────┐
│                  Frontend (React + TypeScript + Vite)             │
│                                                                    │
│  • 카메라/갤러리로 이미지 선택 → Canvas API로 1024×1024 리사이즈   │
│  • 분석 유형 선택 (안면피부 / 병변)                                 │
│  • 분석 결과: 위험도 배지, 감지 상태, AI 설명, 피부 지표 게이지     │
│  • 분석 이력 목록 및 상세 조회                                      │
└──────────────────────┬───────────────────────────────────────────┘
                       │  REST API (JWT 인증)
                       ▼
┌──────────────────────────────────────────────────────────────────┐
│                     Backend (FastAPI · Python)                     │
│                                                                    │
│  ① 이미지 수신 — 멀티파트 수신, 포맷·크기 검증 (최대 20MB)          │
│                                                                    │
│  ② 병렬 처리 (asyncio.gather)                                      │
│     ├─ [이미지 저장]  →  AWS S3 업로드, 저장 경로(key) 반환         │
│     └─ [AI 추론]     →  SageMaker → 로컬 서버 → Mock 순 fallback   │
│                                                                    │
│  ③ 위험도 판정 (룰 기반)                                            │
│     └─ suspicious / danger → 전문의 방문 권장 플래그 자동 설정      │
│                                                                    │
│  ④ AI 설명 생성 (Gemini 2.0 Flash)                                 │
│     └─ 분석 결과 + 과거 이력 전달 → 상태 설명, 관리법 텍스트 생성   │
│        Redis 캐시 → 동일 결과 중복 호출 방지 / 실패 시 fallback     │
│                                                                    │
│  ⑤ DB 저장 및 응답 반환                                             │
│     └─ 분석 결과 전체를 RDS에 저장, 면책 문구 포함하여 응답          │
│                                                                    │
└──────┬───────────────────┬──────────────────┬────────────────────┘
       │                   │                  │
       ▼                   ▼                  ▼
┌─────────────┐   ┌──────────────────┐   ┌──────────────────────┐
│  AI 모델    │   │   AWS S3          │   │   AWS RDS            │
│  (SageMaker │   │   (이미지 저장소)  │   │   (PostgreSQL)       │
│   or Mock)  │   │                  │   │                      │
│             │   │ • user_image/    │   │ • users              │
│ • 안면피부  │   │   skin/          │   │ • analyses           │
│   분류      │   │   lesion/        │   │ • lesion_tracks      │
│ • 병변 분류 │   │ • Presigned URL  │   │ • lesion_analyses    │
│ • 신뢰도   │   │   방식 접근       │   │ • alembic_version    │
└─────────────┘   └──────────────────┘   └──────────────────────┘
```

---

## 기술 스택

| 영역 | 기술 |
|------|------|
| **Frontend** | React 18, TypeScript, Vite, React Router v6 |
| **Backend** | FastAPI, SQLAlchemy (async), Alembic, Pydantic, python-jose, bcrypt |
| **Database** | AWS RDS PostgreSQL, asyncpg |
| **이미지 저장소** | AWS S3, boto3 |
| **AI 추론** | AWS SageMaker (미연동 시 Mock fallback) |
| **AI 설명** | Google Gemini 2.0 Flash (미설정 시 fallback 메시지) |
| **캐시** | ElastiCache Redis (미연동 시 메모리 캐시 fallback) |

---

## 환경 변수 설정 (.env)

프로젝트 루트에 `.env` 파일을 생성합니다.

```env
# ── AWS 자격증명 ───────────────────────────────────────
AWS_REGION=ap-northeast-2
AWS_ACCESS_KEY_ID=발급받은-액세스-키-ID
AWS_SECRET_ACCESS_KEY=발급받은-시크릿-키

# ── Database (AWS RDS PostgreSQL) ──────────────────────
DATABASE_URL=postgresql+asyncpg://유저명:비밀번호@RDS엔드포인트:5432/postgres?ssl=require

# ── 이미지 저장소 (AWS S3) ─────────────────────────────
STORAGE_ENDPOINT=
STORAGE_ACCESS_KEY=
STORAGE_SECRET_KEY=
STORAGE_BUCKET=버킷이름
STORAGE_REGION=ap-northeast-2

# ── AI 모델 (SageMaker) ────────────────────────────────
# 비워두면 로컬 서버 → Mock 순으로 fallback
SAGEMAKER_ENDPOINT_NAME=

# ── 로컬 모델 서버 ─────────────────────────────────────
AI_MODEL_BASE_URL=http://127.0.0.1:8001

# ── 캐시 (ElastiCache Redis) ───────────────────────────
# 비워두면 메모리 캐시 fallback
REDIS_URL=

# ── Gemini API ─────────────────────────────────────────
# 비워두면 fallback 메시지 반환
GEMINI_API_KEY=

# ── JWT ────────────────────────────────────────────────
JWT_SECRET=랜덤-시크릿-문자열
JWT_EXPIRE_MINUTES=60

# ── CORS ───────────────────────────────────────────────
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

---

## 로컬 실행 방법

### 사전 요구사항

| 도구 | 버전 |
|------|------|
| Python | 3.13 |
| Node.js | 18 이상 |
| npm | 8 이상 |

---

### 1단계 — 백엔드 실행

```powershell
cd backend
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

> `alembic upgrade head` — DB 테이블 최초 생성 시 한 번만 실행합니다.

---

### 2단계 — 프론트엔드 실행

```powershell
cd frontend
npm install
npm run dev
```

---

### 3단계 — 모델 서버 실행 (선택)

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

## AI 추론 우선순위

서비스는 아래 순서로 AI 추론을 시도합니다. 상위 서비스가 실패하면 자동으로 다음으로 fallback됩니다.

```
1순위: AWS SageMaker 엔드포인트   (SAGEMAKER_ENDPOINT_NAME 설정 시)
2순위: 로컬 모델 서버              (AI_MODEL_BASE_URL 서버 실행 시)
3순위: Mock                       (항상 동작, 랜덤 결과 반환)
```

---

## 주의사항

- `.env` 파일은 `.gitignore`에 포함되어 있습니다.
- RDS 보안 그룹은 운영 환경에서 EC2 보안 그룹 ID만 허용하도록 변경하십시오.
- 본 서비스의 AI 분석 결과는 의학적 진단이 아닙니다.
