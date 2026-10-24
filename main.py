# ... keep all your python code same, ONLY replace HTML part with this:

HTML = """
<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width,initial-scale=1"><title>LONMA ORBIT</title>
<script src="https://unpkg.com/html5-qrcode@2.3.8/html5-qrcode.min.js"></script>
<style>
:root{--teal:#0A9EBB}
body{margin:0;font-family:Arial;background:var(--teal);color:#fff}
.nav{position:fixed;top:0;width:100%;background:var(--teal);padding:8px 15px;display:flex;justify-content:space-between;align-items:center;z-index:100}
.logo-img{height:50px;width:auto;border-radius:8px;background:#fff;padding:3px;box-shadow:0 2px 8px rgba(0,0,0,0.2)}
.page{display:none;padding:80px 15px 110px;min-height:100vh;background:var(--teal)}
.page.active{display:block}
.card{background:#fff;color:#000;border-radius:14px;padding:15px;margin:10px 0}
.btn{background:var(--teal);color:#fff;border:none;padding:12px;border-radius:25px;width:100%;font-weight:bold;margin-top:10px}
input{width:100%;padding:12px;border-radius:8px;border:1px solid #ddd;background:#f7f7f7;margin:6px 0}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px}
.bottom{position:fixed;bottom:0;width:100%;background:#fff;display:flex;justify-content:space-around;padding:10px;z-index:100}
.bottom div{font-size:10px;color:#000;text-align:center;cursor:pointer}
#botBtn{position:fixed;bottom:80px;right:15px;background:#fff;color:var(--teal);width:56px;height:56px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:26px;cursor:pointer;z-index:200;box-shadow:0 4px 15px rgba(0,0,0,0.3)}
#botBox{display:none;position:fixed;bottom:145px;right:15px;width:90%;max-width:350px;height:400px;background:#fff;border-radius:15px;z-index:200;flex-direction:column;overflow:hidden}
#botBox.open{display:flex}
</style></head><body>

<div class="nav">
<div class="logo"><img src="logo.png" class="logo-img" onerror="this.src='https://via.placeholder.com/110x50?text=LO'"></div>
<div><a onclick="show('login')" style="background:rgba(255,255,255,0.25);color:#fff;padding:8px 16px;border-radius:20px;font-size:13px;cursor:pointer">Log in</a><a onclick="show('signin')" style="background:#fff;color:#0A9EBB;padding:8px 16px;border-radius:20px;font-size:13px;font-weight:bold;cursor:pointer">Sign in</a></div>
</div>

<!-- rest of your pages stay same - products, login, etc -->
<div id="products" class="page active"><h2>Products</h2><div class="grid" id="plist"></div><div class="card"><input id="phone" placeholder="07xxxxxxxx"><input id="amount" type="number" placeholder="Amount"><button class="btn" onclick="pay()">PAY WITH M-PESA</button><p id="paystatus"></p></div></div>
<div id="login" class="page"><h2>Log In</h2><div class="card"><input id="lemail" placeholder="Email"><input id="lpass" type="password" placeholder="Password"><button class="btn" onclick="login()">Log In</button><p id="lstatus"></p></div></div>
<div id="signin" class="page"><h2>Sign Up</h2><div class="card"><input id="sname" placeholder="Full Name"><input id="semail" placeholder="Email"><input id="spass" type="password" placeholder="Password"><button class="btn" onclick="signin()">Create Account</button><p id="sstatus"></p></div></div>
<div id="terms" class="page"><h2>Terms</h2><div class="card"><p>Original products, M-Pesa final, Nairobi same-day</p></div></div>
<div id="locations" class="page"><h2>Locations</h2><div id="loclist"></div></div>
<div id="scan" class="page"><h2>Code Scan</h2><div class="card"><div id="reader"></div><button class="btn" onclick="startScan()">START CAMERA</button><input id="manualcode" placeholder="LONMA-001"><button class="btn" onclick="verifyCode()">VERIFY</button><p id="scanresult"></p></div></div>

<div class="bottom"><div onclick="show('products')">🛍️<br>Products</div><div onclick="show('scan')">📷<br>Scan</div><div onclick="show('locations')">📍<br>Locations</div><div onclick="show('terms')">📄<br>Terms</div><div onclick="show('login')">👤<br>Account</div></div>

<div id="botBtn" onclick="toggleBot()">🤖</div>
<div id="botBox"><div style="padding:12px;background:#0A9EBB;color:#fff;font-weight:bold;display:flex;justify-content:space-between"><span>LO BOT</span><span onclick="toggleBot()" style="cursor:pointer">✕</span></div><div id="botMsgs" style="flex:1;overflow-y:auto;padding:10px;background:#f9f9f9"><div style="background:#fff;border:1px solid #eee;padding:10px;border-radius:12px;font-size:13px;color:#000">Welcome to LONMA ORBIT 💙 Ask about products, M-Pesa, locations!</div></div><div style="display:flex;padding:10px;border-top:1px solid #eee;background:#fff"><input id="botInput" style="flex:1" placeholder="Ask..." onkeypress="if(event.key==='Enter')sendBot()"><button onclick="sendBot()" style="background:#0A9EBB;color:#fff;border:none;padding:12px 15px;border-radius:0 20px 20px 0">Send</button></div></div>

<script>
function show(id){document.querySelectorAll('.page').forEach(p=>p.classList.remove('active'));document.getElementById(id).classList.add('active')}
async function loadProducts(){let r=await fetch('/api/products');let d=await r.json();document.getElementById('plist').innerHTML=d.map(p=>`<div class="card"><img src="${p.image}" style="width:100%;border-radius:8px"><h4>${p.name}</h4><p>KSh ${p.price}</p><small>${p.code}</small><button class="btn" onclick="document.getElementById('amount').value=${p.price}">BUY</button></div>`).join('')}
async function loadLoc(){let r=await fetch('/api/locations');let d=await r.json();document.getElementById('loclist').innerHTML=d.map(l=>`<div class="card"><h4>${l.name}</h4><p>${l.address}</p><a href="https://maps.google.com/?q=${l.lat},${l.lng}" target="_blank"><button class="btn">Directions</button></a></div>`).join('')}
async function login(){let r=await fetch('/api/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({email:document.getElementById('lemail').value,password:document.getElementById('lpass').value})});let d=await r.json();document.getElementById('lstatus').innerText=d.message}
async function signin(){let r=await fetch('/api/signin',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name:document.getElementById('sname').value,email:document.getElementById('semail').value,password:document.getElementById('spass').value})});let d=await r.json();document.getElementById('sstatus').innerText=d.message}
async function pay(){let phone=document.getElementById('phone').value;let amount=document.getElementById('amount').value;document.getElementById('paystatus').innerText='Sending STK...';let r=await fetch('/mpesa/stkpush',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({phone,amount})});let d=await r.json();document.getElementById('paystatus').innerText=JSON.stringify(d)}
async function verifyCode(){let code=document.getElementById('manualcode').value;let r=await fetch(`/api/verify/${code}`);let d=await r.json();document.getElementById('scanresult').innerHTML=d.valid?`✅ ${d.product.name}`:`❌ Invalid`}
let html5QrCode;function startScan(){html5QrCode=new Html5Qrcode("reader");html5QrCode.start({facingMode:"environment"},{fps:10,qrbox:250},(dec)=>{document.getElementById('manualcode').value=dec;verifyCode();html5QrCode.stop()})}
function toggleBot(){document.getElementById('botBox').classList.toggle('open')}
async function sendBot(){let i=document.getElementById('botInput');let m=i.value;if(!m)return;let b=document.getElementById('botMsgs');b.innerHTML+=`<div style="background:#0A9EBB;color:#fff;margin-left:auto;padding:10px;border-radius:12px;max-width:80%;margin-top:6px;font-size:13px">${m}</div>`;i.value='';let r=await fetch('/api/bot',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({message:m})});let d=await r.json();b.innerHTML+=`<div style="background:#fff;border:1px solid #eee;padding:10px;border-radius:12px;max-width:80%;margin-top:6px;font-size:13px;color:#000">${d.reply}</div>`;b.scrollTop=b.scrollHeight}
loadProducts();loadLoc();
</script></body></html>
"""
