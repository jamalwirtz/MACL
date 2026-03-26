<img width="1536" height="1024" alt="image" src="https://github.com/user-attachments/assets/5a8c7b1a-16ab-4eed-8048-e796563c5db6" /># 🌿 Muddo Agro Chemicals LTD — Website

A professional Flask web application for **Muddo Agro Chemicals LTD**, Uganda's trusted agrochemical distributor.

---

## 🚀 Quick Start

```bash
# 1. Install Flask
pip install flask

# 2. Run the app
python app.py
```

Then open: **http://localhost:5000**

---

## 🔑 Admin Access

URL: http://localhost:5000/admin/login

| Username | Password         |
|----------|------------------|
| admin    | muddo@admin2024  |

> ⚠️ Change the password in `app.py` before deploying to production.

---

## 📄 Pages

| URL                  | Page                          |
|----------------------|-------------------------------|
| `/`                  | Home — Hero, categories, about |
| `/pesticides`        | Pesticide products listing     |
| `/herbicides`        | Herbicide products listing     |
| `/fungicides`        | Fungicide products listing     |
| `/other-products`    | Fertilizers & equipment        |
| `/product/<id>`      | Full product detail page       |
| `/distributors`      | Interactive store locator map  |
| `/contact`           | Contact form & info            |
| `/admin`             | Admin dashboard                |

---

## 🗺️ Google Maps Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create/select a project → Enable the **Maps JavaScript API**
3. Create an API key
4. Open `templates/distributors.html` and replace:
   ```
   YOUR_GOOGLE_MAPS_API_KEY
   ```
   with your actual key.

The store locator will degrade gracefully without a key — the sidebar list and filters still work fully.

---

## 🗂️ Project Structure

```
muddo_agro/
├── app.py                  # Flask app, routes, DB setup
├── requirements.txt
├── muddo.db                # SQLite database (auto-created)
├── static/
│   ├── css/style.css       # All styles
│   └── js/main.js          # Navbar, filters, animations
└── templates/
    ├── base.html            # Base layout with nav & footer
    ├── index.html           # Home page
    ├── pesticides.html
    ├── herbicides.html
    ├── fungicides.html
    ├── other_products.html
    ├── product_detail.html
    ├── distributors.html    # Map + store locator
    ├── contact.html
    └── admin/
        ├── login.html
        ├── base_admin.html  # Admin layout
        ├── dashboard.html
        ├── products.html
        ├── distributors.html
        └── requests.html
```

---

## ⚙️ Admin Features

- **Dashboard** — KPI cards, recent requests, product breakdown chart
- **Products** — Add / delete products with full specs; searchable table
- **Distributors** — Add/remove outlets by region; GPS coordinates for map pins
- **Contact Requests** — View, filter, and update status (new → pending → resolved)

---

## 🌍 Pre-Seeded Data

**16 products** across 4 categories:
- 4 Herbicides (MD-Maize Plus, Thrash 56EC, Weed Master, Cleaner)
- 4 Pesticides (Bulldock, Acephate, Lambda Super, Dursban)
- 4 Fungicides (Ridomil Gold, Score 250EC, Mancozeb, Copper Oxychloride)
- 4 Other (Urea, NPK, Foliar Boost, Knapsack Sprayer)

**10 distributor outlets** across all 4 Ugandan regions (Central, Eastern, Northern, Western).

---

## 🔒 Production Checklist

- [ ] Change `app.secret_key` to a strong random value
- [ ] Change admin password
- [ ] Add Google Maps API key (restrict to your domain)
- [ ] Use a production WSGI server (gunicorn/uWSGI)
- [ ] Set `debug=False`

---

*Built for Muddo Agro Chemicals LTD — Kampala, Uganda*

also change the green theme u have used for the  and put more colorful themes of  tanned red blue and green for the website , and  then work on the failing pages and the admin whole system and also check why tthhe admin can`t login   also check that search for oulets /distributors on the map  can also use google maps so that the user can get updated info about the places. then replace this image as the logo and also the buisness card. for the biusness card, place on the login page with some extended discription of the company. then remove the header with the contacts  and address of the company and only include them in the footer
