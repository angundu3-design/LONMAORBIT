from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import os

app = FastAPI()

class Login(BaseModel):
    username: str
    password: str
class Pay(BaseModel):
    phone: str
    amount: int
class Chat(BaseModel):
    msg: str

PRODUCTS = [
    {"id":1,"name":"Sawa Lotion Men 500ML","price":450,"code":"SWA-MEN-017","comment":"Best seller","cat":"Body Lotion"},
    {"id":2,"name":"Fresh Fri 5L","price":850,"code":"FF-5L-001","comment":"SALE - Limited stock","cat":"Cooking Oil"},
    {"id":3,"name":"Sawa Lotion Women","price":450,"code":"SWA-WOM-018","comment":"New","cat":"Body Lotion"},
    {"id":4,"name":"Detox Tea","price":1200,"code":"DTX-001","comment":"SALE","cat":"Wellness"},
    {"id":5,"name":"Salt 2kg","price":180,"code":"SLT-2KG-005","comment":"Essential","cat":"Groceries"},
    {"id":6,"name":"Sawa Lotion 250ML","price":250,"code":"SWA-250-019","comment":"","cat":"Body Lotion"},
    {"id":7,"name":"Fresh Fri 2L","price":400,"code":"FF-2L-002","comment":"","cat":"Cooking Oil"},
    {"id":8,"name":"Sugar 2kg","price":320,"code":"SUG-2KG-010","comment":"","cat":"Groceries"},
    {"id":9,"name":"Rice 5kg","price":650,"code":"RIC-5KG-011","comment":"","cat":"Groceries"},
    {"id":10,"name":"Cooking Oil 1L","price":220,"code":"OIL-1L-003","comment":"","cat":"Cooking Oil"},
    {"id":11,"name":"Bar Soap","price":80,"code":"SOAP-001","comment":"","cat":"Groceries"},
    {"id":12,"name":"Face Cream","price":350,"code":"FACE-001","comment":"","cat":"Body Lotion"},
    {"id":13,"name":"Hair Oil","price":300,"code":"HAIR-001","comment":"","cat":"Body Lotion"},
    {"id":14,"name":"Green Tea","price":250,"code":"TEA-GRN-020","comment":"","cat":"Wellness"},
    {"id":15,"name":"Honey 500g","price":500,"code":"HON-500-021","comment":"","cat":"Wellness"},
    {"id":16,"name":"Flour 2kg","price":180,"code":"FLR-2KG-012","comment":"","cat":"Groceries"},
    {"id":17,"name":"Milk 500ML","price":70,"code":"MLK-500-013","comment":"","cat":"Groceries"},
    {"id":18,"name":"Bread","price":70,"code":"BRD-001","comment":"","cat":"Groceries"},
    {"id":19,"name":"Soda 1L","price":120,"code":"SOD-1L-014","comment":"","cat":"Groceries"},
    {"id":20,"name":"Water 1L","price":40,"code":"WAT-1L-015","comment":"","cat":"Groceries"},
    {"id":21,"name":"Toothpaste","price":150,"code":"TTH-001","comment":"","cat":"Body Lotion"},
]

@app.post("/api/login")
def login(d: Login):
    if (d.username=="Mongelah" and d.password=="1234") or (d.username=="admin" and d.password=="Lonma@2026"):
        return {"ok":True}
    return {"ok":False}

@app.get("/api/products")
def products():
    return PRODUCTS

@app.post("/api/stk")
def stk(d: Pay):
    return {"msg":"DEMO MODE","phone":d.phone,"amount":d.amount}

@app.post("/api/chat")
def chat(d: Chat):
    q = d.msg.lower()
    if "price" in q or "cost" in q:
        return {"reply": "💰 Prices start KES 40 - 1200. Best sellers: Sawa Lotion 450, Fresh Fri 5L 850 (SALE!), Salt 180. What product price you need?"}
    if "delivery" in q or "deliver" in q:
        return {"reply": "🚚 We deliver SAME DAY in Nairobi. KES 100-250 delivery fee. Free delivery over KES 2000!"}
    if "lotion" in q or "sawa" in q:
        return {"reply": "🧴 Sawa Lotion Men 500ML KES 450 (Code SWA-MEN-017) - Best seller! Also Women 450, 250ML 250. Want to add to cart?"}
    if "oil" in q or "fresh fri" in q:
        return {"reply": "🍳 Fresh Fri 5L KES 850 - SALE! Limited stock. 2L KES 400, 1L KES 220. Which size?"}
    if "pay" in q or "mpesa" in q:
        return {"reply": "📱 Pay via M-Pesa: Add items to cart, enter 07xx number, click PAY. You'll get STK prompt instantly!"}
    if "hello" in q or "hi" in q or "habari" in q:
        return {"reply": "👋 Habari! Welcome to LONMA ORBIT. I'm your shopping assistant. Ask me about products, prices, delivery, or how to pay! SHOP • SAVE • DELIVER"}
    return {"reply": f"🤖 LONMA Bot: You asked '{d.msg}'. I can help with: \n• Product prices & stock\n• Delivery info\n• How to pay M-Pesa\n• Best sellers\nTry: 'price of lotion' or 'delivery fee'"}

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def root():
    return FileResponse("static/index.html")
