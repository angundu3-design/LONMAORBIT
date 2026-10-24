import os, base64, requests
from datetime import datetime
from fastapi import FastAPI, Request, Form
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="LONMA ORBIT")

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
    password_str = f"{MPESA_SHORTCODE}{MPESA_PASSKEY}{timestamp}"
    password = base64.b64encode(password_str.encode()).decode()
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
        "TransactionDesc": "Payment for Lonma Orbit"
    }
    r = requests.post(url, json=payload, headers=headers)
    return r.json()

@app.api_route("/", methods=["GET", "HEAD"])
def home():
    return {"status": "LONMA ORBIT LIVE", "mpesa_env": MPESA_ENV, "shortcode": MPESA_SHORTCODE}

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/mpesa/stkpush")
async def stk_push(request: Request):
    data = await request.json()
    phone = data.get("phone")
    amount = data.get("amount", 1)
    if not phone:
        return {"error": "phone required"}
    return lipa_na_mpesa(phone, amount)

@app.post("/mpesa/callback")
async def mpesa_callback(request: Request):
    body = await request.json()
    print(body)
    return {"ResultCode": 0, "ResultDesc": "Accepted"}

@app.post("/login")
def login(username: str = Form(...), password: str = Form(...)):
    return {"username": username, "status": "logged in"}
