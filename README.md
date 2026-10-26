# 문의 답변 도우미

고객 문의에 AI가 답변 초안을 만들어 주는 웹 앱

[기획서](기획서(PRD).md)

## 실행 방법

```bash
pip install -r requirements.txt
set GITHUB_TOKEN=발급받은토큰
uvicorn main:app
```

배포 링크: (https://inquiry-helper-isp829.azurewebsites.net)

샘플 주문번호: `ORD-1001` ~ `ORD-1020`

## 사용 예시
- 샘플 주문번호는 ORD-1001 ~ ORD-1020입니다. 목록에 없는 주문번호는 처리되지 않습니다.
- 예시 1: 고객명 홍길동, 주문번호 ORD-1003, 문의 내용 "배송이 언제 오나요?"
- 예시 2: 고객명 홍길동, 주문번호 ORD-1007, 문의 내용 "환불해 주세요"
- 문의 처리를 누르면 답변이 화면에 표시됩니다. 응답까지 수십 초 걸릴 수 있습니다.
