from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os, base64, datetime, json, urllib.request, urllib.error

app = FastAPI(title="LONMA ORBIT API")

USERS = {
 "admin": {"username":"admin","email":"admin@lonmaorbit.co.ke","password":"Lonma@2026"},
 "Mongelah": {"username":"Mongelah","email":"mongelah@lonmaorbit.co.ke","password":"1234"},
}

# ==================== PRODUCTS WITH CODES + COMMENTS ====================
PRODUCTS = [
 # FOOD - SALE (Fresh Fri + Salit) - YOUR 5Ltrs FIRST
 {"id":42,"name":"Fresh Fri Cooking Oil 5L","price":1250,"cat":"Food","stock":40,"image":"","code":"FF-5L-001","comment":"Fresh Fri 5Ltrs Cooking - Flagship economy jumbo - ON SALE"},
 {"id":32,"name":"Fresh Fri Cooking Oil 2L","price":650,"cat":"Food","stock":60,"image":"","code":"FF-2L-002","comment":"Best seller 2L family size"},
 {"id":43,"name":"Fresh Fri Cooking Oil 3L","price":850,"cat":"Food","stock":50,"image":"","code":"FF-3L-003","comment":"Mid size 3L popular"},
 {"id":44,"name":"Fresh Fri Cooking Oil 1L","price":350,"cat":"Food","stock":80,"image":"","code":"FF-1L-004","comment":"1L small family"},
 {"id":36,"name":"Salit Cooking Oil 5L","price":1250,"cat":"Food","stock":40,"image":"","code":"SLT-5L-005","comment":"Salit 5L premium - ON SALE"},
 {"id":45,"name":"Salit Cooking Oil 3L","price":850,"cat":"Food","stock":45,"image":"","code":"SLT-3L-006","comment":"Salit 3L"},
 {"id":46,"name":"Salit Cooking Oil 2L","price":620,"cat":"Food","stock":55,"image":"","code":"SLT-2L-007","comment":"Salit 2L value pack"},
 {"id":1,"name":"Rice 2kg Pishori","price":280,"cat":"Food","stock":100,"image":"","code":"FD-RICE-020","comment":"Pishori rice"},
 {"id":2,"name":"Sugar 2kg","price":310,"cat":"Food","stock":100,"image":"","code":"FD-SUG-021","comment":"Sugar"},

 # TOILETRIES - SALE (Detrex + Diva + Sawa) - FROM YOUR 14 LINKS
 {"id":33,"name":"Detrex Citronella 110g","price":60,"cat":"Toiletries","stock":200,"image":"","code":"DTX-CIT-008","comment":"Detrex Citronella - Mosquito repellent"},
 {"id":35,"name":"Detrex Pine 110g","price":60,"cat":"Toiletries","stock":200,"image":"","code":"DTX-PINE-009","comment":"Detrex Pine - Fresh forest"},
 {"id":37,"name":"Detrex Cool Mint 110g","price":60,"cat":"Toiletries","stock":200,"image":"","code":"DTX-MINT-010","comment":"Detrex Cool Mint - Cooling"},
 {"id":39,"name":"Detrex Aloe Vera 110g","price":60,"cat":"Toiletries","stock":200,"image":"","code":"DTX-ALOE-011","comment":"Detrex Aloe Vera - Soothing"},
 {"id":47,"name":"Detrex Lemon 110g","price":60,"cat":"Toiletries","stock":200,"image":"","code":"DTX-LEM-012","comment":"Detrex Lemon - Citrus fresh"},
 {"id":48,"name":"Detrex Original 110g","price":60,"cat":"Toiletries","stock":200,"image":"","code":"DTX-ORG-013","comment":"Detrex Original classic"},
 {"id":38,"name":"Diva Anti-Dandruff 250ml","price":280,"cat":"Toiletries","stock":90,"image":"","code":"DVA-DAND-014","comment":"Diva Anti-Dandruff Shampoo"},
 {"id":40,"name":"Diva Anti-Breakage & Growth 250ml","price":300,"cat":"Toiletries","stock":90,"image":"","code":"DVA-BRK-015","comment":"Diva Anti-Breakage for growth"},
 {"id":49,"name":"Diva Conditioning 250ml","price":280,"cat":"Toiletries","stock":90,"image":"","code":"DVA-COND-016","comment":"Diva Conditioning shampoo"},
 {"id":34,"name":"Sawa Lotion For Men 250ml","price":280,"cat":"Toiletries","stock":80,"image":"","code":"SWA-MEN-017","comment":"Sawa Lotion For Men"},
 {"id":50,"name":"Sawa Lotion For Women 250ml","price":280,"cat":"Toiletries","stock":80,"image":"","code":"SWA-WOM-018","comment":"Sawa Lotion For Women"},
 {"id":51,"name":"Sawa Soap 200g","price":70,"cat":"Toiletries","stock":150,"image":"","code":"SWA-SOAP-019","comment":"Sawa bathing soap"},

 # DRINKS
 {"id":26,"name":"Water 1L","price":50,"cat":"Drinks","stock":300,"image":"","code":"DR-WAT-022","comment":"Water"},
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
        with urllib.request.urlopen(req, timeout=20) as r:
            return json.loads(r.read().decode())
    except: return {}

def http_post(url, payload, token=None):
    data = json.dumps(payload).encode()
    req = urllib.request.Request(url, data=data, headers={"Content-Type":"application/json"})
    if token: req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return json.loads(r.read().decode())
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
    USERS[data.get("username","")] = data
    USERS[data.get("email","")] = data
    return {"ok": True}

@app.post("/api/login")
def login(data: dict):
    k = data.get("username","").strip()
    pw = data.get("password","").strip()
    for v in USERS.values():
        if (v.get("email")==k or v.get("username")==k) and v.get("password")==pw:
            return {"ok": True, "username": v["username"], "email": v["email"]}
    return {"ok": False}

@app.post("/api/stk")
async def stk_push(req: Request):
    d = await req.json()
    phone = d.get("phone","").replace(" ","").replace("+","")
    amount = int(d.get("amount", 1))
    if phone.startswith("0"): phone="254"+phone[1:]
    if phone.startswith("7"): phone="254"+phone
    if not CONSUMER_KEY:
        return {"ok": True, "msg":"DEMO MODE", "phone": phone, "amount": amount}
    try:
        token_data = http_get("https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials", auth=(CONSUMER_KEY, CONSUMER_SECRET))
        token = token_data.get("access_token")
        if not token: return {"ok": False, "error": "token failed"}
        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        password = base64.b64encode((SHORTCODE+PASSKEY+timestamp).encode()).decode()
        payload = {
            "BusinessShortCode": SHORTCODE, "Password": password, "Timestamp": timestamp,
            "TransactionType": "CustomerPayBillOnline", "Amount": amount,
            "PartyA": phone, "PartyB": SHORTCODE, "PhoneNumber": phone,
            "CallBackURL": CALLBACK_URL, "AccountReference": "LONMA MART", "TransactionDesc": "LONMA MART"
        }
        resp = http_post("https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest", payload, token=token)
        return {"ok": True, "daraja": resp, "phone": phone}
    except Exception as e: return {"ok": False, "error": str(e)}

@app.post("/api/callback")
async def callback(req: Request):
    data = await req.json()
    print("MPESA CALLBACK:", data)
    return {"ok": True}

if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")
