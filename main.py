from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
import os, sqlite3, urllib.parse, json, datetime, requests, base64, random, string

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

DARAJA_CONSUMER_KEY = os.getenv("DARAJA_KEY", "")
DARAJA_CONSUMER_SECRET = os.getenv("DARAJA_SECRET", "")
DARAJA_SHORTCODE = os.getenv("DARAJA_SHORTCODE", "174379")
DARAJA_PASSKEY = os.getenv("DARAJA_PASSKEY", "")
DARAJA_CALLBACK_URL = os.getenv("CALLBACK_URL", "https://app.lonmaorbit.co.ke/mpesa/callback")
USE_PRODUCTION = os.getenv("DARAJA_ENV", "sandbox") == "production"

conn = sqlite3.connect("lonma.db", check_same_thread=False)
conn.execute("CREATE TABLE IF NOT EXISTS users (email TEXT UNIQUE, password TEXT, name TEXT)")
conn.execute("CREATE TABLE IF NOT EXISTS products (id INTEGER PRIMARY KEY, name TEXT, price INTEGER, code TEXT, image TEXT, category TEXT, stock INTEGER, desc TEXT)")
conn.execute("CREATE TABLE IF NOT EXISTS orders (id INTEGER PRIMARY KEY AUTOINCREMENT, order_no TEXT, name TEXT, phone TEXT, area TEXT, location TEXT, items TEXT, subtotal INTEGER, delivery INTEGER, total INTEGER, status TEXT, created TEXT, mpesa_receipt TEXT, checkout_id TEXT)")
conn.execute("CREATE TABLE IF NOT EXISTS friends (id INTEGER PRIMARY KEY AUTOINCREMENT, user_phone TEXT, friend_phone TEXT, friend_name TEXT, status TEXT, created TEXT)")
conn.execute("CREATE TABLE IF NOT EXISTS referrals (id INTEGER PRIMARY KEY AUTOINCREMENT, code TEXT UNIQUE, owner_phone TEXT, used_by TEXT, discount INTEGER, created TEXT)")
conn.execute("CREATE TABLE IF NOT EXISTS shared_carts (id INTEGER PRIMARY KEY AUTOINCREMENT, share_code TEXT UNIQUE, owner_phone TEXT, items TEXT, created TEXT)")
cur = conn.cursor()
cur.execute("DELETE FROM products")
PRODUCTS = [
    (1, "Fresh Fri Cooking Oil 2L", 850, "LONMA-001", "Cooking Oils", 50, "Pure fortified 2L original"),
    (2, "Detrex Citronella Soap 110g", 90, "LONMA-002", "Soaps", 120, "Anti-bacterial citronella"),
    (3, "Sawa Men Lotion 72Hrs", 299, "LONMA-003", "Lotions", 35, "72Hrs hydration"),
    (4, "Detrex Pine Drops Soap 110g", 90, "LONMA-004", "Soaps", 100, "Pine drops fresh"),
    (5, "Salit Vegetable Oil 5L", 1250, "LONMA-005", "Cooking Oils", 25, "5L family pack"),
    (6, "Detrex Cool Mint Soap 110g", 90, "LONMA-006", "Soaps", 80, "Cool mint"),
    (7, "Diva Anti-Dandruff Pomade 250ml", 250, "LONMA-007", "Pomades", 40, "Anti-dandruff"),
    (8, "Diva Anti-Breakage Pomade", 250, "LONMA-008", "Pomades", 45, "Anti-breakage"),
    (9, "Sawa Cocoa Butter Lotion", 299, "LONMA-009", "Lotions", 30, "Cocoa butter"),
]
for pid, name, price, code, cat, stock, desc in PRODUCTS:
    img = f"/static/{code}.jpg"
    if not os.path.exists(f"static/{code}.jpg"):
        img = f"https://via.placeholder.com/400x300/FFFFFF/0A9EBB?text={urllib.parse.quote(name)}"
    cur.execute("INSERT INTO products VALUES (?,?,?,?,?,?,?,?)", (pid, name, price, code, img, cat, stock, desc))
conn.commit()

def gen_code(n=6):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=n))

def get_daraja_token():
    try:
        base = "https://api.safaricom.co.ke" if USE_PRODUCTION else "https://sandbox.safaricom.co.ke"
        r = requests.get(f"{base}/oauth/v1/generate?grant_type=client_credentials", auth=(DARAJA_CONSUMER_KEY, DARAJA_CONSUMER_SECRET), timeout=10)
        return r.json().get("access_token")
    except:
        return None

@app.api_route("/mpesa/callback", methods=["GET", "POST"])
@app.api_route("/callback", methods=["GET", "POST"])
@app.api_route("/mpesa-callback", methods=["GET", "POST"])
async def mpesa_callback(request: Request):
    try:
        data = await request.json()
        stk = data.get("Body", {}).get("stkCallback", {})
        result_code = stk.get("ResultCode")
        checkout_id = stk.get("CheckoutRequestID", "")
        if result_code == 0:
            receipt = ""
            for it in stk.get("CallbackMetadata", {}).get("Item", []):
                if it.get("Name") == "MpesaReceiptNumber":
                    receipt = it.get("Value")
            cur = conn.cursor()
            cur.execute("UPDATE orders SET status='PAID', mpesa_receipt=? WHERE checkout_id=?", (receipt, checkout_id))
            if cur.rowcount == 0:
                cur.execute("UPDATE orders SET status='PAID', mpesa_receipt=? WHERE status='Pending' ORDER BY id DESC LIMIT 1", (receipt,))
            conn.commit()
        else:
            cur = conn.cursor()
            cur.execute("UPDATE orders SET status='FAILED' WHERE checkout_id=?", (checkout_id,))
            conn.commit()
        return {"ResultCode": 0, "ResultDesc": "Accepted"}
    except:
        return {"ResultCode": 0, "ResultDesc": "Accepted"}

@app.get("/favicon.ico")
def favicon():
    for f in ["logo.png", "static/logo.png"]:
        if os.path.exists(f):
            return FileResponse(f)
    return HTMLResponse("", 200)

@app.get("/api/products")
def products():
    cur = conn.cursor()
    cur.execute("SELECT id,name,price,code,image,category,stock,desc FROM products")
    return [{"id": r[0], "name": r[1], "price": r[2], "code": r[3], "image": r[4], "category": r[5], "stock": r[6], "desc": r[7]} for r in cur.fetchall()]

@app.get("/api/verify/{code}")
def verify(code: str):
    cur = conn.cursor()
    cur.execute("SELECT name FROM products WHERE code=?", (code.strip().upper(),))
    row = cur.fetchone()
    return {"valid": True, "product": {"name": row[0]}} if row else {"valid": False}

@app.get("/api/orders")
def get_orders_by_phone(phone: str = ""):
    cur = conn.cursor()
    if phone:
        cur.execute("SELECT order_no,name,phone,area,location,items,subtotal,delivery,total,status,created FROM orders WHERE phone=? ORDER BY id DESC", (phone,))
    else:
        cur.execute("SELECT order_no,name,phone,area,location,items,subtotal,delivery,total,status,created FROM orders ORDER BY id DESC LIMIT 50")
    return [{"order_no": r[0], "name": r[1], "phone": r[2], "area": r[3], "location": r[4], "items": r[5], "subtotal": r[6], "delivery": r[7], "total": r[8], "status": r[9], "created": r[10]} for r in cur.fetchall()]

@app.get("/api/admin/orders")
def admin_orders():
    cur = conn.cursor()
    cur.execute("SELECT order_no,name,phone,area,location,items,subtotal,delivery,total,status,created,mpesa_receipt,checkout_id FROM orders ORDER BY id DESC")
    return [{"order_no": r[0], "name": r[1], "phone": r[2], "area": r[3], "location": r[4], "items": r[5], "subtotal": r[6], "delivery": r[7], "total": r[8], "status": r[9], "created": r[10], "mpesa_receipt": r[11], "checkout_id": r[12]} for r in cur.fetchall()]

@app.post("/api/admin/orders/{order_no}/{status}")
def admin_update(order_no: str, status: str):
    cur = conn.cursor()
    cur.execute("UPDATE orders SET status=? WHERE order_no=?", (status, order_no))
    conn.commit()
    return {"message": f"Order {order_no} marked {status}"}

@app.get("/api/friends")
def list_friends(phone: str):
    cur = conn.cursor()
    cur.execute("SELECT friend_phone, friend_name, status, created FROM friends WHERE user_phone=? ORDER BY id DESC", (phone,))
    friends = [{"phone": r[0], "name": r[1], "status": r[2], "created": r[3]} for r in cur.fetchall()]
    cur.execute("SELECT code, discount FROM referrals WHERE owner_phone=?", (phone,))
    row = cur.fetchone()
    if not row:
        code = f"LONMA-{gen_code(4)}"
        cur.execute("INSERT INTO referrals (code, owner_phone, discount, created) VALUES (?,?,?,?)", (code, phone, 100, datetime.datetime.now().strftime("%Y-%m-%d")))
        conn.commit()
        referral_code = code
        referral_discount = 100
    else:
        referral_code = row[0]
        referral_discount = row[1]
    return {"friends": friends, "referral_code": referral_code, "referral_discount": referral_discount}

@app.post("/api/friends/invite")
async def invite_friend(req: Request):
    d = await req.json()
    user_phone = d.get("user_phone", "").strip()
    friend_phone = d.get("friend_phone", "").strip()
    friend_name = d.get("friend_name", "Friend").strip()
    if not user_phone or not friend_phone:
        return {"status": "error", "message": "Phone required"}
    cur = conn.cursor()
    cur.execute("SELECT id FROM friends WHERE user_phone=? AND friend_phone=?", (user_phone, friend_phone))
    if cur.fetchone():
        return {"status": "error", "message": "Already invited"}
    cur.execute("INSERT INTO friends (user_phone, friend_phone, friend_name, status, created) VALUES (?,?,?,?,?)", (user_phone, friend_phone, friend_name, "invited", datetime.datetime.now().strftime("%Y-%m-%d %H:%M")))
    conn.commit()
    return {"status": "ok", "message": f"Invite sent to {friend_name}"}

@app.post("/api/friends/accept")
async def accept_friend(req: Request):
    d = await req.json()
    user_phone = d.get("user_phone", "")
    friend_phone = d.get("friend_phone", "")
    cur = conn.cursor()
    cur.execute("UPDATE friends SET status='friends' WHERE user_phone=? AND friend_phone=?", (friend_phone, user_phone))
    cur.execute("INSERT OR IGNORE INTO friends (user_phone, friend_phone, friend_name, status, created) VALUES (?,?,?,?,?)", (user_phone, friend_phone, "Friend", "friends", datetime.datetime.now().strftime("%Y-%m-%d %H:%M")))
    conn.commit()
    return {"status": "ok", "message": "You are now friends"}

@app.post("/api/referral/apply")
async def apply_referral(req: Request):
    d = await req.json()
    code = d.get("code", "").strip().upper()
    user_phone = d.get("user_phone", "")
    cur = conn.cursor()
    cur.execute("SELECT owner_phone, discount FROM referrals WHERE code=?", (code,))
    row = cur.fetchone()
    if not row:
        return {"status": "error", "message": "Invalid referral code"}
    if row[0] == user_phone:
        return {"status": "error", "message": "Cannot use your own code"}
    return {"status": "ok", "message": f"Referral applied - KSh {row[1]} OFF", "discount": row[1]}

@app.post("/api/share-cart")
async def share_cart(req: Request):
    d = await req.json()
    owner = d.get("phone", "guest")
    items = json.dumps(d.get("cart", []))
    share_code = gen_code(8)
    cur = conn.cursor()
    cur.execute("INSERT INTO shared_carts (share_code, owner_phone, items, created) VALUES (?,?,?,?)", (share_code, owner, items, datetime.datetime.now().strftime("%Y-%m-%d %H:%M")))
    conn.commit()
    return {"status": "ok", "share_code": share_code, "share_url": f"https://app.lonmaorbit.co.ke/?share={share_code}"}

@app.get("/api/share-cart/{code}")
def get_shared_cart(code: str):
    cur = conn.cursor()
    cur.execute("SELECT items, owner_phone FROM shared_carts WHERE share_code=?", (code.upper(),))
    row = cur.fetchone()
    if not row:
        return {"status": "error", "message": "Invalid share code"}
    return {"status": "ok", "items": json.loads(row[0]), "owner": row[1]}

@app.post("/api/login")
async def login_api(req: Request):
    d = await req.json()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE email=? AND password=?", (d.get("email"), d.get("password")))
    return {"status": "ok", "message": "Welcome"} if cur.fetchone() else {"status": "error", "message": "Invalid"}

@app.post("/mpesa/stkpush")
async def stk(req: Request):
    d = await req.json()
    raw_phone = d.get('phone', '').strip()
    phone_for_db = raw_phone
    phone = raw_phone.replace(" ", "").replace("+254", "0").replace("+", "")
    if phone.startswith("0"):
        phone = "254" + phone[1:]
    phone = "".join([c for c in phone if c.isdigit()])
    amount = int(d.get('amount', 1))
    order_no = 'LONMA' + datetime.datetime.now().strftime("%H%M%S")
    items_text = json.dumps([f"{c.get('name')} x{c.get('qty')}" for c in d.get('cart', [])])
    try:
        conn.execute("INSERT INTO orders (order_no,name,phone,area,location,items,subtotal,delivery,total,status,created,mpesa_receipt,checkout_id) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)", (order_no, d.get('name', 'Guest'), phone_for_db, d.get('area'), d.get('location'), items_text, d.get('subtotal', 0), d.get('delivery', 0), d.get('amount', 0), 'Pending', datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), "", order_no))
        conn.commit()
    except Exception as e:
        print(e)
    if DARAJA_CONSUMER_KEY and DARAJA_CONSUMER_SECRET and DARAJA_PASSKEY:
        token = get_daraja_token()
        if token:
            timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
            password = base64.b64encode(f"{DARAJA_SHORTCODE}{DARAJA_PASSKEY}{timestamp}".encode()).decode()
            payload = {
                "BusinessShortCode": DARAJA_SHORTCODE,
                "Password": password,
                "Timestamp": timestamp,
                "TransactionType": "CustomerPayBillOnline",
                "Amount": amount,
                "PartyA": phone,
                "PartyB": DARAJA_SHORTCODE,
                "PhoneNumber": phone,
                "CallBackURL": DARAJA_CALLBACK_URL,
                "AccountReference": order_no,
                "TransactionDesc": f"LONMA {order_no}"
            }
            try:
                base = "https://api.safaricom.co.ke" if USE_PRODUCTION else "https://sandbox.safaricom.co.ke"
                r = requests.post(f"{base}/mpesa/stkpush/v1/processrequest", json=payload, headers={"Authorization": f"Bearer {token}"}, timeout=15)
                res = r.json()
                if res.get("ResponseCode") == "0":
                    chk = res.get("CheckoutRequestID", order_no)
                    conn.execute("UPDATE orders SET checkout_id=? WHERE order_no=?", (chk, order_no))
                    conn.commit()
                    return {"status": "ok", "message": f"STK Push sent to {phone_for_db}", "order_no": order_no, "checkout_id": chk}
                else:
                    return {"status": "error", "message": str(res), "order_no": order_no}
            except Exception as e:
                return {"status": "ok", "message": f"Order {order_no} saved - {str(e)}", "order_no": order_no}
    return {"status": "ok", "message": f"Order {order_no} saved - Add Daraja keys for real STK", "order_no": order_no}

HTML = """<!DOCTYPE html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>LONMA ORBIT</title><style>
:root{--teal:#0A9EBB}*{box-sizing:border-box}body{margin:0;font-family:Arial;background:#f7fbfc}
.nav{position:fixed;top:0;width:100%;background:var(--teal);z-index:1000}
.nav-top{padding:8px 12px;display:flex;justify-content:space-between;align-items:center;height:66px}
.logo-circle{background:#0A9EBB;width:56px;height:56px;border-radius:50%;display:flex;align-items:center;justify-content:center;overflow:hidden;border:2px solid #fff}
.logo-circle img{height:52px;width:52px;object-fit:cover;border-radius:50%}
.search-bar-wrap{padding:0 12px 14px;background:var(--teal)}
.search-app-bar{background:#fff;border-radius:16px;padding:0 16px;height:54px;display:flex;align-items:center;gap:12px}
.hamburger{color:var(--teal);font-size:28px;font-weight:bold;cursor:pointer}
.search-app-bar input{border:none;outline:none;flex:1;font-size:16px;background:transparent}
.cart-icon{position:relative;background:#fff;color:var(--teal);padding:9px 16px;border-radius:25px;font-weight:bold;cursor:pointer;font-size:13px}
.cart-count{position:absolute;top:-8px;right:-8px;background:#ff3b30;color:#fff;border-radius:50%;width:20px;height:20px;display:flex;align-items:center;justify-content:center;font-size:11px}
.page{display:none;padding:134px 10px 90px;min-height:100vh}.page.active{display:block}
.card{background:#fff;border-radius:16px;padding:12px;margin:8px 0;box-shadow:0 2px 12px rgba(0,0,0,.06);position:relative;border:1px solid #eef2f7}
.card img{width:100%;height:190px;object-fit:contain;background:#fff;border-radius:12px;padding:8px}
.btn{background:var(--teal);color:#fff;border:none;padding:12px;border-radius:25px;width:100%;font-weight:bold;cursor:pointer}
input,select,textarea{width:100%;padding:12px;border-radius:10px;border:1px solid #ddd;margin:5px 0;font-size:14px}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:8px}
.bottom{position:fixed;bottom:0;width:100%;background:#fff;display:flex;justify-content:space-around;padding:6px 0;border-top:1px solid #eee;z-index:1000}.bottom div{font-size:10px;color:#777;text-align:center;cursor:pointer;flex:1}.bottom div.active{color:var(--teal);font-weight:bold}
.chips{display:flex;gap:6px;overflow-x:auto;padding:8px 0}.chip{white-space:nowrap;background:#fff;border:1px solid #0A9EBB;color:#0A9EBB;padding:7px 14px;border-radius:20px;font-size:12px;cursor:pointer}.chip.active{background:#0A9EBB;color:#fff}
.qty-controls{display:flex;align-items:center;justify-content:space-between;background:#eef9fb;border-radius:25px;padding:5px 8px;margin-top:8px}
.qty-btn{background:var(--teal);color:#fff;border:none;width:30px;height:30px;border-radius:50%;font-weight:bold;cursor:pointer}
.promo{background:#fff;color:#0A9EBB;padding:10px;border-radius:12px;margin:8px 0;text-align:center;font-weight:bold;font-size:12px;border:1px solid #d0eef5}
.side-menu{position:fixed;top:0;left:-285px;width:285px;height:100%;background:#fff;z-index:2000;transition:.3s}.side-menu.open{left:0}.overlay{display:none;position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,.5);z-index:1999}.overlay.open{display:block}
.modal{display:none;position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,.6);z-index:2000;align-items:center;justify-content:center;padding:12px}.modal.open{display:flex}.modal-box{background:#fff;border-radius:16px;max-width:420px;width:100%;max-height:92vh;overflow-y:auto}
.status-badge{padding:3px 8px;border-radius:12px;font-size:10px;color:#fff}.status-Pending{background:#ff9a00}.status-PAID{background:#00c851}.status-Packing{background:#0A9EBB}.status-Transit{background:#6c5ce7}.status-Delivered{background:#2d3436}.status-friends{background:#00c851}.status-invited{background:#ff9a00}
</style></head><body>
<div class="nav"><div class="nav-top"><div class="logo-circle"><img src="/logo.png"></div><div style="display:flex;gap:8px;align-items:center"><div class="cart-icon" onclick="show('cart')">CART <span id="cartCount" class="cart-count" style="display:none">0</span></div><span onclick="show('friends')" style="background:rgba(255,255,255,.25);color:#fff;padding:6px 10px;border-radius:20px;font-size:12px;cursor:pointer">Friends</span></div></div><div class="search-bar-wrap"><div class="search-app-bar"><span class="hamburger" onclick="openSideMenu()">☰</span><input id="searchInput" placeholder="Search products" oninput="filterProducts()"><span style="color:#999;font-size:14px">Search</span></div></div></div>
<div class="overlay" id="overlay" onclick="closeSideMenu()"></div>
<div class="side-menu" id="sideMenu"><div style="background:var(--teal);color:#fff;padding:20px;text-align:center"><div style="background:#0A9EBB;width:80px;height:80px;border-radius:50%;margin:0 auto;display:flex;align-items:center;justify-content:center;border:2px solid #fff;overflow:hidden"><img src="/logo.png" style="height:76px;width:76px;object-fit:cover;border-radius:50%"></div><h3 style="margin:10px 0 0">LONMA ORBIT</h3><p style="margin:4px 0 0;font-size:11px">100% Original Store</p></div><div style="padding:10px"><div style="padding:14px;border-bottom:1px solid #eee;cursor:pointer" onclick="show('products');closeSideMenu()">Products</div><div style="padding:14px;border-bottom:1px solid #eee;cursor:pointer" onclick="show('cart');closeSideMenu()">Cart (<span id="sideCartCount">0</span>)</div><div style="padding:14px;border-bottom:1px solid #eee;cursor:pointer" onclick="show('friends');closeSideMenu()">Friends & Meet</div><div style="padding:14px;border-bottom:1px solid #eee;cursor:pointer" onclick="show('orders');closeSideMenu()">Orders</div><div style="padding:14px;border-bottom:1px solid #eee;cursor:pointer" onclick="show('scan');closeSideMenu()">Verify Code</div><div style="padding:14px;border-bottom:1px solid #eee;cursor:pointer" onclick="show('settings');closeSideMenu()">Settings</div><div style="padding:14px;border-bottom:1px solid #eee;cursor:pointer" onclick="show('login');closeSideMenu()">Account</div><div style="padding:14px;cursor:pointer" onclick="show('admin');closeSideMenu()">Admin</div></div></div>
<div id="products" class="page active">
<div class="promo">100% Original Verified - Same-Day Nairobi 2-3hrs - M-Pesa Secure - FREE Delivery over 2000</div>
<div class="chips"><span class="chip active" onclick="filterCat('All',this)">All 9</span><span class="chip" onclick="filterCat('Cooking Oils',this)">Oils</span><span class="chip" onclick="filterCat('Soaps',this)">Soaps</span><span class="chip" onclick="filterCat('Lotions',this)">Lotions</span><span class="chip" onclick="filterCat('Pomades',this)">Pomades</span></div>
<div class="grid" id="plist"></div>
<div style="background:#fff;padding:14px;border-radius:16px;margin-top:16px;text-align:center;border:1px solid #eef2f7"><div style="display:flex;justify-content:center;gap:6px;margin-bottom:10px"><span style="background:#f0f9fb;color:#0A9EBB;padding:6px 12px;border-radius:20px;font-size:11px;font-weight:bold;border:1px solid #d0eef5">Verified</span><span style="background:#f0f9fb;color:#0A9EBB;padding:6px 12px;border-radius:20px;font-size:11px;font-weight:bold;border:1px solid #d0eef5">Fast Delivery</span><span style="background:#f0f9fb;color:#0A9EBB;padding:6px 12px;border-radius:20px;font-size:11px;font-weight:bold;border:1px solid #d0eef5">Secure Payment</span></div><p style="font-size:11px;color:#888;margin:0">LONMA ORBIT - Trusted Store - CBD Moi Avenue - WhatsApp Support</p></div>
<div style="background:#0A9EBB;color:#fff;padding:14px;border-radius:16px;margin-top:8px;display:flex;justify-content:space-between;align-items:center"><div><p style="margin:0;font-weight:bold;font-size:13px">LONMA ORBIT</p><p style="margin:2px 0 0;font-size:11px;opacity:.9">2026 All rights reserved</p></div><a href="https://wa.me/254700000000" target="_blank" style="background:#25D366;color:#fff;padding:8px 14px;border-radius:20px;font-size:11px;text-decoration:none;font-weight:bold">WhatsApp</a></div>
</div>
<div id="friends" class="page"><h2>Meet Friends & Shop Together</h2>
<div class="card"><h4 style="margin:0 0 8px">My Referral Code</h4><div style="display:flex;gap:8px"><input id="myReferralCode" readonly style="background:#f0f9fb;font-weight:bold;color:#0A9EBB"><button class="btn" style="width:auto;padding:8px 16px" onclick="copyReferral()">Copy</button></div><p style="font-size:11px;color:#666">Share this code - friends get KSh 100 OFF, you get KSh 100 credit</p><div style="display:flex;gap:6px"><button class="btn" style="background:#25D366" onclick="shareReferralWhatsApp()">Share via WhatsApp</button></div></div>
<div class="card"><h4 style="margin:0 0 8px">Invite Friend by Phone</h4><input id="friendName" placeholder="Friend Name"><input id="friendPhone" placeholder="Friend Phone 07xxxxxxxx"><button class="btn" onclick="inviteFriend()">Invite Friend</button><p id="friendStatus" style="font-size:12px;margin-top:8px"></p></div>
<div class="card"><h4 style="margin:0 0 8px">Share My Cart with Friends</h4><p style="font-size:12px">Let friends see and join your cart</p><button class="btn" style="background:#6c5ce7" onclick="shareCart()">Generate Share Link</button><p id="shareLinkResult" style="font-size:12px;margin-top:8px;word-break:break-all"></p></div>
<div class="card"><h4 style="margin:0 0 8px">Join Friend Cart</h4><input id="joinShareCode" placeholder="Enter Share Code LONMA-XXXX"><button class="btn" style="background:#111" onclick="joinSharedCart()">Join Cart</button></div>
<div class="card"><h4>My Friends (<span id="friendsCount">0</span>)</h4><div id="friendsList"></div></div>
<div class="card"><h4>How Friends Shopping Works</h4><p style="font-size:12px;line-height:1.6">1. Invite friend by phone<br>2. Share your referral code - both get KSh 100 OFF<br>3. Share cart link - shop together same cart<br>4. Meet in CBD store - show friend code for extra discount</p></div>
</div>
<div id="cart" class="page"><h2>My Cart</h2><div id="cartItems"></div><div class="card" id="cartSummary" style="display:none"><div style="font-size:13px;line-height:2"><div style="display:flex;justify-content:space-between"><span>Subtotal (<span id="totalItems">0</span>)</span><span>KSh <span id="subTotal">0</span></span></div><div style="display:flex;justify-content:space-between"><span>Delivery</span><span id="deliveryFee"></span></div><div style="display:flex;justify-content:space-between"><span>Referral Discount</span><span id="referralDiscount">KSh 0</span></div><div style="display:flex;justify-content:space-between;border-top:1px solid #eee;margin-top:6px;padding-top:6px;font-weight:bold;font-size:16px;color:#0A9EBB"><span>Total</span><span>KSh <span id="totalPrice">0</span></span></div></div><div id="freeDeliveryMsg" style="background:#e8f5e9;color:#2e7d32;padding:8px;border-radius:8px;font-size:11px;margin-top:8px;text-align:center"></div><div style="background:#fff;border:1px solid #eee;padding:12px;border-radius:12px;margin-top:12px"><h4 style="margin:0 0 8px">Delivery Details</h4><input id="custName" placeholder="Full Name"><input id="phone" placeholder="M-Pesa 07xxxxxxxx"><select id="locationArea"><option value="">Select Area</option><option value="CBD">CBD - 150 (2-3hrs)</option><option value="Westlands">Westlands - 200 (3hrs)</option><option value="Eastlands">Eastlands - 200 (4hrs)</option><option value="Upcountry">Upcountry - 350 (24-48hrs)</option></select><textarea id="exactLocation" placeholder="Estate House No Landmark"></textarea><div style="display:flex;gap:6px"><input id="promoCode" placeholder="Promo Code or Friend Referral"><button class="btn" style="width:auto;padding:8px 12px;font-size:11px" onclick="applyReferralCode()">Apply</button></div><label style="font-size:12px;display:flex;gap:6px;align-items:center;margin-top:8px"><input type="checkbox" id="agreeTerms" style="width:auto"> I agree to Terms</label></div><div style="background:#fff;border:1px solid #eee;padding:12px;border-radius:12px;margin-top:12px"><button class="btn" style="background:#111" onclick="checkout()">PAY KSh <span id="payTotal">0</span> M-PESA</button><button class="btn" style="background:#25D366;margin-top:8px" onclick="orderWhatsApp()">ORDER VIA WHATSAPP</button><button class="btn" style="background:#6c5ce7;margin-top:8px" onclick="shareCart()">SHARE CART WITH FRIENDS</button><p id="paystatus" style="font-size:12px;margin-top:8px"></p></div><button class="btn" style="background:#fff;color:#0A9EBB;border:1px solid #0A9EBB;margin-top:8px" onclick="clearCart()">CLEAR CART</button></div><div class="card" id="emptyCart" style="text-align:center;padding:30px"><h3>Cart Empty</h3><button class="btn" onclick="show('products')">START SHOPPING</button></div></div>
<div id="orders" class="page"><h2>My Orders</h2><div style="display:flex;gap:6px;margin-bottom:8px"><input id="orderPhoneLookup" placeholder="Enter M-Pesa phone to load orders"><button class="btn" style="width:auto;padding:8px 16px" onclick="loadMyOrdersByPhone()">Load</button></div><div id="ordersList"></div><div class="card" id="noOrders" style="text-align:center;padding:30px"><h3>No orders yet</h3><button class="btn" onclick="show('products')">Shop Now</button></div></div>
<div id="scan" class="page"><h2>Verify Original</h2><div class="card"><input id="manualcode" placeholder="LONMA-001"><button class="btn" onclick="verifyCode()">VERIFY CODE</button><p id="scanresult" style="font-weight:bold;margin-top:10px"></p></div></div>
<div id="settings" class="page"><h2>Settings</h2><div class="card"><h4 style="margin:0 0 12px">Preferences</h4><select id="prefLang" onchange="savePrefs()"><option value="en">English</option><option value="sw">Kiswahili</option></select><label style="font-size:12px;display:flex;gap:8px;margin:6px 0"><input type="checkbox" id="prefNotif" style="width:auto" onchange="savePrefs()"> Order updates</label><label style="font-size:12px;display:flex;gap:8px;margin:6px 0"><input type="checkbox" id="prefPromo" style="width:auto" onchange="savePrefs()"> Promo offers</label><select id="prefArea" onchange="savePrefs()"><option value="">Default Area</option><option value="CBD">CBD - 150</option><option value="Westlands">Westlands - 200</option><option value="Eastlands">Eastlands - 200</option><option value="Upcountry">Upcountry - 350</option></select><select id="prefTheme" onchange="savePrefs()"><option value="light">Light</option><option value="dark">Dark</option></select><button class="btn" style="margin-top:12px" onclick="savePrefs()">SAVE</button><p id="prefStatus" style="font-size:12px;color:#00c851;margin-top:8px"></p></div><div class="card"><button class="btn" style="background:#666" onclick="clearPrefs()">Clear Preferences</button><button class="btn" style="background:#ff4444;margin-top:8px" onclick="clearAllData()">Clear All Data</button></div></div>
<div id="login" class="page"><h2>Account</h2><div class="card"><input id="lemail" placeholder="Email"><input id="lpass" type="password" placeholder="Password"><button class="btn" onclick="login()">Log In</button><p id="lstatus"></p></div></div>
<div id="admin" class="page"><h2>Admin</h2><div class="card"><input id="adminPass" type="password" placeholder="lonma2024"><button class="btn" onclick="adminLogin()">Login</button><p id="adminStatus"></p></div><div id="adminContent" style="display:none"><div class="card"><p>Orders <span id="statOrders">0</span> Sales KSh <span id="statSales">0</span></p><button class="btn" onclick="loadAdminOrders()">Refresh Orders</button></div><div id="adminOrdersList"></div></div></div>
<div id="receipt" class="page"><h2>Receipt</h2><div class="card" id="receiptContent"></div><button class="btn" onclick="show('products')">Continue Shopping</button><button class="btn" style="background:#fff;color:#0A9EBB;border:1px solid #0A9EBB;margin-top:8px" onclick="window.print()">Print Receipt</button></div>
<div class="bottom"><div id="b-products" class="active" onclick="show('products')">Products</div><div id="b-cart" onclick="show('cart')">Cart (<span id="bottomCartCount">0</span>)</div><div id="b-friends" onclick="show('friends')">Friends</div><div id="b-orders" onclick="show('orders')">Orders</div><div id="b-settings" onclick="show('settings')">Settings</div></div>
<div id="productModal" class="modal" onclick="if(event.target===this)closeModal()"><div class="modal-box"><div id="modalContent"></div></div></div>
<script>
let allProducts=[],currentCat='All',searchQuery='',cart=[],myOrders=JSON.parse(localStorage.getItem('my_orders')||'[]'),referralDiscountValue=0;
try{let s=localStorage.getItem('lonma_cart'); if(s){cart=JSON.parse(s);} if(!Array.isArray(cart))cart=[];}catch(e){cart=[];}
function safeImage(name){return`https://via.placeholder.com/400x300/FFFFFF/0A9EBB?text=${encodeURIComponent(name)}`;}
function saveCart(){localStorage.setItem('lonma_cart',JSON.stringify(cart));updateCartCount();}
function updateCartCount(){let c=0;for(let i of cart)c+=Number(i.qty)||0;document.getElementById('cartCount').innerText=c;document.getElementById('bottomCartCount').innerText=c;let side=document.getElementById('sideCartCount');if(side)side.innerText=c;document.getElementById('cartCount').style.display=c>0?'flex':'none';}
function openSideMenu(){document.getElementById('sideMenu').classList.add('open');document.getElementById('overlay').classList.add('open');}
function closeSideMenu(){document.getElementById('sideMenu').classList.remove('open');document.getElementById('overlay').classList.remove('open');}
function filterCat(cat,el){currentCat=cat;document.querySelectorAll('.chip').forEach(ch=>ch.classList.remove('active'));if(el)el.classList.add('active');renderProducts();}
function filterProducts(){searchQuery=document.getElementById('searchInput').value.toLowerCase();renderProducts();}
function renderProducts(){let list=allProducts.filter(p=>{let mCat=currentCat==='All'||p.category===currentCat;let mSearch=!searchQuery||p.name.toLowerCase().includes(searchQuery);return mCat&&mSearch;});let html='';for(let p of list){let inCart=cart.find(c=>c.id===p.id);let qtyText=inCart?`In cart: ${inCart.qty}`:'';let img=p.image||safeImage(p.name);let stockColor=p.stock>20?'#00c851':p.stock>5?'#ff9a00':'#ff3b30';let stockText=p.stock>20?`In Stock`:p.stock>0?`Low`: `Out`;html+=`<div class="card"><span style="position:absolute;top:8px;left:8px;background:${stockColor};color:#fff;padding:3px 8px;border-radius:12px;font-size:10px">${stockText}</span><img src="${img}" onclick="openModal(${p.id})"><span style="background:#e0f7fa;color:#0A9EBB;padding:2px 8px;border-radius:10px;font-size:10px">${p.category}</span><h4 style="font-size:12px;margin:6px 0">${p.name}</h4><p style="margin:0;font-weight:bold;color:#0A9EBB">KSh ${p.price}</p><small style="background:#0A9EBB;color:#fff;padding:2px 6px;border-radius:10px;font-size:10px">${p.code}</small><button class="btn" onclick="addToCart(${p.id})">ADD TO CART</button><div style="display:flex;gap:4px;margin-top:4px"><button class="btn" style="background:#fff;color:#0A9EBB;border:1px solid #0A9EBB;font-size:10px;padding:6px" onclick="shareProduct(${p.id})">Share with Friend</button></div><div style="font-size:11px;color:#0A9EBB;text-align:center;font-weight:bold;min-height:14px;margin-top:4px">${qtyText}</div></div>`;}document.getElementById('plist').innerHTML=html;}
function openModal(id){let p=allProducts.find(x=>x.id===id);if(!p)return;document.getElementById('modalContent').innerHTML=`<img src="${p.image}" style="width:100%;height:260px;object-fit:contain;padding:12px"><div style="padding:12px"><h3>${p.name}</h3><p style="color:#0A9EBB;font-weight:bold;font-size:20px">KSh ${p.price}</p><p style="font-size:13px">${p.desc}</p><p style="font-size:12px;color:#666">Stock: ${p.stock}</p><button class="btn" onclick="addToCart(${p.id});closeModal()">ADD TO CART</button><button class="btn" style="background:#25D366;margin-top:8px" onclick="shareProduct(${p.id})">Share with Friend</button><button class="btn" style="background:#fff;color:#0A9EBB;border:1px solid #0A9EBB;margin-top:8px" onclick="closeModal()">Close</button></div>`;document.getElementById('productModal').classList.add('open');}
function closeModal(){document.getElementById('productModal').classList.remove('open');}
function addToCart(id){let p=allProducts.find(x=>x.id===id);if(!p)return;let found=cart.find(c=>c.id===id);if(found){found.qty++;}else{cart.push({id:p.id,name:p.name,price:p.price,image:p.image,code:p.code,qty:1});}saveCart();renderCart();renderProducts();}
function changeQty(id,delta){for(let i=0;i<cart.length;i++)if(cart[i].id===id){cart[i].qty+=delta;if(cart[i].qty<=0)cart.splice(i,1);break;}saveCart();renderCart();renderProducts();}
function clearCart(){cart=[];localStorage.removeItem('lonma_cart');saveCart();renderCart();renderProducts();}
function renderCart(){let cont=document.getElementById('cartItems'),sum=document.getElementById('cartSummary'),empty=document.getElementById('emptyCart');if(cart.length===0){cont.innerHTML='';sum.style.display='none';empty.style.display='block';return;}empty.style.display='none';sum.style.display='block';let totalItems=0,subTotal=0,html='';for(let it of cart){totalItems+=it.qty;subTotal+=it.price*it.qty;html+=`<div class="card" style="display:flex;gap:10px"><img src="${it.image}" style="width:60px;height:60px;object-fit:contain"><div style="flex:1"><h4 style="margin:0;font-size:13px">${it.name}</h4><p>KSh ${it.price} x ${it.qty}</p><div class="qty-controls"><button class="qty-btn" onclick="changeQty(${it.id},-1)">-</button><span>${it.qty}</span><button class="qty-btn" onclick="changeQty(${it.id},1)">+</button></div></div></div>`;}cont.innerHTML=html;let area=document.getElementById('locationArea').value;let delivery=area==='CBD'?150:area==='Upcountry'?350:200;if(subTotal>=2000)delivery=0;let total=subTotal+delivery-referralDiscountValue;if(total<0)total=0;document.getElementById('subTotal').innerText=subTotal;document.getElementById('totalItems').innerText=totalItems;document.getElementById('deliveryFee').innerText=delivery===0?'FREE':'KSh '+delivery;document.getElementById('referralDiscount').innerText='KSh '+referralDiscountValue;document.getElementById('totalPrice').innerText=total;document.getElementById('payTotal').innerText=total;document.getElementById('freeDeliveryMsg').innerHTML=subTotal>=2000?'FREE delivery unlocked':'Add '+(2000-subTotal)+' for FREE delivery';}
document.getElementById('locationArea')?.addEventListener('change',renderCart);
function show(id){document.querySelectorAll('.page').forEach(p=>p.classList.remove('active'));document.getElementById(id).classList.add('active');document.querySelectorAll('.bottom div').forEach(b=>b.classList.remove('active'));let btn=document.getElementById('b-'+id);if(btn)btn.classList.add('active');if(id==='cart')renderCart();if(id==='orders')renderOrders();if(id==='settings')loadPrefs();if(id==='friends')loadFriends();closeSideMenu();window.scrollTo(0,0);}
async function loadProducts(){let r=await fetch('/api/products');let d=await r.json();allProducts=d;renderProducts();let params=new URLSearchParams(window.location.search);let share=params.get('share');if(share){document.getElementById('joinShareCode').value=share;show('friends');}}
async function verifyCode(){let c=document.getElementById('manualcode').value.trim().toUpperCase();let r=await fetch(`/api/verify/${c}`);let d=await r.json();document.getElementById('scanresult').innerHTML=d.valid?`Valid ${d.product.name}`:`Invalid code`;}
async function login(){let r=await fetch('/api/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({email:document.getElementById('lemail').value,password:document.getElementById('lpass').value})});let d=await r.json();document.getElementById('lstatus').innerText=d.message;}
function orderWhatsApp(){let total=document.getElementById('totalPrice').innerText;let name=document.getElementById('custName').value;let area=document.getElementById('locationArea').value;let loc=document.getElementById('exactLocation').value;let phone=document.getElementById('phone').value;let items=cart.map(c=>`${c.name} x${c.qty} KSh ${c.price*c.qty}`).join('%0A');let msg=`Hi LONMA ORBIT%0AName: ${name}%0APhone: ${phone}%0AArea: ${area}%0ALocation: ${loc}%0A%0AItems:%0A${items}%0A%0ATotal: KSh ${total}`;window.open(`https://wa.me/254700000000?text=${msg}`,'_blank');}
async function checkout(){let name=document.getElementById('custName').value.trim(),phone=document.getElementById('phone').value.trim(),area=document.getElementById('locationArea').value,loc=document.getElementById('exactLocation').value.trim(),agree=document.getElementById('agreeTerms').checked;if(!name||!phone||!area||!loc||!agree){document.getElementById('paystatus').innerText='Fill all fields and agree terms';return;}let sub=0;for(let i of cart)sub+=i.price*i.qty;let del=area==='CBD'?150:area==='Upcountry'?350:200;if(sub>=2000)del=0;let tot=sub+del-referralDiscountValue;if(tot<0)tot=0;document.getElementById('paystatus').innerText='Sending STK Push...';let r=await fetch('/mpesa/stkpush',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({phone,amount:tot,cart,name,area,location:loc,subtotal:sub,delivery:del})});let d=await r.json();document.getElementById('paystatus').innerText=d.message;if(d.status==='ok'||d.message.includes('STK')||d.message.includes('saved')){let orderNo=d.order_no||'LONMA'+Date.now().toString().slice(-6);myOrders.unshift({order_no:orderNo,items:[...cart],total:tot,status:'Pending',created:new Date().toLocaleString()});localStorage.setItem('my_orders',JSON.stringify(myOrders));document.getElementById('receiptContent').innerHTML=`<h3>Order ${orderNo}</h3><p>Name: ${name}</p><p>Phone: ${phone}</p><p>Area: ${area}</p><p>Location: ${loc}</p><p>Total: KSh ${tot}</p><p>Status: Pending - Check phone for STK</p><hr>${cart.map(c=>`<p>${c.name} x${c.qty} = KSh ${c.price*c.qty}</p>`).join('')}`;cart=[];localStorage.removeItem('lonma_cart');saveCart();referralDiscountValue=0;setTimeout(()=>show('receipt'),1000);}}
async function loadMyOrdersByPhone(){let phone=document.getElementById('orderPhoneLookup').value.trim();if(!phone){renderOrders();return;}let r=await fetch(`/api/orders?phone=${phone}`);let data=await r.json();let cont=document.getElementById('ordersList'),empty=document.getElementById('noOrders');if(data.length===0){cont.innerHTML='<p>No orders found for this phone</p>';empty.style.display='none';return;}empty.style.display='none';let html='';for(let o of data){html+=`<div class="card"><div style="display:flex;justify-content:space-between"><b>${o.order_no}</b><span class="status-badge status-${o.status}">${o.status}</span></div><p>KSh ${o.total} - ${o.created}</p><p style="font-size:11px">${o.items}</p><p style="font-size:11px">${o.area} - ${o.location}</p></div>`;}cont.innerHTML=html;}
function renderOrders(){let cont=document.getElementById('ordersList'),empty=document.getElementById('noOrders');if(myOrders.length===0){cont.innerHTML='';empty.style.display='block';return;}empty.style.display='none';let html='';for(let o of myOrders){html+=`<div class="card"><div style="display:flex;justify-content:space-between"><b>${o.order_no}</b><span class="status-badge status-${o.status}">${o.status}</span></div><p>KSh ${o.total} - ${o.created}</p></div>`;}cont.innerHTML=html;}
async function adminLogin(){let p=document.getElementById('adminPass').value;if(p!=='lonma2024'){document.getElementById('adminStatus').innerText='Wrong password';return;}document.getElementById('adminContent').style.display='block';document.getElementById('adminStatus').innerText='Admin logged in';loadAdminOrders();}
async function loadAdminOrders(){let r=await fetch('/api/admin/orders');let d=await r.json();document.getElementById('statOrders').innerText=d.length;let sales=0;for(let o of d)sales+=o.total||0;document.getElementById('statSales').innerText=sales;let html='';for(let o of d){html+=`<div class="card"><div style="display:flex;justify-content:space-between"><b>${o.order_no}</b><span class="status-badge status-${o.status}">${o.status}</span></div><p>${o.name} - ${o.phone}</p><p>KSh ${o.total} - ${o.area} - ${o.location}</p><p style="font-size:11px">${o.items}</p><p style="font-size:11px">${o.created} ${o.mpesa_receipt||''}</p><div style="display:flex;gap:4px;margin-top:8px;flex-wrap:wrap"><button class="btn" style="width:auto;padding:6px 10px;font-size:11px" onclick="updateOrderStatus('${o.order_no}','Packing')">Packing</button><button class="btn" style="width:auto;padding:6px 10px;font-size:11px;background:#6c5ce7" onclick="updateOrderStatus('${o.order_no}','Transit')">Transit</button><button class="btn" style="width:auto;padding:6px 10px;font-size:11px;background:#2d3436" onclick="updateOrderStatus('${o.order_no}','Delivered')">Delivered</button><button class="btn" style="width:auto;padding:6px 10px;font-size:11px;background:#00c851" onclick="updateOrderStatus('${o.order_no}','PAID')">Mark PAID</button></div></div>`;}document.getElementById('adminOrdersList').innerHTML=html;}
async function updateOrderStatus(order_no,status){let r=await fetch(`/api/admin/orders/${order_no}/${status}`,{method:'POST'});let d=await r.json();alert(d.message);loadAdminOrders();}
async function loadFriends(){let phone=document.getElementById('phone').value||localStorage.getItem('user_phone')||'';if(!phone){document.getElementById('friendsList').innerHTML='<p style="font-size:12px">Enter phone in Cart to load friends</p>';return;}let r=await fetch(`/api/friends?phone=${phone}`);let data=await r.json();document.getElementById('myReferralCode').value=data.referral_code;document.getElementById('friendsCount').innerText=data.friends.length;let html='';if(data.friends.length===0){html='<p style="font-size:12px;color:#888">No friends yet - Invite friends to shop together</p>';}else{for(let f of data.friends){html+=`<div style="display:flex;justify-content:space-between;align-items:center;padding:8px;border-bottom:1px solid #eee"><div><b>${f.name}</b><br><small>${f.phone}</small></div><span class="status-badge status-${f.status}">${f.status}</span></div>`;}}document.getElementById('friendsList').innerHTML=html;}
async function inviteFriend(){let userPhone=document.getElementById('phone').value||localStorage.getItem('user_phone')||prompt('Your phone 07...');if(!userPhone){return;}localStorage.setItem('user_phone',userPhone);let friendPhone=document.getElementById('friendPhone').value.trim();let friendName=document.getElementById('friendName').value.trim()||'Friend';if(!friendPhone){document.getElementById('friendStatus').innerText='Enter friend phone';return;}let r=await fetch('/api/friends/invite',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({user_phone:userPhone,friend_phone:friendPhone,friend_name:friendName})});let d=await r.json();document.getElementById('friendStatus').innerText=d.message;loadFriends();}
async function applyReferralCode(){let code=document.getElementById('promoCode').value.trim().toUpperCase();let userPhone=document.getElementById('phone').value||localStorage.getItem('user_phone')||'';if(!code){return;}let r=await fetch('/api/referral/apply',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({code,user_phone:userPhone})});let d=await r.json();if(d.status==='ok'){referralDiscountValue=d.discount;document.getElementById('paystatus').innerText=d.message;renderCart();}else{document.getElementById('paystatus').innerText=d.message;}}
async function shareCart(){let phone=document.getElementById('phone').value||localStorage.getItem('user_phone')||'guest';if(cart.length===0){alert('Cart empty');return;}let r=await fetch('/api/share-cart',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({phone,cart})});let d=await r.json();document.getElementById('shareLinkResult').innerHTML=`Share link: <a href="${d.share_url}" target="_blank">${d.share_url}</a><br>Code: <b>${d.share_code}</b><br><button class="btn" style="margin-top:6px;background:#25D366" onclick="window.open('https://wa.me/?text=${encodeURIComponent('Join my LONMA cart '+d.share_url)}','_blank')">Share via WhatsApp</button>`;let shareResult=document.getElementById('paystatus');if(shareResult){shareResult.innerText='Cart shared: '+d.share_code;}}
async function joinSharedCart(){let code=document.getElementById('joinShareCode').value.trim().toUpperCase();if(!code){return;}let r=await fetch(`/api/share-cart/${code}`);let d=await r.json();if(d.status==='ok'){cart=d.items;saveCart();renderCart();alert('Joined cart from '+d.owner);show('cart');}else{alert(d.message);}}
function shareProduct(id){let p=allProducts.find(x=>x.id===id);if(!p)return;let url=`https://app.lonmaorbit.co.ke/?product=${p.id}`;let msg=`Check this ${p.name} KSh ${p.price} on LONMA ORBIT ${url}`;window.open(`https://wa.me/?text=${encodeURIComponent(msg)}`,'_blank');}
function copyReferral(){let el=document.getElementById('myReferralCode');el.select();document.execCommand('copy');alert('Copied '+el.value);}
function shareReferralWhatsApp(){let code=document.getElementById('myReferralCode').value;let msg=`Use my LONMA ORBIT referral ${code} and get KSh 100 OFF. Shop at https://app.lonmaorbit.co.ke`;window.open(`https://wa.me/?text=${encodeURIComponent(msg)}`,'_blank');}
function loadPrefs(){try{let p=JSON.parse(localStorage.getItem('lonma_prefs')||'{}');document.getElementById('prefLang').value=p.lang||'en';document.getElementById('prefNotif').checked=p.notif!==false;document.getElementById('prefPromo').checked=p.promo!==false;document.getElementById('prefArea').value=p.area||'';document.getElementById('prefTheme').value=p.theme||'light';}catch(e){}}
function savePrefs(){let p={lang:document.getElementById('prefLang').value,notif:document.getElementById('prefNotif').checked,promo:document.getElementById('prefPromo').checked,area:document.getElementById('prefArea').value,theme:document.getElementById('prefTheme').value};localStorage.setItem('lonma_prefs',JSON.stringify(p));document.getElementById('prefStatus').innerText='Saved';setTimeout(()=>document.getElementById('prefStatus').innerText='',2000);}
function clearPrefs(){localStorage.removeItem('lonma_prefs');loadPrefs();}
function clearAllData(){if(confirm('Clear all data?')){localStorage.clear();cart=[];myOrders=[];updateCartCount();renderCart();renderOrders();}}
loadProducts();updateCartCount();renderCart();renderOrders();loadPrefs();
</script></body></html>
"""

@app.api_route("/", methods=["GET", "HEAD"])
def home():
    return HTMLResponse(HTML)

@app.get("/logo.png")
def logo():
    for f in ["logo.png", "static/logo.png"]:
        if os.path.exists(f):
            return FileResponse(f)
    return HTMLResponse("", 200)
