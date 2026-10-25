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
conn.execute("CREATE TABLE IF NOT EXISTS orders (id INTEGER PRIMARY KEY AUTOINCREMENT, order_no TEXT, name TEXT, phone TEXT, area TEXT, location TEXT, items TEXT, subtotal INTEGER, delivery INTEGER, total INTEGER, status TEXT, created TEXT, mpesa_receipt TEXT, checkout_id TEXT, points_earned INTEGER)")
conn.execute("CREATE TABLE IF NOT EXISTS friends (id INTEGER PRIMARY KEY AUTOINCREMENT, user_phone TEXT, friend_phone TEXT, friend_name TEXT, status TEXT, created TEXT)")
conn.execute("CREATE TABLE IF NOT EXISTS referrals (id INTEGER PRIMARY KEY AUTOINCREMENT, code TEXT UNIQUE, owner_phone TEXT, discount INTEGER, created TEXT)")
conn.execute("CREATE TABLE IF NOT EXISTS shared_carts (id INTEGER PRIMARY KEY AUTOINCREMENT, share_code TEXT UNIQUE, owner_phone TEXT, items TEXT, created TEXT)")
conn.execute("CREATE TABLE IF NOT EXISTS wishlist (id INTEGER PRIMARY KEY AUTOINCREMENT, phone TEXT, product_id INTEGER, created TEXT)")
conn.execute("CREATE TABLE IF NOT EXISTS reviews (id INTEGER PRIMARY KEY AUTOINCREMENT, product_id INTEGER, phone TEXT, name TEXT, rating INTEGER, comment TEXT, created TEXT)")
conn.execute("CREATE TABLE IF NOT EXISTS loyalty (phone TEXT PRIMARY KEY, points INTEGER, total_spent INTEGER)")
conn.execute("CREATE TABLE IF NOT EXISTS abandoned (id INTEGER PRIMARY KEY AUTOINCREMENT, phone TEXT, items TEXT, created TEXT, sent INTEGER DEFAULT 0)")
cur = conn.cursor()
cur.execute("DELETE FROM products")
PRODUCTS = [
    (1, "LONMA Cooking Oil 2L", 850, "LONMA-001", "Cooking Oils", 50, "LONMA pure fortified cooking oil 2L - 100% Original"),
    (2, "LONMA Citronella Soap 110g", 90, "LONMA-002", "Soaps", 120, "LONMA anti-bacterial citronella soap 110g"),
    (3, "LONMA Men Lotion 72Hrs", 299, "LONMA-003", "Lotions", 8, "LONMA 72Hrs hydration for men"),
    (4, "LONMA Pine Soap 110g", 90, "LONMA-004", "Soaps", 100, "LONMA pine drops fresh soap 110g"),
    (5, "LONMA Cooking Oil 5L", 1250, "LONMA-005", "Cooking Oils", 25, "LONMA vegetable oil 5L family pack - Pure"),
    (6, "LONMA Cool Mint Soap 110g", 90, "LONMA-006", "Soaps", 3, "LONMA cool mint fresh soap 110g"),
    (7, "LONMA Anti-Dandruff Pomade 250ml", 250, "LONMA-007", "Pomades", 40, "LONMA anti-dandruff pomade 250ml"),
    (8, "LONMA Anti-Breakage Pomade", 250, "LONMA-008", "Pomades", 45, "LONMA anti-breakage pomade"),
    (9, "LONMA Cocoa Butter Lotion", 299, "LONMA-009", "Lotions", 30, "LONMA cocoa butter lotion - Smooth skin"),
]
for pid, name, price, code, cat, stock, desc in PRODUCTS:
    os.makedirs("static", exist_ok=True)
    img = f"/static/{code}.jpg"
    if not os.path.exists(f"static/{code}.jpg"):
        img = f"https://via.placeholder.com/400x400/FFFFFF/0A9EBB?text={urllib.parse.quote(name)}"
    cur.execute("INSERT INTO products VALUES (?,?,?,?,?,?,?,?)", (pid, name, price, code, img, cat, stock, desc))
conn.commit()

def gen_code(n=6): return ''.join(random.choices(string.ascii_uppercase + string.digits, k=n))
def get_daraja_token():
    try:
        base = "https://api.safaricom.co.ke" if USE_PRODUCTION else "https://sandbox.safaricom.co.ke"
        r = requests.get(f"{base}/oauth/v1/generate?grant_type=client_credentials", auth=(DARAJA_CONSUMER_KEY, DARAJA_CONSUMER_SECRET), timeout=10)
        return r.json().get("access_token")
    except: return None
def bulk_price(price, qty):
    if qty >=3 and price==90: return 80
    if qty >=2 and price>=250: return int(price*0.9)
    return price

@app.api_route("/mpesa/callback", methods=["GET", "POST"])
@app.api_route("/callback", methods=["GET", "POST"])
async def mpesa_callback(request: Request):
    try:
        data = await request.json()
        stk = data.get("Body", {}).get("stkCallback", {})
        result_code = stk.get("ResultCode")
        checkout_id = stk.get("CheckoutRequestID", "")
        if result_code == 0:
            receipt = ""
            for it in stk.get("CallbackMetadata", {}).get("Item", []):
                if it.get("Name") == "MpesaReceiptNumber": receipt = it.get("Value")
            cur = conn.cursor()
            cur.execute("UPDATE orders SET status='PAID', mpesa_receipt=? WHERE checkout_id=?", (receipt, checkout_id))
            if cur.rowcount==0:
                cur.execute("UPDATE orders SET status='PAID', mpesa_receipt=? WHERE status='Pending' ORDER BY id DESC LIMIT 1", (receipt,))
            conn.commit()
            cur.execute("SELECT phone,total FROM orders WHERE mpesa_receipt=? ORDER BY id DESC LIMIT 1",(receipt,))
            row=cur.fetchone()
            if row:
                phone, total = row
                points = total//100
                cur.execute("INSERT OR IGNORE INTO loyalty (phone,points,total_spent) VALUES (?,?,?)",(phone,0,0))
                cur.execute("UPDATE loyalty SET points=points+?, total_spent=total_spent+? WHERE phone=?",(points,total,phone))
                conn.commit()
        else:
            cur = conn.cursor()
            cur.execute("UPDATE orders SET status='FAILED' WHERE checkout_id=?", (checkout_id,))
            conn.commit()
        return {"ResultCode":0,"ResultDesc":"Accepted"}
    except: return {"ResultCode":0,"ResultDesc":"Accepted"}

@app.get("/favicon.ico")
def favicon():
    for f in ["logo.png","static/logo.png"]:
        if os.path.exists(f): return FileResponse(f)
    return HTMLResponse("",200)

@app.get("/api/products")
def products():
    cur = conn.cursor()
    cur.execute("SELECT id,name,price,code,image,category,stock,desc FROM products")
    prods=[]
    for r in cur.fetchall():
        cur.execute("SELECT AVG(rating), COUNT(*) FROM reviews WHERE product_id=?",(r[0],))
        avg,cnt=cur.fetchone()
        avg = round(avg,1) if avg else 0
        prods.append({"id":r[0],"name":r[1],"price":r[2],"code":r[3],"image":r[4],"category":r[5],"stock":r[6],"desc":r[7],"rating":avg,"reviews":cnt})
    return prods

@app.get("/api/verify/{code}")
def verify(code: str):
    cur = conn.cursor()
    cur.execute("SELECT name FROM products WHERE code=?",(code.strip().upper(),))
    row=cur.fetchone()
    return {"valid":True,"product":{"name":row[0]}} if row else {"valid":False}

@app.get("/api/orders")
def get_orders_by_phone(phone: str=""):
    cur = conn.cursor()
    if phone:
        cur.execute("SELECT order_no,name,phone,area,location,items,subtotal,delivery,total,status,created FROM orders WHERE phone=? ORDER BY id DESC",(phone,))
    else:
        cur.execute("SELECT order_no,name,phone,area,location,items,subtotal,delivery,total,status,created FROM orders ORDER BY id DESC LIMIT 50")
    return [{"order_no":r[0],"name":r[1],"phone":r[2],"area":r[3],"location":r[4],"items":r[5],"subtotal":r[6],"delivery":r[7],"total":r[8],"status":r[9],"created":r[10]} for r in cur.fetchall()]

@app.get("/api/admin/orders")
def admin_orders():
    cur = conn.cursor()
    cur.execute("SELECT order_no,name,phone,area,location,items,subtotal,delivery,total,status,created,mpesa_receipt,checkout_id,points_earned FROM orders ORDER BY id DESC")
    return [{"order_no":r[0],"name":r[1],"phone":r[2],"area":r[3],"location":r[4],"items":r[5],"subtotal":r[6],"delivery":r[7],"total":r[8],"status":r[9],"created":r[10],"mpesa_receipt":r[11],"checkout_id":r[12],"points_earned":r[13]} for r in cur.fetchall()]

@app.get("/api/admin/analytics")
def analytics():
    cur=conn.cursor()
    cur.execute("SELECT COUNT(*), SUM(total) FROM orders WHERE status!='FAILED'")
    cnt, sales = cur.fetchone()
    cur.execute("SELECT SUM(stock) FROM products")
    stock = cur.fetchone()[0]
    cur.execute("SELECT name,stock FROM products WHERE stock<5 ORDER BY stock ASC")
    low = [{"name":r[0],"stock":r[1]} for r in cur.fetchall()]
    cur.execute("SELECT phone,points,total_spent FROM loyalty ORDER BY points DESC LIMIT 10")
    top = [{"phone":r[0],"points":r[1],"spent":r[2]} for r in cur.fetchall()]
    return {"orders":cnt or 0,"sales":sales or 0,"stock":stock or 0,"low_stock":low,"top_customers":top}

@app.post("/api/admin/orders/{order_no}/{status}")
def admin_update(order_no: str, status: str):
    cur = conn.cursor()
    cur.execute("UPDATE orders SET status=? WHERE order_no=?",(status,order_no))
    conn.commit()
    return {"message":f"Order {order_no} marked {status}"}

@app.get("/api/friends")
def list_friends(phone: str):
    cur = conn.cursor()
    cur.execute("SELECT friend_phone, friend_name, status, created FROM friends WHERE user_phone=? ORDER BY id DESC",(phone,))
    friends=[{"phone":r[0],"name":r[1],"status":r[2],"created":r[3]} for r in cur.fetchall()]
    cur.execute("SELECT code, discount FROM referrals WHERE owner_phone=?",(phone,))
    row=cur.fetchone()
    if not row:
        code=f"LONMA-{gen_code(4)}"
        cur.execute("INSERT INTO referrals (code, owner_phone, discount, created) VALUES (?,?,?,?)",(code,phone,100,datetime.datetime.now().strftime("%Y-%m-%d")))
        conn.commit()
        referral_code=code
    else: referral_code=row[0]
    return {"friends":friends,"referral_code":referral_code,"referral_discount":100}

@app.post("/api/friends/invite")
async def invite_friend(req: Request):
    d=await req.json()
    user_phone=d.get("user_phone","").strip()
    friend_phone=d.get("friend_phone","").strip()
    friend_name=d.get("friend_name","Friend").strip()
    if not user_phone or not friend_phone: return {"status":"error","message":"Phone required"}
    cur=conn.cursor()
    cur.execute("SELECT id FROM friends WHERE user_phone=? AND friend_phone=?",(user_phone,friend_phone))
    if cur.fetchone(): return {"status":"error","message":"Already invited"}
    cur.execute("INSERT INTO friends (user_phone, friend_phone, friend_name, status, created) VALUES (?,?,?,?,?)",(user_phone,friend_phone,friend_name,"invited",datetime.datetime.now().strftime("%Y-%m-%d %H:%M")))
    conn.commit()
    return {"status":"ok","message":f"Invite sent to {friend_name}"}

@app.post("/api/referral/apply")
async def apply_referral(req: Request):
    d=await req.json()
    code=d.get("code","").strip().upper()
    user_phone=d.get("user_phone","")
    cur=conn.cursor()
    cur.execute("SELECT owner_phone, discount FROM referrals WHERE code=?",(code,))
    row=cur.fetchone()
    if not row: return {"status":"error","message":"Invalid code"}
    if row[0]==user_phone: return {"status":"error","message":"Cannot use own code"}
    return {"status":"ok","message":f"KSh {row[1]} OFF applied","discount":row[1]}

@app.post("/api/share-cart")
async def share_cart_api(req: Request):
    d=await req.json()
    owner=d.get("phone","guest")
    items=json.dumps(d.get("cart",[]))
    share_code=gen_code(8)
    cur=conn.cursor()
    cur.execute("INSERT INTO shared_carts (share_code, owner_phone, items, created) VALUES (?,?,?,?)",(share_code,owner,items,datetime.datetime.now().strftime("%Y-%m-%d %H:%M")))
    conn.commit()
    return {"status":"ok","share_code":share_code,"share_url":f"https://app.lonmaorbit.co.ke/?share={share_code}"}

@app.get("/api/share-cart/{code}")
def get_shared_cart(code: str):
    cur=conn.cursor()
    cur.execute("SELECT items, owner_phone FROM shared_carts WHERE share_code=?",(code.upper(),))
    row=cur.fetchone()
    if not row: return {"status":"error","message":"Invalid code"}
    return {"status":"ok","items":json.loads(row[0]),"owner":row[1]}

@app.get("/api/wishlist")
def get_wishlist(phone: str):
    cur=conn.cursor()
    cur.execute("SELECT p.id,p.name,p.price,p.image FROM wishlist w JOIN products p ON w.product_id=p.id WHERE w.phone=?",(phone,))
    return [{"id":r[0],"name":r[1],"price":r[2],"image":r[3]} for r in cur.fetchall()]

@app.post("/api/wishlist/toggle")
async def toggle_wishlist(req: Request):
    d=await req.json()
    phone=d.get("phone")
    pid=d.get("product_id")
    cur=conn.cursor()
    cur.execute("SELECT id FROM wishlist WHERE phone=? AND product_id=?",(phone,pid))
    if cur.fetchone():
        cur.execute("DELETE FROM wishlist WHERE phone=? AND product_id=?",(phone,pid))
        conn.commit()
        return {"status":"removed"}
    cur.execute("INSERT INTO wishlist (phone,product_id,created) VALUES (?,?,?)",(phone,pid,datetime.datetime.now().strftime("%Y-%m-%d")))
    conn.commit()
    return {"status":"added"}

@app.get("/api/reviews/{pid}")
def get_reviews(pid: int):
    cur=conn.cursor()
    cur.execute("SELECT name,rating,comment,created FROM reviews WHERE product_id=? ORDER BY id DESC LIMIT 20",(pid,))
    return [{"name":r[0],"rating":r[1],"comment":r[2],"created":r[3]} for r in cur.fetchall()]

@app.post("/api/reviews")
async def add_review(req: Request):
    d=await req.json()
    cur=conn.cursor()
    cur.execute("INSERT INTO reviews (product_id,phone,name,rating,comment,created) VALUES (?,?,?,?,?,?)",(d.get("product_id"),d.get("phone"),d.get("name","Customer"),d.get("rating",5),d.get("comment",""),datetime.datetime.now().strftime("%Y-%m-%d %H:%M")))
    conn.commit()
    return {"status":"ok"}

@app.get("/api/loyalty/{phone}")
def get_loyalty(phone: str):
    cur=conn.cursor()
    cur.execute("SELECT points,total_spent FROM loyalty WHERE phone=?",(phone,))
    row=cur.fetchone()
    if not row: return {"points":0,"total_spent":0}
    return {"points":row[0],"total_spent":row[1]}

@app.post("/api/loyalty/redeem")
async def redeem_loyalty(req: Request):
    d=await req.json()
    phone=d.get("phone")
    points=int(d.get("points",0))
    cur=conn.cursor()
    cur.execute("SELECT points FROM loyalty WHERE phone=?",(phone,))
    row=cur.fetchone()
    if not row or row[0]<points: return {"status":"error","message":"Not enough points"}
    discount=points*10
    cur.execute("UPDATE loyalty SET points=points-? WHERE phone=?",(points,phone))
    conn.commit()
    return {"status":"ok","discount":discount,"message":f"KSh {discount} redeemed"}

@app.post("/api/abandoned")
async def save_abandoned(req: Request):
    d=await req.json()
    cur=conn.cursor()
    cur.execute("INSERT INTO abandoned (phone,items,created) VALUES (?,?,?)",(d.get("phone",""),json.dumps(d.get("cart",[])),datetime.datetime.now().strftime("%Y-%m-%d %H:%M")))
    conn.commit()
    return {"status":"ok"}

@app.post("/api/login")
async def login_api(req: Request):
    d=await req.json()
    cur=conn.cursor()
    cur.execute("SELECT * FROM users WHERE email=? AND password=?",(d.get("email"),d.get("password")))
    return {"status":"ok","message":"Welcome"} if cur.fetchone() else {"status":"error","message":"Invalid"}

@app.post("/mpesa/stkpush")
async def stk(req: Request):
    d=await req.json()
    raw_phone=d.get('phone','').strip()
    phone_for_db=raw_phone
    phone=raw_phone.replace(" ","").replace("+254","0").replace("+","")
    if phone.startswith("0"): phone="254"+phone[1:]
    phone="".join([c for c in phone if c.isdigit()])
    amount=int(d.get('amount',1))
    order_no='LONMA'+datetime.datetime.now().strftime("%H%M%S")
    items_text=json.dumps([f"{c.get('name')} x{c.get('qty')} @ {bulk_price(c.get('price'),c.get('qty'))}" for c in d.get('cart',[])])
    points_earned=amount//100
    try:
        conn.execute("INSERT INTO orders (order_no,name,phone,area,location,items,subtotal,delivery,total,status,created,mpesa_receipt,checkout_id,points_earned) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",(order_no,d.get('name','Guest'),phone_for_db,d.get('area'),d.get('location'),items_text,d.get('subtotal',0),d.get('delivery',0),d.get('amount',0),'Pending',datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),"",order_no,points_earned))
        conn.commit()
    except: pass
    if DARAJA_CONSUMER_KEY and DARAJA_CONSUMER_SECRET and DARAJA_PASSKEY:
        token=get_daraja_token()
        if token:
            timestamp=datetime.datetime.now().strftime("%Y%m%d%H%M%S")
            password=base64.b64encode(f"{DARAJA_SHORTCODE}{DARAJA_PASSKEY}{timestamp}".encode()).decode()
            payload={"BusinessShortCode":DARAJA_SHORTCODE,"Password":password,"Timestamp":timestamp,"TransactionType":"CustomerPayBillOnline","Amount":amount,"PartyA":phone,"PartyB":DARAJA_SHORTCODE,"PhoneNumber":phone,"CallBackURL":DARAJA_CALLBACK_URL,"AccountReference":order_no,"TransactionDesc":f"LONMA {order_no}"}
            try:
                base="https://api.safaricom.co.ke" if USE_PRODUCTION else "https://sandbox.safaricom.co.ke"
                r=requests.post(f"{base}/mpesa/stkpush/v1/processrequest",json=payload,headers={"Authorization":f"Bearer {token}"},timeout=15)
                res=r.json()
                if res.get("ResponseCode")=="0":
                    chk=res.get("CheckoutRequestID",order_no)
                    conn.execute("UPDATE orders SET checkout_id=? WHERE order_no=?",(chk,order_no))
                    conn.commit()
                    return {"status":"ok","message":f"STK sent to {phone_for_db}","order_no":order_no,"checkout_id":chk}
                else:
                    return {"status":"error","message":str(res),"order_no":order_no}
            except Exception as e:
                return {"status":"ok","message":f"Order {order_no} saved - {str(e)}","order_no":order_no}
    return {"status":"ok","message":f"Order {order_no} saved","order_no":order_no}

HTML = """<!DOCTYPE html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>LONMA ORBIT - 100% LONMA</title><style>
:root{--teal:#0A9EBB}*{box-sizing:border-box}body{margin:0;font-family:Arial;background:#f5f8fa}
.nav{position:fixed;top:0;width:100%;background:var(--teal);z-index:1000}
.nav-top{padding:8px 12px;display:flex;justify-content:space-between;align-items:center;height:60px}
.logo-circle{background:#fff;width:44px;height:44px;border-radius:50%;display:flex;align-items:center;justify-content:center;overflow:hidden}
.logo-circle img{height:40px;width:40px;object-fit:cover;border-radius:50%}
.search-bar-wrap{padding:0 12px 12px;background:var(--teal)}
.search-app-bar{background:#fff;border-radius:14px;padding:0 14px;height:48px;display:flex;align-items:center;gap:10px}
.hamburger{color:var(--teal);font-size:24px;cursor:pointer}
.search-app-bar input{border:none;outline:none;flex:1;font-size:15px;background:transparent}
.cart-icon{position:relative;background:#fff;color:var(--teal);padding:8px 14px;border-radius:20px;font-weight:bold;cursor:pointer;font-size:12px}
.cart-count{position:absolute;top:-6px;right:-6px;background:#ff3b30;color:#fff;border-radius:50%;width:18px;height:18px;display:flex;align-items:center;justify-content:center;font-size:11px}
.page{display:none;padding:126px 8px 80px;min-height:100vh}.page.active{display:block}
.card{background:#fff;border-radius:14px;padding:10px;margin:6px 0;box-shadow:0 1px 6px rgba(0,0,0,.06);position:relative;border:1px solid #eef2f7}
.card img{width:100%;height:160px;object-fit:contain;background:#fff;border-radius:10px;padding:6px}
.btn{background:var(--teal);color:#fff;border:none;padding:10px;border-radius:22px;width:100%;font-weight:bold;cursor:pointer;font-size:13px}
input,select,textarea{width:100%;padding:11px;border-radius:10px;border:1px solid #ddd;margin:4px 0;font-size:13px}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:8px}
.bottom{position:fixed;bottom:0;width:100%;background:#fff;display:flex;justify-content:space-around;padding:5px 0;border-top:1px solid #eee;z-index:1000}.bottom div{font-size:10px;color:#777;text-align:center;cursor:pointer;flex:1}.bottom div.active{color:var(--teal);font-weight:bold}
.chips{display:flex;gap:6px;overflow-x:auto;padding:8px 0}.chip{white-space:nowrap;background:#fff;border:1px solid #0A9EBB;color:#0A9EBB;padding:6px 12px;border-radius:18px;font-size:11px;cursor:pointer}.chip.active{background:#0A9EBB;color:#fff}
.qty-controls{display:flex;align-items:center;justify-content:space-between;background:#eef9fb;border-radius:20px;padding:4px 6px;margin-top:6px}
.qty-btn{background:var(--teal);color:#fff;border:none;width:28px;height:28px;border-radius:50%;font-weight:bold;cursor:pointer}
.promo{background:#fff;color:#0A9EBB;padding:8px;border-radius:10px;margin:6px 0;text-align:center;font-weight:bold;font-size:11px;border:1px solid #d0eef5}
.side-menu{position:fixed;top:0;left:-285px;width:285px;height:100%;background:#fff;z-index:2000;transition:.3s}.side-menu.open{left:0}.overlay{display:none;position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,.5);z-index:1999}.overlay.open{display:block}
.modal{display:none;position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,.6);z-index:2000;align-items:center;justify-content:center;padding:12px}.modal.open{display:flex}.modal-box{background:#fff;border-radius:16px;max-width:400px;width:100%;max-height:90vh;overflow-y:auto}
.status-badge{padding:2px 7px;border-radius:10px;font-size:9px;color:#fff}.status-Pending{background:#ff9a00}.status-PAID{background:#00c851}.status-Packing{background:#0A9EBB}.status-Transit{background:#6c5ce7}.status-Delivered{background:#2d3436}.status-friends{background:#00c851}.status-invited{background:#ff9a00}
.badge-low{position:absolute;top:6px;left:6px;padding:3px 7px;border-radius:10px;font-size:9px;color:#fff;font-weight:bold}
.share-icon{position:absolute;top:6px;right:6px;background:rgba(255,255,255,.9);width:28px;height:28px;border-radius:50%;display:flex;align-items:center;justify-content:center;cursor:pointer;font-size:12px;border:1px solid #eee}
.wish-icon{position:absolute;top:6px;left:50%;transform:translateX(-50%);background:rgba(255,255,255,.9);width:28px;height:28px;border-radius:50%;display:flex;align-items:center;justify-content:center;cursor:pointer;font-size:14px;border:1px solid #eee}
.timeline{display:flex;justify-content:space-between;margin:10px 0}.dot{width:24px;height:24px;border-radius:50%;background:#ddd;display:flex;align-items:center;justify-content:center;font-size:10px;color:#fff}.dot.active{background:#00c851}
</style></head><body>
<div class="nav"><div class="nav-top"><div class="logo-circle"><img src="/logo.png"></div><div class="cart-icon" onclick="show('cart')">CART <span id="cartCount" class="cart-count" style="display:none">0</span></div></div><div class="search-bar-wrap"><div class="search-app-bar"><span class="hamburger" onclick="openSideMenu()">☰</span><input id="searchInput" placeholder="Search LONMA..." oninput="filterProducts()"></div></div></div>
<div class="overlay" id="overlay" onclick="closeSideMenu()"></div>
<div class="side-menu" id="sideMenu"><div style="background:var(--teal);color:#fff;padding:18px;text-align:center"><div style="background:#fff;width:70px;height:70px;border-radius:50%;margin:0 auto;display:flex;align-items:center;justify-content:center;overflow:hidden"><img src="/logo.png" style="height:64px;width:64px;object-fit:cover;border-radius:50%"></div><h3 style="margin:8px 0 0">LONMA ORBIT</h3><p style="margin:2px 0 0;font-size:11px">100% LONMA Original</p></div><div style="padding:8px"><div style="padding:12px;border-bottom:1px solid #eee;cursor:pointer" onclick="show('products');closeSideMenu()">LONMA Products</div><div style="padding:12px;border-bottom:1px solid #eee;cursor:pointer" onclick="show('cart');closeSideMenu()">Cart (<span id="sideCartCount">0</span>)</div><div style="padding:12px;border-bottom:1px solid #eee;cursor:pointer" onclick="show('wishlist');closeSideMenu()">Wishlist</div><div style="padding:12px;border-bottom:1px solid #eee;cursor:pointer" onclick="show('friends');closeSideMenu()">Friends & Meet</div><div style="padding:12px;border-bottom:1px solid #eee;cursor:pointer" onclick="show('orders');closeSideMenu()">Orders & Tracking</div><div style="padding:12px;border-bottom:1px solid #eee;cursor:pointer" onclick="show('loyaltyPage');closeSideMenu()">Loyalty Points</div><div style="padding:12px;border-bottom:1px solid #eee;cursor:pointer" onclick="show('scan');closeSideMenu()">Verify LONMA Code</div><div style="padding:12px;cursor:pointer" onclick="show('admin');closeSideMenu()">Admin</div></div></div>
<div id="products" class="page active">
<div class="promo">LONMA ORBIT - 100% LONMA Products | Bulk: 3 Soaps @ 80 | Loyalty KSh 100 = 1 Point</div>
<div class="chips"><span class="chip active" onclick="filterCat('All',this)">All LONMA</span><span class="chip" onclick="filterCat('Cooking Oils',this)">Oils</span><span class="chip" onclick="filterCat('Soaps',this)">Soaps</span><span class="chip" onclick="filterCat('Lotions',this)">Lotions</span><span class="chip" onclick="filterCat('Pomades',this)">Pomades</span></div>
<div class="grid" id="plist"></div>
</div>
<div id="wishlist" class="page"><h2 style="font-size:18px">My LONMA Wishlist</h2><div id="wishlistItems"></div></div>
<div id="loyaltyPage" class="page"><h2 style="font-size:18px">LONMA Loyalty Points</h2>
<div class="card" style="text-align:center;background:linear-gradient(135deg,#0A9EBB,#00c851);color:#fff"><h1 id="loyaltyPoints">0</h1><p>Points (KSh 100 = 1 point, 10 points = KSh 100)</p><p>Total Spent: KSh <span id="loyaltySpent">0</span></p><div style="display:flex;gap:6px;margin-top:10px"><input id="redeemPointsInput" placeholder="Points to redeem" type="number" style="color:#000"><button class="btn" style="background:#fff;color:#0A9EBB;width:auto" onclick="redeemPoints()">Redeem</button></div><p id="loyaltyMsg" style="font-size:11px"></p></div>
</div>
<div id="friends" class="page"><h2 style="font-size:18px">Meet Friends & Shop LONMA Together</h2>
<div class="card"><h4 style="margin:0 0 6px;font-size:13px">My LONMA Referral Code</h4><div style="display:flex;gap:6px"><input id="myReferralCode" readonly style="background:#f0f9fb;font-weight:bold;color:#0A9EBB"><button class="btn" style="width:auto;padding:8px 14px" onclick="copyReferral()">Copy</button></div><button class="btn" style="background:#25D366;margin-top:6px" onclick="shareReferralWhatsApp()">Share via WhatsApp</button></div>
<div class="card"><h4 style="margin:0 0 6px;font-size:13px">Invite Friend</h4><input id="friendName" placeholder="Friend Name"><input id="friendPhone" placeholder="07xxxxxxxx"><button class="btn" onclick="inviteFriend()">Invite</button><p id="friendStatus" style="font-size:11px;margin-top:6px"></p></div>
<div class="card"><h4 style="margin:0 0 6px;font-size:13px">Share My LONMA Cart</h4><button class="btn" style="background:#6c5ce7" onclick="shareCart()">Generate Link</button><p id="shareLinkResult" style="font-size:11px;margin-top:6px;word-break:break-all"></p></div>
<div class="card"><h4 style="margin:0 0 6px;font-size:13px">Join Friend Cart</h4><div style="display:flex;gap:6px"><input id="joinShareCode" placeholder="Share Code"><button class="btn" style="width:auto;padding:8px 12px" onclick="joinSharedCart()">Join</button></div></div>
<div class="card"><h4 style="font-size:13px">My Friends (<span id="friendsCount">0</span>)</h4><div id="friendsList"></div></div>
</div>
<div id="cart" class="page"><h2 style="font-size:18px">My LONMA Cart</h2><div id="cartItems"></div><div class="card" id="cartSummary" style="display:none"><div style="font-size:12px;line-height:2"><div style="display:flex;justify-content:space-between"><span>Subtotal (<span id="totalItems">0</span>)</span><span>KSh <span id="subTotal">0</span></span></div><div style="display:flex;justify-content:space-between"><span>Delivery</span><span id="deliveryFee"></span></div><div style="display:flex;justify-content:space-between"><span>Bulk Discount</span><span id="bulkDiscount">KSh 0</span></div><div style="display:flex;justify-content:space-between"><span>Referral/Loyalty</span><span id="referralDiscount">KSh 0</span></div><div style="display:flex;justify-content:space-between;border-top:1px solid #eee;margin-top:4px;padding-top:4px;font-weight:bold;font-size:15px;color:#0A9EBB"><span>Total</span><span>KSh <span id="totalPrice">0</span></span></div></div><div id="freeDeliveryMsg" style="background:#e8f5e9;color:#2e7d32;padding:6px;border-radius:8px;font-size:10px;margin-top:6px;text-align:center"></div><div style="background:#fff;border:1px solid #eee;padding:10px;border-radius:10px;margin-top:10px"><h4 style="margin:0 0 6px;font-size:13px">Delivery</h4><input id="custName" placeholder="Full Name"><input id="phone" placeholder="M-Pesa 07xxxxxxxx"><select id="locationArea"><option value="">Select Area</option><option value="CBD">CBD - 150 (2-3hrs)</option><option value="Westlands">Westlands - 200</option><option value="Eastlands">Eastlands - 200</option><option value="Upcountry">Upcountry - 350</option></select><textarea id="exactLocation" placeholder="Estate, House No, Landmark"></textarea><div style="display:flex;gap:4px"><input id="promoCode" placeholder="Referral / Loyalty"><button class="btn" style="width:auto;padding:8px 10px;font-size:10px" onclick="applyReferralCode()">Apply</button></div><label style="font-size:11px;display:flex;gap:4px;align-items:center;margin-top:6px"><input type="checkbox" id="agreeTerms" style="width:auto"> Agree to Terms</label></div><div style="background:#fff;border:1px solid #eee;padding:10px;border-radius:10px;margin-top:10px"><button class="btn" style="background:#111" onclick="checkout()">PAY KSh <span id="payTotal">0</span> M-PESA</button><button class="btn" style="background:#25D366;margin-top:6px" onclick="orderWhatsApp()">WhatsApp Order</button><p id="paystatus" style="font-size:11px;margin-top:6px"></p></div><button class="btn" style="background:#fff;color:#0A9EBB;border:1px solid #0A9EBB;margin-top:6px" onclick="clearCart()">Clear Cart</button></div><div class="card" id="emptyCart" style="text-align:center;padding:24px"><h3>Empty</h3><button class="btn" onclick="show('products')">Shop LONMA</button></div></div>
<div id="orders" class="page"><h2 style="font-size:18px">LONMA Orders & Tracking</h2><div style="display:flex;gap:4px;margin-bottom:6px"><input id="orderPhoneLookup" placeholder="M-Pesa phone"><button class="btn" style="width:auto;padding:8px 12px" onclick="loadMyOrdersByPhone()">Load</button></div><div id="ordersList"></div><div class="card" id="noOrders" style="text-align:center;padding:24px"><h3>No LONMA orders</h3><button class="btn" onclick="show('products')">Shop LONMA</button></div></div>
<div id="scan" class="page"><h2 style="font-size:18px">Verify LONMA</h2><div class="card"><input id="manualcode" placeholder="LONMA-001"><button class="btn" onclick="verifyCode()">Verify LONMA Code</button><p id="scanresult" style="font-weight:bold;margin-top:8px"></p></div></div>
<div id="admin" class="page"><h2>LONMA Admin Analytics</h2><div class="card"><input id="adminPass" type="password" placeholder="lonma2024"><button class="btn" onclick="adminLogin()">Login</button><p id="adminStatus"></p></div><div id="adminContent" style="display:none"><div class="card"><div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;text-align:center"><div style="background:#eef9fb;padding:10px;border-radius:10px"><b id="statOrders">0</b><br><small>Orders</small></div><div style="background:#e8f5e9;padding:10px;border-radius:10px"><b id="statSales">0</b><br><small>Sales KSh</small></div><div style="background:#fff3e0;padding:10px;border-radius:10px"><b id="statLow">0</b><br><small>Low Stock</small></div><div style="background:#f3e5f5;padding:10px;border-radius:10px"><b id="statPoints">0</b><br><small>Loyalty Points</small></div></div><button class="btn" style="margin-top:8px" onclick="loadAdminOrders()">Refresh</button></div><div id="lowStockAlert" class="card" style="background:#fff3e0"></div><div id="adminOrdersList"></div><div class="card"><h4>Top LONMA Customers</h4><div id="topCustomers"></div></div></div></div>
<div id="receipt" class="page"><h2>LONMA Receipt</h2><div class="card" id="receiptContent"></div><div class="card"><h4>Tracking</h4><div class="timeline"><div class="dot active">1</div><div class="dot">2</div><div class="dot">3</div><div class="dot">4</div></div><div style="display:flex;justify-content:space-between;font-size:9px"><span>Pending</span><span>Packing</span><span>Transit</span><span>Done</span></div></div><button class="btn" onclick="show('products')">Continue Shopping LONMA</button></div>
<div class="bottom"><div id="b-products" class="active" onclick="show('products')">LONMA</div><div id="b-cart" onclick="show('cart')">Cart (<span id="bottomCartCount">0</span>)</div><div id="b-wishlist" onclick="show('wishlist')">Wishlist</div><div id="b-orders" onclick="show('orders')">Orders</div><div id="b-friends" onclick="show('friends')">Friends</div></div>
<div id="productModal" class="modal" onclick="if(event.target===this)closeModal()"><div class="modal-box"><div id="modalContent"></div></div></div>
<script>
let allProducts=[],currentCat='All',searchQuery='',cart=[],myOrders=JSON.parse(localStorage.getItem('my_orders')||'[]'),referralDiscountValue=0,bulkDiscountValue=0,wishlist=[];
try{let s=localStorage.getItem('lonma_cart'); if(s){cart=JSON.parse(s);} if(!Array.isArray(cart))cart=[];}catch(e){cart=[];}
function safeImage(name){return`https://via.placeholder.com/400x400/FFFFFF/0A9EBB?text=${encodeURIComponent(name)}`;}
function saveCart(){localStorage.setItem('lonma_cart',JSON.stringify(cart));updateCartCount();}
function updateCartCount(){let c=0;for(let i of cart)c+=Number(i.qty)||0;document.getElementById('cartCount').innerText=c;document.getElementById('bottomCartCount').innerText=c;let side=document.getElementById('sideCartCount');if(side)side.innerText=c;document.getElementById('cartCount').style.display=c>0?'flex':'none';}
function openSideMenu(){document.getElementById('sideMenu').classList.add('open');document.getElementById('overlay').classList.add('open');}
function closeSideMenu(){document.getElementById('sideMenu').classList.remove('open');document.getElementById('overlay').classList.remove('open');}
function filterCat(cat,el){currentCat=cat;document.querySelectorAll('.chip').forEach(ch=>ch.classList.remove('active'));if(el)el.classList.add('active');renderProducts();}
function filterProducts(){searchQuery=document.getElementById('searchInput').value.toLowerCase();renderProducts();}
function calcBulk(price,qty){if(qty>=3&&price==90)return 80;if(qty>=2&&price>=250)return Math.floor(price*0.9);return price;}
function renderProducts(){let list=allProducts.filter(p=>{let mCat=currentCat==='All'||p.category===currentCat;let mSearch=!searchQuery||p.name.toLowerCase().includes(searchQuery);return mCat&&mSearch;});let html='';for(let p of list){let inCart=cart.find(c=>c.id===p.id);let qtyText=inCart?`x${inCart.qty} in cart`:'';let img=p.image||safeImage(p.name);let stockHtml='';if(p.stock<=5){stockHtml=`<span class="badge-low" style="background:${p.stock===0?'#ff3b30':'#ff9a00'}">${p.stock===0?'Out':'Low:'+p.stock}</span>`;}let stars='★'.repeat(Math.round(p.rating||0))+'☆'.repeat(5-Math.round(p.rating||0));html+=`<div class="card">${stockHtml}<div class="share-icon" onclick="shareProduct(${p.id})">↗</div><div class="wish-icon" onclick="toggleWishlistUI(${p.id})">♡</div><img src="${img}" onclick="openModal(${p.id})"><h4 style="font-size:12px;margin:6px 0 2px;line-height:1.2">${p.name}</h4><div style="font-size:10px;color:#ffb300">${stars} (${p.reviews||0})</div><p style="margin:0;font-weight:bold;color:#0A9EBB;font-size:14px">KSh ${p.price} ${p.price==90?'<small style="color:#00c851">3@80</small>':''}</p><div style="font-size:10px;color:#0A9EBB;font-weight:bold;min-height:12px;margin:2px 0">${qtyText}</div><button class="btn" onclick="addToCart(${p.id})">ADD</button></div>`;}document.getElementById('plist').innerHTML=html;}
async function openModal(id){let p=allProducts.find(x=>x.id===id);if(!p)return;let r=await fetch(`/api/reviews/${id}`);let reviews=await r.json();let stars='★'.repeat(Math.round(p.rating||0));let revHtml=reviews.length?reviews.map(rv=>`<div style="border-top:1px solid #eee;padding:6px 0"><b style="font-size:11px">${rv.name} ${'★'.repeat(rv.rating)}</b><p style="font-size:11px;margin:2px 0">${rv.comment}</p><small style="font-size:9px;color:#888">${rv.created}</small></div>`).join(''):'<p style="font-size:11px;color:#888">No reviews yet for this LONMA product</p>';document.getElementById('modalContent').innerHTML=`<img src="${p.image}" style="width:100%;height:240px;object-fit:contain;padding:10px"><div style="padding:10px"><h3 style="font-size:15px">${p.name}</h3><div style="font-size:12px;color:#ffb300">${stars} (${p.reviews} reviews)</div><p style="color:#0A9EBB;font-weight:bold;font-size:18px">KSh ${p.price}</p><p style="font-size:12px">${p.desc}</p><p style="font-size:11px;color:#888">Code: ${p.code} | Stock: ${p.stock}</p><button class="btn" onclick="addToCart(${p.id});closeModal()">ADD TO CART</button><button class="btn" style="background:#fff;color:#0A9EBB;border:1px solid #0A9EBB;margin-top:6px" onclick="toggleWishlistUI(${p.id})">♡ Wishlist</button><div style="margin-top:12px"><h4 style="font-size:13px">Add Review for LONMA</h4><input id="revName" placeholder="Your name"><select id="revRating"><option value="5">5 ★</option><option value="4">4 ★</option><option value="3">3 ★</option><option value="2">2 ★</option><option value="1">1 ★</option></select><textarea id="revComment" placeholder="Your review"></textarea><button class="btn" style="background:#ffb300" onclick="submitReview(${p.id})">Submit LONMA Review</button></div><div style="margin-top:12px"><h4 style="font-size:13px">LONMA Reviews</h4>${revHtml}</div><button class="btn" style="background:#fff;color:#0A9EBB;border:1px solid #0A9EBB;margin-top:10px" onclick="closeModal()">Close</button></div>`;document.getElementById('productModal').classList.add('open');}
function closeModal(){document.getElementById('productModal').classList.remove('open');}
function addToCart(id){let p=allProducts.find(x=>x.id===id);if(!p)return;if(p.stock===0){alert('Out of stock');return;}let found=cart.find(c=>c.id===id);if(found){found.qty++;}else{cart.push({id:p.id,name:p.name,price:p.price,image:p.image,code:p.code,qty:1});}saveCart();renderCart();renderProducts();}
function changeQty(id,delta){for(let i=0;i<cart.length;i++)if(cart[i].id===id){cart[i].qty+=delta;if(cart[i].qty<=0)cart.splice(i,1);break;}saveCart();renderCart();renderProducts();}
function clearCart(){cart=[];localStorage.removeItem('lonma_cart');saveCart();renderCart();renderProducts();}
function renderCart(){let cont=document.getElementById('cartItems'),sum=document.getElementById('cartSummary'),empty=document.getElementById('emptyCart');if(cart.length===0){cont.innerHTML='';sum.style.display='none';empty.style.display='block';return;}empty.style.display='none';sum.style.display='block';let totalItems=0,subTotal=0,bulkSave=0,html='';for(let it of cart){let unit=calcBulk(it.price,it.qty);let orig=it.price*it.qty;let discounted=unit*it.qty;bulkSave+=(orig-discounted);totalItems+=it.qty;subTotal+=discounted;html+=`<div class="card" style="display:flex;gap:8px"><img src="${it.image}" style="width:50px;height:50px;object-fit:contain"><div style="flex:1"><h4 style="margin:0;font-size:12px">${it.name}</h4><p style="font-size:11px">KSh ${unit} x ${it.qty} ${unit!=it.price?'<span style="color:#00c851">(bulk LONMA)</span>':''}</p><div class="qty-controls"><button class="qty-btn" onclick="changeQty(${it.id},-1)">-</button><span>${it.qty}</span><button class="qty-btn" onclick="changeQty(${it.id},1)">+</button></div></div></div>`;}cont.innerHTML=html;let area=document.getElementById('locationArea').value;let delivery=area==='CBD'?150:area==='Upcountry'?350:200;if(subTotal>=2000)delivery=0;let total=subTotal+delivery-referralDiscountValue;if(total<0)total=0;bulkDiscountValue=bulkSave;document.getElementById('subTotal').innerText=subTotal;document.getElementById('totalItems').innerText=totalItems;document.getElementById('deliveryFee').innerText=delivery===0?'FREE':'KSh '+delivery;document.getElementById('bulkDiscount').innerText='KSh '+bulkSave;document.getElementById('referralDiscount').innerText='KSh '+referralDiscountValue;document.getElementById('totalPrice').innerText=total;document.getElementById('payTotal').innerText=total;document.getElementById('freeDeliveryMsg').innerHTML=subTotal>=2000?'FREE LONMA delivery + '+(Math.floor(subTotal/100))+' points!':'Add '+(2000-subTotal)+' for FREE LONMA delivery';}
document.getElementById('locationArea')?.addEventListener('change',renderCart);
function show(id){document.querySelectorAll('.page').forEach(p=>p.classList.remove('active'));document.getElementById(id).classList.add('active');document.querySelectorAll('.bottom div').forEach(b=>b.classList.remove('active'));let btn=document.getElementById('b-'+id);if(btn)btn.classList.add('active');if(id==='cart')renderCart();if(id==='orders')renderOrders();if(id==='wishlist')loadWishlist();if(id==='loyaltyPage')loadLoyalty();if(id==='friends')loadFriends();closeSideMenu();window.scrollTo(0,0);}
async function loadProducts(){let r=await fetch('/api/products');let d=await r.json();allProducts=d;renderProducts();let params=new URLSearchParams(window.location.search);let share=params.get('share');if(share){document.getElementById('joinShareCode').value=share;show('friends');}}
async function verifyCode(){let c=document.getElementById('manualcode').value.trim().toUpperCase();let r=await fetch(`/api/verify/${c}`);let d=await r.json();document.getElementById('scanresult').innerHTML=d.valid?`Valid LONMA ${d.product.name}`:`Invalid LONMA code`;}
function orderWhatsApp(){let total=document.getElementById('totalPrice').innerText;let name=document.getElementById('custName').value;let area=document.getElementById('locationArea').value;let loc=document.getElementById('exactLocation').value;let phone=document.getElementById('phone').value;let items=cart.map(c=>`${c.name} x${c.qty}`).join('%0A');let msg=`Hi LONMA%0AName:${name}%0APhone:${phone}%0AArea:${area}%0ALoc:${loc}%0A%0A${items}%0ATotal KSh ${total}`;window.open(`https://wa.me/254700000000?text=${msg}`,'_blank');}
async function checkout(){let name=document.getElementById('custName').value.trim(),phone=document.getElementById('phone').value.trim(),area=document.getElementById('locationArea').value,loc=document.getElementById('exactLocation').value.trim(),agree=document.getElementById('agreeTerms').checked;if(!name||!phone||!area||!loc||!agree){document.getElementById('paystatus').innerText='Fill all fields';return;}let sub=0;for(let i of cart)sub+=calcBulk(i.price,i.qty)*i.qty;let del=area==='CBD'?150:area==='Upcountry'?350:200;if(sub>=2000)del=0;let tot=sub+del-referralDiscountValue;if(tot<0)tot=0;document.getElementById('paystatus').innerText='Sending STK...';let r=await fetch('/mpesa/stkpush',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({phone,amount:tot,cart,name,area,location:loc,subtotal:sub,delivery:del})});let d=await r.json();document.getElementById('paystatus').innerText=d.message;if(d.status==='ok'||d.message.includes('STK')||d.message.includes('saved')){let orderNo=d.order_no;myOrders.unshift({order_no:orderNo,items:[...cart],total:tot,status:'Pending',created:new Date().toLocaleString()});localStorage.setItem('my_orders',JSON.stringify(myOrders));document.getElementById('receiptContent').innerHTML=`<h3>${orderNo}</h3><p>${name} - ${phone}</p><p>${area} - ${loc}</p><p>Total KSh ${tot}</p><p>LONMA Points earned: ${Math.floor(tot/100)}</p><hr>${cart.map(c=>`<p>${c.name} x${c.qty}</p>`).join('')}`;cart=[];localStorage.removeItem('lonma_cart');saveCart();referralDiscountValue=0;setTimeout(()=>show('receipt'),800);}}
async function loadMyOrdersByPhone(){let phone=document.getElementById('orderPhoneLookup').value.trim();if(!phone){renderOrders();return;}let r=await fetch(`/api/orders?phone=${phone}`);let data=await r.json();let cont=document.getElementById('ordersList'),empty=document.getElementById('noOrders');if(data.length===0){cont.innerHTML='<p>No LONMA orders</p>';empty.style.display='none';return;}empty.style.display='none';let html='';for(let o of data){html+=`<div class="card"><div style="display:flex;justify-content:space-between"><b>${o.order_no}</b><span class="status-badge status-${o.status}">${o.status}</span></div><p>KSh ${o.total} - ${o.created}</p><div class="timeline"><div class="dot ${['Pending','PAID','Packing','Transit','Delivered'].indexOf(o.status)>=0?'active':''}">1</div><div class="dot ${['PAID','Packing','Transit','Delivered'].indexOf(o.status)>=1?'active':''}">2</div><div class="dot ${['Packing','Transit','Delivered'].indexOf(o.status)>=1?'active':''}">3</div><div class="dot ${o.status=='Delivered'?'active':''}">4</div></div></div>`;}cont.innerHTML=html;}
function renderOrders(){let cont=document.getElementById('ordersList'),empty=document.getElementById('noOrders');if(myOrders.length===0){cont.innerHTML='';empty.style.display='block';return;}empty.style.display='none';let html='';for(let o of myOrders){html+=`<div class="card"><div style="display:flex;justify-content:space-between"><b>${o.order_no}</b><span class="status-badge status-${o.status}">${o.status}</span></div><p>KSh ${o.total} - ${o.created}</p></div>`;}cont.innerHTML=html;}
async function adminLogin(){let p=document.getElementById('adminPass').value;if(p!=='lonma2024'){document.getElementById('adminStatus').innerText='Wrong';return;}document.getElementById('adminContent').style.display='block';document.getElementById('adminStatus').innerText='LONMA Admin Logged in';loadAdminOrders();}
async function loadAdminOrders(){let r=await fetch('/api/admin/orders');let d=await r.json();let a=await fetch('/api/admin/analytics');let an=await a.json();document.getElementById('statOrders').innerText=an.orders;document.getElementById('statSales').innerText=an.sales;document.getElementById('statLow').innerText=an.low_stock.length;document.getElementById('statPoints').innerText=an.top_customers.reduce((s,c)=>s+c.points,0);document.getElementById('lowStockAlert').innerHTML=an.low_stock.length?`<h4 style="color:#ff9a00">LONMA Low Stock Alert</h4>${an.low_stock.map(l=>`<p style="font-size:11px">${l.name}: ${l.stock} left <button style="font-size:9px" onclick="window.open('https://wa.me/?text=${encodeURIComponent('Restock '+l.name)}','_blank')">WhatsApp Supplier</button></p>`).join('')}`:'<p style="font-size:11px;color:#00c851">All LONMA stock OK</p>';document.getElementById('topCustomers').innerHTML=an.top_customers.map(c=>`<p style="font-size:11px">${c.phone}: ${c.points} pts (KSh ${c.spent})</p>`).join('');let html='';for(let o of d){html+=`<div class="card"><div style="display:flex;justify-content:space-between"><b>${o.order_no}</b><span class="status-badge status-${o.status}">${o.status}</span></div><p>${o.name} - ${o.phone}</p><p>KSh ${o.total} - ${o.area} | Points ${o.points_earned}</p><div style="display:flex;gap:4px;margin-top:6px;flex-wrap:wrap"><button class="btn" style="width:auto;padding:5px 8px;font-size:10px" onclick="updateOrderStatus('${o.order_no}','Packing')">Packing</button><button class="btn" style="width:auto;padding:5px 8px;font-size:10px;background:#6c5ce7" onclick="updateOrderStatus('${o.order_no}','Transit')">Transit</button><button class="btn" style="width:auto;padding:5px 8px;font-size:10px;background:#2d3436" onclick="updateOrderStatus('${o.order_no}','Delivered')">Done</button><button class="btn" style="width:auto;padding:5px 8px;font-size:10px;background:#00c851" onclick="updateOrderStatus('${o.order_no}','PAID')">PAID</button></div></div>`;}document.getElementById('adminOrdersList').innerHTML=html;}
async function updateOrderStatus(order_no,status){let r=await fetch(`/api/admin/orders/${order_no}/${status}`,{method:'POST'});let d=await r.json();alert(d.message);loadAdminOrders();}
async function loadFriends(){let phone=document.getElementById('phone').value||localStorage.getItem('user_phone')||'';if(!phone){document.getElementById('friendsList').innerHTML='<p style="font-size:11px">Enter phone in Cart to see friends</p>';return;}let r=await fetch(`/api/friends?phone=${phone}`);let data=await r.json();document.getElementById('myReferralCode').value=data.referral_code;document.getElementById('friendsCount').innerText=data.friends.length;let html='';if(data.friends.length===0){html='<p style="font-size:11px;color:#888">No friends yet</p>';}else{for(let f of data.friends){html+=`<div style="display:flex;justify-content:space-between;padding:6px;border-bottom:1px solid #eee"><div><b style="font-size:12px">${f.name}</b><br><small>${f.phone}</small></div><span class="status-badge status-${f.status}">${f.status}</span></div>`;}}document.getElementById('friendsList').innerHTML=html;}
async function inviteFriend(){let userPhone=document.getElementById('phone').value||localStorage.getItem('user_phone')||prompt('Your phone 07...');if(!userPhone)return;localStorage.setItem('user_phone',userPhone);let friendPhone=document.getElementById('friendPhone').value.trim();let friendName=document.getElementById('friendName').value.trim()||'Friend';if(!friendPhone){document.getElementById('friendStatus').innerText='Enter phone';return;}let r=await fetch('/api/friends/invite',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({user_phone:userPhone,friend_phone:friendPhone,friend_name:friendName})});let d=await r.json();document.getElementById('friendStatus').innerText=d.message;loadFriends();}
async function applyReferralCode(){let code=document.getElementById('promoCode').value.trim().toUpperCase();let userPhone=document.getElementById('phone').value||'';if(!code){document.getElementById('paystatus').innerText='Enter code';return;}let r=await fetch('/api/referral/apply',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({code,user_phone:userPhone})});let d=await r.json();if(d.status==='ok'){referralDiscountValue=d.discount;document.getElementById('paystatus').innerText=d.message;renderCart();return;}let l=await fetch(`/api/loyalty/${userPhone}`);let ld=await l.json();if(code==='LOYALTY'){referralDiscountValue=Math.floor(ld.points/10)*100;document.getElementById('paystatus').innerText=`Loyalty KSh ${referralDiscountValue} applied`;renderCart();}else{document.getElementById('paystatus').innerText=d.message;}}
async function shareCart(){let phone=document.getElementById('phone').value||localStorage.getItem('user_phone')||'guest';if(cart.length===0){alert('Cart empty');return;}let r=await fetch('/api/share-cart',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({phone,cart})});let d=await r.json();document.getElementById('shareLinkResult').innerHTML=`Link: <a href="${d.share_url}">${d.share_code}</a><br><button class="btn" style="margin-top:4px;background:#25D366" onclick="window.open('https://wa.me/?text=${encodeURIComponent('Join my LONMA cart '+d.share_url)}','_blank')">WhatsApp</button>`;}
async function joinSharedCart(){let code=document.getElementById('joinShareCode').value.trim().toUpperCase();if(!code)return;let r=await fetch(`/api/share-cart/${code}`);let d=await r.json();if(d.status==='ok'){cart=d.items;saveCart();renderCart();alert('Joined '+d.owner);show('cart');}else{alert(d.message);}}
function shareProduct(id){let p=allProducts.find(x=>x.id===id);if(!p)return;let url=`https://app.lonmaorbit.co.ke/?product=${p.id}`;window.open(`https://wa.me/?text=${encodeURIComponent(p.name+' KSh '+p.price+' '+url)}`,'_blank');}
function copyReferral(){let el=document.getElementById('myReferralCode');el.select();document.execCommand('copy');alert('Copied LONMA code');}
function shareReferralWhatsApp(){let code=document.getElementById('myReferralCode').value;window.open(`https://wa.me/?text=${encodeURIComponent('My LONMA code '+code+' gives KSh 100 OFF https://app.lonmaorbit.co.ke')}`,'_blank');}
async function toggleWishlistUI(pid){let phone=document.getElementById('phone').value||localStorage.getItem('user_phone')||prompt('Phone to save LONMA wishlist 07...');if(!phone)return;localStorage.setItem('user_phone',phone);let r=await fetch('/api/wishlist/toggle',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({phone,product_id:pid})});let d=await r.json();alert('LONMA '+d.status);loadWishlist();}
async function loadWishlist(){let phone=document.getElementById('phone').value||localStorage.getItem('user_phone')||'';if(!phone){document.getElementById('wishlistItems').innerHTML='<p style="font-size:11px">Enter phone in Cart to see LONMA wishlist</p>';return;}let r=await fetch(`/api/wishlist?phone=${phone}`);let data=await r.json();if(data.length===0){document.getElementById('wishlistItems').innerHTML='<p>No LONMA wishlist</p>';return;}let html='';for(let it of data){html+=`<div class="card" style="display:flex;gap:8px"><img src="${it.image}" style="width:60px;height:60px"><div><b style="font-size:12px">${it.name}</b><p>KSh ${it.price}</p><button class="btn" style="width:auto;padding:4px 8px;font-size:10px" onclick="addToCart(${it.id})">Add to Cart</button></div></div>`;}document.getElementById('wishlistItems').innerHTML=html;}
async function submitReview(pid){let name=document.getElementById('revName').value||'Customer';let rating=document.getElementById('revRating').value;let comment=document.getElementById('revComment').value;let phone=document.getElementById('phone').value||localStorage.getItem('user_phone')||'guest';let r=await fetch('/api/reviews',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({product_id:pid,phone,name,rating:parseInt(rating),comment})});let d=await r.json();if(d.status==='ok'){alert('LONMA Review added');closeModal();loadProducts();}}
async function loadLoyalty(){let phone=document.getElementById('phone').value||localStorage.getItem('user_phone')||'';if(!phone){document.getElementById('loyaltyPoints').innerText='0';return;}let r=await fetch(`/api/loyalty/${phone}`);let d=await r.json();document.getElementById('loyaltyPoints').innerText=d.points;document.getElementById('loyaltySpent').innerText=d.total_spent;}
async function redeemPoints(){let phone=document.getElementById('phone').value||localStorage.getItem('user_phone')||'';let points=document.getElementById('redeemPointsInput').value;if(!points)return;let r=await fetch('/api/loyalty/redeem',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({phone,points:parseInt(points)})});let d=await r.json();document.getElementById('loyaltyMsg').innerText=d.message||d.discount;if(d.status==='ok'){referralDiscountValue=d.discount;renderCart();loadLoyalty();}}
function clearPrefs(){localStorage.removeItem('lonma_prefs');}
function clearAllData(){if(confirm('Clear all LONMA data?')){localStorage.clear();cart=[];myOrders=[];updateCartCount();renderCart();renderOrders();}}
loadProducts();updateCartCount();renderCart();renderOrders();
setInterval(()=>{if(cart.length>0){let phone=document.getElementById('phone').value||localStorage.getItem('user_phone')||'';if(phone){fetch('/api/abandoned',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({phone,cart})});}}},30000);
</script></body></html>
"""

@app.api_route("/", methods=["GET", "HEAD"])
def home(): return HTMLResponse(HTML)

@app.get("/logo.png")
def logo():
    for f in ["logo.png","static/logo.png"]:
        if os.path.exists(f): return FileResponse(f)
    return HTMLResponse("",200)
