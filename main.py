from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
import os, sqlite3, json, datetime, requests, base64

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

DARAJA_KEY = os.getenv("DARAJA_KEY",""); DARAJA_SECRET=os.getenv("DARAJA_SECRET","")
DARAJA_SHORTCODE=os.getenv("DARAJA_SHORTCODE","174379"); DARAJA_PASSKEY=os.getenv("DARAJA_PASSKEY","")
DARAJA_CALLBACK=os.getenv("CALLBACK_URL","https://app.lonmaorbit.co.ke/mpesa/callback")
USE_PROD=os.getenv("DARAJA_ENV","sandbox")=="production"

conn=sqlite3.connect("lonma.db",check_same_thread=False)
conn.execute("CREATE TABLE IF NOT EXISTS products (id INTEGER PRIMARY KEY, name TEXT, price INTEGER, code TEXT, image TEXT, category TEXT, stock INTEGER)")
conn.execute("CREATE TABLE IF NOT EXISTS orders (id INTEGER PRIMARY KEY AUTOINCREMENT, order_no TEXT, name TEXT, phone TEXT, area TEXT, location TEXT, items TEXT, total INTEGER, status TEXT, created TEXT, mpesa_receipt TEXT, checkout_id TEXT)")
conn.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, phone TEXT UNIQUE, name TEXT, password TEXT)")
cur=conn.cursor()
cur.execute("DELETE FROM products")
PRODS=[(1,"LONMA Cooking Oil 2L",850,"LONMA-001","Cooking Oils",50),(2,"LONMA Citronella Soap 110g",90,"LONMA-002","Soaps",120),(3,"LONMA Men Lotion 72Hrs",299,"LONMA-003","Lotions",8),(4,"LONMA Pine Soap 110g",90,"LONMA-004","Soaps",100),(5,"LONMA Cooking Oil 5L",1250,"LONMA-005","Cooking Oils",25),(6,"LONMA Cool Mint Soap 110g",90,"LONMA-006","Soaps",3),(7,"LONMA Anti-Dandruff Pomade",250,"LONMA-007","Pomades",40),(8,"LONMA Anti-Breakage Pomade",250,"LONMA-008","Pomades",45),(9,"LONMA Cocoa Butter Lotion",299,"LONMA-009","Lotions",30)]
for pid,name,price,code,cat,stock in PRODS:
    img=f"https://via.placeholder.com/400x400/FFFFFF/0A9EBB?text={name.replace(' ','+')}"
    cur.execute("INSERT INTO products VALUES (?,?,?,?,?,?,?)",(pid,name,price,code,img,cat,stock))
conn.commit()

def get_token():
    try:
        base="https://api.safaricom.co.ke" if USE_PROD else "https://sandbox.safaricom.co.ke"
        r=requests.get(f"{base}/oauth/v1/generate?grant_type=client_credentials",auth=(DARAJA_KEY,DARAJA_SECRET),timeout=10)
        return r.json().get("access_token")
    except: return None

@app.api_route("/mpesa/callback",methods=["GET","POST"])
async def callback(request:Request):
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
def prods_api():
    cur=conn.cursor(); cur.execute("SELECT id,name,price,code,image,category,stock FROM products")
    return [{"id":r[0],"name":r[1],"price":r[2],"code":r[3],"image":r[4],"category":r[5],"stock":r[6]} for r in cur.fetchall()]

@app.get("/api/verify/{code}")
def verify(code:str):
    cur=conn.cursor(); cur.execute("SELECT name FROM products WHERE code=?",(code.upper(),))
    row=cur.fetchone(); return {"valid":True,"product":{"name":row[0]}} if row else {"valid":False}

@app.get("/api/orders")
def orders_api(phone:str=""):
    cur=conn.cursor()
    if phone: cur.execute("SELECT order_no,name,total,status,created FROM orders WHERE phone=? ORDER BY id DESC",(phone,))
    else: cur.execute("SELECT order_no,name,total,status,created FROM orders ORDER BY id DESC LIMIT 50")
    return [{"order_no":r[0],"name":r[1],"total":r[2],"status":r[3],"created":r[4]} for r in cur.fetchall()]

@app.get("/api/admin/orders")
def admin_orders():
    cur=conn.cursor(); cur.execute("SELECT order_no,name,phone,total,status,created FROM orders ORDER BY id DESC")
    return [{"order_no":r[0],"name":r[1],"phone":r[2],"total":r[3],"status":r[4],"created":r[5]} for r in cur.fetchall()]

@app.post("/mpesa/stkpush")
async def stk(req:Request):
    d=await req.json()
    raw=d.get('phone','').strip(); phone=raw.replace(" ","").replace("+254","0")
    if phone.startswith("0"): phone="254"+phone[1:]
    phone="".join([c for c in phone if c.isdigit()]); amount=int(d.get('amount',1))
    order_no='LONMA'+datetime.datetime.now().strftime("%H%M%S")
    conn.execute("INSERT INTO orders (order_no,name,phone,area,location,items,total,status,created,mpesa_receipt,checkout_id) VALUES (?,?,?,?,?,?,?,?,?,?,?)",(order_no,d.get('name','Guest'),raw,d.get('area'),d.get('location'),json.dumps(d.get('cart',[])),amount,'Pending',datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),"",order_no))
    conn.commit()
    if DARAJA_KEY and DARAJA_PASSKEY:
        token=get_token()
        if token:
            ts=datetime.datetime.now().strftime("%Y%m%d%H%M%S")
            pwd=base64.b64encode(f"{DARAJA_SHORTCODE}{DARAJA_PASSKEY}{ts}".encode()).decode()
            payload={"BusinessShortCode":DARAJA_SHORTCODE,"Password":pwd,"Timestamp":ts,"TransactionType":"CustomerPayBillOnline","Amount":amount,"PartyA":phone,"PartyB":DARAJA_SHORTCODE,"PhoneNumber":phone,"CallBackURL":DARAJA_CALLBACK,"AccountReference":order_no,"TransactionDesc":order_no}
            try:
                base="https://api.safaricom.co.ke" if USE_PROD else "https://sandbox.safaricom.co.ke"
                r=requests.post(f"{base}/mpesa/stkpush/v1/processrequest",json=payload,headers={"Authorization":f"Bearer {token}"},timeout=15)
                res=r.json()
                if res.get("ResponseCode")=="0":
                    conn.execute("UPDATE orders SET checkout_id=? WHERE order_no=?",(res.get("CheckoutRequestID",order_no),order_no)); conn.commit()
                    return {"status":"ok","message":f"STK sent to {raw}","order_no":order_no}
            except: pass
    return {"status":"ok","message":f"Order {order_no} saved","order_no":order_no}

@app.post("/api/auth/register")
async def reg(req:Request):
    d=await req.json(); phone=d.get("phone","").strip(); name=d.get("name","").strip(); pwd=d.get("password","").strip()
    cur=conn.cursor(); cur.execute("SELECT id FROM users WHERE phone=?",(phone,)); 
    if cur.fetchone(): return {"status":"error","message":"Exists"}
    cur.execute("INSERT INTO users (phone,name,password) VALUES (?,?,?)",(phone,name,pwd)); conn.commit()
    return {"status":"ok","user":{"phone":phone,"name":name}}

@app.post("/api/auth/login")
async def log(req:Request):
    d=await req.json(); cur=conn.cursor(); cur.execute("SELECT phone,name FROM users WHERE phone=? AND password=?",(d.get("phone","").strip(),d.get("password","").strip()))
    row=cur.fetchone(); return {"status":"ok","user":{"phone":row[0],"name":row[1]}} if row else {"status":"error","message":"Wrong"}

HTML="""<!DOCTYPE html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>LONMA ORBIT</title><style>
:root{--teal:#0A9EBB;--dark:#0f172a;--line:#e2e8f0}*{box-sizing:border-box}body{margin:0;font-family:Inter,-apple-system,Arial;background:#f8fafc;color:var(--dark)}
.nav{position:fixed;top:0;width:100%;background:#fff;z-index:1000;border-bottom:1px solid var(--line)}.nav-top{padding:12px 16px;display:flex;justify-content:space-between;align-items:center;height:64px}
.logo{display:flex;align-items:center;gap:10px;cursor:pointer}.logo img{width:38px;height:38px;border-radius:50%}.logo b{font-size:16px;letter-spacing:.5px}
.cart-pill{background:var(--dark);color:#fff;padding:8px 16px;border-radius:30px;font-weight:800;font-size:12px;cursor:pointer;position:relative}
.cart-num{position:absolute;top:-6px;right:-6px;background:var(--teal);color:#fff;border-radius:50%;width:20px;height:20px;display:flex;align-items:center;justify-content:center;font-size:11px}
.search-wrap{padding:0 16px 14px}.search-box{background:#f1f5f9;border-radius:30px;height:44px;display:flex;align-items:center;gap:12px;padding:0 16px;border:1px solid var(--line)}
.search-box input{border:none;outline:none;background:transparent;flex:1;font-size:14px}.burger{font-size:22px;cursor:pointer;color:var(--dark)}
.page{display:none;padding:130px 14px 90px;max-width:480px;margin:0 auto}.page.active{display:block}
.card{background:#fff;border-radius:20px;padding:14px;margin:10px 0;border:1px solid #f1f5f9;box-shadow:0 4px 16px rgba(15,23,42,.04)}
.card img{width:100%;height:160px;object-fit:contain;border-radius:16px;background:#f8fafc}
.btn{background:var(--dark);color:#fff;border:none;padding:14px;border-radius:30px;width:100%;font-weight:800;cursor:pointer;letter-spacing:.3px}.btn-teal{background:var(--teal)}
input,select,textarea{width:100%;padding:14px;border-radius:14px;border:1px solid var(--line);margin:6px 0;font-size:14px;background:#fff}
.bottom{position:fixed;bottom:0;width:100%;background:#fff;border-top:1px solid var(--line);display:flex;justify-content:space-around;padding:10px 0;z-index:1000}
.bottom div{font-size:11px;text-align:center;flex:1;cursor:pointer;color:#94a3b8}.bottom div.active{color:var(--dark);font-weight:800}
.side{position:fixed;top:0;left:-320px;width:300px;height:100%;background:#fff;z-index:2000;transition:.35s cubic-bezier(.4,0,.2,1);box-shadow:20px 0 60px rgba(0,0,0,.12)}.side.open{left:0}.overlay{display:none;position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(15,23,42,.4);backdrop-filter:blur(4px);z-index:1999}.overlay.open{display:block}
.top-box{background:var(--dark);padding:32px 20px;color:#fff;text-align:center;position:relative;overflow:hidden}.top-box::after{content:'';position:absolute;top:-40px;right:-40px;width:120px;height:120px;background:var(--teal);border-radius:50%;opacity:.3}
.lc{width:80px;height:80px;background:#fff;border-radius:50%;margin:0 auto;display:flex;align-items:center;justify-content:center;box-shadow:0 8px 20px rgba(0,0,0,.2);position:relative;z-index:1}.lc img{width:76px;height:76px;border-radius:50%;object-fit:cover}
.menu{padding:12px 0}.mi{display:flex;align-items:center;gap:14px;padding:16px 20px;cursor:pointer;transition:.2s}.mi:hover{background:#f8fafc}.mi b{font-size:14px;font-weight:600;flex:1}.ico{width:40px;height:40px;border-radius:12px;display:flex;align-items:center;justify-content:center;font-size:18px}.tag{font-size:11px;font-weight:800;padding:5px 10px;border-radius:20px}
.div{height:1px;background:#f1f5f9;margin:8px 20px}.label{font-size:10px;font-weight:800;letter-spacing:.2em;color:#94a3b8;padding:16px 20px 6px}
</style></head><body>
<div class="nav"><div class="nav-top"><div class="logo" onclick="show('products')"><img src="/logo.png"><b>LONMA ORBIT</b></div><div class="cart-pill" onclick="show('cart')">CART <span id="cartCount" class="cart-num" style="display:none">0</span></div></div><div class="search-wrap"><div class="search-box"><span class="burger" onclick="openMenu()">☰</span><input id="searchInput" placeholder="Search oil, soap, lotion..." oninput="filterProducts()"></div></div></div>
<div class="overlay" id="overlay" onclick="closeMenu()"></div>
<div class="side" id="side">
<div class="top-box"><div style="text-align:right;position:absolute;top:12px;right:12px;z-index:2"><span style="background:rgba(255,255,255,.15);padding:6px 14px;border-radius:20px;font-size:11px;font-weight:700;cursor:pointer" onclick="show('cart');closeMenu()">VIEW CART</span></div><div class="lc" onclick="show('products');closeMenu()"><img src="/logo.png"></div><div style="font-weight:800;font-size:20px;margin-top:14px;position:relative;z-index:1">LONMA ORBIT</div><div style="margin-top:6px;opacity:.8;font-size:12px;position:relative;z-index:1">100% Genuine • Fast Delivery</div></div>
<div class="menu">
<div class="label">SHOP</div>
<div class="mi" onclick="show('products');closeMenu()"><div class="ico" style="background:#f0fdfa;color:#0A9EBB">🏠</div><b>Home • Products</b><span class="tag" style="background:var(--teal);color:#fff">NEW</span></div>
<div class="mi" onclick="show('cart');closeMenu()"><div class="ico" style="background:#fef3c7">🛒</div><b>Cart</b><span class="tag" style="background:#f1f5f9" id="mc">0</span></div>
<div class="mi" onclick="show('orders');closeMenu()"><div class="ico" style="background:#dbeafe">📦</div><b>Orders & Tracking</b></div>
<div class="div"></div>
<div class="label">SUPPORT</div>
<div class="mi" onclick="show('scan');closeMenu()"><div class="ico" style="background:#dcfce7">🛡️</div><b>Verify Product</b></div>
<div class="mi" onclick="show('account');closeMenu()"><div class="ico" style="background:#f1f5f9">👤</div><b>My Account</b></div>
<div class="mi" onclick="show('terms');closeMenu()"><div class="ico" style="background:#fef3c7">📄</div><b>Terms & Conditions</b></div>
<div class="div"></div>
<div class="mi" onclick="show('admin');closeMenu()" style="opacity:.6"><div class="ico" style="background:#0f172a;color:#fff">🔐</div><b>Admin</b></div>
<div style="text-align:center;padding:18px;color:#94a3b8;font-size:11px">v4.0 Clean • Made in Kenya 🇰🇪</div>
</div></div>

<div id="products" class="page active"><div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px"><h3 style="margin:0">Products</h3><span style="font-size:12px;color:#64748b" id="pCount">9 items</span></div><div id="plist"></div></div>

<div id="cart" class="page"><h3>Cart</h3><div id="cartItems"></div><div id="cartSum" style="display:none"><div class="card"><div style="display:flex;justify-content:space-between"><span>Subtotal (<span id="tItems">0</span>)</span><b>KSh <span id="sub">0</span></b></div><div style="display:flex;justify-content:space-between;margin-top:8px"><span>Delivery</span><b id="delFee"></b></div><div style="display:flex;justify-content:space-between;margin-top:12px;font-size:18px;border-top:1px solid #f1f5f9;padding-top:12px"><span>Total</span><b>KSh <span id="tot">0</span></b></div><div style="margin-top:16px"><input id="custName" placeholder="Full Name"><input id="phone" placeholder="M-Pesa Phone 07..."><select id="area"><option value="">Select Area</option><option value="CBD">CBD - 150</option><option value="Westlands">Westlands - 200</option><option value="Upcountry">Upcountry - 350</option></select><textarea id="loc" placeholder="Exact location / building"></textarea>
<label style="font-size:12px;display:flex;gap:8px;align-items:center;margin:12px 0"><input type="checkbox" id="agree" style="width:auto"> I agree to <a href="#" onclick="show('terms');return false" style="color:#0A9EBB;font-weight:800;text-decoration:underline">Terms</a></label>
</div><button class="btn" onclick="checkout()">Pay KSh <span id="pay">0</span> with M-Pesa</button><p id="ps" style="text-align:center;font-size:13px"></p></div></div><div id="emptyCart" class="card" style="text-align:center;padding:30px"><div style="font-size:40px">🛒</div><h4>Your cart is empty</h4><button class="btn btn-teal" onclick="show('products')">Start Shopping</button></div></div>

<div id="orders" class="page"><h3>Orders</h3><div style="display:flex;gap:8px;margin-bottom:12px"><input id="phLookup" placeholder="Enter phone 07..."><button class="btn" style="width:auto;padding:10px 20px" onclick="loadOrders()">Load</button></div><div id="olist"></div><div id="noOrd" class="card" style="text-align:center"><p>No orders yet</p></div></div>

<div id="scan" class="page"><h3>Verify Authenticity</h3><div class="card" style="padding:20px"><div style="text-align:center"><div style="font-size:40px">🛡️</div><h4>Check LONMA Product</h4><p style="font-size:12px;color:#64748b">Enter code like LONMA-001</p></div><input id="vcode" placeholder="LONMA-001"><button class="btn btn-teal" onclick="verify()">Verify Now</button><p id="vres" style="text-align:center;font-weight:700;margin-top:12px"></p></div></div>

<div id="account" class="page"><div id="out"><div class="card"><h4>Create Account</h4><input id="rn" placeholder="Full name"><input id="rp" placeholder="07xxxxxxxx"><input id="rpass" type="password" placeholder="Password"><button class="btn" onclick="register()">Create Account</button><p id="rs"></p></div><div class="card"><h4>Sign In</h4><input id="lp" placeholder="07xxxxxxxx"><input id="lpass" type="password" placeholder="Password"><button class="btn" style="background:var(--teal)" onclick="login()">Sign In</button><p id="ls"></p></div></div><div id="in" style="display:none"><div class="card" style="background:var(--dark);color:#fff;text-align:center;padding:24px"><h3 id="an" style="margin:12px 0 4px">Welcome</h3><p id="ap" style="opacity:.7;font-size:13px"></p><button class="btn" style="background:#fff;color:var(--dark);margin-top:16px" onclick="logout()">Sign Out</button></div></div></div>

<div id="terms" class="page"><h3>Terms & Conditions</h3><div class="card" style="line-height:1.7;font-size:13px;padding:18px"><h4 style="margin:6px 0">1. Delivery</h4><p>CBD KSh 150, Westlands KSh 200, Upcountry KSh 350. FREE delivery for orders KSh 2000+.</p><h4 style="margin:12px 0 6px">2. Payments</h4><p>All payments via M-Pesa STK Push to LONMA ORBIT. Order confirmed after M-Pesa receipt.</p><h4 style="margin:12px 0 6px">3. Authenticity</h4><p>All products 100% genuine LONMA. Verify using code on package (e.g. LONMA-001) on Verify Product page.</p><h4 style="margin:12px 0 6px">4. Returns</h4><p>Returns within 24hrs if product is unopened, unused and with receipt / order number.</p><h4 style="margin:12px 0 6px">5. Privacy</h4><p>We only use your phone and location for delivery. We do not share data.</p><h4 style="margin:12px 0 6px">6. Contact</h4><p>Email: support@lonmaorbit.co.ke</p><p style="margin-top:16px;font-size:11px;color:#94a3b8">LONMA ORBIT v4.0 • Made in Kenya 🇰🇪</p><button class="btn" style="margin-top:14px" onclick="show('cart')">Back to Cart</button></div></div>

<div id="admin" class="page"><h3>Admin</h3><div class="card"><input id="apass" type="password" placeholder="Password"><button class="btn" onclick="adminLogin()">Login</button><p id="ast"></p></div><div id="acont" style="display:none"><div id="alist"></div></div></div>
<div id="receipt" class="page"><div class="card" style="text-align:center;padding:24px" id="rcont"></div><button class="btn" onclick="show('products')">Continue Shopping</button></div>

<div class="bottom"><div id="b-products" class="active" onclick="show('products')">🏠<br>Home</div><div id="b-cart" onclick="show('cart')">🛒<br>Cart</div><div id="b-orders" onclick="show('orders')">📦<br>Orders</div><div id="b-account" onclick="show('account')">👤<br>Account</div></div>
<script>
let all=[],cart=[],myOrders=JSON.parse(localStorage.getItem('my_orders')||'[]');
try{let s=localStorage.getItem('lonma_cart');if(s)cart=JSON.parse(s);}catch(e){cart=[];}
function save(){localStorage.setItem('lonma_cart',JSON.stringify(cart));updateCount();}
function updateCount(){let c=0;for(let i of cart)c+=i.qty;let el=document.getElementById('cartCount');if(el){el.innerText=c;el.style.display=c>0?'flex':'none';}document.getElementById('mc').innerText=c;}
function openMenu(){document.getElementById('side').classList.add('open');document.getElementById('overlay').classList.add('open');}
function closeMenu(){document.getElementById('side').classList.remove('open');document.getElementById('overlay').classList.remove('open');}
function filterProducts(){let q=document.getElementById('searchInput').value.toLowerCase();let f=all.filter(p=>p.name.toLowerCase().includes(q));render(f);}
function render(list){let h='';for(let p of list){let inC=cart.find(c=>c.id===p.id);h+=`<div class="card" style="padding:12px"><div style="display:flex;gap:12px"><img src="${p.image}" style="width:80px;height:80px;border-radius:12px;flex-shrink:0"><div style="flex:1"><div style="font-weight:700;font-size:13px;line-height:1.3">${p.name}</div><div style="font-size:11px;color:#94a3b8;margin-top:4px">${p.category} • Stock ${p.stock}</div><div style="display:flex;justify-content:space-between;align-items:center;margin-top:8px"><b style="font-size:16px">KSh ${p.price}</b><button class="btn" style="width:auto;padding:8px 18px;border-radius:20px;font-size:12px" onclick="add(${p.id})">${inC?' +'+inC.qty:'Add'}</button></div></div></div></div>`;}document.getElementById('plist').innerHTML=h;document.getElementById('pCount').innerText=list.length+' items';}
function add(id){let p=all.find(x=>x.id===id);let f=cart.find(c=>c.id===id);if(f)f.qty++;else cart.push({id:p.id,name:p.name,price:p.price,image:p.image,qty:1});save();render(all.filter(x=>!document.getElementById('searchInput').value||x.name.toLowerCase().includes(document.getElementById('searchInput').value.toLowerCase())));}
function renderCart(){let cont=document.getElementById('cartItems'),sum=document.getElementById('cartSum'),empty=document.getElementById('emptyCart');if(cart.length===0){cont.innerHTML='';sum.style.display='none';empty.style.display='block';return;}empty.style.display='none';sum.style.display='block';let sub=0,items=0,html='';for(let it of cart){sub+=it.price*it.qty;items+=it.qty;html+=`<div class="card" style="display:flex;gap:12px"><img src="${it.image}" style="width:60px;height:60px;border-radius:12px"><div style="flex:1"><b style="font-size:13px">${it.name}</b><div style="display:flex;gap:8px;align-items:center;margin-top:6px"><button onclick="chg(${it.id},-1)" style="width:28px;height:28px;border-radius:50%;border:1px solid #e2e8f0;background:#fff">-</button><span>${it.qty}</span><button onclick="chg(${it.id},1)" style="width:28px;height:28px;border-radius:50%;border:1px solid #e2e8f0;background:#fff">+</button><span style="margin-left:auto;font-weight:800">KSh ${it.price*it.qty}</span></div></div></div>`;}cont.innerHTML=html;let area=document.getElementById('area').value;let del=area==='CBD'?150:area==='Upcountry'?350:200;if(sub>=2000)del=0;let tot=sub+del;document.getElementById('sub').innerText=sub;document.getElementById('tItems').innerText=items;document.getElementById('delFee').innerText=del==0?'FREE':'KSh '+del;document.getElementById('tot').innerText=tot;document.getElementById('pay').innerText=tot;}
function chg(id,d){let f=cart.find(c=>c.id===id);if(!f)return;f.qty+=d;if(f.qty<=0)cart=cart.filter(c=>c.id!==id);save();renderCart();}
function show(id){document.querySelectorAll('.page').forEach(p=>p.classList.remove('active'));document.getElementById(id).classList.add('active');document.querySelectorAll('.bottom div').forEach(b=>b.classList.remove('active'));let btn=document.getElementById('b-'+id);if(btn)btn.classList.add('active');if(id==='cart')renderCart();closeMenu();window.scrollTo(0,0);}
async function loadP(){let r=await fetch('/api/products');all=await r.json();render(all);}
async function verify(){let c=document.getElementById('vcode').value.trim();let r=await fetch('/api/verify/'+c);let d=await r.json();document.getElementById('vres').innerText=d.valid?'✅ Authentic: '+d.product.name:'❌ Invalid Code';}
async function checkout(){let name=document.getElementById('custName').value.trim(),phone=document.getElementById('phone').value.trim(),area=document.getElementById('area').value,loc=document.getElementById('loc').value.trim();if(!name||!phone||!area||!loc||!document.getElementById('agree').checked){document.getElementById('ps').innerText='Fill all fields + agree to Terms';return;}let sub=0;for(let i of cart)sub+=i.price*i.qty;let del=area==='CBD'?150:area==='Upcountry'?350:200;if(sub>=2000)del=0;let tot=sub+del;document.getElementById('ps').innerText='Sending M-Pesa prompt...';let r=await fetch('/mpesa/stkpush',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({phone,amount:tot,cart,name,area,location:loc})});let d=await r.json();document.getElementById('ps').innerText=d.message;if(d.status==='ok'){myOrders.unshift({order_no:d.order_no,total:tot,status:'Pending',created:new Date().toLocaleString()});localStorage.setItem('my_orders',JSON.stringify(myOrders));document.getElementById('rcont').innerHTML=`<div style="font-size:50px">✅</div><h3>${d.order_no}</h3><p>Total KSh ${tot}</p><p style="font-size:12px;color:#64748b">Check phone for M-Pesa prompt</p>`;cart=[];localStorage.removeItem('lonma_cart');save();show('receipt');}}
async function loadOrders(){let ph=document.getElementById('phLookup').value.trim();let r=await fetch('/api/orders?phone='+ph);let data=await r.json();document.getElementById('olist').innerHTML=data.map(o=>`<div class="card"><div style="display:flex;justify-content:space-between"><b>${o.order_no}</b><span style="background:#f1f5f9;padding:4px 10px;border-radius:20px;font-size:11px">${o.status}</span></div><div style="margin-top:6px">KSh ${o.total} • ${o.created}</div></div>`).join('');document.getElementById('noOrd').style.display=data.length?'none':'block';}
async function adminLogin(){let p=document.getElementById('apass').value;if(p!=='lonma2024'){document.getElementById('ast').innerText='Wrong';return;}document.getElementById('acont').style.display='block';let r=await fetch('/api/admin/orders');let d=await r.json();document.getElementById('alist').innerHTML=d.map(o=>`<div class="card"><b>${o.order_no}</b> ${o.phone} - KSh ${o.total} - ${o.status}</div>`).join('');}
async function register(){let name=document.getElementById('rn').value.trim(),phone=document.getElementById('rp').value.trim(),pass=document.getElementById('rpass').value.trim();let r=await fetch('/api/auth/register',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name,phone,password:pass})});let d=await r.json();document.getElementById('rs').innerText=d.status==='ok'?'Created':'Error';if(d.status==='ok'){localStorage.setItem('lonma_user',JSON.stringify(d.user));show('products');}}
async function login(){let phone=document.getElementById('lp').value.trim(),pass=document.getElementById('lpass').value.trim();let r=await fetch('/api/auth/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({phone,password:pass})});let d=await r.json();document.getElementById('ls').innerText=d.status==='ok'?'Welcome':'Wrong';if(d.status==='ok'){localStorage.setItem('lonma_user',JSON.stringify(d.user));show('products');}}
function logout(){localStorage.removeItem('lonma_user');show('account');}
document.getElementById('area')?.addEventListener('change',renderCart);
loadP();updateCount();
</script></body></html>
"""

@app.api_route("/",methods=["GET","HEAD"])
def home(): return HTMLResponse(HTML)
@app.get("/logo.png")
def logo():
    for f in ["logo.png","static/logo.png","./logo.png"]:
        if os.path.exists(f): return FileResponse(f)
    return HTMLResponse("",200)
