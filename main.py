from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os, requests, base64, datetime

app = FastAPI()

USERS = {
 "admin": {"username":"admin","email":"admin@lonmaorbit.co.ke","password":"Lonma@2026"},
 "Mongelah": {"username":"Mongelah","email":"mongelah@lonmaorbit.co.ke","password":"1234"},
}

PRODUCTS = [
 {"id":1,"name":"Rice 2kg Pishori","price":280,"cat":"Food","stock":100},
 {"id":2,"name":"Cooking Oil 1L","price":220,"cat":"Food","stock":80},
 {"id":3,"name":"Sugar 2kg Kabras","price":310,"cat":"Food","stock":90},
 {"id":4,"name":"Bread 400g","price":60,"cat":"Food","stock":50},
 {"id":5,"name":"Milk 500ml Fresh","price":60,"cat":"Food","stock":100},
 {"id":7,"name":"Eggs Tray 30pcs","price":650,"cat":"Food","stock":40},
 {"id":11,"name":"Extension 4-Way","price":850,"cat":"Electronics","stock":25},
 {"id":12,"name":"LED Bulb 12W","price":250,"cat":"Electronics","stock":100},
 {"id":13,"name":"Phone Charger Fast","price":650,"cat":"Electronics","stock":40},
 {"id":14,"name":"Power Bank 10000mAh","price":1800,"cat":"Electronics","stock":15},
 {"id":19,"name":"T-Shirt Unisex","price":450,"cat":"Clothes","stock":60},
 {"id":20,"name":"Trouser Jeans","price":1200,"cat":"Clothes","stock":35},
 {"id":26,"name":"Water 1L","price":50,"cat":"Drinks","stock":300},
 {"id":27,"name":"Juice 1L Mango","price":150,"cat":"Drinks","stock":80},
 {"id":28,"name":"Yoghurt 500ml","price":90,"cat":"Drinks","stock":70},
 {"id":29,"name":"Beer Tusker 500ml","price":180,"cat":"Drinks","stock":100},
 {"id":30,"name":"Wine 750ml","price":850,"cat":"Drinks","stock":20},
 {"id":31,"name":"Soda 500ml","price":60,"cat":"Drinks","stock":200},
]

# --- DARAJA CONFIG ---
# Set these in Render -> Environment
CONSUMER_KEY = os.getenv("MPESA_CONSUMER_KEY", "")
CONSUMER_SECRET = os.getenv("MPESA_CONSUMER_SECRET", "")
SHORTCODE = os.getenv("MPESA_SHORTCODE", "174379") # Test paybill
PASSKEY = os.getenv("MPESA_PASSKEY", "bfb279f9aa9bdbcf158e97dd71a467cd2e0c893059b10f78e6b72ada1ed2c919")
CALLBACK_URL = os.getenv("MPESA_CALLBACK", "https://app.lonmaorbit.co.ke/api/callback")

def get_token():
    if not CONSUMER_KEY: return None
    url = "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"
    r = requests.get(url, auth=(CONSUMER_KEY, CONSUMER_SECRET))
    return r.json().get("access_token")

@app.get("/")
def root(): return FileResponse("static/index.html")

@app.get("/api/products")
def get_products(cat: str = None):
    if cat and cat!="All": return [p for p in PRODUCTS if p["cat"]==cat]
    return PRODUCTS

@app.post("/api/register")
def register(data: dict):
    USERS[data.get("username","")]=data
    USERS[data.get("email","")]=data
    return {"ok":True}

@app.post("/api/login")
def login(data: dict):
    k=data.get("username","").strip(); pw=data.get("password","").strip()
    for v in USERS.values():
        if (v.get("email")==k or v.get("username")==k) and v.get("password")==pw:
            return {"ok":True,"username":v["username"],"email":v["email"]}
    return {"ok":False}

@app.post("/api/stk")
async def stk_push(req: Request):
    d = await req.json()
    phone = d.get("phone","").replace(" ","").replace("+","")
    amount = int(d.get("amount",1))
    if phone.startswith("0"): phone = "254"+phone[1:]
    if phone.startswith("7"): phone = "254"+phone
    # If Daraja keys not set, simulate success (for testing)
    if not CONSUMER_KEY:
        return {"ok":True,"msg":"DEMO - Enter PIN on phone","phone":phone,"amount":amount,"note":"Set MPESA keys in Render to go live"}
    try:
        token = get_token()
        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        password = base64.b64encode((SHORTCODE+PASSKEY+timestamp).encode()).decode()
        headers = {"Authorization": f"Bearer {token}"}
        payload = {
            "BusinessShortCode": SHORTCODE,
            "Password": password,
            "Timestamp": timestamp,
            "TransactionType": "CustomerPayBillOnline",
            "Amount": amount,
            "PartyA": phone,
            "PartyB": SHORTCODE,
            "PhoneNumber": phone,
            "CallBackURL": CALLBACK_URL,
            "AccountReference": "LONMA MART",
            "TransactionDesc": "LONMA MART Payment"
        }
        url = "https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest"
        resp = requests.post(url, json=payload, headers=headers)
        return {"ok":True,"daraja":resp.json(),"phone":phone}
    except Exception as e:
        return {"ok":False,"error":str(e)}

@app.post("/api/callback")
async def callback(req: Request):
    data = await req.json()
    print("M-PESA CALLBACK:", data)
    return {"ok":True}

if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")
