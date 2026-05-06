# 🎂 SweetCrust Bakery — Full Stack Website

## Files இந்த folder-ல இருக்கு:

| File | என்ன |
|------|------|
| `server.py` | Python Backend Server (API + Database) |
| `index.html` | Customer-facing website (frontend) |
| `admin.html` | Admin Dashboard (orders பார்க்கலாம்) |
| `sweetcrust.db` | SQLite Database (auto-create ஆகும்) |

---

## ▶️ எப்படி Start பண்றது?

### Step 1 — Backend Start பண்ணுங்க
```bash
cd sweetcrust-backend
python3 server.py
```
Terminal-ல இப்படி வரும்:
```
🚀 Server running at http://localhost:8000
```

### Step 2 — Website Open பண்ணுங்க
- Customer site  → `index.html` browser-ல open பண்ணுங்க
- Admin panel    → `admin.html` browser-ல open பண்ணுங்க

---

## 🔗 API Endpoints

| Method | URL | என்ன பண்ணும் |
|--------|-----|-------------|
| GET | `/api/health` | Server running-ஆ? |
| GET | `/api/menu` | Menu items எல்லாம் |
| GET | `/api/menu?category=cakes` | Category filter |
| GET | `/api/orders` | All orders |
| GET | `/api/orders?status=Pending` | Status filter |
| GET | `/api/orders/:id` | Single order |
| POST | `/api/orders` | New order place |
| PUT | `/api/orders/:id/status` | Status update |
| DELETE | `/api/orders/:id` | Order delete |
| GET | `/api/stats` | Dashboard numbers |

---

## 📦 POST /api/orders — Body Format

```json
{
  "name": "Priya Rajan",
  "phone": "9876543210",
  "items": "Chocolate Truffle Cake, Butter Croissant",
  "order_date": "2025-05-07",
  "order_type": "Dine-in",
  "special_req": "Extra cream please",
  "total_amount": 530
}
```

---

## 📊 Order Status Flow

```
Pending → Confirmed → Ready → Completed
                   ↘ Cancelled
```

---

## ⚙️ Requirements

- Python 3.x (built-in, no pip needed!)
- Modern browser (Chrome/Firefox/Edge)
- No external libraries needed 🎉
