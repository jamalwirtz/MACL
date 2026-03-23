# Muddo Agro Chemicals LTD — Deployment Guide

## Quick Start (Development)
```bash
pip install -r requirements.txt
python app.py
# → http://localhost:5000
```

## Production Setup (Ubuntu + Nginx + Gunicorn)

### 1. Install dependencies
```bash
sudo apt update && sudo apt install python3-pip python3-venv nginx certbot python3-certbot-nginx -y
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt gunicorn
```

### 2. Environment variables
```bash
export MAIL_PASSWORD=your_gmail_app_password
export GA_MEASUREMENT_ID=G-XXXXXXXXXX
export FLASK_SECRET_KEY=change_to_long_random_string
```

### 3. Start with Gunicorn
```bash
gunicorn -w 4 -b 127.0.0.1:5000 --timeout 120 app:app
```

### 4. Systemd service (see muddo_agro.service)
```bash
sudo cp muddo_agro.service /etc/systemd/system/
sudo systemctl enable --now muddo_agro
```

### 5. Nginx reverse proxy (see muddo_agro.nginx)
```bash
sudo cp muddo_agro.nginx /etc/nginx/sites-available/muddo_agro
sudo ln -s /etc/nginx/sites-available/muddo_agro /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
```

### 6. SSL with Let's Encrypt
```bash
sudo certbot --nginx -d yourdomain.com
```

## Admin Credentials
- URL: /login → select "Administrator"
- Username: admin
- Password: muddo@admin2024
- ⚠️ CHANGE PASSWORD IMMEDIATELY via Admin → Settings

## Environment Variables
| Variable | Purpose |
|---|---|
| MAIL_PASSWORD | Gmail App Password — enables all email notifications |
| GA_MEASUREMENT_ID | Google Analytics 4 Measurement ID (G-XXXXXXXXXX) |
| FLASK_SECRET_KEY | Session security key — required in production |
