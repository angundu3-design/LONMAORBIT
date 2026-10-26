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
PRODUCTS = [(1,"LONMA Cooking Oil 2L",850,"LONMA-001","Cooking Oils",50,"LONMA pure fortified 2L"),(2,"LONMA Citronella Soap 110g",90,"LONMA-002","Soaps",120,"LONMA citronella 110g"),(3,"LONMA Men Lotion 72Hrs",299,"LONMA-003","Lotions",8,"LONMA 72Hrs"),(4,"LONMA Pine Soap 110g",90,"LONMA-004","Soaps",100,"LONMA pine"),(5,"LONMA Cooking Oil 5L",1250,"LONMA-005","Cooking Oils",25,"LONMA 5L"),(6,"LONMA Cool Mint Soap 110g",90,"LONMA-006","Soaps",3,"LONMA mint"),(7,"LONMA Anti-Dandruff Pomade",250,"LONMA-007","Pomades",40,"LONMA"),(8,"LONMA Anti-Breakage Pomade",250,"LONMA-008","Pomades",45,"LONMA"),(9,"LONMA Cocoa Butter Lotion",299,"LONMA-009","Lotions",30,"LONMA cocoa")]
for pid,name,price,code,cat,stock,desc in PRODUCTS:
    os.makedirs("static", exist_ok=True)
    img=f"/static/{code}.jpg"
    if not os.path.exists(f"static/{code}.jpg"): img=f"https://via.placeholder.com/400x400/FFFFFF/0A9EBB?text={urllib.parse.quote(name)}"
    cur.execute("INSERT INTO products VALUES (?,?,?,?,?,?,?,?)",(pid,name,price,code,img,cat,stock,desc))
conn.commit()

def gen_code(n=6): return ''.join(random.choices(string.ascii_uppercase + string.digits, k=n))
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

@app.get("/favicon.ico")
def favicon():
    for f in ["logo.png","static/logo.png"]:
        if os.path.exists(f): return FileResponse(f)
    return HTMLResponse("",200)

@app.get("/api/products")
def products_api():
    cur=conn.cursor()
    cur.execute("SELECT id,name,price,code,image,category,stock,desc FROM products")
    prods=[]
    for r in cur.fetchall():
        cur.execute("SELECT AVG(rating), COUNT(*) FROM reviews WHERE product_id=?",(r[0],))
        avg,cnt=cur.fetchone()
        prods.append({"id":r[0],"name":r[1],"price":r[2],"code":r[3],"image":r[4],"category":r[5],"stock":r[6],"desc":r[7],"rating":round(avg,1) if avg else 0,"reviews":cnt})
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

@app.post("/api/admin/orders/{order_no}/{status}")
def admin_update(order_no: str, status: str):
    conn.execute("UPDATE orders SET status=? WHERE order_no=?",(status,order_no))
    conn.commit()
    return {"message":f"Marked {status}"}

@app.get("/api/friends")
def list_friends_api(phone: str):
    cur=conn.cursor()
    cur.execute("SELECT friend_phone, friend_name, status, created FROM friends WHERE user_phone=?",(phone,))
    friends=[{"phone":r[0],"name":r[1],"status":r[2],"created":r[3]} for r in cur.fetchall()]
    cur.execute("SELECT code FROM referrals WHERE owner_phone=?",(phone,))
    row=cur.fetchone()
    if not row:
        code=f"LONMA-{gen_code(4)}"
        cur.execute("INSERT INTO referrals (code, owner_phone, discount, created) VALUES (?,?,?,?)",(code,phone,100,datetime.datetime.now().strftime("%Y-%m-%d")))
        conn.commit()
        referral_code=code
    else: referral_code=row[0]
    return {"friends":friends,"referral_code":referral_code}

@app.post("/api/friends/invite")
async def invite_friend_api(req: Request):
    d=await req.json()
    conn.execute("INSERT INTO friends (user_phone, friend_phone, friend_name, status, created) VALUES (?,?,?,?,?)",(d.get("user_phone"),d.get("friend_phone"),d.get("friend_name","Friend"),"invited",datetime.datetime.now().strftime("%Y-%m-%d %H:%M")))
    conn.commit()
    return {"status":"ok","message":"Invited"}

@app.post("/api/referral/apply")
async def apply_referral_api(req: Request):
    d=await req.json()
    cur=conn.cursor()
    cur.execute("SELECT owner_phone, discount FROM referrals WHERE code=?",(d.get("code","").upper(),))
    row=cur.fetchone()
    if not row: return {"status":"error","message":"Invalid"}
    return {"status":"ok","message":f"KSh {row[1]} OFF","discount":row[1]}

@app.post("/api/share-cart")
async def share_cart_api(req: Request):
    d=await req.json()
    code=gen_code(8)
    conn.execute("INSERT INTO shared_carts (share_code, owner_phone, items, created) VALUES (?,?,?,?)",(code,d.get("phone","guest"),json.dumps(d.get("cart",[])),datetime.datetime.now().strftime("%Y-%m-%d %H:%M")))
    conn.commit()
    return {"status":"ok","share_code":code,"share_url":f"https://app.lonmaorbit.co.ke/?share={code}"}

@app.get("/api/share-cart/{code}")
def get_shared_cart_api(code: str):
    cur=conn.cursor()
    cur.execute("SELECT items, owner_phone FROM shared_carts WHERE share_code=?",(code.upper(),))
    row=cur.fetchone()
    if not row: return {"status":"error","message":"Invalid"}
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

@app.get("/api/reviews/{pid}")
def get_reviews_api(pid: int):
    cur=conn.cursor()
    cur.execute("SELECT name,rating,comment,created FROM reviews WHERE product_id=? ORDER BY id DESC LIMIT 20",(pid,))
    return [{"name":r[0],"rating":r[1],"comment":r[2],"created":r[3]} for r in cur.fetchall()]

@app.post("/api/reviews")
async def add_review_api(req: Request):
    d=await req.json()
    conn.execute("INSERT INTO reviews (product_id,phone,name,rating,comment,created) VALUES (?,?,?,?,?,?)",(d.get("product_id"),d.get("phone"),d.get("name","Customer"),d.get("rating",5),d.get("comment",""),datetime.datetime.now().strftime("%Y-%m-%d %H:%M")))
    conn.commit()
    return {"status":"ok"}

@app.get("/api/loyalty/{phone}")
def loyalty_api(phone: str):
    cur=conn.cursor()
    cur.execute("SELECT points,total_spent FROM loyalty WHERE phone=?",(phone,))
    row=cur.fetchone()
    return {"points":row[0] if row else 0,"total_spent":row[1] if row else 0}

@app.post("/api/loyalty/redeem")
async def redeem_api(req: Request):
    d=await req.json()
    cur=conn.cursor()
    cur.execute("SELECT points FROM loyalty WHERE phone=?",(d.get("phone"),))
    row=cur.fetchone()
    if not row or row[0]<int(d.get("points",0)): return {"status":"error","message":"Not enough"}
    discount=int(d.get("points",0))*10
    cur.execute("UPDATE loyalty SET points=points-? WHERE phone=?",(int(d.get("points",0)),d.get("phone")))
    conn.commit()
    return {"status":"ok","discount":discount}

@app.post("/api/auth/register")
async def register_api(req: Request):
    d=await req.json()
    phone=d.get("phone","").strip()
    name=d.get("name","").strip()
    password=d.get("password","").strip()
    if not phone or not name or not password: return {"status":"error","message":"All fields required"}
    cur=conn.cursor()
    cur.execute("SELECT id FROM users WHERE phone=?",(phone,))
    if cur.fetchone(): return {"status":"error","message":"Phone already registered"}
    cur.execute("INSERT INTO users (phone,name,password,created) VALUES (?,?,?,?)",(phone,name,password,datetime.datetime.now().strftime("%Y-%m-%d %H:%M")))
    conn.commit()
    return {"status":"ok","message":"Account created","user":{"phone":phone,"name":name}}

@app.post("/api/auth/login")
async def login_api(req: Request):
    d=await req.json()
    phone=d.get("phone","").strip()
    password=d.get("password","").strip()
    cur=conn.cursor()
    cur.execute("SELECT phone,name FROM users WHERE phone=? AND password=?",(phone,password))
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
                    chk=res.get("CheckoutRequestID",order_no)
                    conn.execute("UPDATE orders SET checkout_id=? WHERE order_no=?",(chk,order_no))
                    conn.commit()
                    return {"status":"ok","message":f"STK sent to {raw_phone}","order_no":order_no}
            except: pass
    return {"status":"ok","message":f"Order {order_no} saved","order_no":order_no}

HTML = """<!DOCTYPE html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>LONMA ORBIT</title><style>
:root{--teal:#0A9EBB;--ink:#0f172a;--muted:#64748b;--line:#eef2f7}*{box-sizing:border-box}body{margin:0;font-family:-apple-system,BlinkMacSystemFont,'Inter',Arial,sans-serif;background:#f8fafc;color:var(--ink);letter-spacing:-0.01em}
.nav{position:fixed;top:0;width:100%;background:var(--teal);z-index:1000}
.nav-top{padding:10px 14px;display:flex;justify-content:space-between;align-items:center;height:58px}
.logo-circle{background:#fff;width:38px;height:38px;border-radius:50%;display:flex;align-items:center;justify-content:center;overflow:hidden;cursor:pointer}
.logo-circle img{height:34px;width:34px;object-fit:cover;border-radius:50%}
.search-bar-wrap{padding:0 12px 12px;background:var(--teal)}
.search-app-bar{background:#fff;border-radius:12px;padding:0 14px;height:44px;display:flex;align-items:center;gap:10px;box-shadow:0 1px 2px rgba(0,0,0,.05)}
.hamburger{color:var(--teal);font-size:22px;cursor:pointer;font-weight:300}
.search-app-bar input{border:none;outline:none;flex:1;font-size:14px;background:transparent;color:var(--ink)} .search-app-bar input::placeholder{color:#94a3b8}
.cart-icon{position:relative;background:#fff;color:var(--teal);padding:7px 14px;border-radius:20px;font-weight:600;cursor:pointer;font-size:11px;letter-spacing:.04em}
.cart-count{position:absolute;top:-6px;right:-6px;background:#0f172a;color:#fff;border-radius:50%;width:18px;height:18px;display:flex;align-items:center;justify-content:center;font-size:10px}
.page{display:none;padding:118px 12px 80px;min-height:100vh}.page.active{display:block}
.card{background:#fff;border-radius:16px;padding:12px;margin:8px 0;box-shadow:0 1px 3px rgba(15,23,42,.06);position:relative;border:1px solid var(--line)}
.card img{width:100%;height:160px;object-fit:contain;background:#fff;border-radius:12px;padding:6px}
.btn{background:var(--teal);color:#fff;border:none;padding:11px;border-radius:24px;width:100%;font-weight:600;cursor:pointer;font-size:13px;letter-spacing:.01em}
input,select,textarea{width:100%;padding:12px 14px;border-radius:12px;border:1px solid var(--line);margin:5px 0;font-size:13px;outline:none;background:#fff;color:var(--ink)} input:focus,select:focus,textarea:focus{border-color:var(--teal);box-shadow:0 0 0 3px rgba(10,158,187,.12)}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:10px}
.bottom{position:fixed;bottom:0;width:100%;background:#ffffffdd;backdrop-filter:blur(10px);display:flex;justify-content:space-around;padding:8px 0 6px;border-top:1px solid var(--line);z-index:1000}.bottom div{font-size:10px;color:var(--muted);text-align:center;cursor:pointer;flex:1;font-weight:500;letter-spacing:.02em}.bottom div.active{color:var(--teal);font-weight:700}
.chips{display:flex;gap:8px;overflow-x:auto;padding:8px 0}.chip{white-space:nowrap;background:#fff;border:1px solid var(--line);color:var(--muted);padding:7px 14px;border-radius:20px;font-size:12px;cursor:pointer;font-weight:500}.chip.active{background:var(--ink);color:#fff;border-color:var(--ink)}
.qty-controls{display:flex;align-items:center;justify-content:space-between;background:#f8fafc;border-radius:20px;padding:4px 6px;margin-top:8px;border:1px solid var(--line)}
.qty-btn{background:var(--ink);color:#fff;border:none;width:28px;height:28px;border-radius:50%;font-weight:600;cursor:pointer}
.side-menu{position:fixed;top:0;left:-300px;width:300px;height:100%;background:#fff;z-index:2000;transition:.28s cubic-bezier(.2,.8,.2,1);overflow-y:auto;box-shadow:8px 0 30px rgba(15,23,42,.08)}.side-menu.open{left:0}.overlay{display:none;position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(15,23,42,.32);z-index:1999;backdrop-filter:blur(2px)}.overlay.open{display:block}
.modal{display:none;position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(15,23,42,.5);z-index:2000;align-items:center;justify-content:center;padding:12px}.modal.open{display:flex}.modal-box{background:#fff;border-radius:20px;max-width:400px;width:100%;max-height:90vh;overflow-y:auto;box-shadow:0 20px 60px rgba(0,0,0,.2)}
.status-badge{padding:3px 8px;border-radius:10px;font-size:10px;color:#fff;font-weight:600}.status-Pending{background:#f59e0b}.status-PAID{background:#10b981}.status-Packing{background:#0A9EBB}.status-Transit{background:#6366f1}.status-Delivered{background:#0f172a}
.menu-item{display:flex;align-items:center;gap:12px;padding:15px 18px;border-bottom:1px solid #f8fafc;cursor:pointer;color:var(--ink);font-size:14px;font-weight:500;transition:.15s}.menu-item:hover{background:#f8fafc}.menu-item:active{background:#f1f5f9}
.menu-item .mi-icon{width:22px;height:22px;border-radius:6px;background:#f8fafc;display:flex;align-items:center;justify-content:center;font-size:12px;color:var(--muted)}
.menu-item.active{color:var(--teal);background:#f0fbfd}.menu-item.active .mi-icon{background:var(--teal);color:#fff}
.menu-head{padding:22px 18px 18px;background:#fff;border-bottom:1px solid var(--line);display:flex;align-items:center;gap:12px}
.menu-head .brand{font-weight:800;font-size:16px;letter-spacing:-.02em}.menu-head .sub{font-size:12px;color:var(--muted);margin-top:2px}
.menu-section-label{padding:14px 18px 6px;font-size:10px;font-weight:700;letter-spacing:.12em;color:#94a3b8;text-transform:uppercase}
.menu-foot{padding:12px 14px}
.menu-primary{background:var(--ink);color:#fff;border-radius:14px;padding:13px 14px;display:flex;align-items:center;justify-content:space-between;font-weight:600;font-size:13px;cursor:pointer}
</style></head><body>
<div class="nav"><div class="nav-top"><div class="logo-circle" onclick="show('products')"><img src="/logo.png"></div><div class="cart-icon" onclick="show('cart')">CART <span id="cartCount" class="cart-count" style="display:none">0</span></div></div><div class="search-bar-wrap"><div class="search-app-bar"><span class="hamburger" onclick="openSideMenu()">☰</span><input id="searchInput" placeholder="Search products..." oninput="filterProducts()"></div></div></div>
<div class="overlay" id="overlay" onclick="closeSideMenu()"></div>
<div class="side-menu" id="sideMenu">
<div class="menu-head"><div class="logo-circle" style="width:40px;height:40px;border:1px solid var(--line)" onclick="show('products');closeSideMenu()"><img src="/logo.png"></div><div><div class="brand">LONMA ORBIT</div><div class="sub" id="sideUserName">Authentic products</div></div></div>
<div class="menu-section-label">Account</div>
<div class="menu-item" onclick="show('account');closeSideMenu()"><div class="mi-icon">A</div> My Account</div>
<div class="menu-section-label">Shop</div>
<div class="menu-item active" id="m-products" onclick="show('products');closeSideMenu()"><div class="mi-icon">•</div> Products <span style="margin-left:auto;font-size:11px;color:var(--muted)" id="sideCartCount">0</span></div>
<div class="menu-item" onclick="show('cart');closeSideMenu()"><div class="mi-icon">C</div> Cart</div>
<div class="menu-item" onclick="show('wishlist');closeSideMenu()"><div class="mi-icon">W</div> Wishlist</div>
<div class="menu-section-label">Social</div>
<div class="menu-item" onclick="show('friends');closeSideMenu()"><div class="mi-icon">F</div> Friends</div>
<div class="menu-item" onclick="show('loyaltyPage');closeSideMenu()"><div class="mi-icon">L</div> Loyalty</div>
<div class="menu-section-label">Support</div>
<div class="menu-item" onclick="show('orders');closeSideMenu()"><div class="mi-icon">O</div> Orders</div>
<div class="menu-item" onclick="show('scan');closeSideMenu()"><div class="mi-icon">V</div> Verify Product</div>
<div class="menu-item" onclick="show('settings');closeSideMenu()"><div class="mi-icon">S</div> Settings</div>
<div class="menu-foot"><div class="menu-primary" onclick="show('admin');closeSideMenu()"><span>Admin</span><span style="opacity:.6">→</span></div></div>
</div>
<div id="products" class="page active"><div class="grid" id="plist"></div></div>
<div id="account" class="page"><h3 style="font-weight:800;letter-spacing:-.02em">Account</h3>
<div id="accountLoggedOut">
<div class="card"><h4 style="margin:6px 0">Create account</h4><input id="regName" placeholder="Full name"><input id="regPhone" placeholder="07xxxxxxxx"><input id="regPass" type="password" placeholder="Password"><button class="btn" onclick="registerUser()">Create account</button><p id="regStatus" style="font-size:12px;color:var(--muted)"></p></div>
<div class="card"><h4 style="margin:6px 0">Sign in</h4><input id="loginPhone" placeholder="07xxxxxxxx"><input id="loginPass" type="password" placeholder="Password"><button class="btn" style="background:var(--ink)" onclick="loginUser()">Sign in</button><p id="loginStatus" style="font-size:12px;color:var(--muted)"></p></div>
</div>
<div id="accountLoggedIn" style="display:none"><div class="card" style="background:var(--ink);color:#fff"><h2 id="accName" style="margin:6px 0">Welcome</h2><p id="accPhone" style="opacity:.8;margin:0"></p><button class="btn" style="background:#fff;color:var(--ink);margin-top:14px" onclick="logoutUser()">Sign out</button></div></div>
</div>
<div id="friends" class="page"><h3 style="font-weight:800">Friends</h3><div class="card"><div style="display:flex;gap:8px"><input id="myReferralCode" readonly><button class="btn" style="width:auto" onclick="copyReferral()">Copy</button></div><div style="display:flex;gap:8px;margin-top:8px"><button class="btn" style="background:var(--ink)" onclick="shareReferralWhatsApp()">Share referral</button><button class="btn" style="background:#fff;color:var(--ink);border:1px solid var(--line)" onclick="shareCart()">Share cart</button></div><p id="shareLinkResult" style="word-break:break-all;font-size:12px"></p></div><div class="card"><input id="friendName" placeholder="Friend name"><input id="friendPhone" placeholder="Friend phone"><button class="btn" onclick="inviteFriend()">Invite</button><p id="friendStatus" style="font-size:12px"></p></div><div class="card"><div style="display:flex;gap:8px"><input id="joinShareCode" placeholder="Enter code"><button class="btn" style="width:auto" onclick="joinSharedCart()">Join</button></div></div><div class="card"><div id="friendsList"></div></div></div>
<div id="wishlist" class="page"><h3 style="font-weight:800">Wishlist</h3><div id="wishlistItems"></div></div>
<div id="loyaltyPage" class="page"><h3 style="font-weight:800">Loyalty</h3><div class="card" style="text-align:center"><h1 id="loyaltyPoints" style="font-size:42px;margin:8px 0">0</h1><p style="color:var(--muted)">Points • Spent KSh <span id="loyaltySpent">0</span></p><div style="display:flex;gap:8px;margin-top:10px"><input id="redeemPointsInput" placeholder="Points" type="number"><button class="btn" style="width:auto" onclick="redeemPoints()">Redeem</button></div><p id="loyaltyMsg" style="font-size:12px"></p></div></div>
<div id="cart" class="page"><h3 style="font-weight:800">Cart</h3><div id="cartItems"></div><div class="card" id="cartSummary" style="display:none"><div style="font-size:13px;line-height:2.2"><div style="display:flex;justify-content:space-between"><span>Subtotal (<span id="totalItems">0</span>)</span><span>KSh <span id="subTotal">0</span></span></div><div style="display:flex;justify-content:space-between;color:var(--muted)"><span>Delivery</span><span id="deliveryFee"></span></div><div style="display:flex;justify-content:space-between;color:var(--muted)"><span>Discount</span><span id="referralDiscount">0</span></div><div style="display:flex;justify-content:space-between;border-top:1px solid var(--line);font-weight:700;font-size:16px"><span>Total</span><span>KSh <span id="totalPrice">0</span></span></div></div><div style="background:#f8fafc;border:1px solid var(--line);padding:12px;border-radius:12px;margin-top:12px"><input id="custName" placeholder="Full name"><input id="phone" placeholder="07xxxxxxxx"><select id="locationArea"><option value="">Select area</option><option value="CBD">CBD - 150</option><option value="Westlands">Westlands - 200</option><option value="Eastlands">Eastlands - 200</option><option value="Upcountry">Upcountry - 350</option></select><textarea id="exactLocation" placeholder="Estate, house"></textarea><div style="display:flex;gap:8px"><input id="promoCode" placeholder="Referral code"><button class="btn" style="width:auto" onclick="applyReferralCode()">Apply</button></div><label style="font-size:12px;display:flex;gap:8px;align-items:center;margin-top:8px;color:var(--muted)"><input type="checkbox" id="agreeTerms" style="width:auto"> I agree to terms</label></div><div style="margin-top:12px"><button class="btn" style="background:var(--ink)" onclick="checkout()">Pay KSh <span id="payTotal">0</span> • M-Pesa</button><p id="paystatus" style="font-size:12px;color:var(--muted);margin-top:8px"></p></div></div><div class="card" id="emptyCart" style="text-align:center;padding:28px"><p style="color:var(--muted)">Cart empty</p><button class="btn" style="background:var(--ink)" onclick="show('products')">Shop products</button></div></div>
<div id="orders" class="page"><h3 style="font-weight:800">Orders</h3><div style="display:flex;gap:8px;margin-bottom:10px"><input id="orderPhoneLookup" placeholder="Phone"><button class="btn" style="width:auto" onclick="loadMyOrdersByPhone()">Load</button></div><div id="ordersList"></div><div class="card" id="noOrders" style="text-align:center;padding:28px"><p style="color:var(--muted)">No orders</p></div></div>
<div id="scan" class="page"><h3 style="font-weight:800">Verify</h3><div class="card"><input id="manualcode" placeholder="LONMA-001"><button class="btn" onclick="verifyCode()">Verify</button><p id="scanresult" style="font-weight:600;margin-top:10px"></p></div></div>
<div id="settings" class="page"><h3 style="font-weight:800">Settings</h3><div class="card"><button class="btn" style="background:#fff;color:#ef4444;border:1px solid #fee2e2" onclick="clearAllData()">Clear data</button></div></div>
<div id="admin" class="page"><h3 style="font-weight:800">Admin</h3><div class="card"><input id="adminPass" type="password" placeholder="Password"><button class="btn" onclick="adminLogin()">Login</button><p id="adminStatus"></p></div><div id="adminContent" style="display:none"><div class="card"><div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;text-align:center"><div style="background:#f8fafc;padding:12px;border-radius:12px"><b id="statOrders">0</b><br><small>Orders</small></div><div style="background:#f8fafc;padding:12px;border-radius:12px"><b id="statSales">0</b><br><small>Sales</small></div></div></div><div id="lowStockAlert" class="card"></div><div id="adminOrdersList"></div></div></div>
<div id="receipt" class="page"><h3 style="font-weight:800">Receipt</h3><div class="card" id="receiptContent"></div><button class="btn" onclick="show('products')">Continue</button></div>
<div class="bottom"><div id="b-products" class="active" onclick="show('products')">Products</div><div id="b-cart" onclick="show('cart')">Cart</div><div id="b-wishlist" onclick="show('wishlist')">Wishlist</div><div id="b-orders" onclick="show('orders')">Orders</div><div id="b-account" onclick="show('account')">Account</div></div>
<div id="productModal" class="modal" onclick="if(event.target===this)closeModal()"><div class="modal-box"><div id="modalContent"></div></div></div>
<script>
let allProducts=[],currentCat='All',searchQuery='',cart=[],myOrders=JSON.parse(localStorage.getItem('my_orders')||'[]'),referralDiscountValue=0;
try{let s=localStorage.getItem('lonma_cart'); if(s){cart=JSON.parse(s);} if(!Array.isArray(cart))cart=[];}catch(e){cart=[];}
function saveCart(){localStorage.setItem('lonma_cart',JSON.stringify(cart));updateCartCount();}
function updateCartCount(){let c=0;for(let i of cart)c+=Number(i.qty)||0;document.getElementById('cartCount').innerText=c;document.getElementById('sideCartCount').innerText=c;document.getElementById('cartCount').style.display=c>0?'flex':'none';}
function openSideMenu(){document.getElementById('sideMenu').classList.add('open');document.getElementById('overlay').classList.add('open');}
function closeSideMenu(){document.getElementById('sideMenu').classList.remove('open');document.getElementById('overlay').classList.remove('open');}
function filterCat(cat,el){currentCat=cat;document.querySelectorAll('.chip').forEach(ch=>ch.classList.remove('active'));if(el)el.classList.add('active');renderProducts();}
function filterProducts(){searchQuery=document.getElementById('searchInput').value.toLowerCase();renderProducts();}
function calcBulk(price,qty){if(qty>=3&&price==90)return 80;if(qty>=2&&price>=250)return Math.floor(price*0.9);return price;}
function renderProducts(){let list=allProducts.filter(p=>{let mCat=currentCat==='All'||p.category===currentCat;let mSearch=!searchQuery||p.name.toLowerCase().includes(searchQuery);return mCat&&mSearch;});let html='';for(let p of list){let inCart=cart.find(c=>c.id===p.id);let qtyText=inCart?`• ${inCart.qty} in cart`:'';html+=`<div class="card"><div style="position:absolute;top:10px;left:10px;font-size:10px;font-weight:700;color:var(--muted)">${p.stock<=5?(p.stock==0?'OUT':'LOW') : ''}</div><img src="${p.image}" onclick="openModal(${p.id})"><div style="font-size:13px;font-weight:600;margin:8px 0 2px;letter-spacing:-.01em">${p.name}</div><div style="font-size:11px;color:var(--muted)">${p.rating? '★ '+p.rating : ''} ${qtyText}</div><div style="display:flex;justify-content:space-between;align-items:center;margin-top:8px"><div style="font-weight:800">KSh ${p.price}</div><button class="btn" style="width:auto;padding:7px 14px;font-size:12px" onclick="addToCart(${p.id})">Add</button></div></div>`;}document.getElementById('plist').innerHTML='<div style="display:flex;gap:8px;overflow-x:auto;padding:8px 0" class="chips"><span class="chip active" onclick="filterCat(\'All\',this)">All</span><span class="chip" onclick="filterCat(\'Cooking Oils\',this)">Oils</span><span class="chip" onclick="filterCat(\'Soaps\',this)">Soaps</span><span class="chip" onclick="filterCat(\'Lotions\',this)">Lotions</span><span class="chip" onclick="filterCat(\'Pomades\',this)">Pomades</span></div><div class="grid">'+html+'</div>';}
async function openModal(id){let p=allProducts.find(x=>x.id===id);if(!p)return;let r=await fetch(`/api/reviews/${id}`);let reviews=await r.json();document.getElementById('modalContent').innerHTML=`<img src="${p.image}" style="width:100%;height:240px;object-fit:contain;padding:14px"><div style="padding:14px"><div style="font-weight:800;font-size:16px">${p.name}</div><div style="font-weight:800;margin:8px 0">KSh ${p.price}</div><div style="font-size:13px;color:var(--muted)">${p.desc}</div><button class="btn" style="margin-top:12px" onclick="addToCart(${p.id});closeModal()">Add to cart</button></div>`;document.getElementById('productModal').classList.add('open');}
function closeModal(){document.getElementById('productModal').classList.remove('open');}
function addToCart(id){let p=allProducts.find(x=>x.id===id);if(!p||p.stock===0)return;let f=cart.find(c=>c.id===id);if(f)f.qty++;else cart.push({id:p.id,name:p.name,price:p.price,image:p.image,code:p.code,qty:1});saveCart();renderProducts();}
function clearCart(){cart=[];localStorage.removeItem('lonma_cart');saveCart();renderCart();renderProducts();}
function renderCart(){let cont=document.getElementById('cartItems'),sum=document.getElementById('cartSummary'),empty=document.getElementById('emptyCart');if(cart.length===0){cont.innerHTML='';sum.style.display='none';empty.style.display='block';return;}empty.style.display='none';sum.style.display='block';let totalItems=0,subTotal=0,html='';for(let it of cart){let unit=calcBulk(it.price,it.qty);subTotal+=unit*it.qty;totalItems+=it.qty;html+=`<div class="card" style="display:flex;gap:10px"><img src="${it.image}" style="width:56px;height:56px"><div style="flex:1"><div style="font-size:13px;font-weight:600">${it.name}</div><div style="font-size:12px;color:var(--muted)">KSh ${unit} x ${it.qty}</div></div></div>`;}cont.innerHTML=html;let area=document.getElementById('locationArea').value;let delivery=area==='CBD'?150:area==='Upcountry'?350:200;if(subTotal>=2000)delivery=0;let total=subTotal+delivery-referralDiscountValue;document.getElementById('subTotal').innerText=subTotal;document.getElementById('totalItems').innerText=totalItems;document.getElementById('deliveryFee').innerText=delivery===0?'FREE':'KSh '+delivery;document.getElementById('referralDiscount').innerText='KSh '+referralDiscountValue;document.getElementById('totalPrice').innerText=total<0?0:total;document.getElementById('payTotal').innerText=total<0?0:total;}
function show(id){document.querySelectorAll('.page').forEach(p=>p.classList.remove('active'));document.getElementById(id).classList.add('active');document.querySelectorAll('.bottom div').forEach(b=>b.classList.remove('active'));let btn=document.getElementById('b-'+id);if(btn)btn.classList.add('active');document.querySelectorAll('.menu-item').forEach(m=>m.classList.remove('active'));let mi=document.getElementById('m-'+id);if(mi)mi.classList.add('active');if(id==='cart')renderCart();if(id==='orders')renderOrders();if(id==='wishlist')loadWishlist();if(id==='loyaltyPage')loadLoyalty();if(id==='friends')loadFriends();if(id==='account')checkAccountUI();closeSideMenu();window.scrollTo(0,0);}
async function loadProducts(){let r=await fetch('/api/products');allProducts=await r.json();renderProducts();}
async function verifyCode(){let c=document.getElementById('manualcode').value.trim().toUpperCase();let r=await fetch(`/api/verify/${c}`);let d=await r.json();document.getElementById('scanresult').innerText=d.valid?`Valid: ${d.product.name}`:'Invalid code';}
async function checkout(){let name=document.getElementById('custName').value.trim(),phone=document.getElementById('phone').value.trim(),area=document.getElementById('locationArea').value,loc=document.getElementById('exactLocation').value.trim(),agree=document.getElementById('agreeTerms').checked;if(!name||!phone||!area||!loc||!agree){document.getElementById('paystatus').innerText='Fill all fields';return;}let sub=0;for(let i of cart)sub+=calcBulk(i.price,i.qty)*i.qty;let del=area==='CBD'?150:area==='Upcountry'?350:200;if(sub>=2000)del=0;let tot=sub+del-referralDiscountValue;document.getElementById('paystatus').innerText='Sending STK...';let r=await fetch('/mpesa/stkpush',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({phone,amount:tot,cart,name,area,location:loc,subtotal:sub,delivery:del})});let d=await r.json();document.getElementById('paystatus').innerText=d.message;if(d.status==='ok'){myOrders.unshift({order_no:d.order_no,total:tot,status:'Pending',created:new Date().toLocaleString()});localStorage.setItem('my_orders',JSON.stringify(myOrders));document.getElementById('receiptContent').innerHTML=`<h3>${d.order_no}</h3><p>${name} - ${phone}</p><p>KSh ${tot}</p>`;cart=[];localStorage.removeItem('lonma_cart');saveCart();referralDiscountValue=0;setTimeout(()=>show('receipt'),800);}}
async function loadMyOrdersByPhone(){let phone=document.getElementById('orderPhoneLookup').value.trim();let r=await fetch(`/api/orders?phone=${phone}`);let data=await r.json();let cont=document.getElementById('ordersList');cont.innerHTML=data.map(o=>`<div class="card"><b>${o.order_no}</b> <span class="status-badge status-${o.status}">${o.status}</span><div style="font-size:13px;margin-top:6px">KSh ${o.total} • ${o.created}</div></div>`).join('');}
function renderOrders(){let cont=document.getElementById('ordersList');if(myOrders.length===0){document.getElementById('noOrders').style.display='block';cont.innerHTML='';return;}document.getElementById('noOrders').style.display='none';cont.innerHTML=myOrders.map(o=>`<div class="card"><b>${o.order_no}</b> <span class="status-badge status-${o.status}">${o.status}</span><div style="font-size:13px;margin-top:6px">KSh ${o.total} • ${o.created}</div></div>`).join('');}
async function adminLogin(){let p=document.getElementById('adminPass').value;if(p!=='lonma2024'){document.getElementById('adminStatus').innerText='Wrong';return;}document.getElementById('adminContent').style.display='block';loadAdminOrders();}
async function loadAdminOrders(){let r=await fetch('/api/admin/orders');let d=await r.json();let a=await fetch('/api/admin/analytics');let an=await a.json();document.getElementById('statOrders').innerText=an.orders;document.getElementById('statSales').innerText=an.sales;document.getElementById('adminOrdersList').innerHTML=d.map(o=>`<div class="card"><b>${o.order_no}</b> ${o.status}<div>${o.name} - ${o.phone} - KSh ${o.total}</div></div>`).join('');}
async function loadFriends(){let phone=document.getElementById('phone').value||localStorage.getItem('user_phone')||JSON.parse(localStorage.getItem('lonma_user')||'{}').phone||'';if(!phone)return;let r=await fetch(`/api/friends?phone=${phone}`);let data=await r.json();document.getElementById('myReferralCode').value=data.referral_code;document.getElementById('friendsList').innerHTML=data.friends.map(f=>`<div style="padding:8px 0;border-bottom:1px solid var(--line);display:flex;justify-content:space-between"><span>${f.name} • ${f.phone}</span><span style="font-size:11px;color:var(--muted)">${f.status}</span></div>`).join('');}
async function inviteFriend(){let userPhone=document.getElementById('phone').value||localStorage.getItem('user_phone')||JSON.parse(localStorage.getItem('lonma_user')||'{}').phone;let fp=document.getElementById('friendPhone').value.trim();let fn=document.getElementById('friendName').value.trim();let r=await fetch('/api/friends/invite',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({user_phone:userPhone,friend_phone:fp,friend_name:fn})});let d=await r.json();document.getElementById('friendStatus').innerText=d.message;loadFriends();}
async function applyReferralCode(){let code=document.getElementById('promoCode').value.trim().toUpperCase();let r=await fetch('/api/referral/apply',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({code})});let d=await r.json();if(d.status==='ok'){referralDiscountValue=d.discount;renderCart();}}
async function shareCart(){let phone=document.getElementById('phone').value||'guest';if(cart.length===0)return;let r=await fetch('/api/share-cart',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({phone,cart})});let d=await r.json();document.getElementById('shareLinkResult').innerText=d.share_url;}
async function joinSharedCart(){let code=document.getElementById('joinShareCode').value.trim().toUpperCase();let r=await fetch(`/api/share-cart/${code}`);let d=await r.json();if(d.status==='ok'){cart=d.items;saveCart();show('cart');}}
function copyReferral(){let el=document.getElementById('myReferralCode');el.select();document.execCommand('copy');}
function shareReferralWhatsApp(){let code=document.getElementById('myReferralCode').value;window.open(`https://wa.me/?text=${encodeURIComponent('LONMA code '+code+' https://app.lonmaorbit.co.ke')}`,'_blank');}
async function loadWishlist(){let phone=document.getElementById('phone').value||localStorage.getItem('user_phone')||JSON.parse(localStorage.getItem('lonma_user')||'{}').phone||'';if(!phone)return;let r=await fetch(`/api/wishlist?phone=${phone}`);let data=await r.json();document.getElementById('wishlistItems').innerHTML=data.map(it=>`<div class="card" style="display:flex;gap:10px"><img src="${it.image}" style="width:60px;height:60px"><div><div style="font-weight:600">${it.name}</div><div>KSh ${it.price}</div></div></div>`).join('');}
async function loadLoyalty(){let phone=document.getElementById('phone').value||localStorage.getItem('user_phone')||JSON.parse(localStorage.getItem('lonma_user')||'{}').phone||'';if(!phone)return;let r=await fetch(`/api/loyalty/${phone}`);let d=await r.json();document.getElementById('loyaltyPoints').innerText=d.points;}
function clearAllData(){localStorage.clear();cart=[];myOrders=[];updateCartCount();show('products');}
async function registerUser(){let name=document.getElementById('regName').value.trim(), phone=document.getElementById('regPhone').value.trim(), pass=document.getElementById('regPass').value.trim();let r=await fetch('/api/auth/register',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name,phone,password:pass})});let d=await r.json();document.getElementById('regStatus').innerText=d.message;if(d.status==='ok'){localStorage.setItem('lonma_user',JSON.stringify(d.user));localStorage.setItem('user_phone',phone);checkAccountUI();show('products');}}
async function loginUser(){let phone=document.getElementById('loginPhone').value.trim(), pass=document.getElementById('loginPass').value.trim();let r=await fetch('/api/auth/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({phone,password:pass})});let d=await r.json();document.getElementById('loginStatus').innerText=d.message;if(d.status==='ok'){localStorage.setItem('lonma_user',JSON.stringify(d.user));localStorage.setItem('user_phone',phone);checkAccountUI();show('products');}}
function logoutUser(){localStorage.removeItem('lonma_user');checkAccountUI();show('account');}
function checkAccountUI(){let u=JSON.parse(localStorage.getItem('lonma_user')||'null');if(u){document.getElementById('accountLoggedOut').style.display='none';document.getElementById('accountLoggedIn').style.display='block';document.getElementById('accName').innerText=u.name;document.getElementById('accPhone').innerText=u.phone;document.getElementById('sideUserName').innerText=u.name;}else{document.getElementById('accountLoggedOut').style.display='block';document.getElementById('accountLoggedIn').style.display='none';document.getElementById('sideUserName').innerText='Authentic products';}}
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
