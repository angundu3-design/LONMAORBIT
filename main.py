import json, hashlib, time, os, base64, urllib.request, urllib.parse
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
    {"id":7,"name":"Blue Band 500g","price":280,"cat":"Cooking","img":"🧈","stock":40,"real":"Blue Band"},
    {"id":8,"name":"Tea Leaves 250g","price":180,"cat":"Beverages","img":"🍵","stock":60,"real":"Kericho Gold"},
    {"id":9,"name":"Soda 1.25L","price":120,"cat":"Drinks","img":"🥤","stock":100,"real":"Coca Cola"},
    {"id":10,"name":"Eggs Tray 30","price":480,"cat":"Dairy","img":"🥚","stock":20,"real":"Farm Eggs"},
]
ADMIN_PASS = "lonma2026"
LOGO = "<svg xmlns='http://www.w3.org/2000/svg' width='160' height='40' viewBox='0 0 160 40'><rect width='160' height='40' rx='10' fill='#0096B2'/><text x='10' y='28' font-family='serif' font-size='32' font-weight='900' fill='white'>LO</text><rect x='55' y='10' width='95' height='18' rx='5' fill='white'/><text x='60' y='22' font-size='8' letter-spacing='1.5' font-weight='700'>LONMA ORBIT</text></svg>"

def hash_pw(p): return hashlib.sha256(p.encode()).hexdigest()
def get_user(email: str = Cookie(default=None)):
    return {"email":email,**USERS[email]} if email and email in USERS else None

def page(content, user=None, admin=False):
    if admin:
        nav = "<a href='/' style='color:#fff'>Shop</a> | <a href='/scan' style='color:#fff'>📷 Scan</a> | <a href='/video' style='color:#fff'>📹 Video</a> | <b style='color:#ffeb3b'>Admin</b> | <a href='/logout' style='color:#fff'>Logout</a>"
    else:
        base = "<a href='/scan' style='color:#fff;margin-right:10px'>📷 Scan</a><a href='/video' style='color:#fff;margin-right:10px'>📹 Video</a><a href='/terms' style='color:#fff;margin-right:10px'>Terms</a>"
        nav = f"{base} 👤 {user['name'].split()[0]} | <a href='/admin' style='color:#ffeb3b'>Admin</a> | <a href='/logout' style='color:#ffeb3b'>Logout</a>" if user else f"{base} <a href='/login' style='background:#fff;color:#0096B2;padding:8px 14px;border-radius:20px;text-decoration:none;font-weight:800'>Sign In</a> | <a href='/admin/login' style='color:#ffeb3b;margin-left:10px'>Admin</a>"
    return f"<!DOCTYPE html><html><head><meta name='viewport' content='width=device-width,initial-scale=1'><title>LONMA MART</title><style>body{{margin:0;font-family:system-ui;background:#f5f7f8}}header{{background:#0096B2;color:#fff;padding:10px 16px;display:flex;justify-content:space-between;align-items:center;position:sticky;top:0;z-index:10}} .grid{{display:grid;grid-template-columns:1fr 1fr;gap:12px;padding:15px 15px 90px}} .card{{background:#fff;padding:14px;border-radius:16px;text-align:center;position:relative}} button{{background:#0096B2;color:#fff;border:0;padding:11px;border-radius:10px;width:100%;font-weight:700;cursor:pointer}} input,select{{width:100%;padding:12px;margin:8px 0;border-radius:10px;border:1px solid #ddd;box-sizing:border-box}} .form{{max-width:600px;margin:20px auto;background:#fff;padding:24px;border-radius:20px}} table{{width:100%;border-collapse:collapse}} th,td{{padding:10px;border-bottom:1px solid #eee;text-align:left;font-size:13px}} .badge{{background:#e6f9fc;color:#0096B2;padding:4px 10px;border-radius:20px;font-size:12px}} .qr{{width:100px;height:100px}}</style></head><body><header><div style='display:flex;align-items:center;gap:8px;background:#fff;border-radius:10px;padding:2px'>{LOGO}</div><div>{nav}</div></header>{content}</body></html>"

@app.api_route("/", methods=["GET","HEAD"])
async def home(user_email: str = Cookie(default=None)):
    u=get_user(user_email)
    content=f"""
    <div style='padding:12px;display:flex;gap:8px'><input id='s' placeholder='Search real products...' onkeyup='f()' style='flex:1'><select id='cat' onchange='f()'><option value='all'>All Categories</option><option>Flour</option><option>Dairy</option><option>Bakery</option><option>Cooking</option><option>Sugar</option><option>Rice</option><option>Beverages</option><option>Drinks</option></select></div>
    <div style='padding:0 12px;display:flex;gap:8px'><a href='/scan' style='flex:1;background:#111;color:#fff;padding:10px;text-align:center;border-radius:10px;text-decoration:none'>📷 Scan Product QR</a><a href='/video' style='flex:1;background:#0096B2;color:#fff;padding:10px;text-align:center;border-radius:10px;text-decoration:none'>📹 Video Support</a></div>
    <div class='grid' id='g'></div>
    <div style='position:fixed;bottom:0;left:0;right:0;background:#111;color:#fff;padding:12px 18px;display:flex;justify-content:space-between;border-radius:18px 18px 0 0'><div><span id='cc'>0</span> items • <b id='ct'>KSh 0</b></div><button style='width:auto;background:#fff;color:#111' onclick='co()'>Checkout → M-Pesa + QR</button></div>
    <div id='ck' style='display:none;position:fixed;inset:0;background:#fff;padding:20px;z-index:20;overflow:auto'><h2>Checkout + M-Pesa + QR Receipt</h2><div id='list'></div><h3 id='tt'></h3><div id='qrBox' style='text-align:center;margin:15px 0'></div><form method='post' action='/order'><input type='hidden' name='cart_data' id='cd'><input name='phone' placeholder='07xx M-Pesa' value="{u['phone'] if u else ''}" required><input name='location' placeholder='Estate / Street' required><button>Place Order → M-Pesa STK</button><button type='button' onclick="document.getElementById('ck').style.display='none'" style='background:#eee;color:#333;margin-top:10px'>Back</button></form></div>
    <script>
    const P={json.dumps(PRODUCTS)};
    let cart=JSON.parse(localStorage.getItem('lonma_cart')||'[]');
    function qrUrl(t){{return `https://api.qrserver.com/v1/create-qr-code/?size=150x150&data=${{encodeURIComponent(t)}}`;}}
    function render(){{let h='';P.forEach(p=>{{h+=`<div class=card><div style=font-size:32px>${{p.img}}</div><h4>${{p.name}}</h4><small style=color:#666>${{p.real}}</small><br><span class=badge>${{p.cat}} • ${{p.stock}} left</span><div style=margin:8px 0><b style=color:#0096B2>KSh ${{p.price}}</b></div><img class=qr src="${{qrUrl(p.name+'|'+p.price)}}" alt="QR"/><div style=font-size:10px;color:#999>QR: ${{p.id}}</div><button onclick=add(${{p.id}}) style=margin-top:6px>Add</button></div>`;}});document.getElementById('g').innerHTML=h;up();}
    function add(id){{let pr=P.find(x=>x.id==id);cart.push(pr);localStorage.setItem('lonma_cart',JSON.stringify(cart));up();}}
    function up(){{document.getElementById('cc').innerText=cart.length;let t=cart.reduce((s,i)=>s+i.price,0);document.getElementById('ct').innerText='KSh '+t;document.getElementById('tt').innerText='Total KSh '+t;document.getElementById('cd').value=JSON.stringify(cart);document.getElementById('list').innerHTML=cart.map(c=>`<p>${{c.name}} - KSh ${{c.price}}</p>`).join('');if(t>0){{document.getElementById('qrBox').innerHTML=`<p>Order QR (show to rider):</p><img src="${{qrUrl('LONMA|'+t+'|'+cart.length+' items|'+Date.now())}}" style=width:150px />`;}}}}
    function co(){{if(cart.length==0)return alert('Empty');document.getElementById('ck').style.display='block';}}
    function f(){{let q=document.getElementById('s').value.toLowerCase();let cat=document.getElementById('cat').value;document.querySelectorAll('.card').forEach((el,i)=>{{let ok=P[i].name.toLowerCase().includes(q)||P[i].real.toLowerCase().includes(q);if(cat!='all')ok=ok&&P[i].cat==cat;el.style.display=ok?'block':'none';}});}}
    // Handle QR scan param ?add=ID
    const urlParams=new URLSearchParams(window.location.search);let addId=urlParams.get('add');if(addId){{let pr=P.find(x=>x.id==parseInt(addId));if(pr){{cart.push(pr);localStorage.setItem('lonma_cart',JSON.stringify(cart));alert(pr.name+' added from QR scan!');}}}}
    render();
    </script>
    """
    return HTMLResponse(page(content,u))

@app.get("/terms", response_class=HTMLResponse)
async def terms(user_email: str = Cookie(default=None)):
    u=get_user(user_email)
    c = """
    <div class='form' style='max-width:800px'><h1>Terms & Conditions - LONMA MART</h1>
    <h3>1. Products</h3><p>All products are real Kenyan brands: Jogoo, Brookside, Supa Loaf, Elianto, Kabras, Pishori, Blue Band, etc. Prices in KSh.</p>
    <h3>2. Orders & M-Pesa</h3><p>Checkout pushes M-Pesa STK to your phone. Enter PIN to complete. Orders delivered within 2 hours in Thika area.</p>
    <h3>3. QR Code</h3><p>Each product has QR for quick scan-to-cart. Receipt QR must be shown to delivery rider.</p>
    <h3>4. Scan Code</h3><p>Use /scan page to scan product QR with camera to add to cart instantly.</p>
    <h3>5. Video Calls</h3><p>Support via video call at /video for order help, product inquiries.</p>
    <h3>6. Privacy</h3><p>Phone, location used only for delivery. No sharing.</p>
    <h3>7. Returns</h3><p>Wrong/damaged products returnable within 24h with QR receipt.</p>
    <p><b>Contact:</b> support@lonmaorbit.co.ke | Thika, Kenya</p>
    <a href='/'><button>Back to Shop</button></a></div>
    """
    return HTMLResponse(page(c,u))

@app.get("/scan", response_class=HTMLResponse)
async def scan_page(user_email: str = Cookie(default=None)):
    u=get_user(user_email)
    c = """
    <div class='form' style='text-align:center'><h1>📷 Scan Product QR</h1><p>Point camera at product QR code</p>
    <div id='reader' style='width:100%;border-radius:16px;overflow:hidden'></div>
    <div id='result' style='margin-top:15px;padding:12px;background:#e6f9fc;border-radius:12px;display:none'></div>
    <a href='/' style='display:block;margin-top:20px'><button>Back to Shop</button></a>
    </div>
    <script src='https://unpkg.com/html5-qrcode@2.3.8/html5-qrcode.min.js'></script>
    <script>
    function onScanSuccess(decodedText) {
        document.getElementById('result').style.display='block';
        document.getElementById('result').innerHTML=`Scanned: <b>${decodedText}</b><br><a href='/?add='+encodeURIComponent(decodedText.split('|')[0].match(/\\d+/)||'')><button style=margin-top:10px>Add to Cart</button></a><br><br><small>Full: ${decodedText}</small>`;
        // Try to parse ID
        let m=decodedText.match(/ID:(\\d+)|^(\\d+)$/);
        if(m){ window.location.href='/?add='+(m[1]||m[2]); return; }
        // If product name, search
        let products = """+json.dumps(PRODUCTS)+""";
        let found = products.find(p=>decodedText.toLowerCase().includes(p.name.toLowerCase()) || decodedText.includes(String(p.id)));
        if(found){ window.location.href='/?add='+found.id; }
    }
    let html5QrcodeScanner = new Html5QrcodeScanner("reader", { fps: 10, qrbox: {width:250,height:250} }, false);
    html5QrcodeScanner.render(onScanSuccess, (err)=>{});
    </script>
    """
    return HTMLResponse(page(c,u))

@app.get("/video", response_class=HTMLResponse)
async def video_page(user_email: str = Cookie(default=None)):
    u=get_user(user_email)
    c = """
    <div class='form' style='max-width:900px'><h1>📹 Video Support Call</h1>
    <p>Talk to LONMA support via video. Share screen for order issues.</p>
    <div style='display:flex;gap:10px;margin:15px 0'>
      <a href='https://meet.jit.si/lonmaorbit-support' target='_blank' style='flex:1'><button>Jitsi Video Call (Free)</button></a>
      <a href='https://meet.jit.si/lonmaorbit-orders' target='_blank' style='flex:1;background:#111'><button style='background:#111'>Orders Room</button></a>
    </div>
    <div style='background:#000;border-radius:16px;overflow:hidden;height:500px'>
      <iframe src='https://meet.jit.si/lonmaorbit-support#config.prejoinConfig.enabled=false' allow='camera; microphone; fullscreen; display-capture' style='width:100%;height:100%;border:0'></iframe>
    </div>
    <h3 style='margin-top:20px'>How it works:</h3><ol><li>Click Join video</li><li>Allow camera/mic</li><li>Show your order QR</li><li>Support sees you live</li></ol>
    <a href='/'><button>Back to Shop</button></a>
    </div>
    """
    return HTMLResponse(page(c,u))

# --- AUTH + ORDER + ADMIN (same as before, shortened) ---
@app.get("/login", response_class=HTMLResponse)
async def lp(): return HTMLResponse(page("<div class='form'><h2>Sign In</h2><form method='post' action='/login'><input name='email' type='email' required placeholder='Email'><input name='password' type='password' required placeholder='Password'><button>Sign In</button></form><p><a href='/register'>Create</a></p></div>"))
@app.post("/login")
async def lg(email: str = Form(...), password: str = Form(...)):
    if email in USERS and USERS[email]['password']==hash_pw(password):
        r=RedirectResponse("/",303);r.set_cookie("user_email",email,max_age=2592000);return r
    return HTMLResponse(page("<div class='form'><h3 style='color:red'>Wrong</h3></div>"))
@app.get("/register", response_class=HTMLResponse)
async def rp(): return HTMLResponse(page("<div class='form'><h2>Create Account</h2><form method='post' action='/register'><input name='name' required placeholder='Name'><input name='email' type='email' required placeholder='Email'><input name='phone' required placeholder='07xx'><input name='password' type='password' required placeholder='Password'><button>Create</button></form></div>"))
@app.post("/register")
async def rg(name: str = Form(...), email: str = Form(...), phone: str = Form(...), password: str = Form(...)):
    USERS[email]={"name":name,"phone":phone,"password":hash_pw(password)};r=RedirectResponse("/",303);r.set_cookie("user_email",email,max_age=2592000);return r
@app.get("/logout")
async def lo(): r=RedirectResponse("/",303);r.delete_cookie("user_email");r.delete_cookie("admin_auth");return r

@app.post("/order")
async def order(phone: str = Form(...), location: str = Form(...), cart_data: str = Form(...), user_email: str = Cookie(default=None)):
    cart=json.loads(cart_data);total=sum(i['price'] for i in cart)
    order_id=f"LO{int(time.time())}"
    ORDERS.append({"id":order_id,"time":datetime.now().strftime("%Y-%m-%d %H:%M"),"user":user_email or "Guest","phone":phone,"location":location,"items":cart,"total":total,"status":"Pending"})
    qr_data = f"LONMA ORDER {order_id} KSh {total} {phone}"
    qr_img = f"https://api.qrserver.com/v1/create-qr-code/?size=200x200&data={urllib.parse.quote(qr_data)}"
    return HTMLResponse(page(f"<div class='form' style='text-align:center'><h1>✅ Order {order_id}</h1><p>KSh {total} to {location}</p><img src='{qr_img}' style='width:200px;margin:15px'/><p><b>Show this QR to rider</b></p><p style='background:#e6f9fc;padding:10px;border-radius:10px'>M-Pesa STK sent to {phone}</p><a href='/'><button>Continue</button></a><div style='display:flex;gap:8px;margin-top:10px'><a href='/video' style='flex:1'><button style='background:#111'>📹 Video Support</button></a><a href='/terms' style='flex:1'><button style='background:#eee;color:#333'>Terms</button></a></div></div>", get_user(user_email)))

@app.get("/admin/login", response_class=HTMLResponse)
async def admin_login_page(): return HTMLResponse(page("<div class='form'><h2>Admin</h2><form method='post' action='/admin/login'><input name='password' type='password' placeholder='lonma2026' required><button>Login</button></form></div>"))
@app.post("/admin/login")
async def admin_login(password: str = Form(...)):
    if password==ADMIN_PASS:
        r=RedirectResponse("/admin",303);r.set_cookie("admin_auth","yes",max_age=86400);return r
    return HTMLResponse(page("<div class='form'><h3 style='color:red'>Wrong</h3></div>"))

@app.get("/admin", response_class=HTMLResponse)
async def admin_dashboard(admin_auth: str = Cookie(default=None), user_email: str = Cookie(default=None)):
    if admin_auth!="yes": return RedirectResponse("/admin/login")
    orders_html="".join([f"<tr><td>{o['id']}<br><img src='https://api.qrserver.com/v1/create-qr-code/?size=80x80&data={o['id']}'/></td><td>{o['time']}</td><td>{o['phone']}</td><td>{o['location']}</td><td>{', '.join([i['name'] for i in o['items']])}</td><td>KSh {o['total']}</td><td><a href='/video' target='_blank'>📹 Call Customer</a></td></tr>" for o in reversed(ORDERS[-50:])]) or "<tr><td colspan=7>No orders</td></tr>"
    prod_html="".join([f"<tr><td>{p['img']} {p['name']}<br><small>{p['real']}</small><br><img src='https://api.qrserver.com/v1/create-qr-code/?size=60x60&data={p['id']}'/></td><td>KSh {p['price']}</td><td>{p['cat']}</td><td>{p['stock']}</td><td><form method='post' action='/admin/delete-product'><input type='hidden' name='pid' value='{p['id']}'><button style='width:auto;background:red;padding:4px 8px'>Del</button></form></td></tr>" for p in PRODUCTS])
    return HTMLResponse(page(f"<div style='max-width:1100px;margin:20px auto;padding:0 16px'><h1>Admin + QR + Video</h1><div style='display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px;margin:20px 0'><div style='background:#fff;padding:16px;border-radius:12px'><h3>{len(ORDERS)}</h3><p>Orders</p></div><div style='background:#fff;padding:16px;border-radius:12px'><h3>KSh {sum(o['total'] for o in ORDERS)}</h3><p>Revenue</p></div><div style='background:#fff;padding:16px;border-radius:12px'><h3>{len(PRODUCTS)}</h3><p>Real Products</p></div></div><h2>Add Real Product</h2><div class='form' style='margin:10px 0'><form method='post' action='/admin/add-product'><input name='name' placeholder='Name' required><input name='real' placeholder='Real Brand e.g. Brookside' required><input name='price' type='number' required placeholder='Price'><input name='cat' placeholder='Category' required><input name='img' placeholder='Emoji' required><input name='stock' type='number' required placeholder='Stock'><button>Add Real Product</button></form></div><h2>Products with QR</h2><div style='background:#fff;padding:12px;border-radius:12px;overflow:auto'><table><tr><th>Product + QR</th><th>Price</th><th>Cat</th><th>Stock</th><th>Action</th></tr>{prod_html}</table></div><h2 style='margin-top:30px'>Orders with QR + Video Call</h2><div style='background:#fff;padding:12px;border-radius:12px;overflow:auto'><table><tr><th>ID + QR</th><th>Time</th><th>Phone</th><th>Loc</th><th>Items</th><th>Total</th><th>Video</th></tr>{orders_html}</table></div><div style='margin-top:20px;display:flex;gap:10px'><a href='/scan' style='flex:1'><button>📷 Scan Page</button></a><a href='/video' style='flex:1'><button style='background:#111'>📹 Video Support Room</button></a><a href='/terms' style='flex:1'><button style='background:#eee;color:#333'>Terms</button></a></div></div>", get_user(user_email), admin=True))

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
    print("MPESA:",data)
    return {"ResultCode":0}
