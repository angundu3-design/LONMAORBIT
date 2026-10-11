USERS = {
 "admin": {"username":"admin","email":"admin@lonmaorbit.co.ke","password":"Lonma@2026","name":"Admin","outlet":"Admin"},
 "Mongelah": {"username":"Mongelah","email":"mongelah@lonmaorbit.co.ke","password":"1234","name":"Mongelah","outlet":"Isibania"}
}

@app.post("/api/register")
def register(data: dict):
    u = data.get("username"); e = data.get("email")
    if not u or not e: return {"ok":False,"error":"Missing fields"}
    if u in USERS: return {"ok":False,"error":"Username exists"}
    USERS[u] = data
    USERS[e] = data # allow login with email too
    return {"ok":True}

@app.post("/api/login")
def login(data: dict):
    key = data.get("username"); pw = data.get("password")
    user = USERS.get(key)
    if user and user.get("password")==pw:
        return {"ok":True,"username":user["username"],"email":user["email"]}
    # also check by email loop
    for k,v in USERS.items():
        if (v["email"]==key or v["username"]==key) and v["password"]==pw:
            return {"ok":True,"username":v["username"],"email":v["email"]}
    return {"ok":False,"error":"Invalid"}

@app.post("/api/forgot")
def forgot(data: dict):
    return {"ok":True,"msg":"If email exists, reset sent to "+data.get("email","")}
