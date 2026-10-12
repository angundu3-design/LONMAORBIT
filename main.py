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
 {"id":1,"name":"Fresh Fri 5L","price":850,"code":"FF-5L-001","comment":"SALE","cat":"Cooking Oil"},
 {"id":2,"name":"Fresh Fri 2L","price":400,"code":"FF-2L-002","comment":"SALE","cat":"Cooking Oil"},
 {"id":3,"name":"Fresh Fri 1L","price":220,"code":"FF-1L-003","comment":"SALE","cat":"Cooking Oil"},
 {"id":4,"name":"Salt 2kg","price":180,"code":"SLT-2KG-005","comment":"SALE","cat":"Groceries"},
 {"id":5,"name":"Salt 1kg","price":100,"code":"SLT-1KG-006","comment":"SALE","cat":"Groceries"},
 {"id":6,"name":"Detox Tea","price":1200,"code":"DTX-001","comment":"SALE","cat":"Wellness"},
 {"id":7,"name":"Green Tea","price":250,"code":"DTX-020","comment":"SALE","cat":"Wellness"},
 {"id":8,"name":"Sawa Lotion Men 500ML","price":450,"code":"SWA-MEN-017","comment":"Best Seller","cat":"Body Lotion"},
 {"id":9,"name":"Sawa Lotion Women","price":450,"code":"SWA-WOM-018","comment":"Best Seller","cat":"Body Lotion"},
 {"id":10,"name":"Sawa 250ML","price":250,"code":"SWA-250-019","comment":"","cat":"Body Lotion"},
 {"id":11,"name":"Sugar 2kg","price":320,"code":"SUG-010","comment":"","cat":"Groceries"},
 {"id":12,"name":"Rice 5kg","price":650,"code":"RIC-011","comment":"","cat":"Groceries"},
]
@app.post("/api/login")
def login(d: Login):
 if (d.username=="Mongelah" and d.password=="1234") or (d.username=="admin" and d.password=="Lonma@2026"):
  return {"ok":True}
 return {"ok":False}
@app.get("/api/products")
def products():
 return sorted(PRODUCTS, key=lambda p: 0 if p["code"].startswith(("FF","SLT","DTX")) else 1)
@app.post("/api/stk")
def stk(d: Pay):
 return {"msg":"DEMO","phone":d.phone,"amount":d.amount}
@app.post("/api/chat")
def chat(d: Chat):
 q=d.msg.lower()
 if "code" in q:
  return {"reply":"FF=Fresh Fri, SLT=Salt, DTX=Detox, SWA=Sawa"}
 if "sale" in q:
  return {"reply":"SALE: Fresh Fri 5L 850, 2L 400, Salt 180, Detox 1200"}
 return {"reply":"Ask about codes or sale"}
app.mount("/static", StaticFiles(directory="static"), name="static")
@app.get("/")
def root():
 return FileResponse("static/index.html")
