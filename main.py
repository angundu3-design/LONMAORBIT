from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os, base64, datetime, json, urllib.request, urllib.error

app = FastAPI()

USERS = {
 "admin": {"username":"admin","email":"admin@lonmaorbit.co.ke","password":"Lonma@2026"},
 "Mongelah": {"username":"Mongelah","email":"mongelah@lonmaorbit.co.ke","password":"1234"},
}

PRODUCTS = [
 {"id":1,"name":"Rice 2kg Pishori","price":280,"cat":"Food","stock":100,"image":""},
 {"id":2,"name":"Cooking Oil 1L","price":220,"cat":"Food","stock":80,"image":""},
 {"id":3,"name":"Sugar 2kg Kabras","price":310,"cat":"Food","stock":90,"image":""},
 {"id":4,"name":"Bread 400g","price":60,"cat":"Food","stock":50,"image":""},
 {"id":5,"name":"Milk 500ml Fresh","price":60,"cat":"Food","stock":100,"image":""},
 {"id":7,"name":"Eggs Tray 30pcs","price":650,"cat":"Food","stock":40,"image":""},
 {"id":11,"name":"Extension 4-Way","price":850,"cat":"Electronics","stock":25,"image":""},
 {"id":12,"name":"LED Bulb 12W","price":250,"cat":"Electronics","stock":100,"image":""},
 {"id":13,"name":"Phone Charger Fast","price":650,"cat":"Electronics","stock":40,"image":""},
 {"id":14,"name":"Power Bank 10000mAh","price":1800,"cat":"Electronics","stock":15,"image":""},
 {"id":19,"name":"T-Shirt Unisex","price":450,"cat":"Clothes","stock":60,"image":""},
 {"id":20,"name":"Trouser Jeans","price":1200,"cat":"Clothes","stock":35,"image":""},
 {"id":26,"name":"Water 1L","price":50,"cat":"Drinks","stock":300,"image":""},
 {"id":27,"name":"Juice 1L Mango","price":150,"cat":"Drinks","stock":80,"image":""},
 {"id":28,"name":"Yoghurt 500ml","price":90,"cat":"Drinks","stock":70,"image":""},
 {"id":29,"name":"Beer Tusker 500ml","price":180,"cat":"Drinks","stock":100,"image":""},
 {"id":30,"name":"Wine 750ml","price":850,"cat":"Drinks","stock":20,"image":""},
 {"id":31,"name":"Soda 500ml","price":60,"cat":"Drinks","stock":200,"image":""},
 {"id":32,"name":"Fresh Fri Cooking Oil 2L","price":650,"cat":"Food","stock":60,"image":"freshfri.jpg"},
 {"id":33,"name":"Detrex Citronella Oil","price":60,"cat":"Toiletries","stock":200,"image":"detrex_citronella.jpg"},
 {"id":34,"name":"Sawa Lotion For Men 72Hrs","price":280,"cat":"Toiletries","stock":80,"image":"sawa.jpg"},
 {"id":35,"name":"Detrex Pine Drops","price":60,"cat":"Toiletries","stock":200,"image":"detrex_pine.jpg"},
 {"id":36,"name":"Salit Cooking Oil 5L","price":1250,"cat":"Food","stock":40,"image":"salit.jpg"},
 {"id":37,"name":"Detrex Cool Mint","price":60,"cat":"Toiletries","stock":200,"image":"detrex_cool.jpg"},
 {"id":38,"name":"Diva Anti-Dandruff 250ml","price":280,"cat":"Toiletries","stock":90,"image":"diva_dandruff.jpg"},
 {"id":39,"name":"Detrex Aloe Vera","price":60,"cat":"Toiletries","stock":200,"image":"detrex_aloe.jpg"},
 {"id":40,"name":"Diva Anti-Breakage & Growth 250ml","price":300,"cat":"Toiletries","stock":90,"image":"diva_growth.jpg"},
]

CONSUMER_KEY = os.getenv("MPESA_CONSUMER_KEY", "")
CONSUMER_SECRET = os.getenv("MPESA_CONSUMER_SECRET", "")
SHORTCODE = os.getenv("MPESA_SHORTCODE", "174379")
PASSKEY = os.getenv("MPESA_PASSKEY", "bfb279f9aa9bdbcf158e97dd71a467cd2e0c893059b10f78e6b72ada1ed2c919")
CALLBACK_URL = os.getenv("MPESA_CALLBACK", "https://app.lonmaorbit.co.ke/api/callback")

def http_get(url, auth=None):
    req = urllib.request.Request(url)
    if auth:
        cred = base64.b64encode(f"{auth[0]}:{auth[1]}".encode()).decode()
        req.add_header("Authorization", f"Basic {cred}")
    try:
        with urllib.request.urlopen(req, timeout=20) as r: return json.loads(r.read().decode())
    except: return {}

def http_post(url, payload, token=None):
    data = json.dumps(payload).encode()
    req = urllib.request.Request(url, data=data, headers={"Content-Type":"application/json"})
    if token: req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=20) as r: return json.loads(r.read().decode())
    except urllib.error.HTTPError as e: return {"error": e.read().decode()}
    except Exception as e: return {"error": str(e)}

@app.get("/")
def root(): return FileResponse("static/index.html")

@app.get("/api/products")
def get_products(cat: str = None):
    if cat and cat!="All": return [p for p in PRODUCTS if p["cat"]==cat]
    return PRODUCTS

@app.post("/api/register")
def register(data: dict):
    USERS[data.get("username","")]=data; USERS[data.get("email","")]=data
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
    if not CONSUMER_KEY: return {"ok":True,"msg":"DEMO MODE - Enter M-Pesa PIN on phone","phone":phone,"amount":amount}
    try:
        token_data = http_get("https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials", auth=(CONSUMER_KEY, CONSUMER_SECRET))
        token = token_data.get("access_token")
        if not token: return {"ok":False,"error":"token failed","detail":token_data}
        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        password = base64.b64encode((SHORTCODE+PASSKEY+timestamp).encode()).decode()
        payload = {"BusinessShortCode": SHORTCODE,"Password": password,"Timestamp": timestamp,"TransactionType": "CustomerPayBillOnline","Amount": amount,"PartyA": phone,"PartyB": SHORTCODE,"PhoneNumber": phone,"CallBackURL": CALLBACK_URL,"AccountReference": "LONMA MART","TransactionDesc": "LONMA MART"}
        resp = http_post("https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest", payload, token=token)
        return {"ok":True,"daraja":resp,"phone":phone}
    except Exception as e: return {"ok":False,"error":str(e)}

@app.post("/api/callback")
async def callback(req: Request):
    data = await req.json(); print("CALLBACK:", data); return {"ok":True}

if os.path.exists("static"): app.mount("/static", StaticFiles(directory="static"), name="static")
