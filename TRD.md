# 문의 답변 도우미 TRD

## 1. 문서 목적

[PRD.md](PRD.md)에 정의한 문의 답변 도우미의 기술 구성과 구현 방식을 정리한다.

## 2. 시스템 구성

```
브라우저 (HTML 폼)
   ↓ POST
FastAPI 앱 (main.py)
   ├─ 앱 메모리: 샘플 주문 20건, 처리한 문의 목록
   └─ GitHub Copilot SDK (CopilotClient) → Copilot CLI → 언어 모델
```

- 서버 렌더링 방식이다. 페이지는 Jinja2 템플릿으로 만들고, 자바스크립트는 쓰지 않는다.
- 모든 코드는 `main.py` 파일 하나에 있다.

## 3. 기술 스택

| 구분 | 내용 |
|---|---|
| 언어 | Python 3.11 |
| 웹 프레임워크 | FastAPI, Jinja2 템플릿, python-multipart (폼 처리) |
| 실행 서버 | gunicorn + uvicorn 워커 1개, 타임아웃 120초 |
| AI 연결 | GitHub Copilot SDK (`github-copilot-sdk`), Copilot CLI (`@github/copilot`, Node.js 22) |
| 데이터 저장 | 앱 메모리 (파이썬 딕셔너리·리스트) |
| 호스팅 | Azure App Service (Linux, B1) |

## 4. 화면과 API

| 메서드 | 경로 | 기능 | 템플릿 |
|---|---|---|---|
| GET | `/` | 문의 입력 화면 | `index.html` |
| POST | `/` | 문의 처리: AI 답변 생성, 환불 상태 변경, 결과 표시 | `index.html` |
| GET | `/inquiries?status=` | 문의 목록. 환불 상태(전체/없음/환불완료)로 필터 | `list.html` |
| GET | `/admin` | 데이터 초기화 화면 | `admin.html` |
| POST | `/admin` | 비밀번호가 맞으면 주문과 문의 목록을 처음 상태로 되돌림 | `admin.html` |

POST `/` 입력값:

| 필드 | 필수 | 제한 |
|---|:-:|---|
| `customer_name` | O | |
| `order_number` | O | `ORD-1001` ~ `ORD-1020` |
| `inquiry` | O | 최대 2000자 |

## 5. 데이터 구조

### 5.1 주문 (`orders`)

앱이 시작될 때 `create_sample_orders()`가 주문 20건(`ORD-1001` ~ `ORD-1020`)을 만든다.

| 필드 | 예시 | 설명 |
|---|---|---|
| `order_number` | `ORD-1003` | 주문번호 |
| `customer_name` | `고객3` | 고객명 |
| `phone` | `010-0000-1003` | 연락처 |
| `product_name` | `샘플 상품 3` | 상품명 |
| `amount` | `30000` | 금액 (번호 × 10,000원) |
| `order_date` | `2026-10-03` | 주문일 |
| `shipping_status` | `배송완료` | 배송준비 / 배송중 / 배송완료 순환 |
| `refund_status` | `없음` | 없음 / 환불완료 |

### 5.2 문의 (`inquiries`)

| 필드 | 설명 |
|---|---|
| `customer_name` | 입력한 고객명 |
| `order_number` | 입력한 주문번호 |
| `inquiry` | 문의 내용 |
| `raw_response` | 모델 원본 응답 |
| `reply` | 답변 |
| `refund_status` | 처리 직후 환불 상태 |

데이터는 메모리에만 있다. 앱이 다시 시작되면 처음 상태로 돌아간다.

## 6. AI 처리 흐름

1. 입력한 주문번호로 `orders`에서 주문 정보를 찾는다.
2. `CopilotClient`를 만들고 시작한다.
3. 세션을 만든다.
   - 모델: `auto`
   - 권한 처리: `PermissionHandler.approve_all`
4. 프롬프트를 보낸다. 프롬프트에는 주문 정보와 문의 내용이 들어 있고, 다음 형식의 JSON으로만 답하라고 지시한다.
   ```json
   {"reply": "답변", "refund": true 또는 false}
   ```
5. `send_and_wait`로 응답을 기다린 뒤 클라이언트를 종료한다.
6. 응답을 JSON으로 읽는다. JSON이 아니면 응답 전체를 답변으로 쓰고 `refund`는 `false`로 둔다.
7. `refund`가 `true`이면 주문의 `refund_status`를 `환불완료`로 바꾼다.
8. 문의 기록을 `inquiries`에 추가하고, 모델 원본 응답을 결과 영역에 표시한다.

문의 1건마다 Copilot 클라이언트를 새로 시작하고 종료한다. 에이전트 프레임워크는 쓰지 않고, 프롬프트를 한 번 보내고 응답을 한 번 받는다.

## 7. 인증과 설정

| 항목 | 방식 |
|---|---|
| Copilot 인증 | 환경변수 `GITHUB_TOKEN` (Copilot SDK가 읽음) |
| 관리자 비밀번호 | `main.py`의 상수 `ADMIN_PASSWORD` |
| 사용자 인증 | 없음. 로그인 없이 모든 화면에 접근 |

`.env`와 `copilot-prompt.md`는 `.gitignore`와 `.dockerignore`로 저장소와 이미지에서 제외한다.

## 8. 배포
