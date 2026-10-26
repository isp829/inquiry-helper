import json

from fastapi import FastAPI, Form, Request
from fastapi.templating import Jinja2Templates
from copilot import CopilotClient
from copilot.session import PermissionHandler


ADMIN_PASSWORD = "admin1234"

app = FastAPI()
templates = Jinja2Templates(directory="templates")


def create_sample_orders():
    orders = {}
    for number in range(1001, 1021):
        order_number = f"ORD-{number}"
        orders[order_number] = {
            "order_number": order_number,
            "customer_name": f"고객{number - 1000}",
            "phone": f"010-0000-{number}",
            "product_name": f"샘플 상품 {number - 1000}",
            "amount": (number - 1000) * 10000,
            "order_date": f"2026-10-{(number - 1000):02d}",
            "shipping_status": ("배송준비", "배송중", "배송완료")[
                (number - 1001) % 3
            ],
            "refund_status": "없음",
        }
    return orders


orders = create_sample_orders()
inquiries = []


@app.get("/")
async def home(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"result": None},
    )


@app.post("/")
async def process_inquiry(
    request: Request,
    customer_name: str = Form(...),
    order_number: str = Form(...),
    inquiry: str = Form(..., max_length=2000),
):
    order = orders[order_number]
    client = CopilotClient()
    await client.start()
    session = await client.create_session(
        on_permission_request=PermissionHandler.approve_all,
        model="auto",
    )
    prompt = (
        '다음 주문 정보와 고객 문의를 참고해 답변을 작성하세요. '
        '반드시 {"reply": "답변", "refund": true 또는 false} 형식의 JSON만 답하세요.\n'
        f"주문 정보: {order}\n"
        f"고객 문의: {inquiry}"
    )
    response = await session.send_and_wait(prompt)
    await client.stop()
    raw_response = response.data.content
    try:
        response_data = json.loads(raw_response)
    except json.JSONDecodeError:
        response_data = {"reply": raw_response, "refund": False}

    if response_data["refund"] is True:
        order["refund_status"] = "환불완료"

    print(customer_name, order["phone"], inquiry)
    inquiries.append(
        {
            "customer_name": customer_name,
            "order_number": order_number,
            "inquiry": inquiry,
            "raw_response": raw_response,
            "reply": response_data["reply"],
            "refund_status": order["refund_status"],
        }
    )
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"result": raw_response},
    )


@app.get("/inquiries")
async def inquiry_list(request: Request, status: str = "전체"):
    status_filters = {
        "전체": None,
        "없음": "없음",
        "환불완료": "환불완료",
    }
    status_filter = status_filters[status]
    filtered_inquiries = inquiries
    if status_filter is not None:
        filtered_inquiries = [
            item
            for item in inquiries
            if orders[item["order_number"]]["refund_status"] == status_filter
        ]
    return templates.TemplateResponse(
        request=request,
        name="list.html",
        context={
            "inquiries": filtered_inquiries,
            "status": status,
        },
    )


@app.get("/admin")
async def admin_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="admin.html",
        context={"message": None},
    )


@app.post("/admin")
async def reset_data(request: Request, password: str = Form(...)):
    global orders
    if password == ADMIN_PASSWORD:
        orders = create_sample_orders()
        inquiries.clear()
        message = "초기화되었습니다."
    else:
        message = "비밀번호가 맞지 않습니다."
    return templates.TemplateResponse(
        request=request,
        name="admin.html",
        context={"message": message},
    )
