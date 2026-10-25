from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, FileResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
import os, sqlite3, urllib.parse, json, datetime

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

conn = sqlite3.connect("lonma.db", check_same_thread=False)
conn.execute("CREATE TABLE IF NOT EXISTS users (email TEXT UNIQUE, password TEXT, name TEXT)")
conn.execute("CREATE TABLE IF NOT EXISTS products (id INTEGER PRIMARY KEY, name TEXT, price INTEGER, code TEXT, image TEXT, category TEXT, stock INTEGER, desc TEXT)")
conn.execute("CREATE TABLE IF NOT EXISTS orders (id INTEGER PRIMARY KEY AUTOINCREMENT, order_no TEXT, name TEXT, phone TEXT, area TEXT, location TEXT, items TEXT, subtotal INTEGER, delivery INTEGER, total INTEGER, status TEXT, created TEXT)")
cur = conn.cursor()
cur.execute("DELETE FROM products")
PRODUCTS = [
    (1, "Fresh Fri Cooking Oil 2L", 850, "LONMA-001", "Cooking Oils", 50, "Pure fortified oil"),
    (2, "Detrex Citronella Soap 110g", 90, "LONMA-002", "Soaps", 120, "Germ protection"),
    (3, "Sawa Men Lotion 72Hrs", 299, "LONMA-003", "Lotions", 35, "72Hrs hydration"),
    (4, "Detrex Pine Drops Soap 110g", 90, "LONMA-004", "Soaps", 100, "Pine fresh"),
    (5, "Salit Vegetable Oil 5L", 1250, "LONMA-005", "Cooking Oils", 25, "5L family pack"),
    (6, "Detrex Cool Mint Soap 110g", 90, "LONMA-006", "Soaps", 80, "Cool mint"),
    (7, "Diva Anti-Dandruff Pomade 250ml", 250, "LONMA-007", "Pomades", 40, "Anti-dandruff"),
    (8, "Diva Anti-Breakage Pomade", 250, "LONMA-008", "Pomades", 45, "Anti-breakage"),
    (9, "Sawa Cocoa Butter Lotion", 299, "LONMA-009", "Lotions", 30, "Cocoa butter"),
]
for pid, name, price, code, cat, stock, desc in PRODUCTS:
    img = f"https://via.placeholder.com/400x300/FFFFFF/0A9EBB?text={urllib.parse.quote(name)}"
    cur.execute("INSERT INTO products VALUES (?,?,?,?,?,?,?,?)", (pid, name, price, code, img, cat, stock, desc))
conn.commit()

HTML = """<!DOCTYPE html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>LONMA ORBIT</title><style>
:root{--teal:#0A9EBB}*{box-sizing:border-box}body{margin:0;font-family:Arial;background:#f0f9fb}
.nav{position:fixed;top:0;width:100%;background:var(--teal);z-index:1000}
.nav-top{padding:8px 12px;display:flex;justify-content:space-between;align-items:center;height:64px}
.logo-box{background:#fff;padding:6px 12px;border-radius:12px;display:flex;align-items:center;height:50px;min-width:160px;box-shadow:0 2px 8px rgba(0,0,0,.15)}
.logo-box img{height:38px;width:150px;object-fit:contain;display:block}
.search-bar-wrap{padding:0 12px 14px;background:var(--teal)}
.search-app-bar{background:#fff;border-radius:16px;padding:0 16px;height:54px;display:flex;align-items:center;gap:12px;box-shadow:0 4px 12px rgba(0,0,0,.15)}
.hamburger{color:var(--teal);font-size:28px;font-weight:bold;cursor:pointer}
.search-app-bar input{border:none;outline:none;flex:1;font-size:16px;background:transparent}
.cart-icon{position:relative;background:#fff;color:var(--teal);padding:9px 16px;border-radius:25px;font-weight:bold;cursor:pointer}
.cart-count{position:absolute;top:-8px;right:-8px;background:#ff3b30;color:#fff;border-radius:50%;width:20px;height:20px;display:flex;align-items:center;justify-content:center;font-size:11px}
.page{display:none;padding:132px 10px 90px;min-height:100vh;background:#f0f9fb}.page.active{display:block}
.card{background:#fff;border-radius:16px;padding:12px;margin:8px 0;box-shadow:0 2px 8px rgba(0,0,0,.08);position:relative}
.card img{width:100%;height:190px;object-fit:contain;background:#fff;border-radius:12px;padding:8px}
.btn{background:var(--teal);color:#fff;border:none;padding:12px;border-radius:25px;width:100%;font-weight:bold;cursor:pointer}
input,select,textarea{width:100%;padding:12px;border-radius:10px;border:1px solid #ddd;margin:5px 0}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:8px}
.bottom{position:fixed;bottom:0;width:100%;background:#fff;display:flex;justify-content:space-around;padding:6px 0;border-top:1px solid #eee;z-index:1000}.bottom div{font-size:10px;color:#777;text-align:center;cursor:pointer;flex:1}.bottom div.active{color:var(--teal);font-weight:bold}
.chips{display:flex;gap:6px;overflow-x:auto;padding:8px 0}.chip{white-space:nowrap;background:#fff;border:1px solid #0A9EBB;color:#0A9EBB;padding:7px 14px;border-radius:20px;font-size:12px;cursor:pointer}.chip.active{background:#0A9EBB;color:#fff}
.qty-controls{display:flex;align-items:center;justify-content:space-between;background:#eef9fb;border-radius:25px;padding:5px 8px;margin-top:8px}
.qty-btn{background:var(--teal);color:#fff;border:none;width:30px;height:30px;border-radius:50%;font-weight:bold;cursor:pointer}
.side-menu{position:fixed;top:0;left:-280px;width:280px;height:100%;background:#fff;z-index:2000;transition:.3s;box-shadow:2px 0 12px rgba(0,0,0,.2)}.side-menu.open{left:0}.overlay{display:none;position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,.5);z-index:1999}.overlay.open{display:block}
.modal{display:none;position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,.6);z-index:2000;align-items:center;justify-content:center;padding:12px}.modal.open{display:flex}.modal-box{background:#fff;border-radius:16px;max-width:420px;width:100%;max-height:92vh;overflow-y:auto}
</style></head><body>
<div class="nav"><div class="nav-top"><div class="logo-box"><img src="/logo.png" onerror="this.src='https://via.placeholder.com/300x80/FFFFFF/0A9EBB?text=LONMA+ORBIT'" alt="LONMA"></div><div class="cart-icon" onclick="show('cart')">🛒 CART <span id="cartCount" class="cart-count" style="display:none">0</span></div></div><div class="search-bar-wrap"><div class="search-app-bar"><span class="hamburger" onclick="openSideMenu()">☰</span><input id="searchInput" placeholder="Search App" oninput="filterProducts()"><span style="color:#999">🔍</span></div></div></div>
<div class="overlay" id="overlay" onclick="closeSideMenu()"></div><div class="side-menu" id="sideMenu"><div style="background:var(--teal);color:#fff;padding:20px"><h3 style="margin:0">LONMA ORBIT</h3></div><div style="padding:12px"><div style="padding:14px;border-bottom:1px solid #eee" onclick="show('products');closeSideMenu()">🛍️ Products</div><div style="padding:14px;border-bottom:1px solid #eee" onclick="show('cart');closeSideMenu()">🛒 Cart (<span id="sideCartCount">0</span>)</div><div style="padding:14px;border-bottom:1px solid #eee" onclick="show('orders');closeSideMenu()">📦 Orders</div><div style="padding:14px;border-bottom:1px solid #eee" onclick="show('scan');closeSideMenu()">📷 Verify</div><div style="padding:14px" onclick="show('admin');closeSideMenu()">🔐 Admin</div></div></div>
<div id="products" class="page active"><div class="chips"><span class="chip active" onclick="filterCat('All',this)">All</span><span class="chip" onclick="filterCat('Cooking Oils',this)">Oils</span><span class="chip" onclick="filterCat('Soaps',this)">Soaps</span><span class="chip" onclick="filterCat('Lotions',this)">Lotions</span><span class="chip" onclick="filterCat('Pomades',this)">Pomades</span></div><div class="grid" id="plist"></div></div>
<div id="cart" class="page"><h2>Cart</h2><div id="cartItems"></div><div class="card" id="cartSummary" style="display:none"><p>Subtotal KSh <span id="subTotal">0</span> (<span id="totalItems">0</span>)</p><p>Delivery <span id="deliveryFee"></span></p><p style="font-weight:bold;color:#0A9EBB;font-size:18px">Total KSh <span id="totalPrice">0</span></p><p id="freeDeliveryMsg" style="background:#e8f5e9;padding:8px;border-radius:8px;font-size:11px"></p><input id="custName" placeholder="Full Name *"><input id="phone" placeholder="07xx *"><select id="locationArea"><option value="">Select Area *</option><option value="CBD">CBD 150</option><option value="Westlands">Westlands 200</option><option value="Upcountry">Upcountry 350</option></select><textarea id="exactLocation" placeholder="Location *"></textarea><label style="font-size:12px"><input type="checkbox" id="agreeTerms" style="width:auto"> Agree</label><button class="btn" style="background:#111;margin-top:8px" onclick="checkout()">PAY KSh <span id="payTotal">0</span></button><button class="btn" style="background:#25D366;margin-top:6px" onclick="orderWhatsApp()">WHATSAPP</button><p id="paystatus"></p><button class="btn" style="background:#666;margin-top:8px" onclick="clearCart()">Clear</button></div><div class="card" id="emptyCart" style="text-align:center"><h3>Empty</h3><button class="btn" onclick="show('products')">Shop</button></div></div>
<div id="orders" class="page"><h2>Orders</h2><div id="ordersList"></div><div class="card" id="noOrders" style="text-align:center"><h3>No orders</h3></div></div>
<div id="scan" class="page"><h2>Verify</h2><div class="card"><input id="manualcode" placeholder="LONMA-001"><button class="btn" onclick="verifyCode()">VERIFY</button><p id="scanresult"></p></div></div>
<div id="admin" class="page"><h2>Admin</h2><div class="card"><input id="adminPass" type="password" placeholder="lonma2024"><button class="btn" onclick="adminLogin()">Login</button><p id="adminStatus"></p></div><div id="adminContent" style="display:none"><div class="card"><p>Orders: <span id="statOrders">0</span> Sales <span id="statSales">0</span></p><button class="btn" onclick="loadAdminOrders()">Refresh</button></div><div id="adminOrdersList"></div></div></div>
<div id="receipt" class="page"><h2>Receipt</h2><div class="card" id="receiptContent"></div><button class="btn" onclick="show('products')">Continue</button></div>
<div id="login" class="page"><h2>Account</h2><div class="card"><input id="lemail" placeholder="Email"><input id="lpass" type="password" placeholder="Pass"><button class="btn" onclick="login()">Login</button><p id="lstatus"></p></div></div>
<div id="locations" class="page"><h2>Stores</h2><div class="card"><p>Moi Ave</p></div></div>
<div id="terms" class="page"><h2>Terms</h2><div class="card"><p>Free delivery over 2000</p></div></div>
<div class="bottom"><div id="b-products" class="active" onclick="show('products')">🛍️<br>Products</div><div id="b-cart" onclick="show('cart')">🛒<br>Cart (<span id="bottomCartCount">0</span>)</div><div id="b-orders" onclick="show('orders')">📦<br>Orders</div><div id="b-scan" onclick="show('scan')">📷<br>Verify</div><div id="b-login" onclick="show('login')">👤<br>Account</div></div>
<div id="productModal" class="modal" onclick="if(event.target===this)closeModal()"><div class="modal-box"><div id="modalContent"></div></div></div>
<script>
let rawCart=localStorage.getItem('lonma_cart'); if(rawCart&&rawCart.includes('undefined')){localStorage.removeItem('lonma_cart');}
let allProducts=[],currentCat='All',searchQuery='',cart=[],myOrders=JSON.parse(localStorage.getItem('my_orders')||'[]');
try{let s=localStorage.getItem('lonma_cart'); if(s){cart=JSON.parse(s); cart=cart.filter(c=>c&&c.image&&!String(c.image).includes('undefined'));} if(!Array.isArray(cart))cart=[];}catch(e){cart=[]; localStorage.removeItem('lonma_cart');}
function safeImage(name){return`https://via.placeholder.com/400x300/FFFFFF/0A9EBB?text=${encodeURIComponent(name)}`;}
function saveCart(){localStorage.setItem('lonma_cart',JSON.stringify(cart));updateCartCount();}
function updateCartCount(){let c=0;for(let i of cart)c+=Number(i.qty)||0;document.getElementById('cartCount').innerText=c;document.getElementById('bottomCartCount').innerText=c;let side=document.getElementById('sideCartCount');if(side)side.innerText=c;document.getElementById('cartCount').style.display=c>0?'flex':'none';}
function openSideMenu(){document.getElementById('sideMenu').classList.add('open');document.getElementById('overlay').classList.add('open');}
function closeSideMenu(){document.getElementById('sideMenu').classList.remove('open');document.getElementById('overlay').classList.remove('open');}
function filterCat(cat,el){currentCat=cat;document.querySelectorAll('.chip').forEach(ch=>ch.classList.remove('active'));if(el)el.classList.add('active');renderProducts();}
function filterProducts(){searchQuery=document.getElementById('searchInput').value.toLowerCase();renderProducts();}
function renderProducts(){
let list=allProducts.filter(p=>{let mCat=currentCat==='All'||p.category===currentCat;let mSearch=!searchQuery||p.name.toLowerCase().includes(searchQuery)||p.category.toLowerCase().includes(searchQuery);return mCat&&mSearch;});
let html='';for(let p of list){let inCart=cart.find(c=>c.id===p.id);let qtyText=inCart?`In cart: ${inCart.qty}`:'';let img=p.image&&!String(p.image).includes('undefined')?p.image:safeImage(p.name);html+=`<div class="card"><img src="${img}" onclick="openModal(${p.id})"><span style="background:#e0f7fa;color:#0A9EBB;padding:2px 8px;border-radius:10px;font-size:10px">${p.category}</span><h4 style="font-size:12px;margin:6px 0">${p.name}</h4><p style="margin:0;font-weight:bold;color:#0A9EBB">KSh ${p.price}</p><button class="btn" onclick="addToCart(${p.id})">🛒 ADD TO CART</button><div style="font-size:11px;color:#0A9EBB;text-align:center;font-weight:bold">${qtyText}</div></div>`;}
document.getElementById('plist').innerHTML=html;
}
function openModal(id){let p=allProducts.find(x=>x.id===id);if(!p)return;let img=p.image&&!String(p.image).includes('undefined')?p.image:safeImage(p.name);document.getElementById('modalContent').innerHTML=`<img src="${img}" style="width:100%;height:260px;object-fit:contain;padding:12px"><div style="padding:12px"><h3>${p.name}</h3><p style="color:#0A9EBB;font-weight:bold;font-size:20px">KSh ${p.price}</p><div style="display:flex;gap:8px"><button class="btn" style="flex:1" onclick="addToCart(${p.id});closeModal()">ADD</button><button class="btn" style="flex:1;background:#25D366" onclick="orderWhatsAppSingle(${p.id})">WHATSAPP</button></div><button class="btn" style="background:#fff;color:#0A9EBB;border:1px solid #0A9EBB;margin-top:8px" onclick="closeModal()">Close</button></div>`;document.getElementById('productModal').classList.add('open');}
function closeModal(){document.getElementById('productModal').classList.remove('open');}
function addToCart(id){let p=allProducts.find(x=>x.id===id);if(!p)return;let found=cart.find(c=>c.id===id);if(found){found.qty++;}else{cart.push({id:p.id,name:p.name,price:p.price,image:p.image,code:p.code,qty:1,stock:p.stock});}saveCart();renderCart();renderProducts();}
function changeQty(id,delta){for(let i=0;i<cart.length;i++)if(cart[i].id===id){cart[i].qty+=delta;if(cart[i].qty<=0)cart.splice(i,1);break;}saveCart();renderCart();renderProducts();}
function clearCart(){cart=[];localStorage.removeItem('lonma_cart');saveCart();renderCart();renderProducts();}
function renderCart(){
let cont=document.getElementById('cartItems'),sum=document.getElementById('cartSummary'),empty=document.getElementById('emptyCart');
if(cart.length===0){cont.innerHTML='';sum.style.display='none';empty.style.display='block';return;}
empty.style.display='none';sum.style.display='block';
let totalItems=0,subTotal=0,html='';for(let it of cart){totalItems+=it.qty;subTotal+=it.price*it.qty;let img=it.image&&!String(it.image).includes('undefined')?it.image:safeImage(it.name);html+=`<div class="card" style="display:flex;gap:10px"><img src="${img}" style="width:60px;height:60px;object-fit:contain"><div style="flex:1"><h4 style="margin:0;font-size:13px">${it.name}</h4><p>KSh ${it.price} x ${it.qty}</p><div class="qty-controls"><button class="qty-btn" onclick="changeQty(${it.id},-1)">-</button><span>${it.qty}</span><button class="qty-btn" onclick="changeQty(${it.id},1)">+</button></div></div></div>`;}
cont.innerHTML=html;let area=document.getElementById('locationArea').value;let delivery=area==='CBD'?150:area==='Upcountry'?350:200;if(subTotal>=2000)delivery=0;
document.getElementById('subTotal').innerText=subTotal;document.getElementById('totalItems').innerText=totalItems;document.getElementById('deliveryFee').innerText=delivery===0?'FREE':'KSh '+delivery;let total=subTotal+delivery;document.getElementById('totalPrice').innerText=total;document.getElementById('payTotal').innerText=total;document.getElementById('freeDeliveryMsg').innerHTML=subTotal>=2000?'FREE delivery!':`Add ${2000-subTotal} for FREE!`;
}
document.getElementById('locationArea')?.addEventListener('change',renderCart);
function show(id){document.querySelectorAll('.page').forEach(p=>p.classList.remove('active'));document.getElementById(id).classList.add('active');document.querySelectorAll('.bottom div').forEach(b=>b.classList.remove('active'));let btn=document.getElementById('b-'+id);if(btn)btn.classList.add('active');if(id==='cart')renderCart();if(id==='orders')renderOrders();closeSideMenu();window.scrollTo(0,0);}
async function loadProducts(){let r=await fetch('/api/products');let d=await r.json();allProducts=d.map(p=>({id:p.id,name:p.name,price:p.price,code:p.code,image:p.image,category:p.category,stock:p.stock,desc:p.desc}));renderProducts();}
async function verifyCode(){let c=document.getElementById('manualcode').value.trim().toUpperCase();let r=await fetch(`/api/verify/${c}`);let d=await r.json();document.getElementById('scanresult').innerHTML=d.valid?`✅ ${d.product.name} ORIGINAL`:`❌ Invalid`;}
async function login(){let r=await fetch('/api/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({email:document.getElementById('lemail').value,password:document.getElementById('lpass').value})});let d=await r.json();document.getElementById('lstatus').innerText=d.message;}
function orderWhatsApp(){let total=document.getElementById('totalPrice').innerText;let items=cart.map(c=>`${c.name} x${c.qty}`).join(', ');window.open(`https://wa.me/254700000000?text=${encodeURIComponent('Hi LONMA '+items+' KSh '+total)}`,'_blank');}
function orderWhatsAppSingle(id){let p=allProducts.find(x=>x.id===id);window.open(`https://wa.me/254700000000?text=${encodeURIComponent('Hi LONMA I want '+p.name)}`,'_blank');}
async function checkout(){let name=document.getElementById('custName').value.trim(),phone=document.getElementById('phone').value.trim(),area=document.getElementById('locationArea').value,loc=document.getElementById('exactLocation').value.trim(),agree=document.getElementById('agreeTerms').checked;if(!name||!phone||!area||!loc||!agree){document.getElementById('paystatus').innerText='Fill all *';return;}let sub=0;for(let i of cart)sub+=i.price*i.qty;let del=area==='CBD'?150:350;if(sub>=2000)del=0;let tot=sub+del;document.getElementById('paystatus').innerText=`Sending KSh ${tot}...`;let r=await fetch('/mpesa/stkpush',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({phone,amount:tot,cart,name,area,location:loc,subtotal:sub,delivery:del})});let d=await r.json();document.getElementById('paystatus').innerText=d.message;let orderNo='LONMA'+Date.now().toString().slice(-6);myOrders.unshift({order_no:orderNo,items:[...cart],total:tot,status:'Pending',created:new Date().toLocaleString()});localStorage.setItem('my_orders',JSON.stringify(myOrders));cart=[];localStorage.removeItem('lonma_cart');saveCart();setTimeout(()=>show('receipt'),800);}
function renderOrders(){let cont=document.getElementById('ordersList'),empty=document.getElementById('noOrders');if(myOrders.length===0){cont.innerHTML='';empty.style.display='block';return;}empty.style.display='none';let html='';for(let o of myOrders){html+=`<div class="card"><b>${o.order_no}</b> KSh ${o.total}</div>`;}cont.innerHTML=html;}
async function adminLogin(){let p=document.getElementById('adminPass').value;if(p!=='lonma2024'){document.getElementById('adminStatus').innerText='Wrong';return;}document.getElementById('adminContent').style.display='block';loadAdminOrders();}
async function loadAdminOrders(){let r=await fetch('/api/admin/orders');let d=await r.json();document.getElementById('statOrders').innerText=d.length;let sales=0;for(let o of d)sales+=o.total||0;document.getElementById('statSales').innerText=sales;let html='';for(let o of d){html+=`<div class="card"><b>${o.order_no}</b> KSh ${o.total}</div>`;}document.getElementById('adminOrdersList').innerHTML=html;}
loadProducts();updateCartCount();renderCart();renderOrders();
</script></body></html>
"""

@app.api_route("/", methods=["GET","HEAD"])
def home():
    return HTMLResponse(HTML)

@app.get("/logo.png")
def logo():
    for f in ["logo.png","static/logo.png"]:
        if os.path.exists(f):
            return FileResponse(f)
    return HTMLResponse("logo",404)

@app.get("/undefined")
def handle_undefined():
    return RedirectResponse("https://via.placeholder.com/400x300", status_code=302)

@app.get("/api/products")
def products():
    cur=conn.cursor()
    cur.execute("SELECT id,name,price,code,image,category,stock,desc FROM products")
    result=[]
    for r in cur.fetchall():
        img=r[4]
        if not img or "undefined" in str(img):
            img=f"https://via.placeholder.com/400x300/FFFFFF/0A9EBB?text={urllib.parse.quote(r[1])}"
        result.append({"id":r[0],"name":r[1],"price":r[2],"code":r[3],"image":img,"category":r[5],"stock":r[6],"desc":r[7]})
    return result

@app.get("/api/verify/{code}")
def verify(code: str):
    cur=conn.cursor()
    cur.execute("SELECT name FROM products WHERE code=?",(code.strip().upper(),))
    row=cur.fetchone()
    return {"valid":True,"product":{"name":row[0]}} if row else {"valid":False}

@app.get("/api/admin/orders")
def admin_orders():
    cur=conn.cursor()
    cur.execute("SELECT order_no,total FROM orders ORDER BY id DESC")
    return [{"order_no":r[0],"total":r[1]} for r in cur.fetchall()]

@app.post("/api/login")
async def login_api(req: Request):
    d=await req.json()
    cur=conn.cursor()
    cur.execute("SELECT * FROM users WHERE email=? AND password=?",(d.get("email"),d.get("password")))
    return {"status":"ok","message":"Welcome!"} if cur.fetchone() else {"status":"error","message":"Invalid"}

@app.post("/mpesa/stkpush")
async def stk(req: Request):
    d=await req.json()
    order_no='LONMA'+datetime.datetime.now().strftime("%H%M%S")
    items_text=json.dumps([f"{c.get('name')} x{c.get('qty')}" for c in d.get('cart',[])])
    try:
        conn.execute("INSERT INTO orders (order_no,name,phone,area,location,items,subtotal,delivery,total,status,created) VALUES (?,?,?,?,?,?,?,?,?,?,?)",(order_no,d.get('name'),d.get('phone'),d.get('area'),d.get('location'),items_text,d.get('subtotal',0),d.get('delivery',0),d.get('amount',0),'Pending',datetime.datetime.now().strftime("%Y-%m-%d %H:%M")))
        conn.commit()
    except:
        pass
    return {"message":f"STK KSh {d.get('amount')} sent to {d.get('phone')}"}
