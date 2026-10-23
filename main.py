import json, hashlib, time, os, base64, urllib.parse
from fastapi import FastAPI, Form, Cookie, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from datetime import datetime

app = FastAPI()
USERS = {}
ORDERS = []
PRODUCTS = [
    {"id":1,"name":"Unga Jogoo 2kg","price":180,"cat":"Flour","img":"🌾","stock":50,"real":"Unga wa Dola"},
    {"id":2,"name":"Fresh Milk 500ml","price":70,"cat":"Dairy","img":"🥛","stock":100,"real":"Brookside"},
    {"id":3,"name":"Bread 400g","price":65,"cat":"Bakery","img":"🍞","stock":30,"real":"Supa Loaf"},
    {"id":4,"name":"Elianto Oil 1L","price":320,"cat":"Cooking","img":"🫒","stock":40,"real":"Elianto"},
    {"id":5,"name":"Kabras Sugar 2kg","price":310,"cat":"Sugar","img":"🍬","stock":60,"real":"Kabras"},
    {"id":6,"name":"Pishori Rice 2kg","price":420,"cat":"Rice","img":"🍚","stock":25,"real":"Pishori"},
]
ADMIN_PASS = "lonma2026"

def hash_pw(p): return hashlib.sha256(p.encode()).hexdigest()
def get_user(email: str = Cookie(default=None)):
    return {"email":email,**USERS[email]} if email and email in USERS else None

def base_page(content, user=None, admin=False):
    nav = "<a href='/' style='color:#fff'>Shop</a> | <a href='/scan'>Scan</a> | <a href='/video'>Video</a> | <b>Admin</b>" if admin else "<a href='/scan'>Scan</a> <a href='/video'>Video</a> <a href='/terms'>Terms</a> | "
    if user and not admin:
        nav += f" {user['name'].split()[0]} | <a href='/admin'>Admin</a> | <a href='/logout'>Logout</a>"
    elif not admin:
        nav += "<a href='/login'>Sign In</a> | <a href='/admin/login'>Admin</a>"
    return f"<html><head><meta name='viewport' content='width=device-width,initial-scale=1'><title>LONMA</title><style>body{{margin:0;font-family:system-ui;background:#f5f7f8}}header{{background:#0096B2;color:#fff;padding:10px 16px;display:flex;justify-content:space-between;position:sticky;top:0}} .grid{{display:grid;grid-template-columns:1fr 1fr;gap:12px;padding:15px 15px 90px}} .card{{background:#fff;padding:14px;border-radius:16px;text-align:center}} button{{background:#0096B2;color:#fff;border:0;padding:11px;border-radius:10px;width:100%;font-weight:700}} input,select{{width:100%;padding:12px;margin:8px 0;border-radius:10px;border:1px solid #ddd}} .form{{max-width:600px;margin:20px auto;background:#fff;padding:24px;border-radius:20px}} table{{width:100%;border-collapse:collapse}} th,td{{padding:8px;border-bottom:1px solid #eee;font-size:13px}}</style></head><body><header><div style='background:#fff;color:#0096B2;padding:4px 10px;border-radius:10px;font-weight:900'>LONMA ORBIT</div><div>{nav}</div></header>{content}</body></html>"

@app.api_route("/", methods=["GET","HEAD"])
async def home(user_email: str = Cookie(default=None)):
    u = get_user(user_email)
    prod_json = json.dumps(PRODUCTS)
    phone_val = u['phone'] if u else ''
    html = """
    <div style='padding:12px;display:flex;gap:8px'><input id='s' placeholder='Search real products...' onkeyup='doFilter()' style='flex:1'><select id='cat' onchange='doFilter()'><option value='all'>All</option><option>Flour</option><option>Dairy</option><option>Bakery</option><option>Cooking</option><option>Sugar</option><option>Rice</option></select></div>
    <div style='padding:0 12px;display:flex;gap:8px'><a href='/scan' style='flex:1;background:#111;color:#fff;padding:10px;text-align:center;border-radius:10px;text-decoration:none'>Scan QR</a><a href='/video' style='flex:1;background:#0096B2;color:#fff;padding:10px;text-align:center;border-radius:10px;text-decoration:none'>Video Support</a></div>
    <div class='grid' id='g'></div>
    <div style='position:fixed;bottom:0;left:0;right:0;background:#111;color:#fff;padding:12px 18px;display:flex;justify-content:space-between;border-radius:18px 18px 0 0'><div><span id='cc'>0</span> items - <b id='ct'>KSh 0</b></div><button style='width:auto;background:#fff;color:#111' onclick='openCheckout()'>Checkout QR</button></div>
    <div id='ck' style='display:none;position:fixed;inset:0;background:#fff;padding:20px;z-index:20;overflow:auto'><h2>Checkout + M-Pesa + QR</h2><div id='list'></div><h3 id='tt'></h3><div id='qrBox' style='text-align:center'></div><form method='post' action='/order'><input type='hidden' name='cart_data' id='cd'><input name='phone' placeholder='07xx M-Pesa' value='PHONEVAL' required><input name='location' placeholder='Estate' required><button>Place Order - STK Push</button><button type='button' onclick="document.getElementById('ck').style.display='none'" style='background:#eee;color:#333;margin-top:10px'>Back</button></form></div>
    <script>
    const P = PRODJSON;
    let cart = JSON.parse(localStorage.getItem('lonma_cart')||'[]');
    function qrUrl(t){ return 'https://api.qrserver.com/v1/create-qr-code/?size=120x120&data='+encodeURIComponent(t); }
    function render(){
      let h=''; 
      for(let p of P){
        h+='<div class="card"><div style="font-size:32px">'+p.img+'</div><h4>'+p.name+'</h4><small>'+p.real+'</small><br><b style="color:#0096B2">KSh '+p.price+'</b><br><img src="'+qrUrl(p.id+'|'+p.name)+'" style="width:80px;margin:6px"/><br><button onclick="add('+p.id+')">Add</button></div>';
      }
      document.getElementById('g').innerHTML=h; update();
    }
    function add(id){ let pr=P.find(x=>x.id==id); cart.push(pr); localStorage.setItem('lonma_cart', JSON.stringify(cart)); update(); }
    function update(){
      document.getElementById('cc').innerText=cart.length;
      let t=0; for(let c of cart) t+=c.price;
      document.getElementById('ct').innerText='KSh '+t;
      document.getElementById('tt').innerText='Total KSh '+t;
      document.getElementById('cd').value=JSON.stringify(cart);
      let list=''; for(let c of cart) list+='<p>'+c.name+' - '+c.price+'</p>'; document.getElementById('list').innerHTML=list;
      if(t>0) document.getElementById('qrBox').innerHTML='<p>Order QR:</p><img src="'+qrUrl('LONMA|'+t+'|'+Date.now())+'" style="width:150px"/>';
    }
    function openCheckout(){ if(cart.length==0){alert('Empty');return;} document.getElementById('ck').style.display='block'; }
    function doFilter(){
      let q=document.getElementById('s').value.toLowerCase();
      let cat=document.getElementById('cat').value;
      let cards=document.querySelectorAll('.card');
      for(let i=0;i<cards.length;i++){
        let p=P[i];
        let ok = p.name.toLowerCase().includes(q) || p.real.toLowerCase().includes(q);
        if(cat!='all') ok = ok && p.cat==cat;
        cards[i].style.display= ok ? 'block':'none';
      }
    }
    let params=new URLSearchParams(window.location.search); let addId=params.get('add'); if(addId){ let pr=P.find(x=>x.id==parseInt(addId)); if(pr){ cart.push(pr); localStorage.setItem('lonma_cart', JSON.stringify(cart)); alert(pr.name+' added from QR!'); } }
    render();
    </script>
    """.replace("PRODJSON", prod_json).replace("PHONEVAL", phone_val)
    return HTMLResponse(base_page(html, u))

@app.get("/terms", response_class=HTMLResponse)
async def terms(user_email: str = Cookie(default=None)):
    u=get_user(user_email)
    c="<div class='form'><h1>Terms - LONMA MART</h1><h3>1. Real Products</h3><p>Jogoo, Brookside, Supa Loaf, Elianto, Kabras, Pishori - real Kenyan brands.</p><h3>2. M-Pesa STK</h3><p>STK push on checkout. Delivery 2h in Thika.</p><h3>3. QR Code</h3><p>Each product has QR. Scan to add to cart. Receipt QR for rider.</p><h3>4. Scan</h3><p>/scan uses camera to scan QR.</p><h3>5. Video Calls</h3><p>/video support via Jitsi video call.</p><h3>6. Privacy</h3><p>Data only for delivery.</p><p>Contact: support@lonmaorbit.co.ke</p><a href='/'><button>Back</button></a></div>"
    return HTMLResponse(base_page(c,u))

@app.get("/scan", response_class=HTMLResponse)
async def scan_page(user_email: str = Cookie(default=None)):
    u=get_user(user_email)
    c="""
    <div class='form' style='text-align:center'><h1>Scan Product QR</h1><p>Point camera at product QR</p>
    <div id='reader' style='width:100%'></div><div id='result' style='margin-top:15px;padding:12px;background:#e6f9fc;border-radius:12px;display:none'></div>
    <a href='/'><button>Back to Shop</button></a></div>
    <script src='https://unpkg.com/html5-qrcode@2.3.8/html5-qrcode.min.js'></script>
    <script>
    function onScanSuccess(text){
      document.getElementById('result').style.display='block';
      document.getElementById('result').innerHTML='Scanned: <b>'+text+'</b><br><a href="/?add='+text.split('|')[0]+'"><button>Add to Cart</button></a>';
      let id=parseInt(text.split('|')[0]); if(!isNaN(id)) window.location.href='/?add='+id;
    }
    var scanner=new Html5QrcodeScanner('reader',{fps:10,qrbox:{width:250,height:250}},false);
    scanner.render(onScanSuccess);
    </script>
    """
    return HTMLResponse(base_page(c,u))

@app.get("/video", response_class=HTMLResponse)
async def video_page(user_email: str = Cookie(default=None)):
    u=get_user(user_email)
    c="""
    <div class='form' style='max-width:900px'><h1>Video Support Call</h1><p>Talk to LONMA support live</p>
    <div style='display:flex;gap:10px;margin:10px 0'><a href='https://meet.jit.si/lonmaorbit-support' target='_blank' style='flex:1'><button>Jitsi Room</button></a></div>
    <div style='background:#000;border-radius:16px;overflow:hidden;height:500px'><iframe src='https://meet.jit.si/lonmaorbit-support#config.prejoinConfig.enabled=false' allow='camera; microphone; fullscreen; display-capture' style='width:100%;height:100%;border:0'></iframe></div>
    <a href='/'><button style='margin-top:15px'>Back</button></a></div>
    """
    return HTMLResponse(base_page(c,u))

@app.get("/login", response_class=HTMLResponse)
async def lp(): return HTMLResponse(base_page("<div class='form'><h2>Sign In</h2><form method='post' action='/login'><input name='email' type='email' required><input name='password' type='password' required><button>Sign In</button></form><p><a href='/register'>Create</a></p></div>"))
@app.post("/login")
async def lg(email: str = Form(...), password: str = Form(...)):
    if email in USERS and USERS[email]['password']==hash_pw(password):
        r=RedirectResponse("/",303); r.set_cookie("user_email",email,max_age=2592000); return r
    return HTMLResponse(base_page("<div class='form'><h3>Wrong</h3></div>"))
@app.get("/register", response_class=HTMLResponse)
async def rp(): return HTMLResponse(base_page("<div class='form'><h2>Create</h2><form method='post' action='/register'><input name='name' required placeholder='Name'><input name='email' type='email' required><input name='phone' required placeholder='07xx'><input name='password' type='password' required><button>Create</button></form></div>"))
@app.post("/register")
async def rg(name: str = Form(...), email: str = Form(...), phone: str = Form(...), password: str = Form(...)):
    USERS[email]={"name":name,"phone":phone,"password":hash_pw(password)}; r=RedirectResponse("/",303); r.set_cookie("user_email",email,max_age=2592000); return r
@app.get("/logout")
async def lo(): r=RedirectResponse("/",303); r.delete_cookie("user_email"); r.delete_cookie("admin_auth"); return r

@app.post("/order")
async def order(phone: str = Form(...), location: str = Form(...), cart_data: str = Form(...), user_email: str = Cookie(default=None)):
    cart=json.loads(cart_data); total=sum(i['price'] for i in cart)
    order_id=f"LO{int(time.time())}"
    ORDERS.append({"id":order_id,"time":datetime.now().strftime("%Y-%m-%d %H:%M"),"user":user_email or "Guest","phone":phone,"location":location,"items":cart,"total":total,"status":"Pending"})
    qr_data=f"LONMA {order_id} KSh {total}"
    qr_img=f"https://api.qrserver.com/v1/create-qr-code/?size=200x200&data={urllib.parse.quote(qr_data)}"
    return HTMLResponse(base_page(f"<div class='form' style='text-align:center'><h1>Order {order_id}</h1><p>KSh {total}</p><img src='{qr_img}' style='width:200px'/><p>Show QR to rider</p><p>M-Pesa STK to {phone}</p><a href='/'><button>Continue</button></a><div style='display:flex;gap:8px;margin-top:10px'><a href='/video' style='flex:1'><button style='background:#111'>Video Support</button></a><a href='/terms' style='flex:1'><button style='background:#eee;color:#333'>Terms</button></a></div></div>", get_user(user_email)))

@app.get("/admin/login", response_class=HTMLResponse)
async def admin_login_page(): return HTMLResponse(base_page("<div class='form'><h2>Admin</h2><form method='post' action='/admin/login'><input name='password' type='password' placeholder='lonma2026' required><button>Login</button></form></div>"))
@app.post("/admin/login")
async def admin_login(password: str = Form(...)):
    if password==ADMIN_PASS:
        r=RedirectResponse("/admin",303); r.set_cookie("admin_auth","yes",max_age=86400); return r
    return HTMLResponse(base_page("<div class='form'><h3>Wrong</h3></div>"))

@app.get("/admin", response_class=HTMLResponse)
async def admin_dashboard(admin_auth: str = Cookie(default=None), user_email: str = Cookie(default=None)):
    if admin_auth!="yes": return RedirectResponse("/admin/login")
    orders_html="".join([f"<tr><td>{o['id']}<br><img src='https://api.qrserver.com/v1/create-qr-code/?size=60x60&data={o['id']}'/></td><td>{o['time']}</td><td>{o['phone']}</td><td>{o['location']}</td><td>{', '.join([i['name'] for i in o['items']])}</td><td>KSh {o['total']}</td><td><a href='/video' target='_blank'>Video Call</a></td></tr>" for o in reversed(ORDERS[-50:])]) or "<tr><td colspan=7>No orders</td></tr>"
    prod_html="".join([f"<tr><td>{p['img']} {p['name']}<br><small>{p['real']}</small><br><img src='https://api.qrserver.com/v1/create-qr-code/?size=50x50&data={p['id']}'/></td><td>KSh {p['price']}</td><td>{p['cat']}</td><td>{p['stock']}</td><td><form method='post' action='/admin/delete-product'><input type='hidden' name='pid' value='{p['id']}'><button style='width:auto;background:red;padding:4px 8px'>Del</button></form></td></tr>" for p in PRODUCTS])
    return HTMLResponse(base_page(f"<div style='max-width:1100px;margin:20px auto;padding:0 16px'><h1>Admin + QR + Video</h1><div style='display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px'><div style='background:#fff;padding:16px;border-radius:12px'><h3>{len(ORDERS)}</h3><p>Orders</p></div><div style='background:#fff;padding:16px;border-radius:12px'><h3>KSh {sum(o['total'] for o in ORDERS)}</h3><p>Revenue</p></div><div style='background:#fff;padding:16px;border-radius:12px'><h3>{len(PRODUCTS)}</h3><p>Products</p></div></div><h2>Add Real Product</h2><div class='form' style='margin:10px 0'><form method='post' action='/admin/add-product'><input name='name' placeholder='Name' required><input name='real' placeholder='Real Brand' required><input name='price' type='number' required><input name='cat' placeholder='Category' required><input name='img' placeholder='Emoji' required><input name='stock' type='number' required><button>Add</button></form></div><h2>Products with QR</h2><div style='background:#fff;padding:12px;border-radius:12px;overflow:auto'><table><tr><th>Product+QR</th><th>Price</th><th>Cat</th><th>Stock</th><th>Action</th></tr>{prod_html}</table></div><h2>Orders with QR + Video</h2><div style='background:#fff;padding:12px;border-radius:12px;overflow:auto'><table><tr><th>ID+QR</th><th>Time</th><th>Phone</th><th>Loc</th><th>Items</th><th>Total</th><th>Video</th></tr>{orders_html}</table></div><div style='display:flex;gap:10px;margin-top:20px'><a href='/scan' style='flex:1'><button>Scan</button></a><a href='/video' style='flex:1'><button style='background:#111'>Video</button></a><a href='/terms' style='flex:1'><button style='background:#eee;color:#333'>Terms</button></a></div></div>", get_user(user_email), admin=True))

@app.post("/admin/add-product")
async def add_prod(name: str = Form(...), real: str = Form(...), price: int = Form(...), cat: str = Form(...), img: str = Form(...), stock: int = Form(...), admin_auth: str = Cookie(default=None)):
    if admin_auth!="yes": return RedirectResponse("/admin/login")
    new_id=max([p['id'] for p in PRODUCTS], default=0)+1
    PRODUCTS.append({"id":new_id,"name":name,"real":real,"price":price,"cat":cat,"img":img,"stock":stock})
    return RedirectResponse("/admin",303)

@app.post("/admin/delete-product")
async def del_prod(pid: int = Form(...), admin_auth: str = Cookie(default=None)):
    if admin_auth!="yes": return RedirectResponse("/admin/login")
    global PRODUCTS
    PRODUCTS=[p for p in PRODUCTS if p['id']!=pid]
    return RedirectResponse("/admin",303)

@app.post("/mpesa/callback")
async def mpesa_callback(request: Request):
    data=await request.json()
    print(data)
    return {"ResultCode":0}
