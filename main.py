import json, hashlib, time, os, urllib.parse
from fastapi import FastAPI, Form, Cookie, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from datetime import datetime

app = FastAPI()
USERS = {}
ORDERS = []
PRODUCTS = [
    {"id":1,"name":"Unga Jogoo 2kg","price":180,"cat":"Flour","img":"🌾","stock":50,"real":"Unga wa Dola"},
    {"id":2,"name":"Milk 500ml","price":70,"cat":"Dairy","img":"🥛","stock":100,"real":"Brookside"},
    {"id":3,"name":"Bread 400g","price":65,"cat":"Bakery","img":"🍞","stock":30,"real":"Supa Loaf"},
    {"id":4,"name":"Oil 1L","price":320,"cat":"Cooking","img":"🫒","stock":40,"real":"Elianto"},
    {"id":5,"name":"Sugar 2kg","price":310,"cat":"Sugar","img":"🍬","stock":60,"real":"Kabras"},
    {"id":6,"name":"Rice 2kg","price":420,"cat":"Rice","img":"🍚","stock":25,"real":"Pishori"},
]
ADMIN_PASS = "lonma2026"

def hash_pw(p):
    return hashlib.sha256(p.encode()).hexdigest()

def get_user(email=None):
    if email and email in USERS:
        return USERS[email]
    return None

def layout(body, title="LONMA"):
    return "<html><head><meta name='viewport' content='width=device-width,initial-scale=1'><title>"+title+"</title><style>body{margin:0;font-family:system-ui;background:#f5f7f8}header{background:#0096B2;color:#fff;padding:10px 16px;display:flex;justify-content:space-between;position:sticky;top:0;z-index:10}a{color:#fff;text-decoration:none;margin:0 6px}.grid{display:grid;grid-template-columns:1fr 1fr;gap:12px;padding:15px 15px 90px}.card{background:#fff;padding:14px;border-radius:16px;text-align:center}button{background:#0096B2;color:#fff;border:0;padding:11px;border-radius:10px;width:100%;font-weight:700}input,select{width:100%;padding:12px;margin:8px 0;border-radius:10px;border:1px solid #ddd}.form{max-width:600px;margin:20px auto;background:#fff;padding:24px;border-radius:20px}table{width:100%;border-collapse:collapse}th,td{padding:8px;border-bottom:1px solid #eee;font-size:13px}</style></head><body><header><div style='background:#fff;color:#0096B2;padding:4px 10px;border-radius:10px;font-weight:900'>LONMA ORBIT</div><div><a href='/'>Shop</a><a href='/scan'>Scan</a><a href='/video'>Video</a><a href='/terms'>Terms</a><a href='/admin'>Admin</a></div></header>"+body+"</body></html>"

@app.api_route("/", methods=["GET","HEAD"], response_class=HTMLResponse)
async def home(user_email: str = Cookie(default=None)):
    u = get_user(user_email)
    prod_json = json.dumps(PRODUCTS)
    phone = u["phone"] if u else ""
    body = """
<div style='padding:12px;display:flex;gap:8px'><input id='s' placeholder='Search...' onkeyup='filterProd()' style='flex:1'><select id='cat' onchange='filterProd()'><option value='all'>All</option><option>Flour</option><option>Dairy</option><option>Bakery</option><option>Cooking</option></select></div>
<div style='padding:0 12px;display:flex;gap:8px'><a href='/scan' style='flex:1;background:#111;color:#fff;padding:10px;text-align:center;border-radius:10px;text-decoration:none'>Scan QR</a><a href='/video' style='flex:1;background:#0096B2;color:#fff;padding:10px;text-align:center;border-radius:10px;text-decoration:none'>Video Support</a></div>
<div class='grid' id='g'></div>
<div style='position:fixed;bottom:0;left:0;right:0;background:#111;color:#fff;padding:12px 18px;display:flex;justify-content:space-between'><div><span id='cc'>0</span> items - <b id='ct'>KSh 0</b></div><button style='width:auto;background:#fff;color:#111' onclick='openCK()'>Checkout QR</button></div>
<div id='ck' style='display:none;position:fixed;inset:0;background:#fff;padding:20px;z-index:20;overflow:auto'><h2>Checkout QR + M-Pesa</h2><div id='list'></div><h3 id='tt'></h3><div id='qrBox'></div><form method='post' action='/order'><input type='hidden' name='cart_data' id='cd'><input name='phone' value='PHONEX' required><input name='location' placeholder='Estate' required><button>Place Order STK</button><button type='button' onclick="document.getElementById('ck').style.display='none'" style='background:#eee;color:#333;margin-top:10px'>Back</button></form></div>
<script>
var P = JSONDATA;
var cart = JSON.parse(localStorage.getItem('lonma_cart')||'[]');
function qr(t){return 'https://api.qrserver.com/v1/create-qr-code/?size=100x100&data='+encodeURIComponent(t);}
function render(){var h='';for(var i=0;i<P.length;i++){var p=P[i];h+='<div class=card><div style=font-size:32px>'+p.img+'</div><h4>'+p.name+'</h4><small>'+p.real+'</small><br><b>KSh '+p.price+'</b><br><img src="'+qr(p.id+'|'+p.name)+'" style=width:70px;margin:5px><br><button onclick=add('+p.id+')>Add</button></div>';}document.getElementById('g').innerHTML=h;upd();}
function add(id){var pr=null;for(var i=0;i<P.length;i++)if(P[i].id==id)pr=P[i];cart.push(pr);localStorage.setItem('lonma_cart',JSON.stringify(cart));upd();}
function upd(){document.getElementById('cc').innerText=cart.length;var t=0;for(var i=0;i<cart.length;i++)t+=cart[i].price;document.getElementById('ct').innerText='KSh '+t;document.getElementById('tt').innerText='Total KSh '+t;document.getElementById('cd').value=JSON.stringify(cart);var l='';for(var i=0;i<cart.length;i++)l+='<p>'+cart[i].name+' - '+cart[i].price+'</p>';document.getElementById('list').innerHTML=l;if(t>0)document.getElementById('qrBox').innerHTML='<img src="'+qr('LONMA|'+t+'|'+Date.now())+'" style=width:150px>';}
function openCK(){if(cart.length==0){alert('Empty');return;}document.getElementById('ck').style.display='block';}
function filterProd(){var q=document.getElementById('s').value.toLowerCase();var cat=document.getElementById('cat').value;var cards=document.querySelectorAll('.card');for(var i=0;i<cards.length;i++){var p=P[i];var ok=p.name.toLowerCase().indexOf(q)>=0 || p.real.toLowerCase().indexOf(q)>=0;if(cat!='all')ok=ok&&p.cat==cat;cards[i].style.display=ok?'block':'none';}}
var params=new URLSearchParams(window.location.search);var addId=params.get('add');if(addId){var pr=null;for(var i=0;i<P.length;i++)if(P[i].id==parseInt(addId))pr=P[i];if(pr){cart.push(pr);localStorage.setItem('lonma_cart',JSON.stringify(cart));alert(pr.name+' added from QR');}}
render();
</script>
""".replace("JSONDATA", prod_json).replace("PHONEX", phone)
    return HTMLResponse(layout(body, "LONMA MART"))

@app.get("/terms", response_class=HTMLResponse)
async def terms():
    b = "<div class='form'><h1>Terms - LONMA MART</h1><h3>Real Products</h3><p>Jogoo, Brookside, Supa Loaf, Elianto, Kabras, Pishori - real Kenyan brands.</p><h3>M-Pesa</h3><p>STK push on checkout. Delivery 2h Thika.</p><h3>QR</h3><p>Each product QR. Scan to add. Receipt QR for rider.</p><h3>Scan</h3><p>/scan camera scan.</p><h3>Video</h3><p>/video Jitsi support.</p><p>Contact support@lonmaorbit.co.ke</p><a href='/'><button>Back</button></a></div>"
    return HTMLResponse(layout(b, "Terms"))

@app.get("/scan", response_class=HTMLResponse)
async def scan():
    b = "<div class='form' style='text-align:center'><h1>Scan QR</h1><p>Point camera at product QR</p><div id='reader' style='width:100%'></div><div id='res' style='margin-top:15px;padding:12px;background:#e6f9fc;display:none'></div><a href='/'><button>Back</button></a></div><script src='https://unpkg.com/html5-qrcode@2.3.8/html5-qrcode.min.js'></script><script>function onOK(txt){document.getElementById('res').style.display='block';document.getElementById('res').innerHTML='Scanned: '+txt+'<br><a href=/?add='+txt.split('|')[0]+'><button>Add</button></a>';var id=parseInt(txt.split('|')[0]);if(!isNaN(id))window.location.href='/?add='+id;}var sc=new Html5QrcodeScanner('reader',{fps:10,qrbox:{width:250,height:250}},false);sc.render(onOK);</script>"
    return HTMLResponse(layout(b, "Scan"))

@app.get("/video", response_class=HTMLResponse)
async def video():
    b = "<div class='form' style='max-width:900px'><h1>Video Support</h1><div style='background:#000;border-radius:16px;overflow:hidden;height:500px'><iframe src='https://meet.jit.si/lonmaorbit-support' allow='camera; microphone; fullscreen' style='width:100%;height:100%;border:0'></iframe></div><a href='/'><button style='margin-top:15px'>Back</button></a></div>"
    return HTMLResponse(layout(b, "Video"))

@app.get("/login", response_class=HTMLResponse)
async def lp(): return HTMLResponse(layout("<div class='form'><h2>Sign In</h2><form method='post' action='/login'><input name='email' type='email' required><input name='password' type='password' required><button>Sign In</button></form><a href='/register'>Create</a></div>"))
@app.post("/login")
async def lg(email: str = Form(...), password: str = Form(...)):
    if email in USERS and USERS[email]["password"]==hash_pw(password):
        r=RedirectResponse("/",303);r.set_cookie("user_email",email,max_age=2592000);return r
    return HTMLResponse(layout("<div class='form'><h3>Wrong</h3></div>"))
@app.get("/register", response_class=HTMLResponse)
async def rp(): return HTMLResponse(layout("<div class='form'><h2>Create</h2><form method='post' action='/register'><input name='name' required><input name='email' type='email' required><input name='phone' required><input name='password' type='password' required><button>Create</button></form></div>"))
@app.post("/register")
async def rg(name: str = Form(...), email: str = Form(...), phone: str = Form(...), password: str = Form(...)):
    USERS[email]={"name":name,"phone":phone,"password":hash_pw(password)};r=RedirectResponse("/",303);r.set_cookie("user_email",email,max_age=2592000);return r
@app.get("/logout")
async def lo(): r=RedirectResponse("/",303);r.delete_cookie("user_email");r.delete_cookie("admin_auth");return r

@app.post("/order")
async def order(phone: str = Form(...), location: str = Form(...), cart_data: str = Form(...), user_email: str = Cookie(default=None)):
    cart=json.loads(cart_data);total=sum(i["price"] for i in cart)
    oid="LO"+str(int(time.time()))
    ORDERS.append({"id":oid,"time":datetime.now().strftime("%Y-%m-%d %H:%M"),"user":user_email or "Guest","phone":phone,"location":location,"items":cart,"total":total})
    qr="https://api.qrserver.com/v1/create-qr-code/?size=200x200&data="+urllib.parse.quote("LONMA "+oid+" KSh "+str(total))
    return HTMLResponse(layout(f"<div class='form' style='text-align:center'><h1>Order {oid}</h1><p>KSh {total}</p><img src='{qr}' style='width:200px'><p>Show QR to rider</p><p>M-Pesa STK to {phone}</p><a href='/'><button>Continue</button></a><a href='/video'><button style='background:#111;margin-top:10px'>Video Support</button></a></div>"))

@app.get("/admin/login", response_class=HTMLResponse)
async def al(): return HTMLResponse(layout("<div class='form'><h2>Admin</h2><form method='post' action='/admin/login'><input name='password' type='password' placeholder='lonma2026' required><button>Login</button></form></div>"))
@app.post("/admin/login")
async def al2(password: str = Form(...)):
    if password==ADMIN_PASS:
        r=RedirectResponse("/admin",303);r.set_cookie("admin_auth","yes",max_age=86400);return r
    return HTMLResponse(layout("<div class='form'><h3>Wrong</h3></div>"))
@app.get("/admin", response_class=HTMLResponse)
async def admin(admin_auth: str = Cookie(default=None)):
    if admin_auth!="yes": return RedirectResponse("/admin/login")
    oh=""; 
    for o in reversed(ORDERS[-50:]):
        names=", ".join([i["name"] for i in o["items"]])
        oh+=f"<tr><td>{o['id']}<br><img src='https://api.qrserver.com/v1/create-qr-code/?size=50x50&data={o['id']}'></td><td>{o['time']}</td><td>{o['phone']}</td><td>{o['location']}</td><td>{names}</td><td>KSh {o['total']}</td><td><a href='/video' style='color:#0096B2'>Video</a></td></tr>"
    if not oh: oh="<tr><td colspan=7>No orders</td></tr>"
    ph="";
    for p in PRODUCTS:
        ph+=f"<tr><td>{p['img']} {p['name']}<br><small>{p['real']}</small><br><img src='https://api.qrserver.com/v1/create-qr-code/?size=40x40&data={p['id']}'></td><td>KSh {p['price']}</td><td>{p['cat']}</td><td>{p['stock']}</td><td><form method='post' action='/admin/delete-product'><input type='hidden' name='pid' value='{p['id']}'><button style='width:auto;background:red;padding:4px 8px'>Del</button></form></td></tr>"
    body = f"<div style='max-width:1100px;margin:20px auto;padding:0 16px'><h1>Admin + QR + Video</h1><div style='display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px'><div style='background:#fff;padding:16px;border-radius:12px'><h3>{len(ORDERS)}</h3><p>Orders</p></div><div style='background:#fff;padding:16px;border-radius:12px'><h3>KSh {sum(o['total'] for o in ORDERS)}</h3><p>Revenue</p></div><div style='background:#fff;padding:16px;border-radius:12px'><h3>{len(PRODUCTS)}</h3><p>Products</p></div></div><h2>Add Real Product</h2><div class='form' style='margin:10px 0'><form method='post' action='/admin/add-product'><input name='name' placeholder='Name' required><input name='real' placeholder='Real Brand' required><input name='price' type='number' required><input name='cat' placeholder='Category' required><input name='img' placeholder='Emoji' required><input name='stock' type='number' required><button>Add</button></form></div><h2>Products with QR</h2><div style='background:#fff;padding:12px;border-radius:12px;overflow:auto'><table><tr><th>Product+QR</th><th>Price</th><th>Cat</th><th>Stock</th><th>Action</th></tr>{ph}</table></div><h2>Orders with QR + Video</h2><div style='background:#fff;padding:12px;border-radius:12px;overflow:auto'><table><tr><th>ID+QR</th><th>Time</th><th>Phone</th><th>Loc</th><th>Items</th><th>Total</th><th>Video</th></tr>{oh}</table></div><div style='display:flex;gap:10px;margin-top:20px'><a href='/scan' style='flex:1'><button>Scan</button></a><a href='/video' style='flex:1'><button style='background:#111'>Video</button></a><a href='/terms' style='flex:1'><button style='background:#eee;color:#333'>Terms</button></a></div></div>"
    return HTMLResponse(layout(body,"Admin"))
@app.post("/admin/add-product")
async def addp(name: str = Form(...), real: str = Form(...), price: int = Form(...), cat: str = Form(...), img: str = Form(...), stock: int = Form(...), admin_auth: str = Cookie(default=None)):
    if admin_auth!="yes": return RedirectResponse("/admin/login")
    nid=max([p["id"] for p in PRODUCTS], default=0)+1
    PRODUCTS.append({"id":nid,"name":name,"real":real,"price":price,"cat":cat,"img":img,"stock":stock})
    return RedirectResponse("/admin",303)
@app.post("/admin/delete-product")
async def delp(pid: int = Form(...), admin_auth: str = Cookie(default=None)):
    if admin_auth!="yes": return RedirectResponse("/admin/login")
    global PRODUCTS
    PRODUCTS=[p for p in PRODUCTS if p["id"]!=pid]
    return RedirectResponse("/admin",303)
@app.post("/mpesa/callback")
async def cb(request: Request):
    data=await request.json()
    print(data)
    return {"ResultCode":0}
