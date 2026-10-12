from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

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
    {"id":1,"name":"Fresh Fri Cooking Oil 5L","price":850,"code":"FF-5L-001","comment":"SALE - Best Deal","cat":"Cooking Oil"},
    {"id":2,"name":"Fresh Fri Cooking Oil 2L","price":400,"code":"FF-2L-002","comment":"SALE","cat":"Cooking Oil"},
    {"id":3,"name":"Fresh Fri Cooking Oil 1L","price":220,"code":"FF-1L-003","comment":"SALE","cat":"Cooking Oil"},
    {"id":4,"name":"Himalayan Salt 2kg","price":180,"code":"SLT-2KG-005","comment":"SALE - Essential","cat":"Groceries"},
    {"id":5,"name":"Himalayan Salt 1kg","price":100,"code":"SLT-1KG-006","comment":"SALE","cat":"Groceries"},
    {"id":6,"name":"Detox Slim Tea 28 Days","price":1200,"code":"DTX-SLIM-001","comment":"SALE - Wellness","cat":"Wellness"},
    {"id":7,"name":"Detox Green Tea","price":250,"code":"DTX-GRN-020","comment":"SALE","cat":"Wellness"},
    {"id":8,"name":"Sawa Body Lotion Men 500ML","price":450,"code":"SWA-MEN-500-017","comment":"Best Seller Men","cat":"Body Lotion"},
    {"id":9,"name":"Sawa Body Lotion Women 500ML","price":450,"code":"SWA-WOM-500-018","comment":"Best Seller Women","cat":"Body Lotion"},
    {"id":10,"name":"Sawa Lotion 250ML","price":250,"code":"SWA-250-019","comment":"Travel Size","cat":"Body Lotion"},
    {"id":11,"name":"Sugar 2kg Kabras","price":320,"code":"SUG-2KG-010","comment":"Daily Essential","cat":"Groceries"},
    {"id":12,"name":"Pishori Rice 5kg","price":650,"code":"RIC-PIS-5KG-011","comment":"Premium","cat":"Groceries"},
    {"id":13,"name":"Wheat Flour 2kg","price":180,"code":"FLR-WHT-2KG-012","comment":"","cat":"Groceries"},
    {"id":14,"name":"Fresh Milk 500ML","price":70,"code":"MLK-500-013","comment":"","cat":"Groceries"},
    {"id":15,"name":"White Bread 400g","price":70,"code":"BRD-WHT-001","comment":"","cat":"Groceries"},
    {"id":16,"name":"Bar Soap 200g","price":80,"code":"SOAP-BAR-001","comment":"","cat":"Groceries"},
    {"id":17,"name":"Honey 500g Pure","price":500,"code":"HON-PUR-500-021","comment":"Natural","cat":"Wellness"},
    {"id":18,"name":"Face Cream Glow","price":350,"code":"FACE-GLW-001","comment":"","cat":"Body Lotion"},
    {"id":19,"name":"Hair Growth Oil","price":300,"code":"HAIR-GRO-001","comment":"","cat":"Body Lotion"},
    {"id":20,"name":"Soda 1L","price":120,"code":"SOD-1L-014","comment":"","cat":"Groceries"},
    {"id":21,"name":"Water 1L","price":40,"code":"WAT-1L-015","comment":"","cat":"Groceries"},
]

@app.post("/api/login")
def login(d: Login):
    if (d.username=="Mongelah" and d.password=="1234") or (d.username=="admin" and d.password=="Lonma@2026"):
        return {"ok":True}
    return {"ok":False}

@app.get("/api/products")
def products():
    def sale_priority(p):
        code = p.get("code","")
        if code.startswith(("FF","SLT","DTX")):
            return 0
        return 1
    return sorted(PRODUCTS, key=sale_priority)

@app.post("/api/stk")
def stk(d: Pay):
    return {"msg":"DEMO","phone":d.phone,"amount":d.amount}

@app.post("/api/chat")
def chat(d: Chat):
    q=d.msg.lower()
    if "code" in q:
        return {"reply":"CODES: FF=Fresh Fri Oil, SLT=Salt, DTX=Detox Tea, SWA=Sawa Lotion, SUG=Sugar, RIC=Rice. Each code is unique SKU."}
    if "sale" in q:
        return {"reply":"ON SALE: Fresh Fri 5L 850, 2L 400, 1L 220, Salt 2kg 180, Detox Tea 1200, Green Tea 250. Gold border!"}
    if "price" in q:
        return {"reply":"Prices KES 40-1200. Best: Sawa 450, Fresh Fri 5L 850 SALE!"}
    return {"reply":f"Bot: You said '{d.msg}'. Ask 'what is code' or 'sale items'"}

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def root():
    return FileResponse("static/index.html")
