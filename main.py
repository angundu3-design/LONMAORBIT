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
conn.execute("CREATE TABLE IF NOT EXISTS products (id INTEGER PRIMARY KEY, name TEXT, price INTEGER, code TEXT, image TEXT, category TEXT, stock INTEGER, desc TEXT)")
conn.execute("CREATE TABLE IF NOT EXISTS orders (id INTEGER PRIMARY KEY AUTOINCREMENT, order_no TEXT, name TEXT, phone TEXT, area TEXT, location TEXT, items TEXT, subtotal INTEGER, delivery INTEGER, total INTEGER, status TEXT, created TEXT, mpesa_receipt TEXT, checkout_id TEXT, points_earned INTEGER)")
conn.execute("CREATE TABLE IF NOT EXISTS friends (id INTEGER PRIMARY KEY AUTOINCREMENT, user_phone TEXT, friend_phone TEXT, friend_name TEXT, status TEXT, created TEXT)")
conn.execute("CREATE TABLE IF NOT EXISTS referrals (id INTEGER PRIMARY KEY AUTOINCREMENT, code TEXT UNIQUE, owner_phone TEXT, discount INTEGER, created TEXT)")
conn.execute("CREATE TABLE IF NOT EXISTS shared_carts (id INTEGER PRIMARY KEY AUTOINCREMENT, share_code TEXT UNIQUE, owner_phone TEXT, items TEXT, created TEXT)")
conn.execute("CREATE TABLE IF NOT EXISTS wishlist (id INTEGER PRIMARY KEY AUTOINCREMENT, phone TEXT, product_id INTEGER, created TEXT)")
conn.execute("CREATE TABLE IF NOT EXISTS reviews (id INTEGER PRIMARY KEY AUTOINCREMENT, product_id INTEGER, phone TEXT, name TEXT, rating INTEGER, comment TEXT, created TEXT)")
conn.execute("CREATE TABLE IF NOT EXISTS loyalty (phone TEXT PRIMARY KEY, points INTEGER, total_spent INTEGER)")
conn.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, phone TEXT UNIQUE, name TEXT, password TEXT, created TEXT)")
cur = conn.cursor()
cur.execute("DELETE FROM products")
PRODUCTS = [(1,"LONMA Cooking Oil 2L",850,"LONMA-001","Cooking Oils",50,"Pure fortified"),(2,"LONMA Citronella Soap 110g",90,"LONMA-002","Soaps",120,"Citronella"),(3,"LONMA Men Lotion 72Hrs",299,"LONMA-003","Lotions",8,"72Hrs men"),(4,"LONMA Pine Soap 110g",90,"LONMA-004","Soaps",100,"Pine"),(5,"LONMA Cooking Oil 5L",1250,"LONMA-005","Cooking Oils",25,"5L family"),(6,"LONMA Cool Mint Soap 110g",90,"LONMA-006","Soaps",3,"Mint"),(7,"LONMA Anti-Dandruff Pomade",250,"LONMA-007","Pomades",40,"Anti-Dandruff"),(8,"LONMA Anti-Breakage Pomade",250,"LONMA-008","Pomades",45,"Anti-Breakage"),(9,"LONMA Cocoa Butter Lotion",299,"LONMA-009","Lotions",30,"Cocoa Butter")]
for pid,name,price,code,cat,stock,desc in PRODUCTS:
    img=f"https://via.placeholder.com/400x400/FFFFFF/0A9EBB?text={urllib.parse.quote(name)}"
    cur.execute("INSERT INTO products VALUES (?,?,?,?,?,?,?,?)",(pid,name,price,code,img,cat,stock,desc))
conn.commit()

def gen_code(n=6): return ''.join(random.choices(string.ascii_uppercase+string.digits,k=n))
def get_daraja_token():
    try:
        base="https://api.safaricom.co.ke" if USE_PRODUCTION else "https://sandbox.safaricom.co.ke"
        r=requests.get(f"{base}/oauth/v1/generate?grant_type=client_credentials",auth=(DARAJA_CONSUMER_KEY,DARAJA_CONSUMER_SECRET),timeout=10)
        return r.json().get("access_token")
    except: return None

@app.api_route("/mpesa/callback", methods=["GET","POST"])
@app.api_route("/callback", methods=["GET","POST"])
async def mpesa_callback(request: Request):
    try:
        data=await request.json()
        stk=data.get("Body",{}).get("stkCallback",{})
        if stk.get("ResultCode")==0:
            receipt=""
            for it in stk.get("CallbackMetadata",{}).get("Item",[]):
                if it.get("Name")=="MpesaReceiptNumber": receipt=it.get("Value")
            conn.execute("UPDATE orders SET status='PAID', mpesa_receipt=? WHERE checkout_id=?",(receipt,stk.get("CheckoutRequestID","")))
            conn.commit()
        return {"ResultCode":0,"ResultDesc":"Accepted"}
    except: return {"ResultCode":0,"ResultDesc":"Accepted"}

@app.get("/api/products")
def products_api():
    cur=conn.cursor()
    cur.execute("SELECT id,name,price,code,image,category,stock,desc FROM products")
    prods=[]
    for r in cur.fetchall():
        prods.append({"id":r[0],"name":r[1],"price":r[2],"code":r[3],"image":r[4],"category":r[5],"stock":r[6],"desc":r[7],"rating":5,"reviews":12})
    return prods
@app.get("/api/verify/{code}")
def verify(code: str):
    cur=conn.cursor()
    cur.execute("SELECT name FROM products WHERE code=?",(code.upper(),))
    row=cur.fetchone()
    return {"valid":True,"product":{"name":row[0]}} if row else {"valid":False}
@app.get("/api/orders")
def get_orders(phone: str=""):
    cur=conn.cursor()
    if phone: cur.execute("SELECT order_no,name,phone,area,location,items,subtotal,delivery,total,status,created FROM orders WHERE phone=? ORDER BY id DESC",(phone,))
    else: cur.execute("SELECT order_no,name,phone,area,location,items,subtotal,delivery,total,status,created FROM orders ORDER BY id DESC LIMIT 50")
    return [{"order_no":r[0],"name":r[1],"phone":r[2],"area":r[3],"location":r[4],"items":r[5],"subtotal":r[6],"delivery":r[7],"total":r[8],"status":r[9],"created":r[10]} for r in cur.fetchall()]
@app.get("/api/admin/orders")
def admin_orders_api():
    cur=conn.cursor()
    cur.execute("SELECT order_no,name,phone,area,location,items,subtotal,delivery,total,status,created,mpesa_receipt,checkout_id,points_earned FROM orders ORDER BY id DESC")
    return [{"order_no":r[0],"name":r[1],"phone":r[2],"area":r[3],"location":r[4],"items":r[5],"subtotal":r[6],"delivery":r[7],"total":r[8],"status":r[9],"created":r[10],"mpesa_receipt":r[11],"checkout_id":r[12],"points_earned":r[13]} for r in cur.fetchall()]
@app.get("/api/admin/analytics")
def analytics_api():
    cur=conn.cursor()
    cur.execute("SELECT COUNT(*), SUM(total) FROM orders WHERE status!='FAILED'")
    cnt,sales=cur.fetchone()
    cur.execute("SELECT name,stock FROM products WHERE stock<5")
    low=[{"name":r[0],"stock":r[1]} for r in cur.fetchall()]
    return {"orders":cnt or 0,"sales":sales or 0,"low_stock":low}
@app.get("/api/friends")
def list_friends_api(phone: str):
    cur=conn.cursor()
    cur.execute("SELECT friend_phone,friend_name,status FROM friends WHERE user_phone=?",(phone,))
    friends=[{"phone":r[0],"name":r[1],"status":r[2]} for r in cur.fetchall()]
    cur.execute("SELECT code FROM referrals WHERE owner_phone=?",(phone,))
    row=cur.fetchone()
    if not row:
        code=f"LONMA-{gen_code(4)}"
        cur.execute("INSERT INTO referrals (code,owner_phone,discount,created) VALUES (?,?,?,?)",(code,phone,100,datetime.datetime.now().strftime("%Y-%m-%d")))
        conn.commit()
        referral_code=code
    else: referral_code=row[0]
    return {"friends":friends,"referral_code":referral_code}
@app.post("/api/friends/invite")
async def invite_friend_api(req: Request):
    d=await req.json()
    conn.execute("INSERT INTO friends (user_phone,friend_phone,friend_name,status,created) VALUES (?,?,?,?,?)",(d.get("user_phone"),d.get("friend_phone"),d.get("friend_name","Friend"),"invited",datetime.datetime.now().strftime("%Y-%m-%d %H:%M")))
    conn.commit()
    return {"status":"ok"}
@app.post("/api/referral/apply")
async def apply_referral_api(req: Request):
    d=await req.json()
    cur=conn.cursor()
    cur.execute("SELECT owner_phone,discount FROM referrals WHERE code=?",(d.get("code","").upper(),))
    row=cur.fetchone()
    if not row: return {"status":"error","message":"Invalid"}
    return {"status":"ok","message":f"KSh {row[1]} OFF","discount":row[1]}
@app.post("/api/share-cart")
async def share_cart_api(req: Request):
    d=await req.json()
    code=gen_code(8)
    conn.execute("INSERT INTO shared_carts (share_code,owner_phone,items,created) VALUES (?,?,?,?)",(code,d.get("phone","guest"),json.dumps(d.get("cart",[])),datetime.datetime.now().strftime("%Y-%m-%d %H:%M")))
    conn.commit()
    return {"status":"ok","share_code":code,"share_url":f"https://app.lonmaorbit.co.ke/?share={code}"}
@app.get("/api/share-cart/{code}")
def get_shared_cart_api(code: str):
    cur=conn.cursor()
    cur.execute("SELECT items,owner_phone FROM shared_carts WHERE share_code=?",(code.upper(),))
    row=cur.fetchone()
    if not row: return {"status":"error"}
    return {"status":"ok","items":json.loads(row[0]),"owner":row[1]}
@app.get("/api/wishlist")
def wishlist_api(phone: str):
    cur=conn.cursor()
    cur.execute("SELECT p.id,p.name,p.price,p.image FROM wishlist w JOIN products p ON w.product_id=p.id WHERE w.phone=?",(phone,))
    return [{"id":r[0],"name":r[1],"price":r[2],"image":r[3]} for r in cur.fetchall()]
@app.post("/api/wishlist/toggle")
async def toggle_wishlist_api(req: Request):
    d=await req.json()
    cur=conn.cursor()
    cur.execute("SELECT id FROM wishlist WHERE phone=? AND product_id=?",(d.get("phone"),d.get("product_id")))
    if cur.fetchone():
        cur.execute("DELETE FROM wishlist WHERE phone=? AND product_id=?",(d.get("phone"),d.get("product_id")))
        conn.commit()
        return {"status":"removed"}
    cur.execute("INSERT INTO wishlist (phone,product_id,created) VALUES (?,?,?)",(d.get("phone"),d.get("product_id"),datetime.datetime.now().strftime("%Y-%m-%d")))
    conn.commit()
    return {"status":"added"}
@app.get("/api/loyalty/{phone}")
def loyalty_api(phone: str):
    cur=conn.cursor()
    cur.execute("SELECT points,total_spent FROM loyalty WHERE phone=?",(phone,))
    row=cur.fetchone()
    return {"points":row[0] if row else 0,"total_spent":row[1] if row else 0}
@app.post("/api/auth/register")
async def register_api(req: Request):
    d=await req.json()
    phone=d.get("phone","").strip()
    name=d.get("name","").strip()
    password=d.get("password","").strip()
    if not phone or not name or not password: return {"status":"error","message":"All required"}
    cur=conn.cursor()
    cur.execute("SELECT id FROM users WHERE phone=?",(phone,))
    if cur.fetchone(): return {"status":"error","message":"Phone exists"}
    cur.execute("INSERT INTO users (phone,name,password,created) VALUES (?,?,?,?)",(phone,name,password,datetime.datetime.now().strftime("%Y-%m-%d %H:%M")))
    conn.commit()
    return {"status":"ok","message":"Created","user":{"phone":phone,"name":name}}
@app.post("/api/auth/login")
async def login_api(req: Request):
    d=await req.json()
    cur=conn.cursor()
    cur.execute("SELECT phone,name FROM users WHERE phone=? AND password=?",(d.get("phone","").strip(),d.get("password","").strip()))
    row=cur.fetchone()
    if not row: return {"status":"error","message":"Wrong phone or password"}
    return {"status":"ok","message":"Logged in","user":{"phone":row[0],"name":row[1]}}
@app.post("/mpesa/stkpush")
async def stk_api(req: Request):
    d=await req.json()
    raw_phone=d.get('phone','').strip()
    phone=raw_phone.replace(" ","").replace("+254","0")
    if phone.startswith("0"): phone="254"+phone[1:]
    phone="".join([c for c in phone if c.isdigit()])
    amount=int(d.get('amount',1))
    order_no='LONMA'+datetime.datetime.now().strftime("%H%M%S")
    items_text=json.dumps([f"{c.get('name')} x{c.get('qty')}" for c in d.get('cart',[])])
    conn.execute("INSERT INTO orders (order_no,name,phone,area,location,items,subtotal,delivery,total,status,created,mpesa_receipt,checkout_id,points_earned) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",(order_no,d.get('name','Guest'),raw_phone,d.get('area'),d.get('location'),items_text,d.get('subtotal',0),d.get('delivery',0),d.get('amount',0),'Pending',datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),"",order_no,amount//100))
    conn.commit()
    if DARAJA_CONSUMER_KEY and DARAJA_CONSUMER_SECRET and DARAJA_PASSKEY:
        token=get_daraja_token()
        if token:
            ts=datetime.datetime.now().strftime("%Y%m%d%H%M%S")
            pwd=base64.b64encode(f"{DARAJA_SHORTCODE}{DARAJA_PASSKEY}{ts}".encode()).decode()
            payload={"BusinessShortCode":DARAJA_SHORTCODE,"Password":pwd,"Timestamp":ts,"TransactionType":"CustomerPayBillOnline","Amount":amount,"PartyA":phone,"PartyB":DARAJA_SHORTCODE,"PhoneNumber":phone,"CallBackURL":DARAJA_CALLBACK_URL,"AccountReference":order_no,"TransactionDesc":f"LONMA {order_no}"}
            try:
                base="https://api.safaricom.co.ke" if USE_PRODUCTION else "https://sandbox.safaricom.co.ke"
                r=requests.post(f"{base}/mpesa/stkpush/v1/processrequest",json=payload,headers={"Authorization":f"Bearer {token}"},timeout=15)
                res=r.json()
                if res.get("ResponseCode")=="0":
                    conn.execute("UPDATE orders SET checkout_id=? WHERE order_no=?",(res.get("CheckoutRequestID",order_no),order_no))
                    conn.commit()
                    return {"status":"ok","message":f"STK sent to {raw_phone}","order_no":order_no}
            except: pass
    return {"status":"ok","message":f"Order {order_no} saved","order_no":order_no}

HTML = """<!DOCTYPE html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>LONMA ORBIT</title><style>
:root{--teal:#0A9EBB;--line:#f1f5f9;--muted:#94a3b8;--ink:#0f172a}*{box-sizing:border-box}body{margin:0;font-family:-apple-system,Inter,Arial;background:#f8fafc;color:var(--ink)}
.nav{position:fixed;top:0;width:100%;background:var(--teal);z-index:1000}.nav-top{padding:10px 14px;display:flex;justify-content:space-between;align-items:center;height:56px}
.logo-circle{background:#fff;width:36px;height:36px;border-radius:50%;display:flex;align-items:center;justify-content:center;overflow:hidden;cursor:pointer}
.logo-circle img{width:32px;height:32px;object-fit:cover;border-radius:50%}
.search-bar-wrap{padding:0 12px 12px;background:var(--teal)}.search-app-bar{background:#fff;border-radius:12px;height:42px;display:flex;align-items:center;gap:10px;padding:0 14px}
.search-app-bar input{border:none;outline:none;flex:1;font-size:14px}.hamburger{color:var(--teal);font-size:22px;cursor:pointer}
.cart-icon{background:#fff;color:var(--teal);padding:7px 14px;border-radius:20px;font-weight:700;font-size:11px;position:relative;cursor:pointer}
.cart-count{position:absolute;top:-6px;right:-6px;background:var(--ink);color:#fff;border-radius:50%;width:18px;height:18px;display:flex;align-items:center;justify-content:center;font-size:10px}
.page{display:none;padding:112px 10px 80px}.page.active{display:block}
.card{background:#fff;border-radius:16px;padding:12px;margin:8px 0;border:1px solid var(--line);box-shadow:0 1px 3px rgba(0,0,0,.04)}
.card img{width:100%;height:150px;object-fit:contain;background:#fff;border-radius:12px}
.btn{background:var(--teal);color:#fff;border:none;padding:11px;border-radius:24px;width:100%;font-weight:700;cursor:pointer}
input,select,textarea{width:100%;padding:12px;border-radius:12px;border:1px solid var(--line);margin:5px 0;font-size:13px}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:10px}
.bottom{position:fixed;bottom:0;width:100%;background:#ffffffee;backdrop-filter:blur(8px);display:flex;justify-content:space-around;padding:8px 0;border-top:1px solid var(--line);z-index:1000}
.bottom div{font-size:10px;color:var(--muted);text-align:center;flex:1;cursor:pointer}.bottom div.active{color:var(--teal);font-weight:700}
.side-menu{position:fixed;top:0;left:-320px;width:300px;height:100%;background:#fff;z-index:2000;transition:.32s;overflow-y:auto}
.side-menu.open{left:0}.overlay{display:none;position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(15,23,42,.32);z-index:1999}.overlay.open{display:block}
.top-grad{background:linear-gradient(135deg,#0A9EBB 0%,#14b8a6 100%);padding:16px 14px 28px;color:#fff}
.logo-center{width:64px;height:64px;background:#fff;border-radius:50%;margin:0 auto;display:flex;align-items:center;justify-content:center;overflow:hidden;box-shadow:0 4px 12px rgba(0,0,0,.15)}
.user-card{margin:-18px 12px 0;background:#fff;border-radius:16px;padding:12px;display:flex;align-items:center;gap:12px;box-shadow:0 8px 24px rgba(15,23,42,.08);border:1px solid #f1f5f9;cursor:pointer}
.avatar{width:42px;height:42px;border-radius:50%;background:#0A9EBB;color:#fff;display:flex;align-items:center;justify-content:center;font-weight:800}
.sec-label{font-size:10px;font-weight:800;letter-spacing:.16em;color:#94a3b8;text-align:center;margin:18px 0 8px}
.menu-row{display:flex;align-items:center;gap:12px;padding:12px 16px;cursor:pointer}
.menu-row:hover{background:#f8fafc}
.icon-box{width:36px;height:36px;border-radius:10px;display:flex;align-items:center;justify-content:center;font-size:15px}
.badge{margin-left:auto;font-size:11px;font-weight:700;padding:4px 9px;border-radius:20px}
.admin-btn{margin:16px 12px;background:linear-gradient(135deg,#0A9EBB,#0891b2);color:#fff;border-radius:16px;padding:14px;text-align:center;cursor:pointer;box-shadow:0 6px 16px rgba(10,158,187,.3)}
</style></head><body>
<div class="nav"><div class="nav-top"><div class="logo-circle" onclick="show('products')"><img src="/logo.png"></div><div class="cart-icon" onclick="show('cart')">CART <span id="cartCount" class="cart-count" style="display:none">0</span></div></div><div class="search-bar-wrap"><div class="search-app-bar"><span class="hamburger" onclick="openSideMenu()">☰</span><input id="searchInput" placeholder="Search products..." oninput="filterProducts()"></div></div></div>
<div class="overlay" id="overlay" onclick="closeSideMenu()"></div>
<div class="side-menu" id="sideMenu">
<div class="top-grad">
<div style="display:flex;justify-content:flex-end"><span style="background:rgba(0,0,0,.18);padding:6px 12px;border-radius:20px;font-size:11px;font-weight:700;cursor:pointer" onclick="show('cart');closeSideMenu()">CART</span></div>
<div class="logo-center" onclick="show('products');closeSideMenu()"><img src="/logo.png" style="width:60px;height:60px;object-fit:cover;border-radius:50%"></div>
<div style="text-align:center;margin-top:10px;font-weight:800;font-size:20px">LONMA ORBIT</div>
<div style="text-align:center;margin-top:8px"><span style="background:rgba(255,255,255,.22);padding:5px 12px;border-radius:20px;font-size:11px;font-weight:600">🏠 Home • Tap logo to return</span></div>
</div>
<div class="user-card" onclick="show('account');closeSideMenu()">
<div class="avatar" id="avatarInit">JD</div>
<div style="flex:1"><div style="font-weight:700;font-size:14px" id="sideUserName">John Doe</div><div style="font-size:12px;color:#94a3b8" id="sideUserSub">Guest • Create or Sign In →</div></div>
<div style="color:#cbd5e1">›</div>
</div>
<div class="sec-label">— SHOP —</div>
<div class="menu-row" onclick="show('products');closeSideMenu()"><div class="icon-box" style="background:#dbeafe">🏠</div><div style="font-weight:500">Products • Home</div><span class="badge" style="background:#0A9EBB;color:#fff">New</span></div>
<div class="menu-row" onclick="show('cart');closeSideMenu()"><div class="icon-box" style="background:#ffedd5">🛒</div><div>Cart</div><span class="badge" style="background:#f1f5f9;color:#64748b" id="sideCartCount">0</span></div>
<div class="menu-row" onclick="show('wishlist');closeSideMenu()"><div class="icon-box" style="background:#ffe4e6">♡</div><div>Wishlist</div><span class="badge" style="background:#fecdd3;color:#e11d48" id="sideWishCount">0</span></div>
<div class="sec-label">ACTIVITY</div>
<div class="menu-row" onclick="show('friends');closeSideMenu()"><div class="icon-box" style="background:#ede9fe">👥</div><div>Friends & Share Cart</div><span class="badge" style="background:#f5f3ff;color:#8b5cf6">+ Invite</span></div>
<div class="menu-row" onclick="show('orders');closeSideMenu()"><div class="icon-box" style="background:#dbeafe">📦</div><div>Orders & Tracking</div></div>
<div class="menu-row" onclick="show('loyaltyPage');closeSideMenu()"><div class="icon-box" style="background:#fef3c7">★</div><div>Loyalty Points</div><span class="badge" style="background:#fde68a;color:#92400e" id="sidePoints">0 pts</span></div>
<div class="sec-label">SUPPORT & ACCOUNT</div>
<div class="menu-row" onclick="show('scan');closeSideMenu()"><div class="icon-box" style="background:#dcfce7">🛡️</div><div>Verify LONMA Code</div></div>
<div class="menu-row" onclick="show('settings');closeSideMenu()"><div class="icon-box" style="background:#f1f5f9">⚙️</div><div>Settings</div></div>
<div class="sec-label">ADMIN</div>
<div class="admin-btn" onclick="show('admin');closeSideMenu()"><div style="font-weight:800">🔐 Admin Analytics</div><div style="font-size:11px;opacity:.9;margin-top:2px">Admin access only</div></div>
<div style="text-align:center;padding:10px 0 20px;font-size:11px;color:#94a3b8">ⓥ v2.1.0 • Help & Support</div>
</div>

<div id="products" class="page active"><div id="plist"></div></div>
<div id="account" class="page"><h3>Account</h3><div id="accountLoggedOut"><div class="card"><h4>Create</h4><input id="regName" placeholder="Full name"><input id="regPhone" placeholder="07xxxxxxxx"><input id="regPass" type="password" placeholder="Password"><button class="btn" onclick="registerUser()">Create</button><p id="regStatus"></p></div><div class="card"><h4>Sign in</h4><input id="loginPhone" placeholder="07xxxxxxxx"><input id="loginPass" type="password" placeholder="Password"><button class="btn" style="background:#0f172a" onclick="loginUser()">Sign in</button><p id="loginStatus"></p></div></div><div id="accountLoggedIn" style="display:none"><div class="card" style="background:#0f172a;color:#fff"><h2 id="accName">Welcome</h2><p id="accPhone"></p><button class="btn" style="background:#fff;color:#0f172a;margin-top:10px" onclick="logoutUser()">Sign out</button></div></div></div>
<div id="friends" class="page"><h3>Friends</h3><div class="card"><input id="myReferralCode" readonly><button class="btn" onclick="copyReferral()">Copy</button><button class="btn" style="background:#0f172a;margin-top:6px" onclick="shareReferralWhatsApp()">Share</button><p id="shareLinkResult"></p></div><div class="card"><input id="friendName" placeholder="Friend name"><input id="friendPhone" placeholder="Friend phone"><button class="btn" onclick="inviteFriend()">Invite</button><p id="friendStatus"></p></div><div class="card"><input id="joinShareCode" placeholder="Share code"><button class="btn" onclick="joinSharedCart()">Join</button></div><div id="friendsList"></div></div>
<div id="wishlist" class="page"><h3>Wishlist</h3><div id="wishlistItems"></div></div>
<div id="loyaltyPage" class="page"><h3>Loyalty</h3><div class="card" style="text-align:center"><h1 id="loyaltyPoints">0</h1><p>Points</p></div></div>
<div id="cart" class="page"><h3>Cart</h3><div id="cartItems"></div><div class="card" id="cartSummary" style="display:none"><div>Subtotal (<span id="totalItems">0</span>): KSh <span id="subTotal">0</span></div><div>Delivery: <span id="deliveryFee"></span></div><div>Total: KSh <span id="totalPrice">0</span></div><div style="margin-top:10px"><input id="custName" placeholder="Full name"><input id="phone" placeholder="07xxxxxxxx"><select id="locationArea"><option value="">Area</option><option value="CBD">CBD - 150</option><option value="Westlands">Westlands - 200</option><option value="Upcountry">Upcountry - 350</option></select><textarea id="exactLocation" placeholder="Location"></textarea><div style="display:flex;gap:6px"><input id="promoCode" placeholder="Referral"><button class="btn" style="width:auto" onclick="applyReferralCode()">Apply</button></div><label style="font-size:12px"><input type="checkbox" id="agreeTerms" style="width:auto"> Agree</label></div><button class="btn" style="background:#0f172a;margin-top:10px" onclick="checkout()">Pay KSh <span id="payTotal">0</span></button><p id="paystatus"></p></div><div class="card" id="emptyCart" style="text-align:center"><p>Cart empty</p><button class="btn" onclick="show('products')">Shop</button></div></div>
<div id="orders" class="page"><h3>Orders</h3><div style="display:flex;gap:6px"><input id="orderPhoneLookup" placeholder="Phone"><button class="btn" style="width:auto" onclick="loadMyOrdersByPhone()">Load</button></div><div id="ordersList"></div><div id="noOrders" class="card" style="text-align:center"><p>No orders</p></div></div>
<div id="scan" class="page"><h3>Verify</h3><div class="card"><input id="manualcode" placeholder="LONMA-001"><button class="btn" onclick="verifyCode()">Verify</button><p id="scanresult"></p></div></div>
<div id="settings" class="page"><h3>Settings</h3><div class="card"><button class="btn" style="background:#fff;color:#ef4444;border:1px solid #fecaca" onclick="clearAllData()">Clear data</button></div></div>
<div id="admin" class="page"><h3>Admin</h3><div class="card"><input id="adminPass" type="password" placeholder="lonma2024"><button class="btn" onclick="adminLogin()">Login</button><p id="adminStatus"></p></div><div id="adminContent" style="display:none"><div class="card"><b>Orders:</b> <span id="statOrders">0</span> | Sales: <span id="statSales">0</span></div><div id="adminOrdersList"></div></div></div>
<div id="receipt" class="page"><h3>Receipt</h3><div class="card" id="receiptContent"></div><button class="btn" onclick="show('products')">Continue</button></div>
<div class="bottom"><div id="b-products" class="active" onclick="show('products')">Products</div><div id="b-cart" onclick="show('cart')">Cart</div><div id="b-wishlist" onclick="show('wishlist')">Wishlist</div><div id="b-orders" onclick="show('orders')">Orders</div><div id="b-account" onclick="show('account')">Account</div></div>
<script>
let allProducts=[],searchQuery='',cart=[],myOrders=JSON.parse(localStorage.getItem('my_orders')||'[]'),referralDiscountValue=0;
try{let s=localStorage.getItem('lonma_cart');if(s)cart=JSON.parse(s);}catch(e){cart=[];}
function saveCart(){localStorage.setItem('lonma_cart',JSON.stringify(cart));updateCartCount();}
function updateCartCount(){let c=0;for(let i of cart)c+=i.qty;document.getElementById('cartCount').innerText=c;document.getElementById('sideCartCount').innerText=c;document.getElementById('cartCount').style.display=c>0?'flex':'none';fetchWishlistCount();fetchLoyaltyCount();}
function openSideMenu(){document.getElementById('sideMenu').classList.add('open');document.getElementById('overlay').classList.add('open');}
function closeSideMenu(){document.getElementById('sideMenu').classList.remove('open');document.getElementById('overlay').classList.remove('open');}
function filterProducts(){searchQuery=document.getElementById('searchInput').value.toLowerCase();renderProducts();}
function calcBulk(p,q){if(q>=3&&p==90)return 80;if(q>=2&&p>=250)return Math.floor(p*0.9);return p;}
function renderProducts(){let list=allProducts.filter(p=>!searchQuery||p.name.toLowerCase().includes(searchQuery));let html='';for(let p of list){let inCart=cart.find(c=>c.id===p.id);html+=`<div class="card"><img src="${p.image}"><div style="font-weight:700;margin-top:6px;font-size:13px">${p.name}</div><div style="font-weight:800">KSh ${p.price}</div><div style="font-size:11px;color:#94a3b8">${inCart?'• '+inCart.qty+' in cart':''}</div><button class="btn" style="margin-top:8px" onclick="addToCart(${p.id})">Add</button></div>`;}document.getElementById('plist').innerHTML=`<div class="grid">${html}</div>`;}
function addToCart(id){let p=allProducts.find(x=>x.id===id);let f=cart.find(c=>c.id===id);if(f)f.qty++;else cart.push({id:p.id,name:p.name,price:p.price,image:p.image,qty:1});saveCart();renderProducts();}
function renderCart(){let cont=document.getElementById('cartItems'),sum=document.getElementById('cartSummary'),empty=document.getElementById('emptyCart');if(cart.length===0){cont.innerHTML='';sum.style.display='none';empty.style.display='block';return;}empty.style.display='none';sum.style.display='block';let sub=0,items=0,html='';for(let it of cart){let u=calcBulk(it.price,it.qty);sub+=u*it.qty;items+=it.qty;html+=`<div class="card" style="display:flex;gap:10px"><img src="${it.image}" style="width:50px;height:50px"><div><div style="font-weight:600">${it.name}</div><div>KSh ${u} x ${it.qty}</div></div></div>`;}cont.innerHTML=html;let area=document.getElementById('locationArea').value;let del=area==='CBD'?150:area==='Upcountry'?350:200;if(sub>=2000)del=0;let tot=sub+del-referralDiscountValue;document.getElementById('subTotal').innerText=sub;document.getElementById('totalItems').innerText=items;document.getElementById('deliveryFee').innerText=del==0?'FREE':'KSh '+del;document.getElementById('totalPrice').innerText=tot<0?0:tot;document.getElementById('payTotal').innerText=tot<0?0:tot;}
function show(id){document.querySelectorAll('.page').forEach(p=>p.classList.remove('active'));document.getElementById(id).classList.add('active');document.querySelectorAll('.bottom div').forEach(b=>b.classList.remove('active'));let btn=document.getElementById('b-'+id);if(btn)btn.classList.add('active');if(id==='cart')renderCart();if(id==='orders')renderOrders();if(id==='wishlist')loadWishlist();if(id==='loyaltyPage')loadLoyalty();if(id==='friends')loadFriends();if(id==='account')checkAccountUI();closeSideMenu();window.scrollTo(0,0);}
async function loadProducts(){let r=await fetch('/api/products');allProducts=await r.json();renderProducts();}
async function verifyCode(){let c=document.getElementById('manualcode').value.trim();let r=await fetch(`/api/verify/${c}`);let d=await r.json();document.getElementById('scanresult').innerText=d.valid?'Valid '+d.product.name:'Invalid';}
async function checkout(){let name=document.getElementById('custName').value.trim(),phone=document.getElementById('phone').value.trim(),area=document.getElementById('locationArea').value,loc=document.getElementById('exactLocation').value.trim();if(!name||!phone||!area||!loc||!document.getElementById('agreeTerms').checked){document.getElementById('paystatus').innerText='Fill all';return;}let sub=0;for(let i of cart)sub+=calcBulk(i.price,i.qty)*i.qty;let del=area==='CBD'?150:area==='Upcountry'?350:200;if(sub>=2000)del=0;let tot=sub+del-referralDiscountValue;document.getElementById('paystatus').innerText='Sending STK...';let r=await fetch('/mpesa/stkpush',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({phone,amount:tot,cart,name,area,location:loc,subtotal:sub,delivery:del})});let d=await r.json();document.getElementById('paystatus').innerText=d.message;if(d.status==='ok'){myOrders.unshift({order_no:d.order_no,total:tot,status:'Pending',created:new Date().toLocaleString()});localStorage.setItem('my_orders',JSON.stringify(myOrders));document.getElementById('receiptContent').innerHTML=`<h3>${d.order_no}</h3><p>KSh ${tot}</p>`;cart=[];localStorage.removeItem('lonma_cart');saveCart();show('receipt');}}
async function loadMyOrdersByPhone(){let ph=document.getElementById('orderPhoneLookup').value.trim();let r=await fetch(`/api/orders?phone=${ph}`);let data=await r.json();document.getElementById('ordersList').innerHTML=data.map(o=>`<div class="card"><b>${o.order_no}</b> ${o.status}<br>KSh ${o.total}</div>`).join('');}
function renderOrders(){let c=document.getElementById('ordersList');if(myOrders.length==0){document.getElementById('noOrders').style.display='block';c.innerHTML='';return;}document.getElementById('noOrders').style.display='none';c.innerHTML=myOrders.map(o=>`<div class="card"><b>${o.order_no}</b> ${o.status}<br>KSh ${o.total}</div>`).join('');}
async function adminLogin(){let p=document.getElementById('adminPass').value;if(p!=='lonma2024'){document.getElementById('adminStatus').innerText='Wrong';return;}document.getElementById('adminContent').style.display='block';let r=await fetch('/api/admin/orders');let d=await r.json();let a=await fetch('/api/admin/analytics');let an=await a.json();document.getElementById('statOrders').innerText=an.orders;document.getElementById('statSales').innerText=an.sales;document.getElementById('adminOrdersList').innerHTML=d.map(o=>`<div class="card">${o.order_no} - ${o.phone} - KSh ${o.total} - ${o.status}</div>`).join('');}
async function loadFriends(){let phone=document.getElementById('phone').value||localStorage.getItem('user_phone')||JSON.parse(localStorage.getItem('lonma_user')||'{}').phone||'';if(!phone)return;let r=await fetch(`/api/friends?phone=${phone}`);let data=await r.json();document.getElementById('myReferralCode').value=data.referral_code;document.getElementById('friendsList').innerHTML=data.friends.map(f=>`<div class="card">${f.name} - ${f.phone}</div>`).join('');}
async function inviteFriend(){let up=document.getElementById('phone').value||localStorage.getItem('user_phone');let fp=document.getElementById('friendPhone').value;let fn=document.getElementById('friendName').value;let r=await fetch('/api/friends/invite',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({user_phone:up,friend_phone:fp,friend_name:fn})});let d=await r.json();document.getElementById('friendStatus').innerText='Invited';loadFriends();}
async function applyReferralCode(){let code=document.getElementById('promoCode').value.trim().toUpperCase();let r=await fetch('/api/referral/apply',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({code})});let d=await r.json();if(d.status==='ok'){referralDiscountValue=d.discount;renderCart();}}
function copyReferral(){let el=document.getElementById('myReferralCode');el.select();document.execCommand('copy');}
function shareReferralWhatsApp(){let c=document.getElementById('myReferralCode').value;window.open(`https://wa.me/?text=${encodeURIComponent('My LONMA code '+c+' https://app.lonmaorbit.co.ke')}`,'_blank');}
async function loadWishlist(){let ph=document.getElementById('phone').value||localStorage.getItem('user_phone')||'';if(!ph)return;let r=await fetch(`/api/wishlist?phone=${ph}`);let data=await r.json();document.getElementById('wishlistItems').innerHTML=data.map(i=>`<div class="card">${i.name} - KSh ${i.price}</div>`).join('');}
async function fetchWishlistCount(){let ph=document.getElementById('phone').value||localStorage.getItem('user_phone')||JSON.parse(localStorage.getItem('lonma_user')||'{}').phone||'';if(!ph)return;let r=await fetch(`/api/wishlist?phone=${ph}`);let d=await r.json();document.getElementById('sideWishCount').innerText=d.length;}
async function loadLoyalty(){let ph=document.getElementById('phone').value||localStorage.getItem('user_phone')||JSON.parse(localStorage.getItem('lonma_user')||'{}').phone||'';if(!ph)return;let r=await fetch(`/api/loyalty/${ph}`);let d=await r.json();document.getElementById('loyaltyPoints').innerText=d.points;document.getElementById('sidePoints').innerText=d.points+' pts';}
async function fetchLoyaltyCount(){let ph=document.getElementById('phone').value||localStorage.getItem('user_phone')||JSON.parse(localStorage.getItem('lonma_user')||'{}').phone||'';if(!ph)return;let r=await fetch(`/api/loyalty/${ph}`);let d=await r.json();document.getElementById('sidePoints').innerText=d.points+' pts';}
function clearAllData(){localStorage.clear();cart=[];myOrders=[];updateCartCount();show('products');}
async function registerUser(){let name=document.getElementById('regName').value.trim(),phone=document.getElementById('regPhone').value.trim(),pass=document.getElementById('regPass').value.trim();let r=await fetch('/api/auth/register',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name,phone,password:pass})});let d=await r.json();document.getElementById('regStatus').innerText=d.message;if(d.status==='ok'){localStorage.setItem('lonma_user',JSON.stringify(d.user));localStorage.setItem('user_phone',phone);checkAccountUI();show('products');}}
async function loginUser(){let phone=document.getElementById('loginPhone').value.trim(),pass=document.getElementById('loginPass').value.trim();let r=await fetch('/api/auth/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({phone,password:pass})});let d=await r.json();document.getElementById('loginStatus').innerText=d.message;if(d.status==='ok'){localStorage.setItem('lonma_user',JSON.stringify(d.user));localStorage.setItem('user_phone',phone);checkAccountUI();show('products');}}
function logoutUser(){localStorage.removeItem('lonma_user');checkAccountUI();show('account');}
function checkAccountUI(){let u=JSON.parse(localStorage.getItem('lonma_user')||'null');if(u){document.getElementById('accountLoggedOut').style.display='none';document.getElementById('accountLoggedIn').style.display='block';document.getElementById('accName').innerText=u.name;document.getElementById('accPhone').innerText=u.phone;document.getElementById('sideUserName').innerText=u.name;document.getElementById('sideUserSub').innerText=u.phone+' • Signed In';document.getElementById('avatarInit').innerText=u.name.substring(0,2).toUpperCase();}else{document.getElementById('accountLoggedOut').style.display='block';document.getElementById('accountLoggedIn').style.display='none';document.getElementById('sideUserName').innerText='John Doe';document.getElementById('sideUserSub').innerText='Guest • Create or Sign In →';document.getElementById('avatarInit').innerText='JD';}}
async function joinSharedCart(){let code=document.getElementById('joinShareCode').value.trim().toUpperCase();let r=await fetch(`/api/share-cart/${code}`);let d=await r.json();if(d.status==='ok'){cart=d.items;saveCart();show('cart');}}
document.getElementById('locationArea')?.addEventListener('change',renderCart);
loadProducts();updateCartCount();setTimeout(checkAccountUI,400);
</script></body></html>
"""

@app.api_route("/", methods=["GET", "HEAD"])
def home(): return HTMLResponse(HTML)

@app.get("/logo.png")
def logo():
    for f in ["logo.png","static/logo.png","./logo.png"]:
        if os.path.exists(f): return FileResponse(f)
    return HTMLResponse("",200)
