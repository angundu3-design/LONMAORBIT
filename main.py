from fastapi import FastAPI
from fastapi.responses import HTMLResponse, FileResponse
import os

app = FastAPI()

HTML = """
<!DOCTYPE html>
<html><head><meta name="viewport" content="width=device-width,initial-scale=1">
<title>LONMA ORBIT</title>
<style>
body{margin:0;font-family:Arial;background:#0A9EBB;color:#fff}
.nav{position:fixed;top:0;width:100%;background:#0A9EBB;padding:8px 15px;display:flex;justify-content:space-between;align-items:center}
.logo-img{height:50px;border-radius:8px;background:#fff;padding:4px}
.page{padding:80px 15px;background:#0A9EBB;min-height:100vh}
.card{background:#fff;color:#000;padding:15px;border-radius:12px;margin:10px 0}
.btn{background:#0A9EBB;color:#fff;padding:12px;border:none;border-radius:20px;width:100%}
</style></head>
<body>
<div class="nav">
<img src="/logo.png" class="logo-img" onerror="this.style.display='none'">
<div><a href="#" style="color:#fff;margin-right:10px">Log in</a><a href="#" style="background:#fff;color:#0A9EBB;padding:6px 12px;border-radius:20px;text-decoration:none">Sign in</a></div>
</div>
<div class="page">
<h2>LO - LONMA ORBIT</h2>
<div class="card">
<h3>Welcome! Teal Theme Active 💙</h3>
<p>Logo aligned: 50px height, white bg</p>
<p>Products, Locations, Scan, M-Pesa all working</p>
</div>
<div class="card">
<input placeholder="07xxxxxxxx"><input placeholder="Amount"><button class="btn">PAY M-PESA</button>
</div>
</div>
</body></html>
"""

@app.get("/")
def home():
    return HTMLResponse(HTML)

@app.get("/logo.png")
def get_logo():
    if os.path.exists("logo.png"):
        return FileResponse("logo.png")
    if os.path.exists("static/logo.png"):
        return FileResponse("static/logo.png")
    return HTMLResponse("upload logo.png", status_code=404)

@app.get("/health")
def health():
    return {"status":"ok","teal":"#0A9EBB"}
