from fastapi import FastAPI, Form, Cookie
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
import json, hashlib, os

app = FastAPI()

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

USERS = {}
PRODUCTS = [
    {"id":1,"name":"Unga 2kg","price":180,"img":"🌾"},
    {"id":2,"name":"Milk 500ml","price":70,"img":"🥛"},
    {"id":3,"name":"Bread","price":65,"img":"🍞"},
    {"id":4,"name":"Oil 1L","price":320,"img":"🫒"},
    {"id":5,"name":"Sugar 2kg","price":310,"img":"🍬"},
    {"id":6,"name":"Rice 2kg","price":420,"img":"🍚"},
    {"id":7,"name":"Eggs 30","price":550,"img":"🥚"},
    {"id":8,"name":"Soda 1.5L","price":110,"img":"🥤"},
]

def hash_pw(p): return hashlib.sha256(p.encode()).hexdigest()
def get_user(email: str = Cookie(default=None)):
    if email and email in USERS: return {"email":email, **USERS[email]}
    return None

# EMBEDDED LO LOGO - teal bg, white LO, LONMA ORBIT bar - NO FILE NEEDED
LOGO_SVG = """<svg xmlns='http://www.w3.org/2000/svg' width='180' height='48' viewBox='0 0 180 48'><rect width='180' height='48' rx='10' fill='#0096B2'/><text x='12' y='34' font-family='serif' font-size='38' font-weight='900' fill='white'>LO</text><rect x='58' y='14' width='110' height='20' rx='6' fill='white'/><text x='64' y='28' font-family='sans-serif' font-size='9' letter-spacing='2' font-weight='700' fill='#111'>LONMA ORBIT</text></svg>"""

def base_page(content, user=None):
    uh = f"👤 {user['name'].split()[0]} | <a href='/logout' style='color:#ffeb3b'>Logout</a>" if user else "<a href='/login' style='background:#fff;color:#0096B2;padding:8px 16px;border-radius:20px;text-decoration:none;font-weight:800'>Sign In</a>"
    return f"""<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width,initial-scale=1"><title>LONMA MART</title>
    <style>body{{margin:0;font-family:system-ui;background:#f5f7f8}} header{{background:#0096B2;color:#fff;padding:10px 18px;display:flex;justify-content:space-between;align-items:center;position:sticky;top:0;z-index:10}} .grid{{display:grid;grid-template-columns:1fr 1fr;gap:12px;padding:15px 15px 100px}} .card{{background:#fff;padding:14px;border-radius:16px;text-align:center}} button{{background:#0096B2;color:#fff;border:0;padding:11px;border-radius:10px;width:100%;font-weight:700}} input{{width:100%;padding:14px;margin:8px 0;border-radius:10px;border:1px solid #ddd;box-sizing:border-box}} .form-wrap{{max-width:400px;margin:40px auto;background:#fff;padding:28px;border-radius:20px}} @media(min-width:700px){{.grid{{grid-template-columns:repeat(4,1fr)}}}}</style></head><body>
    <header><div style="display:flex;align-items:center;gap:10px"><div style="background:#fff;border-radius:10px;padding:2px">{LOGO_SVG}</div></div><div>{uh}</div></header>{content}</body></html>"""

@app.api_route("/", methods=["GET","HEAD"])
async def home(user_email: str = Cookie(default=None)):
    user=get_user(user_email)
    content=f"""
    <div style="padding:12px"><input id="s" placeholder="Search products..." onkeyup="f()" style="padding:14px;border-radius:12px;border:1px solid #ddd;width:100%"></div>
    <div class="grid" id="grid"></div>
    <div style="position:fixed;bottom:0;left:0;right:0;background:#111;color:#fff;padding:14px 18px;display:flex;justify-content:space-between;border-radius:18px 18px 0 0"><div><span id="cc">0</span> items • <b id="ct">KSh 0</b></div><button style="width:auto;background:#fff;color:#111" onclick="co()">Checkout</button></div>
    <div id="ck" style="display:none;position:fixed;inset:0;background:#fff;padding:25px;z-index:20"><h2>Checkout</h2><div id="list"></div><h3 id="tt"></h3>
    <form method="post" action="/order"><input type="hidden" name="cart_data" id="cd"><input name="phone" placeholder="M-Pesa 07xx" value="{user['phone'] if user else ''}" required><input name="location" placeholder="Estate" required><button>Place Order</button><button type="button" onclick="document.getElementById('ck').style.display='none'" style="background:#eee;color:#333;margin-top:10px">Back</button></form></div>
    <script>
    const P={json.dumps(PRODUCTS)};let cart=JSON.parse(localStorage.getItem('lonma_cart')||'[]');
    function render(){{let h='';P.forEach(p=>{{h+=`<div class="card"><div style="font-size:36px">${{p.img}}</div><h4>${{p.name}}</h4><b style="color:#0096B2">KSh ${{p.price}}</b><button onclick="add(${{p.id}})" style="margin-top:8px">Add</button></div>`}});document.getElementById('grid').innerHTML=h;up();}}
    function add(id){{cart.push(P.find(x=>x.id==id));localStorage.setItem('lonma_cart',JSON.stringify(cart));up();}}
    function up(){{document.getElementById('cc').innerText=cart.length;let t=cart.reduce((s,i)=>s+i.price,0);document.getElementById('ct').innerText='KSh '+t;document.getElementById('tt').innerText='Total KSh '+t;document.getElementById('cd').value=JSON.stringify(cart);document.getElementById('list').innerHTML=cart.map(c=>`<p>${{c.name}} - ${{c.price}}</p>`).join('');}}
    function co(){{if(cart.length==0)return alert('Empty');document.getElementById('ck').style.display='block';}} function f(){{let q=document.getElementById('s').value.toLowerCase();document.querySelectorAll('.card').forEach((el,i)=>{{el.style.display=P[i].name.toLowerCase().includes(q)?'block':'none';}});}} render();
    </script>"""
    return HTMLResponse(base_page(content,user))

@app.get("/login", response_class=HTMLResponse)
async def lp(): return HTMLResponse(base_page("<div class='form-wrap'><h2>Sign In</h2><form method='post' action='/login'><input name='email' type='email' placeholder='Email' required><input name='password' type='password' placeholder='Password' required><button>Sign In</button></form><p style='text-align:center'>No account? <a href='/register'>Create</a></p></div>"))
@app.post("/login")
async def lg(email: str = Form(...), password: str = Form(...)):
    if email in USERS and USERS[email]['password']==hash_pw(password):
        r=RedirectResponse("/",303);r.set_cookie("user_email",email,max_age=2592000);return r
    return HTMLResponse(base_page("<div class='form-wrap'><h3 style='color:red'>Wrong login</h3><a href='/login'>Try again</a></div>"))

@app.get("/register", response_class=HTMLResponse)
async def rp(): return HTMLResponse(base_page("<div class='form-wrap'><h2>Create Account</h2><form method='post' action='/register'><input name='name' placeholder='Full Name' required><input name='email' type='email' placeholder='Email' required><input name='phone' placeholder='Phone' required><input name='password' type='password' placeholder='Password' required><button>Create</button></form></div>"))
@app.post("/register")
async def rg(name: str = Form(...), email: str = Form(...), phone: str = Form(...), password: str = Form(...)):
    USERS[email]={"name":name,"phone":phone,"password":hash_pw(password)};r=RedirectResponse("/",303);r.set_cookie("user_email",email,max_age=2592000);return r
@app.get("/profile", response_class=HTMLResponse)
async def pf(user_email: str = Cookie(default=None)):
    u=get_user(user_email); 
    if not u: return RedirectResponse("/login")
    return HTMLResponse(base_page(f"<div class='form-wrap'><h2>{u['name']}</h2><p>{u['email']}</p><p>{u['phone']}</p><a href='/logout'><button style='background:#111'>Logout</button></a></div>",u))
@app.get("/logout")
async def lo():
    r=RedirectResponse("/",303);r.delete_cookie("user_email");return r
@app.post("/order")
async def order(phone: str = Form(...), location: str = Form(...), cart_data: str = Form(...), user_email: str = Cookie(default=None)):
    cart=json.loads(cart_data);total=sum(i['price'] for i in cart);return HTMLResponse(base_page(f"<div class='form-wrap'><h1 style='color:#0096B2'>✅ Order Received</h1><p>KSh {total} to {location} - {phone}</p><a href='/'><button>Continue</button></a></div>",get_user(user_email)))
@app.get("/health")
async def h(): return {"ok":True}

