import os, base64, requests, sqlite3
from datetime import datetime
from fastapi import FastAPI, Request, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="LONMA ORBIT")
templates = Jinja2Templates(directory="templates")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

MPESA_CONSUMER_KEY = os.getenv("MPESA_CONSUMER_KEY")
MPESA_CONSUMER_SECRET = os.getenv("MPESA_CONSUMER_SECRET")
MPESA_SHORTCODE = os.getenv("MPESA_SHORTCODE", "174379")
MPESA_PASSKEY = os.getenv("MPESA_PASSKEY")
MPESA_CALLBACK_URL = os.getenv("MPESA_CALLBACK_URL") or os.getenv("CALLBACK_URL", "https://app.lonmaorbit.co.ke/mpesa/callback")
MPESA_ENV = os.getenv("MPESA_ENV", "sandbox").lower()

if MPESA_ENV == "production":
    BASE_URL = "https://api.safaricom.co.ke"
else:
    BASE_URL = "https://sandbox.safaricom.co.ke"

conn = sqlite3.connect("lonma.db", check_same_thread=False)
conn.execute("CREATE TABLE IF NOT EXISTS products (id INTEGER PRIMARY KEY, name TEXT, price INTEGER, image TEXT)")
conn.execute("CREATE TABLE IF NOT EXISTS orders (id INTEGER PRIMARY KEY, phone TEXT, amount INTEGER, status TEXT, mpesa_code TEXT, created TEXT)")
cur = conn.cursor()
cur.execute("SELECT COUNT(*) FROM products")
if cur.fetchone()[0] == 0:
    conn.execute("INSERT INTO products (name, price, image) VALUES (?,?,?)", ("Orbit Shirt", 1500, "https://via.placeholder.com/300"))
    conn.execute("INSERT INTO products (name, price, image) VALUES (?,?,?)", ("Orbit Hoodie", 3500, "https://via.placeholder.com/300"))
    conn.execute("INSERT INTO products (name, price, image) VALUES (?,?,?)", ("Orbit Cap", 1200, "https://via.placeholder.com/300"))
    conn.commit()

def get_mpesa_token():
    if not MPESA_CONSUMER_KEY or not MPESA_CONSUMER_SECRET:
        return None
    url = f"{BASE_URL}/oauth/v1/generate?grant_type=client_credentials"
    auth = base64.b64encode(f"{MPESA_CONSUMER_KEY}:{MPESA_CONSUMER_SECRET}".encode()).decode()
    headers = {"Authorization": f"Basic {auth}"}
    try:
        r = requests.get(url, headers=headers, timeout=15)
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
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    payload = {
        "BusinessShortCode": MPESA_SHORTCODE,
        "Password": password,
        "Timestamp": timestamp,
        "TransactionType": "CustomerPayBillOnline",
        "Amount": int(amount),
        "PartyA": phone,
        "PartyB": MPESA_SHORTCODE,
        "PhoneNumber": phone,
        "CallBackURL": MPESA_CALLBACK_URL,
        "AccountReference": "LONMA-ORBIT",
        "TransactionDesc": "Lonma Orbit Payment"
    }
    r = requests.post(url, json=payload, headers=headers)
    return r.json()

@app.api_route("/", methods=["GET", "HEAD"])
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/api/products")
def get_products():
    cur = conn.cursor()
    cur.execute("SELECT * FROM products")
    rows = cur.fetchall()
    return [{"id": r[0], "name": r[1], "price": r[2], "image": r[3]} for r in rows]

@app.post("/api/products")
def add_product(name: str = Form(...), price: int = Form(...), image: str = Form(...)):
    conn.execute("INSERT INTO products (name, price, image) VALUES (?,?,?)", (name, price, image))
    conn.commit()
    return {"status": "added"}

@app.post("/mpesa/stkpush")
async def stk_push(request: Request):
    data = await request.json()
    phone = data.get("phone")
    amount = data.get("amount")
    if not phone or not amount:
        return {"error": "phone and amount required"}
    result = lipa_na_mpesa(phone, amount)
    conn.execute("INSERT INTO orders (phone, amount, status, created) VALUES (?,?,?,?)", (phone, amount, "PENDING", datetime.now().isoformat()))
    conn.commit()
    return result

@app.post("/mpesa/callback")
async def mpesa_callback(request: Request):
    body = await request.json()
    print(body)
    try:
        result = body.get("Body", {}).get("stkCallback", {})
        code = result.get("ResultCode")
        if code == 0:
            items = result.get("CallbackMetadata", {}).get("Item", [])
            mpesa_code = ""
            for i in items:
                if i.get("Name") == "MpesaReceiptNumber":
                    mpesa_code = i.get("Value")
            conn.execute("UPDATE orders SET status=?, mpesa_code=? WHERE id=(SELECT MAX(id) FROM orders)", ("PAID", mpesa_code))
            conn.commit()
    except Exception as e:
        print(e)
    return {"ResultCode": 0, "ResultDesc": "Accepted"}

@app.get("/api/orders")
def get_orders():
    cur = conn.cursor()
    cur.execute("SELECT * FROM orders ORDER BY id DESC")
    rows = cur.fetchall()
    return [{"id": r[0], "phone": r[1], "amount": r[2], "status": r[3], "mpesa_code": r[4], "created": r[5]} for r in rows]

@app.post("/login")
def login(username: str = Form(...), password: str = Form(...)):
    return {"username": username, "status": "success", "token": "lonma-token"}
