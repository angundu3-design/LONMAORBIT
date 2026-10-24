import os, base64, requests, sqlite3
from datetime import datetime
from fastapi import FastAPI, Request, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from dotenv import load_dotenv

load_dotenv()
app = FastAPI(title="LONMA ORBIT")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

MPESA_CONSUMER_KEY = os.getenv("MPESA_CONSUMER_KEY")
MPESA_CONSUMER_SECRET = os.getenv("MPESA_CONSUMER_SECRET")
MPESA_SHORTCODE = os.getenv("MPESA_SHORTCODE", "174379")
MPESA_PASSKEY = os.getenv("MPESA_PASSKEY")
MPESA_CALLBACK_URL = os.getenv("MPESA_CALLBACK_URL") or os.getenv("CALLBACK_URL", "https://app.lonmaorbit.co.ke/mpesa/callback")
MPESA_ENV = os.getenv("MPESA_ENV", "sandbox").lower()
BASE_URL = "https://api.safaricom.co.ke" if MPESA_ENV == "production" else "https://sandbox.safaricom.co.ke"

conn = sqlite3.connect("lonma.db", check_same_thread=False)
conn.execute("CREATE TABLE IF NOT EXISTS products (id INTEGER PRIMARY KEY, name TEXT, price INTEGER)")
conn.execute("CREATE TABLE IF NOT EXISTS orders (id INTEGER PRIMARY KEY, phone TEXT, amount INTEGER, status TEXT, mpesa_code TEXT, created TEXT)")
cur = conn.cursor()
cur.execute("SELECT COUNT(*) FROM products")
if cur.fetchone()[0] == 0:
    conn.execute("INSERT INTO products VALUES (1,'Orbit Shirt',1500)")
    conn.execute("INSERT INTO products VALUES (2,'Orbit Hoodie',3500)")
    conn.execute("INSERT INTO products VALUES (3,'Orbit Cap',1200)")
    conn.commit()

def get_mpesa_token():
    if not MPESA_CONSUMER_KEY or not MPESA_CONSUMER_SECRET:
        return None
    url = f"{BASE_URL}/oauth/v1/generate?grant_type=client_credentials"
    auth = base64.b64encode(f"{MPESA_CONSUMER_KEY}:{MPESA_CONSUMER_SECRET}".encode()).decode()
    try:
        r = requests.get(url, headers={"Authorization": f"Basic {auth}"}, timeout=15)
        return r.json().get("access_token")
    except:
        return None

def lipa_na_mpesa(phone, amount):
    token = get_mpesa_token()
    if not token:
        return {"error": "Could not get token"}
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    password = base64.b64encode(f"{MPESA_SHORTCODE}{MPESA_PASSKEY}{timestamp}".encode()).decode()
    if phone.startswith("0"):
        phone = "254" + phone[1:]
    url = f"{BASE_URL}/mpesa/stkpush/v1/processrequest"
    payload = {"BusinessShortCode": MPESA_SHORTCODE, "Password": password, "Timestamp": timestamp, "TransactionType": "CustomerPayBillOnline", "Amount": int(amount), "PartyA": phone, "PartyB": MPESA_SHORTCODE, "PhoneNumber": phone, "CallBackURL": MPESA_CALLBACK_URL, "AccountReference": "LONMA-ORBIT", "TransactionDesc": "Payment"}
    r = requests.post(url, json=payload, headers={"Authorization": f"Bearer {token}"})
    return r.json()

HTML_PAGE = """
<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width,initial-scale=1"><title>LONMA ORBIT</title>
<style>body{font-family:Arial;background:#0a0a0a;color:#fff;margin:0}.header{padding:20px;text-align:center;background:#111;font-size:24px;font-weight:bold}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:15px;padding:20px}.card{background:#1a1a1a;border-radius:12px;padding:15px;text-align:center}.btn{background:#fff;color:#000;border:none;padding:12px;border-radius:25px;width:100%;margin-top:10px;font-weight:bold}.checkout{position:fixed;bottom:0;left:0;right:0;background:#111;padding:20px}input{width:100%;padding:12px;border-radius:8px;border:none;margin:5px 0;box-sizing:border-box}</style>
</head><body><div class="header">LONMA ORBIT - M-PESA LIVE</div><div class="grid" id="products"></div>
<div class="checkout"><input id="phone" placeholder="07xxxxxxxx"><input id="amount" type="number" value="1"><button class="btn" onclick="pay()">PAY WITH M-PESA</button><p id="status"></p></div>
<script>async function load(){let r=await fetch('/api/products');let d=await r.json();document.getElementById('products').innerHTML=d.map(p=>`<div class="card"><h3>${p.name}</h3><p>KSh ${p.price}</p><button class="btn" onclick="document.getElementById('amount').value=${p.price}">BUY</button></div>`).join('')}async function pay(){let phone=document.getElementById('phone').value;let amount=document.getElementById('amount').value;document.getElementById('status').innerText='Sending STK...';let r=await fetch('/mpesa/stkpush',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({phone,amount})});let d=await r.json();document.getElementById('status').innerText=JSON.stringify(d)}load();</script></body></html>
"""

@app.api_route("/", methods=["GET", "HEAD"])
def home():
    return HTMLResponse(content=HTML_PAGE)

@app.get("/api/products")
def get_products():
    cur = conn.cursor()
    cur.execute("SELECT * FROM products")
    return [{"id": r[0], "name": r[1], "price": r[2]} for r in cur.fetchall()]

@app.post("/mpesa/stkpush")
async def stk_push(request: Request):
    data = await request.json()
    result = lipa_na_mpesa(data.get("phone"), data.get("amount"))
    conn.execute("INSERT INTO orders (phone, amount, status, created) VALUES (?,?,?,?)", (data.get("phone"), data.get("amount"), "PENDING", datetime.now().isoformat()))
    conn.commit()
    return result

@app.post("/mpesa/callback")
async def mpesa_callback(request: Request):
    body = await request.json()
    try:
        result = body.get("Body", {}).get("stkCallback", {})
        if result.get("ResultCode") == 0:
            items = result.get("CallbackMetadata", {}).get("Item", [])
            code = ""
            for i in items:
                if i.get("Name") == "MpesaReceiptNumber":
                    code = i.get("Value")
            conn.execute("UPDATE orders SET status=?, mpesa_code=? WHERE id=(SELECT MAX(id) FROM orders)", ("PAID", code))
            conn.commit()
    except:
        pass
    return {"ResultCode": 0, "ResultDesc": "Accepted"}

@app.get("/api/orders")
def get_orders():
    cur = conn.cursor()
    cur.execute("SELECT * FROM orders ORDER BY id DESC")
    return [{"id": r[0], "phone": r[1], "amount": r[2], "status": r[3], "mpesa_code": r[4]} for r in cur.fetchall()]

@app.post("/login")
def login(username: str = Form(...), password: str = Form(...)):
    return {"username": username, "status": "success"}
