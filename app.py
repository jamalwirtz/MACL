"""Muddo Agro Chemicals LTD v6 — All 7 features"""
from flask import (Flask, render_template, request, redirect, url_for,
                   session, jsonify, flash, send_file, abort)
from flask_mail import Mail, Message as MailMessage
import sqlite3, hashlib, os, json, uuid, io, string, random
from datetime import datetime, timedelta
from functools import wraps
from werkzeug.utils import secure_filename
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (SimpleDocTemplate, Table, TableStyle,
                                 Paragraph, Spacer, HRFlowable)
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
import qrcode
from PIL import Image

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'muddo_agro_dev_only_change_in_prod_XK9_2024')
DB_PATH     = os.path.join(os.path.dirname(__file__), 'muddo.db')
UPLOAD_DIR  = os.path.join(os.path.dirname(__file__), 'static', 'uploads', 'products')
ALLOWED_EXT = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

app.config.update(
    MAIL_SERVER='smtp.gmail.com', MAIL_PORT=587, MAIL_USE_TLS=True,
    MAIL_USERNAME=os.environ.get('MAIL_USERNAME','muddoagro811@gmail.com'),
    MAIL_PASSWORD=os.environ.get('MAIL_PASSWORD',''),
    MAIL_DEFAULT_SENDER=('Muddo Agro Chemicals','muddoagro811@gmail.com'),
    MAIL_SUPPRESS_SEND=os.environ.get('MAIL_PASSWORD','')=='',
)
mail = Mail(app)
GA_ID    = os.environ.get('GA_MEASUREMENT_ID','G-XXXXXXXXXX')
WA_NUM   = '256772507582'

def get_db():
    conn = sqlite3.connect(DB_PATH); conn.row_factory = sqlite3.Row; return conn
def allowed_file(fn): return '.' in fn and fn.rsplit('.',1)[1].lower() in ALLOWED_EXT
def gen_ref(pfx='REF'): return f"{pfx}-{''.join(random.choices(string.ascii_uppercase+string.digits,k=8))}"
def send_safe(subj,to,html):
    try:
        if not os.environ.get('MAIL_PASSWORD',''): return False
        m=MailMessage(subj,recipients=to); m.html=html; mail.send(m); return True
    except Exception as e: app.logger.warning(f'Mail failed:{e}'); return False

def init_db():
    conn=get_db(); c=conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS products(id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,category TEXT NOT NULL,description TEXT,active_ingredient TEXT,
        formulation TEXT,crops TEXT,dosage TEXT,packing TEXT,image_url TEXT,image_file TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP)''')
    c.execute('''CREATE TABLE IF NOT EXISTS distributors(id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,region TEXT,district TEXT,address TEXT,phone TEXT,email TEXT,lat REAL,lng REAL,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP)''')
    c.execute('''CREATE TABLE IF NOT EXISTS contact_requests(id INTEGER PRIMARY KEY AUTOINCREMENT,
        ref_number TEXT UNIQUE,name TEXT,email TEXT,phone TEXT,subject TEXT,message TEXT,
        status TEXT DEFAULT 'new',email_sent INTEGER DEFAULT 0,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP)''')
    c.execute('''CREATE TABLE IF NOT EXISTS admins(id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,password TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS agents(id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,username TEXT UNIQUE NOT NULL,email TEXT,phone TEXT,
        region TEXT,district TEXT,password TEXT NOT NULL,status TEXT DEFAULT 'active',
        last_seen TEXT,created_at TEXT DEFAULT CURRENT_TIMESTAMP)''')
    c.execute('''CREATE TABLE IF NOT EXISTS messages(id INTEGER PRIMARY KEY AUTOINCREMENT,
        sender_id INTEGER,sender_role TEXT,receiver_id INTEGER,receiver_role TEXT,
        content TEXT,read INTEGER DEFAULT 0,created_at TEXT DEFAULT CURRENT_TIMESTAMP)''')
    c.execute('''CREATE TABLE IF NOT EXISTS supply_requests(id INTEGER PRIMARY KEY AUTOINCREMENT,
        agent_id INTEGER,product_name TEXT,quantity TEXT,notes TEXT,
        status TEXT DEFAULT 'pending',admin_response TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP)''')
    c.execute('''CREATE TABLE IF NOT EXISTS inventory(id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_id INTEGER UNIQUE,stock_qty INTEGER DEFAULT 0,reorder_level INTEGER DEFAULT 10,
        unit TEXT DEFAULT 'units',last_updated TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(product_id) REFERENCES products(id) ON DELETE CASCADE)''')
    c.execute('''CREATE TABLE IF NOT EXISTS newsletter_subscribers(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT, email TEXT UNIQUE NOT NULL,
        active INTEGER DEFAULT 1,
        subscribed_at TEXT DEFAULT CURRENT_TIMESTAMP)''')

    c.execute('''CREATE TABLE IF NOT EXISTS inventory_log(id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_id INTEGER,change_qty INTEGER,reason TEXT,changed_by TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP)''')

    pw=hashlib.sha256('muddo@admin2024'.encode()).hexdigest()
    c.execute('INSERT OR IGNORE INTO admins(username,password) VALUES(?,?)',('admin',pw))

    prods=[
      ('MD-MAIZE PLUS 40OD','herbicide','Selective post-emergence herbicide for maize. Controls grass and broad-leaved weeds.','Nicosulfuron 400g/l','Oil Dispersion (OD)','Maize','0.5–0.75 L/ha','1L, 5L','https://images.unsplash.com/photo-1625246333195-78d9c38ad449?w=600',None),
      ('THRASH 56EC','herbicide','Broad-spectrum post-emergence herbicide for rice.','2,4-D Amine 200g/l + Propanil 360g/l','Emulsifiable Concentrate','Rice, Sugarcane','2–3 L/ha','500ml, 1L, 5L','https://images.unsplash.com/photo-1464226184884-fa280b87c399?w=600',None),
      ('WEED MASTER 480SL','herbicide','Non-selective systemic herbicide for total vegetation control.','Glyphosate 480g/l','Soluble Liquid','All crops (pre-plant)','3–5 L/ha','1L, 5L, 20L','https://images.unsplash.com/photo-1416879595882-3373a0480b5b?w=600',None),
      ('CLEANER 720SL','herbicide','Contact herbicide — visible results in 24 hours.','Paraquat 200g/l + Diquat 40g/l','Soluble Liquid','Coffee, Tea, Maize','2–3 L/ha','1L, 5L','https://images.unsplash.com/photo-1500651230702-0e2d8a49d4ad?w=600',None),
      ('BULLDOCK 25EC','pesticide','Broad-spectrum pyrethroid with contact and stomach action.','Beta-Cypermethrin 25g/l','Emulsifiable Concentrate','Cotton, Vegetables, Maize','500ml–1L/ha','250ml, 500ml, 1L','https://images.unsplash.com/photo-1599420186946-7b6fb4e297f0?w=600',None),
      ('ACEPHATE 75SP','pesticide','Systemic insecticide for aphids, thrips and caterpillars.','Acephate 750g/kg','Soluble Powder','Vegetables, Coffee, Maize','1–1.5 kg/ha','100g, 250g, 1kg','https://images.unsplash.com/photo-1464226184884-fa280b87c399?w=600',None),
      ('LAMBDA SUPER 2.5EC','pesticide','Fast-acting pyrethroid with quick knockdown.','Lambda-Cyhalothrin 25g/l','Emulsifiable Concentrate','Cotton, Maize, Vegetables','300–500ml/ha','250ml, 500ml, 1L','https://images.unsplash.com/photo-1625246333195-78d9c38ad449?w=600',None),
      ('DURSBAN 480EC','pesticide','Broad-spectrum organophosphate for soil and foliar insects.','Chlorpyrifos 480g/l','Emulsifiable Concentrate','Maize, Vegetables, Fruits','1–2 L/ha','500ml, 1L, 5L','https://images.unsplash.com/photo-1500651230702-0e2d8a49d4ad?w=600',None),
      ('RIDOMIL GOLD 68WP','fungicide','Systemic and contact fungicide. Industry gold standard.','Metalaxyl-M 4% + Mancozeb 64%','Wettable Powder','Tomatoes, Potatoes, Onions','2–2.5 kg/ha','100g, 250g, 1kg','https://images.unsplash.com/photo-1416879595882-3373a0480b5b?w=600',None),
      ('SCORE 250EC','fungicide','Broad-spectrum systemic fungicide, preventive and curative.','Difenoconazole 250g/l','Emulsifiable Concentrate','Coffee, Vegetables, Fruits','300–500ml/ha','100ml, 250ml, 500ml','https://images.unsplash.com/photo-1464226184884-fa280b87c399?w=600',None),
      ('MANCOZEB 80WP','fungicide','Protective fungicide against blight, mildew and downy mildew.','Mancozeb 800g/kg','Wettable Powder','Tomatoes, Potatoes, Grapes','1.5–2.5 kg/ha','100g, 500g, 1kg','https://images.unsplash.com/photo-1625246333195-78d9c38ad449?w=600',None),
      ('COPPER OXYCHLORIDE 850WP','fungicide','Protective fungicide with bactericidal properties.','Copper Oxychloride 850g/kg','Wettable Powder','Coffee, Banana, Vegetables','2–3 kg/ha','100g, 500g, 1kg','https://images.unsplash.com/photo-1500651230702-0e2d8a49d4ad?w=600',None),
      ('UREA 46%N','other','High-analysis nitrogen fertilizer for rapid vegetative growth.','Urea 460g/kg Nitrogen','Granular','All crops','50–200 kg/ha','1kg, 5kg, 25kg, 50kg','https://images.unsplash.com/photo-1416879595882-3373a0480b5b?w=600',None),
      ('NPK 17:17:17','other','Balanced compound fertilizer: equal N, P, K.','N 17% + P2O5 17% + K2O 17%','Granular','All crops','200–400 kg/ha','1kg, 5kg, 25kg, 50kg','https://images.unsplash.com/photo-1464226184884-fa280b87c399?w=600',None),
      ('FOLIAR BOOST 20-20-20','other','Water-soluble foliar fertilizer with micro-nutrients.','N 20% + P2O5 20% + K2O 20% + Traces','Water Soluble Powder','Vegetables, Fruits, Coffee','3–5 g/L water','250g, 500g, 1kg','https://images.unsplash.com/photo-1625246333195-78d9c38ad449?w=600',None),
      ('KNAPSACK SPRAYER 16L','other','Manual knapsack sprayer, anti-drip valve, adjustable nozzle.','N/A','Equipment','All applications','N/A','Per unit','https://images.unsplash.com/photo-1500651230702-0e2d8a49d4ad?w=600',None),
    ]
    for p in prods:
        c.execute('INSERT OR IGNORE INTO products(name,category,description,active_ingredient,formulation,crops,dosage,packing,image_url,image_file) VALUES(?,?,?,?,?,?,?,?,?,?)',p)

    dists=[
      ('Muddo Agro HQ','Central','Kampala','Container Village Nakivubo, Equity Bank Basement','+256 772 507582','muddoagro811@gmail.com',0.3136,32.5811),
      ('Kampala City Branch','Central','Kampala','Owino Market, Stall B23','+256 700 112233','kampala@muddo.ug',0.3163,32.5800),
      ('Entebbe Road Outlet','Central','Wakiso','Namulanda Trading Centre, Entebbe Rd','+256 754 223344','entebbe@muddo.ug',0.0667,32.4833),
      ('Jinja Distributor','Eastern','Jinja','Main Street, Jinja Town, Plot 45','+256 782 334455','jinja@muddo.ug',0.4244,33.2041),
      ('Mbale Agro Store','Eastern','Mbale','Republic Street, Mbale, Shop 12','+256 703 445566','mbale@muddo.ug',1.0796,34.1753),
      ('Gulu Northern Branch','Northern','Gulu','Chwa II Road, Gulu Town','+256 772 556677','gulu@muddo.ug',2.7748,32.2990),
      ('Mbarara Western Hub','Western','Mbarara','High Street, Mbarara, Plot 8','+256 786 667788','mbarara@muddo.ug',-0.6072,30.6545),
      ('Fort Portal Outlet','Western','Kabarole','Bwamba Road, Fort Portal','+256 701 778899','ftportal@muddo.ug',0.6620,30.2750),
      ('Lira Agro Centre','Northern','Lira','Obote Avenue, Lira Town','+256 755 889900','lira@muddo.ug',2.2499,32.8998),
      ('Masaka Distributor','Central','Masaka','Birch Avenue, Masaka Town','+256 789 990011','masaka@muddo.ug',-0.3396,31.7369),
    ]
    for d in dists:
        c.execute('INSERT OR IGNORE INTO distributors(name,region,district,address,phone,email,lat,lng) VALUES(?,?,?,?,?,?,?,?)',d)

    demo_agents=[('Alice Namukasa','alice','alice@muddo.ug','+256 701 111001','Central','Kampala'),
                 ('Robert Opio','robert','robert@muddo.ug','+256 702 222002','Eastern','Jinja'),
                 ('Grace Atim','grace','grace@muddo.ug','+256 703 333003','Northern','Gulu')]
    apw=hashlib.sha256('agent@2024'.encode()).hexdigest()
    for ag in demo_agents:
        c.execute('INSERT OR IGNORE INTO agents(name,username,email,phone,region,district,password) VALUES(?,?,?,?,?,?,?)',(*ag,apw))

    all_prods=c.execute('SELECT id FROM products').fetchall()
    for row in all_prods:
        c.execute('INSERT OR IGNORE INTO inventory(product_id,stock_qty,reorder_level,unit) VALUES(?,?,?,?)',
                  (row['id'],random.randint(5,150),10,'units'))
    conn.commit(); conn.close()

def admin_required(f):
    @wraps(f)
    def d(*a,**k):
        if session.get('role')!='admin': return redirect(url_for('login'))
        return f(*a,**k)
    return d

def agent_required(f):
    @wraps(f)
    def d(*a,**k):
        if session.get('role') not in ('admin','agent'): return redirect(url_for('login'))
        return f(*a,**k)
    return d

def update_last_seen():
    if session.get('role')=='agent' and session.get('user_id'):
        conn=get_db(); conn.execute("UPDATE agents SET last_seen=? WHERE id=?",(datetime.now().isoformat(),session['user_id'])); conn.commit(); conn.close()

@app.context_processor
def inject_globals():
    ctx={'now':datetime.now(),'ga_id':GA_ID,'wa_number':WA_NUM}
    if session.get('role')=='admin':
        try:
            conn=get_db()
            ctx['unread_count']=conn.execute("SELECT COUNT(*) FROM messages WHERE receiver_role='admin' AND read=0").fetchone()[0]
            ctx['pending_supply']=conn.execute("SELECT COUNT(*) FROM supply_requests WHERE status='pending'").fetchone()[0]
            ctx['low_stock_count']=conn.execute("SELECT COUNT(*) FROM inventory WHERE stock_qty<=reorder_level").fetchone()[0]
            conn.close()
        except: pass
    elif session.get('role')=='agent':
        try:
            conn=get_db(); ctx['agent_unread']=conn.execute("SELECT COUNT(*) FROM messages WHERE receiver_id=? AND receiver_role='agent' AND read=0",(session['user_id'],)).fetchone()[0]; conn.close()
        except: pass
    return ctx

@app.template_filter('todatetime')
def to_datetime(s):
    try: return datetime.strptime(str(s)[:19].replace('T',' '),'%Y-%m-%d %H:%M:%S')
    except: return datetime(2000,1,1)

@app.template_filter('timeago')
def timeago(s):
    try:
        diff=datetime.now()-to_datetime(s); secs=int(diff.total_seconds())
        if secs<60: return 'just now'
        if secs<3600: return f'{secs//60}m ago'
        if secs<86400: return f'{secs//3600}h ago'
        return f'{secs//86400}d ago'
    except: return '—'

# ── LOGIN ────────────────────────────────────────────────────────────────────
@app.route('/login',methods=['GET','POST'])
def login():
    if session.get('role')=='admin': return redirect(url_for('admin_dashboard'))
    if session.get('role')=='agent': return redirect(url_for('agent_dashboard'))
    if request.method=='POST':
        u=request.form.get('username','').strip(); p=request.form.get('password','')
        r=request.form.get('role','admin'); ph=hashlib.sha256(p.encode()).hexdigest()
        conn=get_db()
        if r=='admin':
            row=conn.execute("SELECT * FROM admins WHERE username=? AND password=?",(u,ph)).fetchone()
            if row:
                session.update({'role':'admin','user_id':row['id'],'username':row['username'],'user_name':'Administrator'})
                conn.close(); return redirect(url_for('admin_dashboard'))
        else:
            row=conn.execute("SELECT * FROM agents WHERE username=? AND password=? AND status='active'",(u,ph)).fetchone()
            if row:
                conn.execute("UPDATE agents SET last_seen=? WHERE id=?",(datetime.now().isoformat(),row['id'])); conn.commit()
                session.update({'role':'agent','user_id':row['id'],'username':row['username'],'user_name':row['name'],'agent_region':row['region'] or ''})
                conn.close(); return redirect(url_for('agent_dashboard'))
        conn.close(); flash('Invalid username or password.','error')
    return render_template('login.html')

@app.route('/logout')
def logout(): session.clear(); return redirect(url_for('login'))
@app.route('/admin/login')
def admin_login(): return redirect(url_for('login'))

# ── PUBLIC ────────────────────────────────────────────────────────────────────
@app.route('/')
def index():
    conn=get_db()
    stats={k:conn.execute(f"SELECT COUNT(*) FROM products WHERE category='{v}'").fetchone()[0]
           for k,v in [('pesticides','pesticide'),('herbicides','herbicide'),('fungicides','fungicide'),('other','other')]}
    stats['distributors']=conn.execute("SELECT COUNT(*) FROM distributors").fetchone()[0]
    featured=conn.execute("SELECT * FROM products ORDER BY RANDOM() LIMIT 6").fetchall()
    conn.close()
    return render_template('index.html',stats=stats,featured=[dict(f) for f in featured])

def product_page(cat,tpl):
    conn=get_db()
    products=conn.execute("""
        SELECT p.*, COALESCE(i.stock_qty,0) as stock_qty, COALESCE(i.unit,'units') as unit
        FROM products p LEFT JOIN inventory i ON i.product_id=p.id
        WHERE p.category=? ORDER BY p.name""",(cat,)).fetchall()
    conn.close()
    return render_template(tpl,products=[dict(p) for p in products])

@app.route('/pesticides')
def pesticides(): return product_page('pesticide','pesticides.html')
@app.route('/herbicides')
def herbicides(): return product_page('herbicide','herbicides.html')
@app.route('/fungicides')
def fungicides(): return product_page('fungicide','fungicides.html')
@app.route('/other-products')
def other_products(): return product_page('other','other_products.html')

@app.route('/product/<int:product_id>')
def product_detail(product_id):
    conn=get_db()
    p=conn.execute("SELECT p.*,COALESCE(i.stock_qty,0) as stock_qty,COALESCE(i.unit,'units') as unit FROM products p LEFT JOIN inventory i ON i.product_id=p.id WHERE p.id=?",(product_id,)).fetchone()
    if not p: conn.close(); return redirect(url_for('index'))
    related=conn.execute("SELECT * FROM products WHERE category=? AND id!=? ORDER BY RANDOM() LIMIT 3",(p['category'],product_id)).fetchall()
    conn.close()
    return render_template('product_detail.html',product=dict(p),related=[dict(r) for r in related])

@app.route('/distributors')
def distributors():
    conn=get_db()
    all_d=conn.execute("SELECT * FROM distributors ORDER BY region,district").fetchall()
    regions=conn.execute("SELECT DISTINCT region FROM distributors ORDER BY region").fetchall()
    conn.close()
    return render_template('distributors.html',distributors=[dict(d) for d in all_d],regions=regions)

@app.route('/api/distributors')
def api_distributors():
    r=request.args.get('region',''); d=request.args.get('district','')
    conn=get_db(); q="SELECT * FROM distributors WHERE 1=1"; params=[]
    if r: q+=" AND region=?"; params.append(r)
    if d: q+=" AND district=?"; params.append(d)
    rows=conn.execute(q,params).fetchall(); conn.close()
    return jsonify([dict(x) for x in rows])

@app.route('/contact',methods=['GET','POST'])
def contact():
    if request.method=='POST':
        ref=gen_ref('ENQ')
        conn=get_db()
        conn.execute("INSERT INTO contact_requests(ref_number,name,email,phone,subject,message) VALUES(?,?,?,?,?,?)",
            (ref,request.form['name'],request.form['email'],request.form.get('phone',''),request.form['subject'],request.form['message']))
        conn.commit()
        sent=send_safe(f'Muddo Agro — Enquiry Received [{ref}]',[request.form['email']],
            render_template('emails/enquiry_confirmation.html',name=request.form['name'],ref=ref,
                subject=request.form['subject'],message=request.form['message']))
        send_safe(f'New Enquiry [{ref}] from {request.form["name"]}',[app.config['MAIL_USERNAME']],
            render_template('emails/admin_new_enquiry.html',name=request.form['name'],
                email=request.form['email'],phone=request.form.get('phone',''),
                ref=ref,subject=request.form['subject'],message=request.form['message']))
        if sent: conn.execute("UPDATE contact_requests SET email_sent=1 WHERE ref_number=?",(ref,)); conn.commit()
        conn.close()
        flash(f'Message sent! Your reference number is <strong>{ref}</strong>. Save it to track your enquiry.','success')
        return redirect(url_for('contact'))
    return render_template('contact.html')

@app.route('/track')
def track():
    ref=request.args.get('ref','').strip().upper(); result=None
    if ref:
        conn=get_db(); result=conn.execute("SELECT * FROM contact_requests WHERE ref_number=?",(ref,)).fetchone(); conn.close()
    return render_template('track.html',ref=ref,result=dict(result) if result else None)

# ── CHAT API ──────────────────────────────────────────────────────────────────
@app.route('/api/chat/messages')
@agent_required
def api_chat_messages():
    update_last_seen()
    wi=request.args.get('with_id',type=int); wr=request.args.get('with_role','agent')
    after=request.args.get('after',0,type=int); mid=session['user_id']; mr=session['role']
    conn=get_db()
    rows=conn.execute("SELECT * FROM messages WHERE id>? AND ((sender_id=? AND sender_role=? AND receiver_id=? AND receiver_role=?) OR (sender_id=? AND sender_role=? AND receiver_id=? AND receiver_role=?)) ORDER BY id ASC LIMIT 100",
        (after,mid,mr,wi,wr,wi,wr,mid,mr)).fetchall()
    conn.close(); return jsonify({'messages':[dict(r) for r in rows]})

@app.route('/api/chat/send',methods=['POST'])
@agent_required
def api_chat_send():
    update_last_seen(); data=request.get_json()
    ti=data.get('to_id'); tr=data.get('to_role','agent'); content=(data.get('content') or '').strip()
    if not content or not ti: return jsonify({'error':'Missing fields'}),400
    mid=session['user_id']; mr=session['role']
    conn=get_db(); conn.execute("INSERT INTO messages(sender_id,sender_role,receiver_id,receiver_role,content) VALUES(?,?,?,?,?)",(mid,mr,ti,tr,content)); conn.commit()
    msg=conn.execute("SELECT * FROM messages WHERE id=last_insert_rowid()").fetchone(); conn.close()
    return jsonify({'message':dict(msg)})

@app.route('/api/chat/unread')
@agent_required
def api_chat_unread():
    mid=session['user_id']; mr=session['role']
    conn=get_db()
    rows=conn.execute("SELECT sender_id,sender_role,COUNT(*) as cnt FROM messages WHERE receiver_id=? AND receiver_role=? AND read=0 GROUP BY sender_id,sender_role",(mid,mr)).fetchall()
    conn.close()
    return jsonify({'total':sum(r['cnt'] for r in rows),'per_contact':{f"{r['sender_id']}_{r['sender_role']}":r['cnt'] for r in rows}})

@app.route('/api/chat/mark-read',methods=['POST'])
@agent_required
def api_chat_mark_read():
    data=request.get_json(); mid=session['user_id']; mr=session['role']
    conn=get_db(); conn.execute("UPDATE messages SET read=1 WHERE sender_id=? AND sender_role=? AND receiver_id=? AND receiver_role=?",(data.get('from_id'),data.get('from_role'),mid,mr)); conn.commit(); conn.close()
    return jsonify({'ok':True})

# ── AGENT ─────────────────────────────────────────────────────────────────────
@app.route('/agent')
@agent_required
def agent_dashboard():
    update_last_seen(); my_id=session['user_id']
    conn=get_db()
    agent=conn.execute("SELECT * FROM agents WHERE id=?",(my_id,)).fetchone()
    my_requests=conn.execute("SELECT * FROM supply_requests WHERE agent_id=? ORDER BY created_at DESC LIMIT 10",(my_id,)).fetchall()
    unread=conn.execute("SELECT COUNT(*) FROM messages WHERE receiver_id=? AND receiver_role='agent' AND read=0",(my_id,)).fetchone()[0]
    last_msg=conn.execute("SELECT * FROM messages WHERE ((sender_role='admin' AND receiver_id=? AND receiver_role='agent') OR (sender_id=? AND sender_role='agent' AND receiver_role='admin')) ORDER BY id DESC LIMIT 1",(my_id,my_id)).fetchone()
    total_products=conn.execute("SELECT COUNT(*) FROM products").fetchone()[0]
    conn.close()
    return render_template('agent/dashboard.html',agent=dict(agent) if agent else {},my_requests=[dict(r) for r in my_requests],unread=unread,last_msg=dict(last_msg) if last_msg else None,total_products=total_products)

@app.route('/agent/chat')
@agent_required
def agent_chat():
    update_last_seen(); conn=get_db()
    admin=conn.execute("SELECT id FROM admins LIMIT 1").fetchone()
    unread=conn.execute("SELECT COUNT(*) FROM messages WHERE receiver_id=? AND receiver_role='agent' AND read=0",(session['user_id'],)).fetchone()[0]
    conn.close()
    return render_template('agent/chat.html',admin_id=admin['id'] if admin else 1,unread=unread)

@app.route('/agent/supply-request',methods=['POST'])
@agent_required
def agent_supply_request():
    update_last_seen(); conn=get_db()
    conn.execute("INSERT INTO supply_requests(agent_id,product_name,quantity,notes) VALUES(?,?,?,?)",
        (session['user_id'],request.form.get('product_name',''),request.form.get('quantity',''),request.form.get('notes','')))
    conn.commit(); conn.close(); flash('Supply request submitted!','success')
    return redirect(url_for('agent_dashboard'))

# ── ADMIN ─────────────────────────────────────────────────────────────────────
@app.route('/admin')
@admin_required
def admin_dashboard():
    conn=get_db()
    stats={
        'total_products':conn.execute("SELECT COUNT(*) FROM products").fetchone()[0],
        'total_distributors':conn.execute("SELECT COUNT(*) FROM distributors").fetchone()[0],
        'total_requests':conn.execute("SELECT COUNT(*) FROM contact_requests").fetchone()[0],
        'new_requests':conn.execute("SELECT COUNT(*) FROM contact_requests WHERE status='new'").fetchone()[0],
        'total_agents':conn.execute("SELECT COUNT(*) FROM agents").fetchone()[0],
        'active_agents':conn.execute("SELECT COUNT(*) FROM agents WHERE status='active'").fetchone()[0],
        'pending_supply':conn.execute("SELECT COUNT(*) FROM supply_requests WHERE status='pending'").fetchone()[0],
        'unread_msgs':conn.execute("SELECT COUNT(*) FROM messages WHERE receiver_role='admin' AND read=0").fetchone()[0],
        'low_stock':conn.execute("SELECT COUNT(*) FROM inventory WHERE stock_qty<=reorder_level").fetchone()[0],
    }
    rr=conn.execute("SELECT * FROM contact_requests ORDER BY created_at DESC LIMIT 5").fetchall()
    pc=conn.execute("SELECT category,COUNT(*) as cnt FROM products GROUP BY category").fetchall()
    agents=conn.execute("SELECT * FROM agents ORDER BY last_seen DESC LIMIT 20").fetchall()
    rs=conn.execute("SELECT sr.*,a.name as agent_name FROM supply_requests sr JOIN agents a ON sr.agent_id=a.id ORDER BY sr.created_at DESC LIMIT 5").fetchall()
    rm=conn.execute("SELECT m.*,a.name as sender_name FROM messages m LEFT JOIN agents a ON m.sender_id=a.id WHERE m.receiver_role='admin' ORDER BY m.created_at DESC LIMIT 5").fetchall()
    ls=conn.execute("SELECT p.name,p.category,i.stock_qty,i.reorder_level,i.unit FROM inventory i JOIN products p ON p.id=i.product_id WHERE i.stock_qty<=i.reorder_level ORDER BY i.stock_qty ASC LIMIT 5").fetchall()
    conn.close()
    return render_template('admin/dashboard.html',stats=stats,recent_requests=rr,products_by_cat=pc,agents=[dict(a) for a in agents],recent_supply=rs,recent_msgs=rm,low_stock_items=ls)

@app.route('/admin/products')
@admin_required
def admin_products():
    conn=get_db()
    prods=conn.execute("SELECT p.*,COALESCE(i.stock_qty,0) as stock_qty,COALESCE(i.reorder_level,10) as reorder_level,COALESCE(i.unit,'units') as unit FROM products p LEFT JOIN inventory i ON i.product_id=p.id ORDER BY p.category,p.name").fetchall()
    conn.close(); return render_template('admin/products.html',products=prods)

@app.route('/admin/products/add',methods=['POST'])
@admin_required
def admin_add_product():
    img_file=None
    if 'product_image' in request.files:
        f=request.files['product_image']
        if f and f.filename and allowed_file(f.filename):
            fname=secure_filename(f'{uuid.uuid4().hex}_{f.filename}')
            os.makedirs(UPLOAD_DIR,exist_ok=True); f.save(os.path.join(UPLOAD_DIR,fname)); img_file=fname
    conn=get_db()
    conn.execute("INSERT INTO products(name,category,description,active_ingredient,formulation,crops,dosage,packing,image_url,image_file) VALUES(?,?,?,?,?,?,?,?,?,?)",
        (request.form['name'],request.form['category'],request.form['description'],request.form['active_ingredient'],
         request.form['formulation'],request.form['crops'],request.form['dosage'],request.form['packing'],
         request.form.get('image_url',''),img_file))
    conn.commit()
    pid=conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    conn.execute("INSERT OR REPLACE INTO inventory(product_id,stock_qty,reorder_level,unit) VALUES(?,?,?,?)",
        (pid,int(request.form.get('stock_qty',0) or 0),int(request.form.get('reorder_level',10) or 10),request.form.get('unit','units')))
    conn.commit(); conn.close(); flash('Product added!','success')
    return redirect(url_for('admin_products'))

@app.route('/admin/products/delete/<int:pid>',methods=['POST'])
@admin_required
def admin_delete_product(pid):
    conn=get_db()
    p=conn.execute("SELECT image_file FROM products WHERE id=?",(pid,)).fetchone()
    if p and p['image_file']:
        try: os.remove(os.path.join(UPLOAD_DIR,p['image_file']))
        except: pass
    conn.execute("DELETE FROM products WHERE id=?",(pid,)); conn.commit(); conn.close()
    flash('Product deleted.','success'); return redirect(url_for('admin_products'))

@app.route('/admin/requests')
@admin_required
def admin_requests():
    conn=get_db(); reqs=conn.execute("SELECT * FROM contact_requests ORDER BY created_at DESC").fetchall(); conn.close()
    return render_template('admin/requests.html',requests=reqs)

@app.route('/admin/requests/update/<int:rid>',methods=['POST'])
@admin_required
def admin_update_request(rid):
    conn=get_db(); conn.execute("UPDATE contact_requests SET status=? WHERE id=?",(request.form.get('status','resolved'),rid)); conn.commit(); conn.close()
    return redirect(url_for('admin_requests'))

@app.route('/admin/distributors')
@admin_required
def admin_distributors():
    conn=get_db(); d=conn.execute("SELECT * FROM distributors ORDER BY region").fetchall(); conn.close()
    return render_template('admin/distributors.html',distributors=[dict(x) for x in d])

@app.route('/admin/distributors/add',methods=['POST'])
@admin_required
def admin_add_distributor():
    conn=get_db()
    conn.execute("INSERT INTO distributors(name,region,district,address,phone,email,lat,lng) VALUES(?,?,?,?,?,?,?,?)",
        (request.form['name'],request.form['region'],request.form['district'],request.form['address'],
         request.form['phone'],request.form.get('email',''),float(request.form.get('lat',0)),float(request.form.get('lng',0))))
    conn.commit(); conn.close(); flash('Distributor added!','success'); return redirect(url_for('admin_distributors'))

@app.route('/admin/distributors/delete/<int:did>',methods=['POST'])
@admin_required
def admin_delete_distributor(did):
    conn=get_db(); conn.execute("DELETE FROM distributors WHERE id=?",(did,)); conn.commit(); conn.close()
    flash('Distributor removed.','success'); return redirect(url_for('admin_distributors'))

@app.route('/admin/agents')
@admin_required
def admin_agents():
    conn=get_db(); agents=conn.execute("SELECT * FROM agents ORDER BY created_at DESC").fetchall(); conn.close()
    return render_template('admin/agents.html',agents=[dict(a) for a in agents])

@app.route('/admin/agents/add',methods=['POST'])
@admin_required
def admin_add_agent():
    ph=hashlib.sha256(request.form['password'].encode()).hexdigest(); conn=get_db()
    try:
        conn.execute("INSERT INTO agents(name,username,email,phone,region,district,password) VALUES(?,?,?,?,?,?,?)",
            (request.form['name'],request.form['username'],request.form.get('email',''),request.form.get('phone',''),
             request.form.get('region',''),request.form.get('district',''),ph))
        conn.commit()
        if request.form.get('email'):
            send_safe('Welcome to Muddo Agro — Agent Account',[request.form['email']],
                render_template('emails/agent_welcome.html',name=request.form['name'],username=request.form['username']))
        flash(f'Agent added!','success')
    except: flash('Error: Username may exist.','error')
    conn.close(); return redirect(url_for('admin_agents'))

@app.route('/admin/agents/delete/<int:aid>',methods=['POST'])
@admin_required
def admin_delete_agent(aid):
    conn=get_db(); conn.execute("DELETE FROM agents WHERE id=?",(aid,)); conn.commit(); conn.close()
    flash('Agent removed.','success'); return redirect(url_for('admin_agents'))

@app.route('/admin/agents/toggle/<int:aid>',methods=['POST'])
@admin_required
def admin_toggle_agent(aid):
    conn=get_db(); cur=conn.execute("SELECT status FROM agents WHERE id=?",(aid,)).fetchone()
    ns='inactive' if cur and cur['status']=='active' else 'active'
    conn.execute("UPDATE agents SET status=? WHERE id=?",(ns,aid)); conn.commit(); conn.close()
    flash(f'Agent set to {ns}.','success'); return redirect(url_for('admin_agents'))

@app.route('/admin/chat')
@admin_required
def admin_chat():
    conn=get_db()
    agents=conn.execute("SELECT * FROM agents WHERE status='active' ORDER BY name").fetchall()
    ur=conn.execute("SELECT sender_id,COUNT(*) as cnt FROM messages WHERE receiver_role='admin' AND read=0 GROUP BY sender_id").fetchall()
    conn.close()
    return render_template('admin/chat.html',agents=[dict(a) for a in agents],unread_map={r['sender_id']:r['cnt'] for r in ur})

@app.route('/admin/supply-requests')
@admin_required
def admin_supply_requests():
    conn=get_db()
    reqs=conn.execute("SELECT sr.*,a.name as agent_name,a.region FROM supply_requests sr JOIN agents a ON sr.agent_id=a.id ORDER BY sr.created_at DESC").fetchall()
    conn.close(); return render_template('admin/supply_requests.html',requests=reqs)

@app.route('/admin/supply-requests/respond/<int:rid>',methods=['POST'])
@admin_required
def admin_respond_supply(rid):
    status=request.form.get('status','approved'); response=request.form.get('response','')
    conn=get_db()
    conn.execute("UPDATE supply_requests SET status=?,admin_response=? WHERE id=?",(status,response,rid))
    req=conn.execute("SELECT sr.*,a.name as agent_name,a.email FROM supply_requests sr JOIN agents a ON sr.agent_id=a.id WHERE sr.id=?",(rid,)).fetchone()
    if req:
        msg=f"Your supply request for '{req['product_name']}' has been {status}. {response}"
        conn.execute("INSERT INTO messages(sender_id,sender_role,receiver_id,receiver_role,content) VALUES(1,'admin',?,?,?)",(req['agent_id'],'agent',msg))
        if req['email']:
            send_safe(f'Supply Request {status.title()} — Muddo Agro',[req['email']],
                render_template('emails/supply_response.html',agent_name=req['agent_name'],product=req['product_name'],status=status,response=response))
    conn.commit(); conn.close(); flash(f'Supply request {status}.','success')
    return redirect(url_for('admin_supply_requests'))

# ── INVENTORY ─────────────────────────────────────────────────────────────────
@app.route('/admin/inventory')
@admin_required
def admin_inventory():
    conn=get_db()
    items=conn.execute("SELECT p.id,p.name,p.category,p.image_url,p.image_file,COALESCE(i.stock_qty,0) as stock_qty,COALESCE(i.reorder_level,10) as reorder_level,COALESCE(i.unit,'units') as unit,i.last_updated FROM products p LEFT JOIN inventory i ON i.product_id=p.id ORDER BY p.category,p.name").fetchall()
    log=conn.execute("SELECT il.*,p.name as product_name FROM inventory_log il JOIN products p ON p.id=il.product_id ORDER BY il.created_at DESC LIMIT 40").fetchall()
    conn.close()
    return render_template('admin/inventory.html',items=[dict(i) for i in items],log=log)

@app.route('/admin/inventory/update',methods=['POST'])
@admin_required
def admin_update_inventory():
    pid=int(request.form['product_id']); action=request.form.get('action','set')
    qty=int(request.form.get('qty',0) or 0); reason=request.form.get('reason','Manual update')
    unit=request.form.get('unit','units'); reorder=int(request.form.get('reorder_level',10) or 10)
    conn=get_db()
    ex=conn.execute("SELECT stock_qty FROM inventory WHERE product_id=?",(pid,)).fetchone()
    cur=ex['stock_qty'] if ex else 0
    if action=='add': new_qty=cur+qty; change=qty
    elif action=='remove': new_qty=max(0,cur-qty); change=-qty
    else: new_qty=qty; change=qty-cur
    conn.execute("INSERT OR REPLACE INTO inventory(product_id,stock_qty,reorder_level,unit,last_updated) VALUES(?,?,?,?,?)",(pid,new_qty,reorder,unit,datetime.now().isoformat()))
    conn.execute("INSERT INTO inventory_log(product_id,change_qty,reason,changed_by) VALUES(?,?,?,?)",(pid,change,reason,session.get('username','admin')))
    conn.commit(); conn.close()
    return jsonify({'ok':True,'new_qty':new_qty})

# ── QUOTES ────────────────────────────────────────────────────────────────────
@app.route('/admin/quotes')
@admin_required
def admin_quotes():
    conn=get_db(); prods=conn.execute("SELECT * FROM products ORDER BY category,name").fetchall(); conn.close()
    return render_template('admin/quotes.html',products=[dict(p) for p in prods])

@app.route('/admin/quotes/generate',methods=['POST'])
@admin_required
def generate_quote():
    data=request.get_json()
    cname=data.get('client_name','Valued Customer'); cemail=data.get('client_email','')
    cphone=data.get('client_phone',''); items=data.get('items',[]); notes=data.get('notes','')
    valid_days=int(data.get('valid_days',30)); qref=gen_ref('QUO')
    conn=get_db(); pmap={str(p['id']):dict(p) for p in conn.execute("SELECT * FROM products").fetchall()}; conn.close()

    buf=io.BytesIO()
    doc=SimpleDocTemplate(buf,pagesize=A4,leftMargin=18*mm,rightMargin=18*mm,topMargin=16*mm,bottomMargin=16*mm)
    GREEN_DARK=colors.HexColor('#0d2b14'); GREEN_MID=colors.HexColor('#2d6e35')
    GOLD=colors.HexColor('#c8a84b'); BLUE=colors.HexColor('#1565c0')
    LIGHT_GREEN=colors.HexColor('#e8f5e9'); LIGHT_BLUE=colors.HexColor('#e3f2fd')
    LIGHT_GREY=colors.HexColor('#f5f5f5'); BLACK=colors.HexColor('#111111')
    MUTED=colors.HexColor('#565656'); WHITE=colors.white
    bold=ParagraphStyle('B',fontName='Helvetica-Bold',fontSize=10,textColor=BLACK)
    lbl=ParagraphStyle('L',fontName='Helvetica',fontSize=9,textColor=MUTED)
    h1=ParagraphStyle('H1',fontName='Helvetica-Bold',fontSize=22,textColor=WHITE)
    h2=ParagraphStyle('H2',fontName='Helvetica-Bold',fontSize=13,textColor=GREEN_DARK)
    body=ParagraphStyle('BD',fontName='Helvetica',fontSize=10,textColor=BLACK,leading=14)
    small=ParagraphStyle('S',fontName='Helvetica',fontSize=8.5,textColor=MUTED)
    gold_s=ParagraphStyle('G',fontName='Helvetica-Bold',fontSize=11,textColor=GOLD)

    story=[]
    # Header
    ht=Table([[Paragraph('<b>MUDDO AGRO CHEMICALS LTD</b>',h1),
               Paragraph(f'<b>QUOTATION</b><br/><font size="11">{qref}</font>',
                         ParagraphStyle('R',fontName='Helvetica-Bold',fontSize=14,textColor=GOLD,alignment=TA_RIGHT))]],
             colWidths=[95*mm,79*mm])
    ht.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),GREEN_DARK),('PADDING',(0,0),(-1,-1),14),('VALIGN',(0,0),(-1,-1),'MIDDLE')]))
    story.append(ht)
    # Tagline
    tl=Table([[Paragraph('Distributor of Agricultural Chemicals — Container Village Nakivubo, Kampala, Uganda',small),
               Paragraph('+256 772 507582  |  muddoagro811@gmail.com',ParagraphStyle('CT',fontName='Helvetica',fontSize=8.5,textColor=MUTED,alignment=TA_RIGHT))]],
             colWidths=[105*mm,69*mm])
    tl.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),LIGHT_GREEN),('PADDING',(0,0),(-1,-1),8),('LINEBELOW',(0,0),(-1,-1),1,GREEN_MID)]))
    story.append(tl); story.append(Spacer(1,8*mm))
    # Meta
    mt=Table([[Paragraph('<b>PREPARED FOR</b>',lbl),Paragraph('<b>QUOTE DETAILS</b>',lbl)],
              [Paragraph(f'<b>{cname}</b>',bold),Paragraph(f'<b>Ref:</b> {qref}',bold)],
              [Paragraph(cemail or '—',body),Paragraph(f'<b>Date:</b> {datetime.now().strftime("%d %B %Y")}',body)],
              [Paragraph(cphone or '—',body),Paragraph(f'<b>Valid until:</b> {(datetime.now()+timedelta(days=valid_days)).strftime("%d %B %Y")}',body)]],
             colWidths=[87*mm,87*mm])
    mt.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),LIGHT_BLUE),('PADDING',(0,0),(-1,-1),7),('LINEBELOW',(0,0),(-1,0),0.5,BLUE),('LINEBELOW',(0,-1),(-1,-1),0.5,colors.HexColor('#e0e0e0'))]))
    story.append(mt); story.append(Spacer(1,8*mm))
    story.append(Paragraph('<b>ITEMS QUOTED</b>',h2)); story.append(Spacer(1,3*mm))
    cw=[8*mm,60*mm,20*mm,22*mm,18*mm,22*mm,24*mm]
    hdr=['#','Product / Description','Category','Pack Size','Qty','Unit Price (UGX)','Total (UGX)']
    rows=[[Paragraph(f'<b>{h}</b>',ParagraphStyle('TH',fontName='Helvetica-Bold',fontSize=8,textColor=WHITE)) for h in hdr]]
    grand=0
    for i,item in enumerate(items):
        pid=str(item.get('product_id','')); p=pmap.get(pid,{})
        qty=float(item.get('qty',1) or 1); price=float(item.get('unit_price',0) or 0); total=qty*price; grand+=total
        rows.append([Paragraph(str(i+1),small),
                     Paragraph(f'<b>{p.get("name","Item")}</b><br/><font size="7.5" color="#565656">{(p.get("active_ingredient","") or "")[:55]}</font>',body),
                     Paragraph((p.get('category') or '—').title(),small),
                     Paragraph(p.get('packing','—'),small),
                     Paragraph(str(int(qty)),small),
                     Paragraph(f'{price:,.0f}',small),
                     Paragraph(f'{total:,.0f}',bold)])
    rows.append(['']*7)
    rows.append(['','','','','',Paragraph('<b>GRAND TOTAL</b>',bold),Paragraph(f'<b>UGX {grand:,.0f}</b>',ParagraphStyle('GT',fontName='Helvetica-Bold',fontSize=11,textColor=GREEN_MID))])
    it=Table(rows,colWidths=cw,repeatRows=1)
    it.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,0),GREEN_DARK),('TEXTCOLOR',(0,0),(-1,0),WHITE),
        ('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),('FONTSIZE',(0,0),(-1,0),8),
        ('ALIGN',(4,1),(-1,-1),'RIGHT'),('ALIGN',(0,0),(0,-1),'CENTER'),
        ('ROWBACKGROUNDS',(0,1),(-1,-3),[WHITE,LIGHT_GREY]),
        ('BACKGROUND',(0,-1),(-1,-1),LIGHT_GREEN),('FONTNAME',(0,-1),(-1,-1),'Helvetica-Bold'),
        ('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6),
        ('LEFTPADDING',(0,0),(-1,-1),5),('RIGHTPADDING',(0,0),(-1,-1),5),
        ('GRID',(0,0),(-1,-1),0.3,colors.HexColor('#e0e0e0')),
    ]))
    story.append(it); story.append(Spacer(1,6*mm))
    if notes: story.append(Paragraph('<b>NOTES</b>',h2)); story.append(Spacer(1,2*mm)); story.append(Paragraph(notes,body)); story.append(Spacer(1,6*mm))
    story.append(HRFlowable(width="100%",thickness=0.5,color=colors.HexColor('#e0e0e0'))); story.append(Spacer(1,4*mm))
    story.append(Paragraph('<b>TERMS &amp; CONDITIONS</b>',ParagraphStyle('TC',fontName='Helvetica-Bold',fontSize=9,textColor=GREEN_MID))); story.append(Spacer(1,2*mm))
    story.append(Paragraph('1. Prices in UGX, exclusive of delivery. 2. Quote valid for the period stated. 3. 50% deposit required before dispatch; balance on delivery. 4. Lead time: 2–5 days Kampala; 5–10 days upcountry. 5. All products are MAAIF-registered.',small))
    story.append(Spacer(1,6*mm))
    ft=Table([[Paragraph('Thank you for considering Muddo Agro Chemicals LTD',gold_s),Paragraph('Authorised: ________________________',ParagraphStyle('SIG',fontName='Helvetica',fontSize=9,textColor=MUTED,alignment=TA_RIGHT))]],colWidths=[105*mm,69*mm])
    ft.setStyle(TableStyle([('LINEABOVE',(0,0),(-1,0),0.5,colors.HexColor('#e0e0e0')),('TOPPADDING',(0,0),(-1,0),8)]))
    story.append(ft)
    doc.build(story); buf.seek(0)
    return send_file(buf,mimetype='application/pdf',as_attachment=True,download_name=f'Muddo_Agro_Quote_{qref}.pdf')

@app.route('/uploads/products/<filename>')
def uploaded_product_image(filename):
    return send_file(os.path.join(UPLOAD_DIR,filename))

if __name__=='__main__':
    # Warn if using default secret key in what looks like production
    if app.secret_key.startswith('muddo_agro_dev_only') and os.environ.get('PORT'):
        import warnings
        warnings.warn('⚠️  Using default secret key in production! Set FLASK_SECRET_KEY env var.')
    os.makedirs(UPLOAD_DIR,exist_ok=True); init_db()
    app.run(debug=True,port=5000)

# ── HELPER: get display image URL for a product ──────────────────────────────
def get_product_image(product):
    """Return the best image URL: uploaded file > URL > placeholder"""
    if isinstance(product, dict):
        img_file = product.get('image_file')
        img_url  = product.get('image_url', '')
    else:
        img_file = getattr(product, 'image_file', None)
        img_url  = getattr(product, 'image_url', '')
    if img_file:
        return url_for('uploaded_product_image', filename=img_file)
    if img_url:
        return img_url
    return 'https://images.unsplash.com/photo-1416879595882-3373a0480b5b?w=600'

app.jinja_env.globals['get_product_image'] = get_product_image

# ── SETTINGS PAGE ────────────────────────────────────────────────────────────
@app.route('/admin/settings', methods=['GET', 'POST'])
@admin_required
def admin_settings():
    conn = get_db()
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'change_password':
            old_pw   = request.form.get('old_password', '')
            new_pw   = request.form.get('new_password', '')
            conf_pw  = request.form.get('confirm_password', '')
            if new_pw != conf_pw:
                flash('New passwords do not match.', 'error')
            elif len(new_pw) < 8:
                flash('Password must be at least 8 characters.', 'error')
            else:
                old_hash = hashlib.sha256(old_pw.encode()).hexdigest()
                admin = conn.execute("SELECT * FROM admins WHERE id=? AND password=?", (session['user_id'], old_hash)).fetchone()
                if not admin:
                    flash('Current password is incorrect.', 'error')
                else:
                    new_hash = hashlib.sha256(new_pw.encode()).hexdigest()
                    conn.execute("UPDATE admins SET password=? WHERE id=?", (new_hash, session['user_id']))
                    conn.commit()
                    flash('Password updated successfully!', 'success')
        elif action == 'reset_agent_password':
            agent_id = int(request.form.get('agent_id', 0))
            new_pw   = request.form.get('new_agent_password', '')
            if len(new_pw) < 6:
                flash('Password must be at least 6 characters.', 'error')
            else:
                new_hash = hashlib.sha256(new_pw.encode()).hexdigest()
                conn.execute("UPDATE agents SET password=? WHERE id=?", (new_hash, agent_id))
                conn.commit()
                flash('Agent password reset successfully!', 'success')
    agents = conn.execute("SELECT id, name, username, region FROM agents ORDER BY name").fetchall()
    conn.close()
    return render_template('admin/settings.html', agents=agents)

# ── LOW STOCK API ─────────────────────────────────────────────────────────────
@app.route('/api/admin/low-stock')
@admin_required
def api_low_stock():
    conn = get_db()
    items = conn.execute("""
        SELECT p.name, p.category, i.stock_qty, i.reorder_level, i.unit
        FROM inventory i JOIN products p ON p.id=i.product_id
        WHERE i.stock_qty <= i.reorder_level
        ORDER BY i.stock_qty ASC LIMIT 10
    """).fetchall()
    conn.close()
    return jsonify([dict(i) for i in items])

# ── ANALYTICS DATA (dashboard charts) ─────────────────────────────────────────
@app.route('/api/admin/analytics')
@admin_required
def api_analytics():
    conn = get_db()
    # Requests per day (last 14 days)
    daily = conn.execute("""
        SELECT substr(created_at,1,10) as day, COUNT(*) as cnt
        FROM contact_requests
        WHERE created_at >= date('now','-14 days')
        GROUP BY day ORDER BY day
    """).fetchall()
    # Supply requests by status
    supply_stats = conn.execute("SELECT status, COUNT(*) as cnt FROM supply_requests GROUP BY status").fetchall()
    conn.close()
    return jsonify({
        'daily_enquiries': [dict(r) for r in daily],
        'supply_by_status': [dict(r) for r in supply_stats],
    })

# ── ERROR HANDLERS ────────────────────────────────────────────────────────────
@app.errorhandler(404)
def not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def server_error(e):
    return render_template('404.html'), 500  # Reuse 404 template for simplicity

# ═══════════════════════════════════════════════════════════════════════════
# FEATURE 1: SITE-WIDE SEARCH
# ═══════════════════════════════════════════════════════════════════════════
@app.route('/search')
def search():
    q = request.args.get('q', '').strip()
    results = {'products': [], 'distributors': []}
    if q and len(q) >= 2:
        like = f'%{q}%'
        conn = get_db()
        results['products'] = [dict(p) for p in conn.execute(
            "SELECT * FROM products WHERE name LIKE ? OR description LIKE ? OR active_ingredient LIKE ? OR crops LIKE ? ORDER BY name LIMIT 20",
            (like, like, like, like)).fetchall()]
        results['distributors'] = [dict(d) for d in conn.execute(
            "SELECT * FROM distributors WHERE name LIKE ? OR district LIKE ? OR region LIKE ? ORDER BY region LIMIT 10",
            (like, like, like)).fetchall()]
        conn.close()
    return render_template('search.html', q=q, results=results)

@app.route('/api/search')
def api_search():
    q = request.args.get('q', '').strip()
    if len(q) < 2:
        return jsonify([])
    like = f'%{q}%'
    conn = get_db()
    rows = conn.execute(
        "SELECT id, name, category, image_url, image_file FROM products WHERE name LIKE ? OR active_ingredient LIKE ? ORDER BY name LIMIT 8",
        (like, like)).fetchall()
    conn.close()
    out = []
    for r in rows:
        img = get_product_image(dict(r))
        out.append({'id': r['id'], 'name': r['name'], 'category': r['category'], 'image': img})
    return jsonify(out)

# ═══════════════════════════════════════════════════════════════════════════
# FEATURE 2: SEO — sitemap + robots
# ═══════════════════════════════════════════════════════════════════════════
@app.route('/sitemap.xml')
def sitemap():
    conn = get_db()
    products = conn.execute("SELECT id, created_at FROM products ORDER BY id").fetchall()
    conn.close()
    urls = [
        ('/', '1.0', 'weekly'),
        ('/pesticides', '0.9', 'weekly'),
        ('/herbicides', '0.9', 'weekly'),
        ('/fungicides', '0.9', 'weekly'),
        ('/other-products', '0.9', 'weekly'),
        ('/distributors', '0.8', 'monthly'),
        ('/contact', '0.7', 'monthly'),
        ('/track', '0.5', 'monthly'),
    ]
    xml = ['<?xml version="1.0" encoding="UTF-8"?>',
           '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    base = request.host_url.rstrip('/')
    for path, priority, freq in urls:
        xml.append(f'  <url><loc>{base}{path}</loc><priority>{priority}</priority><changefreq>{freq}</changefreq></url>')
    for p in products:
        xml.append(f'  <url><loc>{base}/product/{p["id"]}</loc><priority>0.8</priority><changefreq>monthly</changefreq></url>')
    xml.append('</urlset>')
    return '\n'.join(xml), 200, {'Content-Type': 'application/xml'}

@app.route('/robots.txt')
def robots():
    lines = [
        'User-agent: *',
        'Allow: /',
        'Disallow: /admin',
        'Disallow: /agent',
        'Disallow: /login',
        'Disallow: /api/',
        f'Sitemap: {request.host_url}sitemap.xml',
    ]
    return '\n'.join(lines), 200, {'Content-Type': 'text/plain'}

# ═══════════════════════════════════════════════════════════════════════════
# FEATURE 7: NEWSLETTER SIGNUP
# ═══════════════════════════════════════════════════════════════════════════
@app.route('/newsletter/subscribe', methods=['POST'])
def newsletter_subscribe():
    email = request.form.get('email', '').strip().lower()
    name  = request.form.get('name', '').strip()
    if not email or '@' not in email:
        return jsonify({'ok': False, 'msg': 'Invalid email address.'}), 400
    conn = get_db()
    # Ensure newsletter table exists
    conn.execute('''CREATE TABLE IF NOT EXISTS newsletter_subscribers(
        id INTEGER PRIMARY KEY AUTOINCREMENT, email TEXT UNIQUE NOT NULL,
        name TEXT, subscribed_at TEXT DEFAULT CURRENT_TIMESTAMP, active INTEGER DEFAULT 1)''')
    try:
        conn.execute("INSERT INTO newsletter_subscribers(email,name) VALUES(?,?)", (email, name))
        conn.commit()
        # Welcome email
        send_safe(
            'Welcome to Muddo Agro Updates!',
            [email],
            render_template('emails/newsletter_welcome.html', name=name or 'Farmer', email=email)
        )
        conn.close()
        return jsonify({'ok': True, 'msg': 'Subscribed! Check your email.'})
    except Exception:
        conn.close()
        return jsonify({'ok': False, 'msg': 'Already subscribed — thank you!'}), 400

@app.route('/admin/newsletter')
@admin_required
def admin_newsletter():
    conn = get_db()
    conn.execute('''CREATE TABLE IF NOT EXISTS newsletter_subscribers(
        id INTEGER PRIMARY KEY AUTOINCREMENT, email TEXT UNIQUE NOT NULL,
        name TEXT, subscribed_at TEXT DEFAULT CURRENT_TIMESTAMP, active INTEGER DEFAULT 1)''')
    subs = conn.execute("SELECT * FROM newsletter_subscribers ORDER BY subscribed_at DESC").fetchall()
    conn.close()
    return render_template('admin/newsletter.html', subscribers=subs)

# ═══════════════════════════════════════════════════════════════════════════
# FEATURE 4: CSV BULK IMPORT
# ═══════════════════════════════════════════════════════════════════════════
@app.route('/admin/import', methods=['GET', 'POST'])
@admin_required
def admin_import():
    results = None
    if request.method == 'POST':
        f = request.files.get('csv_file')
        if not f or not f.filename.endswith('.csv'):
            flash('Please upload a .csv file.', 'error')
            return redirect(url_for('admin_import'))
        import csv, io as _io
        content  = f.read().decode('utf-8-sig', errors='replace')
        reader   = csv.DictReader(_io.StringIO(content))
        added    = 0; skipped = 0; errors = []
        conn     = get_db()
        for row in reader:
            try:
                name = (row.get('name') or row.get('Name') or '').strip()
                cat  = (row.get('category') or row.get('Category') or '').strip().lower()
                if not name or cat not in ('pesticide','herbicide','fungicide','other'):
                    skipped += 1; continue
                conn.execute(
                    "INSERT OR IGNORE INTO products(name,category,description,active_ingredient,formulation,crops,dosage,packing,image_url) VALUES(?,?,?,?,?,?,?,?,?)",
                    (name, cat,
                     (row.get('description') or row.get('Description') or '').strip(),
                     (row.get('active_ingredient') or row.get('Active Ingredient') or '').strip(),
                     (row.get('formulation') or row.get('Formulation') or '').strip(),
                     (row.get('crops') or row.get('Crops') or '').strip(),
                     (row.get('dosage') or row.get('Dosage') or '').strip(),
                     (row.get('packing') or row.get('Packing') or '').strip(),
                     (row.get('image_url') or row.get('Image URL') or '').strip()))
                added += 1
            except Exception as e:
                errors.append(str(e))
        conn.commit(); conn.close()
        results = {'added': added, 'skipped': skipped, 'errors': errors}
    return render_template('admin/import.html', results=results)

# ═══════════════════════════════════════════════════════════════════════════
# FEATURE 6: PRINT SPEC SHEET (single-product PDF)
# ═══════════════════════════════════════════════════════════════════════════
@app.route('/product/<int:product_id>/spec-sheet')
def product_spec_sheet(product_id):
    conn = get_db()
    p = conn.execute(
        "SELECT pr.*, COALESCE(i.stock_qty,0) as stock_qty, COALESCE(i.unit,'units') as unit "
        "FROM products pr LEFT JOIN inventory i ON i.product_id=pr.id WHERE pr.id=?",
        (product_id,)).fetchone()
    conn.close()
    if not p:
        abort(404)
    p = dict(p)

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
                            leftMargin=20*mm, rightMargin=20*mm,
                            topMargin=18*mm, bottomMargin=18*mm)
    G_DARK  = colors.HexColor('#0d2b14')
    G_MID   = colors.HexColor('#2d6e35')
    GOLD    = colors.HexColor('#c8a84b')
    LGREY   = colors.HexColor('#f5f5f5')
    LGREEN  = colors.HexColor('#e8f5e9')
    BLACK   = colors.HexColor('#111111')
    MUTED   = colors.HexColor('#565656')
    WHITE   = colors.white

    cat_colors = {'pesticide': colors.HexColor('#e53935'), 'herbicide': G_MID,
                  'fungicide': colors.HexColor('#3f51b5'), 'other': colors.HexColor('#f57c00')}
    cat_color  = cat_colors.get(p.get('category', 'other'), G_MID)

    bold  = ParagraphStyle('B', fontName='Helvetica-Bold',  fontSize=10, textColor=BLACK)
    body  = ParagraphStyle('BD',fontName='Helvetica',        fontSize=10, textColor=BLACK, leading=15)
    small = ParagraphStyle('S', fontName='Helvetica',        fontSize=8.5,textColor=MUTED)
    h1    = ParagraphStyle('H1',fontName='Helvetica-Bold',   fontSize=20, textColor=WHITE)
    h2    = ParagraphStyle('H2',fontName='Helvetica-Bold',   fontSize=12, textColor=G_DARK)
    gold  = ParagraphStyle('G', fontName='Helvetica-Bold',   fontSize=10, textColor=GOLD)

    story = []

    # Header
    cat_label = p.get('category','').title()
    hdr = Table([[
        Paragraph(f'<b>{p["name"]}</b>', h1),
        Paragraph(f'<b>{cat_label}</b><br/><font size="9" color="#c8a84b">TECHNICAL DATA SHEET</font>',
                  ParagraphStyle('HR', fontName='Helvetica-Bold', fontSize=14, textColor=cat_color, alignment=TA_RIGHT))
    ]], colWidths=[120*mm, 54*mm])
    hdr.setStyle(TableStyle([
        ('BACKGROUND', (0,0),(-1,-1), G_DARK),
        ('PADDING',    (0,0),(-1,-1), 14),
        ('VALIGN',     (0,0),(-1,-1), 'MIDDLE'),
    ]))
    story.append(hdr)

    # Colour band
    band = Table([[Paragraph('MUDDO AGRO CHEMICALS LTD  ·  Kampala, Uganda  ·  +256 772 507582  ·  muddoagro811@gmail.com', small)]],
                 colWidths=[174*mm])
    band.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,-1), LGREEN),
        ('PADDING',   (0,0),(-1,-1), 7),
        ('LINEBELOW', (0,0),(-1,-1), 1.5, G_MID),
    ]))
    story.append(band)
    story.append(Spacer(1, 8*mm))

    # Description
    if p.get('description'):
        story.append(Paragraph('<b>PRODUCT DESCRIPTION</b>', h2))
        story.append(Spacer(1, 3*mm))
        story.append(Paragraph(p['description'], body))
        story.append(Spacer(1, 7*mm))

    # Spec table
    story.append(Paragraph('<b>TECHNICAL SPECIFICATIONS</b>', h2))
    story.append(Spacer(1, 3*mm))
    specs = [
        ('Active Ingredient',  p.get('active_ingredient') or '—'),
        ('Formulation Type',   p.get('formulation') or '—'),
        ('Target Crops',       p.get('crops') or '—'),
        ('Application Rate',   p.get('dosage') or '—'),
        ('Pack Sizes',         p.get('packing') or '—'),
        ('Category',           cat_label),
    ]
    spec_rows = [[Paragraph(f'<b>{k}</b>', ParagraphStyle('SK', fontName='Helvetica-Bold', fontSize=9.5, textColor=MUTED)),
                  Paragraph(v, bold)] for k,v in specs]
    spec_tbl = Table(spec_rows, colWidths=[55*mm, 119*mm])
    spec_tbl.setStyle(TableStyle([
        ('ROWBACKGROUNDS', (0,0), (-1,-1), [WHITE, LGREY]),
        ('TOPPADDING',    (0,0), (-1,-1), 9),
        ('BOTTOMPADDING', (0,0), (-1,-1), 9),
        ('LEFTPADDING',   (0,0), (-1,-1), 10),
        ('RIGHTPADDING',  (0,0), (-1,-1), 10),
        ('GRID',          (0,0), (-1,-1), 0.3, colors.HexColor('#e0e0e0')),
        ('LINEBELOW',     (0,-1),(-1,-1), 1.5, G_MID),
    ]))
    story.append(spec_tbl)
    story.append(Spacer(1, 8*mm))

    # Safety / directions
    story.append(Paragraph('<b>SAFE USE DIRECTIONS</b>', h2))
    story.append(Spacer(1, 3*mm))
    safety_rows = [
        ['01', 'Read the complete product label before use.'],
        ['02', 'Wear appropriate PPE: gloves, goggles, face mask, and protective clothing.'],
        ['03', 'Mix product in clean water using a calibrated sprayer. Never exceed the recommended rate.'],
        ['04', 'Observe the pre-harvest interval (PHI) stated on the label before consuming or selling produce.'],
        ['05', 'Store in the original sealed container in a cool, dry place, away from children and food.'],
        ['06', 'Dispose of empty containers by triple-rinsing and puncturing; never burn or reuse.'],
    ]
    s_tbl = Table(safety_rows, colWidths=[12*mm, 162*mm])
    s_tbl.setStyle(TableStyle([
        ('FONTNAME',    (0,0),(0,-1), 'Helvetica-Bold'),
        ('TEXTCOLOR',   (0,0),(0,-1), G_MID),
        ('FONTSIZE',    (0,0),(-1,-1), 9.5),
        ('TOPPADDING',  (0,0),(-1,-1), 8),
        ('BOTTOMPADDING',(0,0),(-1,-1), 8),
        ('LEFTPADDING', (0,0),(-1,-1), 8),
        ('BACKGROUND',  (0,0),(-1,-1), WHITE),
        ('LINEBELOW',   (0,0),(-1,-1), 0.3, colors.HexColor('#e0e0e0')),
        ('LINEBELOW',   (0,-1),(-1,-1), 1.5, G_MID),
    ]))
    story.append(s_tbl)
    story.append(Spacer(1, 8*mm))

    # Footer
    ft = Table([[
        Paragraph('This data sheet is for informational purposes only. Always refer to the registered product label.', small),
        Paragraph(f'Generated: {datetime.now().strftime("%d %b %Y")}',
                  ParagraphStyle('FD', fontName='Helvetica', fontSize=8.5, textColor=MUTED, alignment=TA_RIGHT))
    ]], colWidths=[120*mm, 54*mm])
    ft.setStyle(TableStyle([
        ('LINEABOVE',   (0,0),(-1,0), 0.5, colors.HexColor('#e0e0e0')),
        ('TOPPADDING',  (0,0),(-1,0), 8),
    ]))
    story.append(ft)

    doc.build(story)
    buf.seek(0)
    safe_name = p['name'].replace(' ', '_').replace('/', '-')
    return send_file(buf, mimetype='application/pdf', as_attachment=True,
                     download_name=f'MACL_{safe_name}_DataSheet.pdf')

# ═══════════════════════════════════════════════════════════════════════════
# FEATURE 8: AGENT PERFORMANCE REPORT PDF
# ═══════════════════════════════════════════════════════════════════════════
@app.route('/admin/agents/<int:aid>/report')
@admin_required
def agent_report(aid):
    conn = get_db()
    agent = conn.execute("SELECT * FROM agents WHERE id=?", (aid,)).fetchone()
    if not agent:
        conn.close(); abort(404)
    agent = dict(agent)
    supply_reqs = conn.execute(
        "SELECT * FROM supply_requests WHERE agent_id=? ORDER BY created_at DESC", (aid,)).fetchall()
    msgs = conn.execute(
        "SELECT * FROM messages WHERE sender_id=? AND sender_role='agent' ORDER BY created_at DESC LIMIT 20", (aid,)).fetchall()
    conn.close()

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
                            leftMargin=20*mm, rightMargin=20*mm,
                            topMargin=18*mm, bottomMargin=18*mm)
    G_DARK  = colors.HexColor('#0d2b14')
    G_MID   = colors.HexColor('#2d6e35')
    TEAL    = colors.HexColor('#00695c')
    GOLD    = colors.HexColor('#c8a84b')
    LGREY   = colors.HexColor('#f5f5f5')
    LGREEN  = colors.HexColor('#e8f5e9')
    LTEAL   = colors.HexColor('#e0f2f1')
    BLACK   = colors.HexColor('#111111')
    MUTED   = colors.HexColor('#565656')
    WHITE   = colors.white

    bold  = ParagraphStyle('B', fontName='Helvetica-Bold',  fontSize=10, textColor=BLACK)
    body  = ParagraphStyle('BD',fontName='Helvetica',        fontSize=10, textColor=BLACK, leading=15)
    small = ParagraphStyle('S', fontName='Helvetica',        fontSize=8.5, textColor=MUTED)
    h1    = ParagraphStyle('H1',fontName='Helvetica-Bold',   fontSize=20, textColor=WHITE)
    h2    = ParagraphStyle('H2',fontName='Helvetica-Bold',   fontSize=12, textColor=G_DARK)

    story = []

    # Header
    hdr = Table([[
        Paragraph(f'<b>AGENT REPORT</b>', h1),
        Paragraph(f'<b>{agent["name"]}</b><br/><font size="10" color="#c8a84b">{agent.get("region","") or "—"} Region</font>',
                  ParagraphStyle('AR', fontName='Helvetica-Bold', fontSize=14, textColor=GOLD, alignment=TA_RIGHT))
    ]], colWidths=[100*mm, 74*mm])
    hdr.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),G_DARK),('PADDING',(0,0),(-1,-1),14),('VALIGN',(0,0),(-1,-1),'MIDDLE')]))
    story.append(hdr)
    band = Table([[Paragraph(f'MUDDO AGRO CHEMICALS LTD  ·  Report generated: {datetime.now().strftime("%d %B %Y")}', small)]],
                 colWidths=[174*mm])
    band.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),LGREEN),('PADDING',(0,0),(-1,-1),7),('LINEBELOW',(0,0),(-1,-1),1.5,G_MID)]))
    story.append(band)
    story.append(Spacer(1,8*mm))

    # Agent profile
    story.append(Paragraph('<b>AGENT PROFILE</b>', h2))
    story.append(Spacer(1,3*mm))
    profile = [
        ('Full Name', agent['name']), ('Username', agent['username']),
        ('Email', agent.get('email') or '—'), ('Phone', agent.get('phone') or '—'),
        ('Region', agent.get('region') or '—'), ('District', agent.get('district') or '—'),
        ('Status', agent.get('status','active').title()),
        ('Account Created', (agent.get('created_at') or '')[:10]),
        ('Last Active', (agent.get('last_seen') or 'Never')[:16]),
    ]
    prof_tbl = Table([[Paragraph(f'<b>{k}</b>', ParagraphStyle('PK',fontName='Helvetica-Bold',fontSize=9.5,textColor=MUTED)),
                       Paragraph(v, bold)] for k,v in profile],
                     colWidths=[55*mm,119*mm])
    prof_tbl.setStyle(TableStyle([
        ('ROWBACKGROUNDS',(0,0),(-1,-1),[WHITE,LGREY]),
        ('TOPPADDING',(0,0),(-1,-1),8),('BOTTOMPADDING',(0,0),(-1,-1),8),
        ('LEFTPADDING',(0,0),(-1,-1),10),('RIGHTPADDING',(0,0),(-1,-1),10),
        ('GRID',(0,0),(-1,-1),0.3,colors.HexColor('#e0e0e0')),
        ('LINEBELOW',(0,-1),(-1,-1),1.5,G_MID),
    ]))
    story.append(prof_tbl)
    story.append(Spacer(1,8*mm))

    # Stats summary
    total_reqs  = len(supply_reqs)
    approved    = sum(1 for r in supply_reqs if r['status']=='approved')
    pending     = sum(1 for r in supply_reqs if r['status']=='pending')
    denied      = sum(1 for r in supply_reqs if r['status']=='denied')
    total_msgs  = len(msgs)
    story.append(Paragraph('<b>ACTIVITY SUMMARY</b>', h2))
    story.append(Spacer(1,3*mm))
    stats_data = [
        [Paragraph('<b>Metric</b>', ParagraphStyle('SH',fontName='Helvetica-Bold',fontSize=9,textColor=WHITE)),
         Paragraph('<b>Value</b>', ParagraphStyle('SH2',fontName='Helvetica-Bold',fontSize=9,textColor=WHITE,alignment=TA_RIGHT))],
        [Paragraph('Total Supply Requests', body), Paragraph(str(total_reqs), bold)],
        [Paragraph('Approved', body), Paragraph(str(approved), ParagraphStyle('A',fontName='Helvetica-Bold',fontSize=10,textColor=G_MID))],
        [Paragraph('Pending',  body), Paragraph(str(pending),  ParagraphStyle('P',fontName='Helvetica-Bold',fontSize=10,textColor=colors.HexColor('#c77700')))],
        [Paragraph('Denied',   body), Paragraph(str(denied),   ParagraphStyle('D',fontName='Helvetica-Bold',fontSize=10,textColor=colors.HexColor('#e53935')))],
        [Paragraph('Messages Sent to HQ', body), Paragraph(str(total_msgs), bold)],
    ]
    st = Table(stats_data, colWidths=[130*mm, 44*mm])
    st.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,0),TEAL),('TEXTCOLOR',(0,0),(-1,0),WHITE),
        ('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),
        ('ROWBACKGROUNDS',(0,1),(-1,-1),[WHITE,LGREY]),
        ('ALIGN',(1,0),(-1,-1),'RIGHT'),
        ('TOPPADDING',(0,0),(-1,-1),9),('BOTTOMPADDING',(0,0),(-1,-1),9),
        ('LEFTPADDING',(0,0),(-1,-1),10),('RIGHTPADDING',(0,0),(-1,-1),10),
        ('GRID',(0,0),(-1,-1),0.3,colors.HexColor('#e0e0e0')),
        ('LINEBELOW',(0,-1),(-1,-1),1.5,G_MID),
    ]))
    story.append(st)
    story.append(Spacer(1,8*mm))

    # Supply request history
    if supply_reqs:
        story.append(Paragraph('<b>SUPPLY REQUEST HISTORY</b>', h2))
        story.append(Spacer(1,3*mm))
        sr_hdr = [['#','Product','Quantity','Status','Date']]
        sr_rows = sr_hdr + [[
            str(i+1), r['product_name'] or '—', r['quantity'] or '—',
            r['status'].title(), (r['created_at'] or '')[:10]
        ] for i,r in enumerate(supply_reqs)]
        sr_tbl = Table(sr_rows, colWidths=[10*mm,75*mm,35*mm,30*mm,24*mm])
        sr_tbl.setStyle(TableStyle([
            ('BACKGROUND',(0,0),(-1,0),G_DARK),('TEXTCOLOR',(0,0),(-1,0),WHITE),
            ('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),('FONTSIZE',(0,0),(-1,-1),9),
            ('ROWBACKGROUNDS',(0,1),(-1,-1),[WHITE,LGREY]),
            ('TOPPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),7),
            ('LEFTPADDING',(0,0),(-1,-1),8),('RIGHTPADDING',(0,0),(-1,-1),8),
            ('GRID',(0,0),(-1,-1),0.3,colors.HexColor('#e0e0e0')),
        ]))
        story.append(sr_tbl)

    doc.build(story)
    buf.seek(0)
    safe = agent['name'].replace(' ','_')
    return send_file(buf, mimetype='application/pdf', as_attachment=True,
                     download_name=f'MACL_Agent_Report_{safe}.pdf')

# ─── SEARCH ──────────────────────────────────────────────────────────────────

@app.route('/subscribe', methods=['POST'])
def subscribe():
    data  = request.get_json() or {}
    email = (data.get('email') or '').strip().lower()
    name  = (data.get('name') or '').strip()
    if not email or '@' not in email:
        return jsonify({'ok': False, 'message': 'Please enter a valid email address.'}), 400
    conn = get_db()
    existing = conn.execute("SELECT id, active FROM newsletter_subscribers WHERE email=?", (email,)).fetchone()
    if existing:
        if existing['active']:
            conn.close()
            return jsonify({'ok': True, 'message': "You're already subscribed — thank you!"})
        conn.execute("UPDATE newsletter_subscribers SET active=1, name=? WHERE email=?", (name, email))
    else:
        conn.execute("INSERT INTO newsletter_subscribers(name, email) VALUES(?,?)", (name, email))
        # Welcome email
        send_safe('Welcome to Muddo Agro Updates!', [email],
                  render_template('emails/newsletter_welcome.html', name=name or 'Farmer'))
    conn.commit(); conn.close()
    return jsonify({'ok': True, 'message': 'Subscribed! You\'ll receive our latest updates and offers.'})

@app.route('/unsubscribe')
def unsubscribe():
    email = request.args.get('email', '').strip().lower()
    if email:
        conn = get_db()
        conn.execute("UPDATE newsletter_subscribers SET active=0 WHERE email=?", (email,))
        conn.commit(); conn.close()
    flash('You have been unsubscribed from Muddo Agro email updates.', 'success')
    return redirect(url_for('index'))

# ─── SITEMAP & ROBOTS ─────────────────────────────────────────────────────
# ─── ABOUT / FAQ ──────────────────────────────────────────────────────────────
@app.route('/about')
def about():
    return render_template('about.html')

# ─── PRODUCT COMPARISON ───────────────────────────────────────────────────────
@app.route('/compare')
def compare():
    conn = get_db()
    all_products = conn.execute("""
        SELECT p.*, COALESCE(i.stock_qty,0) as stock_qty
        FROM products p LEFT JOIN inventory i ON i.product_id=p.id
        ORDER BY p.category, p.name
    """).fetchall()
    conn.close()
    return render_template('compare.html', all_products=[dict(p) for p in all_products])
