#!/usr/bin/env python3
"""
SweetCrust Bakery — Backend Server
===================================
Pure Python (no pip needed) — uses only built-in modules:
  http.server  →  HTTP server
  sqlite3      →  Database
  json         →  JSON parsing
  urllib       →  URL utilities

Run:  python3 server.py
API runs on: http://localhost:8000
"""

import http.server
import json
import sqlite3
import os
import sys
from datetime import datetime
from urllib.parse import urlparse, parse_qs

# ── CONFIG ──────────────────────────────────────────────
PORT = int(os.environ.get("PORT", 8000))
DB_FILE = "sweetcrust.db"
# ────────────────────────────────────────────────────────


# ── DATABASE SETUP ───────────────────────────────────────
def init_db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    # Orders table
    c.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT    NOT NULL,
            phone       TEXT    NOT NULL,
            order_date  TEXT    NOT NULL,
            order_type  TEXT    NOT NULL DEFAULT 'Dine-in',
            items       TEXT    NOT NULL,
            special_req TEXT,
            total_amount REAL   DEFAULT 0,
            status      TEXT    NOT NULL DEFAULT 'Pending',
            created_at  TEXT    NOT NULL
        )
    """)

    # Menu items table
    c.execute("""
        CREATE TABLE IF NOT EXISTS menu_items (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            name     TEXT    NOT NULL,
            category TEXT    NOT NULL,
            price    REAL    NOT NULL,
            emoji    TEXT,
            badge    TEXT,
            description TEXT,
            available INTEGER DEFAULT 1
        )
    """)

    # Seed menu data if empty
    c.execute("SELECT COUNT(*) FROM menu_items")
    if c.fetchone()[0] == 0:
        menu = [
            ("Chocolate Truffle Cake",    "cakes",  450, "🍫", "Bestseller", "Rich dark chocolate layers with silky ganache frosting"),
            ("Vanilla Bean Cake",          "cakes",  380, "🎂", None,         "Classic moist sponge with fresh vanilla cream and berries"),
            ("Red Velvet Slice",           "cakes",  120, "🔴", "New",        "Velvety smooth crumb with tangy cream cheese frosting"),
            ("Mango Cream Cake",           "cakes",  520, "🥭", "Seasonal",   "Fresh Alphonso mango layered between light sponge"),
            ("Sourdough Loaf",             "bread",  180, "🍞", None,         "24-hour fermented artisan bread, crusty golden crust"),
            ("Whole Wheat Buns",           "bread",   40, "🥖", None,         "Soft multigrain buns baked fresh, perfect with butter"),
            ("Garlic Herb Focaccia",       "bread",  150, "🫓", "New",        "Italian flatbread with rosemary, roasted garlic and sea salt"),
            ("Butter Croissant",           "pastry",  80, "🥐", "Bestseller", "Flaky, golden, buttery layers folded the traditional French way"),
            ("Almond Danish Pastry",       "pastry",  95, "🥮", None,         "Sweet pastry filled with almond cream and icing drizzle"),
            ("Cinnamon Roll",              "pastry",  75, "🌀", None,         "Soft swirl with warm cinnamon sugar and sweet vanilla glaze"),
            ("Mysore Pak",                 "sweets",  60, "🟡", None,         "Classic soft ghee-rich gram flour sweet"),
            ("Kesar Kalakand",             "sweets",  80, "🍮", "Seasonal",   "Premium milk cake with saffron and pistachio topping"),
            ("Badam Halwa",                "sweets", 100, "🌰", "Special",    "Rich almond halwa with saffron, cardamom and pure ghee"),
            ("Coconut Ladoo",              "sweets",  50, "🤍", None,         "Melt-in-mouth coconut ladoos with cardamom"),
        ]
        c.executemany(
            "INSERT INTO menu_items (name, category, price, emoji, badge, description) VALUES (?,?,?,?,?,?)",
            menu
        )
        print(f"  ✓ Seeded {len(menu)} menu items")

    conn.commit()
    conn.close()
    print(f"  ✓ Database ready: {DB_FILE}")


# ── HELPERS ──────────────────────────────────────────────
def get_db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def rows_to_list(rows):
    return [dict(row) for row in rows]

def json_response(handler, data, status=200):
    body = json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    handler.send_header("Access-Control-Allow-Origin", "*")
    handler.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
    handler.send_header("Access-Control-Allow-Headers", "Content-Type")
    handler.end_headers()
    handler.wfile.write(body)

def read_body(handler):
    length = int(handler.headers.get("Content-Length", 0))
    if length == 0:
        return {}
    raw = handler.rfile.read(length).decode("utf-8")
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {}


# ── REQUEST HANDLER ──────────────────────────────────────
class BakeryHandler(http.server.BaseHTTPRequestHandler):

    def log_message(self, format, *args):
        ts = datetime.now().strftime("%H:%M:%S")
        print(f"  [{ts}] {format % args}")

    # ── OPTIONS (CORS preflight) ──
    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    # ── GET ──
    def do_GET(self):
        parsed = urlparse(self.path)
        path   = parsed.path.rstrip("/")
        params = parse_qs(parsed.query)

        # Health check
        if path == "/api/health":
            json_response(self, {"status": "ok", "bakery": "SweetCrust", "time": datetime.now().isoformat()})

        # GET all orders
        elif path == "/api/orders":
            conn = get_db()
            status_filter = params.get("status", [None])[0]
            if status_filter:
                rows = conn.execute(
                    "SELECT * FROM orders WHERE status=? ORDER BY id DESC", (status_filter,)
                ).fetchall()
            else:
                rows = conn.execute("SELECT * FROM orders ORDER BY id DESC").fetchall()
            conn.close()
            json_response(self, {"orders": rows_to_list(rows), "count": len(rows)})

        # GET single order
        elif path.startswith("/api/orders/"):
            order_id = path.split("/")[-1]
            conn = get_db()
            row = conn.execute("SELECT * FROM orders WHERE id=?", (order_id,)).fetchone()
            conn.close()
            if row:
                json_response(self, {"order": dict(row)})
            else:
                json_response(self, {"error": "Order not found"}, 404)

        # GET menu
        elif path == "/api/menu":
            cat = params.get("category", [None])[0]
            conn = get_db()
            if cat:
                rows = conn.execute(
                    "SELECT * FROM menu_items WHERE category=? AND available=1", (cat,)
                ).fetchall()
            else:
                rows = conn.execute("SELECT * FROM menu_items WHERE available=1").fetchall()
            conn.close()
            json_response(self, {"items": rows_to_list(rows)})

        # GET stats (dashboard summary)
        elif path == "/api/stats":
            conn = get_db()
            total_orders   = conn.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
            pending_orders = conn.execute("SELECT COUNT(*) FROM orders WHERE status='Pending'").fetchone()[0]
            done_orders    = conn.execute("SELECT COUNT(*) FROM orders WHERE status='Completed'").fetchone()[0]
            today_str      = datetime.now().strftime("%Y-%m-%d")
            today_orders   = conn.execute(
                "SELECT COUNT(*) FROM orders WHERE order_date=?", (today_str,)
            ).fetchone()[0]
            revenue_row    = conn.execute("SELECT SUM(total_amount) FROM orders WHERE status='Completed'").fetchone()[0]
            conn.close()
            json_response(self, {
                "total_orders":   total_orders,
                "pending_orders": pending_orders,
                "completed_orders": done_orders,
                "today_orders":   today_orders,
                "total_revenue":  round(revenue_row or 0, 2),
            })

        else:
            # Serve static HTML files
            if path == "" or path == "/":
                filepath = "index.html"
            else:
                filepath = path.lstrip("/")
            
            try:
                with open(filepath, "rb") as f:
                    content = f.read()
                ext = filepath.split(".")[-1]
                mime = {"html": "text/html", "css": "text/css", "js": "application/javascript"}.get(ext, "text/plain")
                self.send_response(200)
                self.send_header("Content-Type", mime)
                self.send_header("Content-Length", str(len(content)))
                self.end_headers()
                self.wfile.write(content)
            except FileNotFoundError:
                json_response(self, {"error": "Not found", "path": path}, 404)

    # ── POST ──
    def do_POST(self):
        path = urlparse(self.path).path.rstrip("/")

        # Place new order
        if path == "/api/orders":
            data = read_body(self)
            # Validate required fields
            required = ["name", "phone", "items"]
            missing  = [f for f in required if not data.get(f, "").strip()]
            if missing:
                json_response(self, {"error": f"Missing fields: {', '.join(missing)}"}, 400)
                return

            name        = data["name"].strip()
            phone       = data["phone"].strip()
            items       = data["items"].strip()
            order_date  = data.get("order_date", datetime.now().strftime("%Y-%m-%d"))
            order_type  = data.get("order_type", "Dine-in")
            special_req = data.get("special_req", "")
            total_amt   = float(data.get("total_amount", 0))
            created_at  = datetime.now().isoformat()

            conn = get_db()
            cursor = conn.execute(
                """INSERT INTO orders
                   (name, phone, order_date, order_type, items, special_req, total_amount, status, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, 'Pending', ?)""",
                (name, phone, order_date, order_type, items, special_req, total_amt, created_at)
            )
            order_id = cursor.lastrowid
            conn.commit()
            row = conn.execute("SELECT * FROM orders WHERE id=?", (order_id,)).fetchone()
            conn.close()

            print(f"  🎂 New order #{order_id} — {name} ({order_type}) — ₹{total_amt}")
            json_response(self, {
                "success": True,
                "message": f"Order placed! Order ID: #{order_id}",
                "order": dict(row)
            }, 201)

        else:
            json_response(self, {"error": "Endpoint not found"}, 404)

    # ── PUT ──
    def do_PUT(self):
        path = urlparse(self.path).path.rstrip("/")

        # Update order status: PUT /api/orders/:id/status
        if "/api/orders/" in path and path.endswith("/status"):
            order_id = path.split("/")[-2]
            data = read_body(self)
            new_status = data.get("status", "").strip()
            valid = ["Pending", "Confirmed", "Ready", "Completed", "Cancelled"]
            if new_status not in valid:
                json_response(self, {"error": f"Status must be one of: {', '.join(valid)}"}, 400)
                return
            conn = get_db()
            conn.execute("UPDATE orders SET status=? WHERE id=?", (new_status, order_id))
            conn.commit()
            row = conn.execute("SELECT * FROM orders WHERE id=?", (order_id,)).fetchone()
            conn.close()
            if row:
                print(f"  ✏️  Order #{order_id} → {new_status}")
                json_response(self, {"success": True, "order": dict(row)})
            else:
                json_response(self, {"error": "Order not found"}, 404)

        else:
            json_response(self, {"error": "Endpoint not found"}, 404)

    # ── DELETE ──
    def do_DELETE(self):
        path = urlparse(self.path).path.rstrip("/")

        if path.startswith("/api/orders/"):
            order_id = path.split("/")[-1]
            conn = get_db()
            row = conn.execute("SELECT * FROM orders WHERE id=?", (order_id,)).fetchone()
            if not row:
                conn.close()
                json_response(self, {"error": "Order not found"}, 404)
                return
            conn.execute("DELETE FROM orders WHERE id=?", (order_id,))
            conn.commit()
            conn.close()
            print(f"  🗑️  Order #{order_id} deleted")
            json_response(self, {"success": True, "message": f"Order #{order_id} deleted"})

        else:
            json_response(self, {"error": "Endpoint not found"}, 404)


# ── MAIN ─────────────────────────────────────────────────
if __name__ == "__main__":
    print("\n" + "="*50)
    print("  🎂  SweetCrust Bakery — Backend Server")
    print("="*50)
    init_db()
    server = http.server.HTTPServer(("0.0.0.0", PORT), BakeryHandler)
    print(f"\n  🚀 Server running at http://localhost:{PORT}")
    print(f"\n  API Endpoints:")
    print(f"    GET    /api/health              — Health check")
    print(f"    GET    /api/menu                — All menu items")
    print(f"    GET    /api/menu?category=cakes — Filter by category")
    print(f"    GET    /api/orders              — All orders")
    print(f"    GET    /api/orders?status=Pending")
    print(f"    GET    /api/orders/:id          — Single order")
    print(f"    POST   /api/orders              — Place new order")
    print(f"    PUT    /api/orders/:id/status   — Update order status")
    print(f"    DELETE /api/orders/:id          — Delete order")
    print(f"    GET    /api/stats               — Dashboard stats")
    print(f"\n  Press Ctrl+C to stop\n")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n  Server stopped.")
