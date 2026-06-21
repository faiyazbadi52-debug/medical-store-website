import os
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv

import db

# Load environment configurations
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'supersecretkey_janaushadhi_2026')

# Initialize DB on application start
db.init_db()

# --- Decorators for Route Protection ---
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            if request.path.startswith('/api/'):
                return jsonify({'error': 'Unauthorized. Please log in.'}), 401
            flash('Please log in to access this page.', 'error')
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_role' not in session or session['user_role'] != 'admin':
            if request.path.startswith('/api/'):
                return jsonify({'error': 'Forbidden. Administrator access required.'}), 403
            flash('Access denied. Administrator privileges required.', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Context processor to make cart count globally accessible in templates
@app.context_processor
def inject_cart_count():
    if 'user_id' in session:
        count_res = db.execute_query(
            "SELECT SUM(quantity) as count FROM cart_items WHERE user_id = %s",
            (session['user_id'],)
        )
        cart_count = count_res[0]['count'] if count_res and count_res[0]['count'] is not None else 0
        session['cart_count'] = cart_count
    else:
        cart_count = 0
    return dict(global_cart_count=cart_count)

# Helper to format stock value in Lakhs if needed
def format_currency_lakh(amount):
    if amount >= 100000:
        return f"₹{amount / 100000:.1f}L"
    return f"₹{amount:,.2f}"

app.jinja_env.filters['lakh_format'] = format_currency_lakh

# --- Routes: Frontend Pages ---

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/catalog')
def catalog():
    active_cat = request.args.get('category', '')
    search = request.args.get('search', '')
    
    # Load all medicines.
    medicines = db.execute_query("SELECT * FROM medicines ORDER BY name ASC")
    return render_template('catalog.html', medicines=medicines, active_category=active_cat, search_query=search)

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        subject = request.form.get('subject')
        message = request.form.get('message')
        
        flash(f'Thank you {name}! Your message regarding "{subject}" has been received. Our support team will respond shortly.', 'success')
        return redirect(url_for('contact'))
        
    return render_template('contact.html')

# --- Route: Order Tracking (Google Stitch Mockup Image 4) ---
@app.route('/track', methods=['GET'])
def track_order():
    order_query_code = request.args.get('order_id', '').strip()
    order = None
    items = []
    
    if order_query_code:
        # Extract numeric ID from format like JAK-882910-24 or #JA-24
        order_id = order_query_code
        if order_query_code.upper().startswith("JAK-882910-"):
            order_id = order_query_code.upper().replace("JAK-882910-", "")
        elif order_query_code.startswith("#JA-"):
            order_id = order_query_code.replace("#JA-", "")
        else:
            # Just extract trailing digits
            digits = "".join(c for c in order_query_code if c.isdigit())
            if digits:
                # If they type 88291024, get the last 2 digits which is the actual ID 24
                if len(digits) > 2 and digits.startswith("882910"):
                    order_id = digits[6:]
                else:
                    order_id = digits
                    
        try:
            # Fetch order details
            order_res = db.execute_query("""
                SELECT o.*, u.name as customer_name, u.email as customer_email
                FROM orders o
                JOIN users u ON o.user_id = u.id
                WHERE o.id = %s
            """, (order_id,))
            
            if order_res:
                order = order_res[0]
                # Fetch order items
                items = db.execute_query("""
                    SELECT oi.*, m.name, m.generic_name, m.image_url, m.dosage_form, m.manufacturer
                    FROM order_items oi
                    JOIN medicines m ON oi.medicine_id = m.id
                    WHERE oi.order_id = %s
                """, (order_id,))
            else:
                flash(f"Order '{order_query_code}' not found. Please verify the code and try again.", "error")
        except Exception as e:
            flash(f"Error retrieving order: {str(e)}", "error")
            
    return render_template('track.html', order=order, items=items, query_code=order_query_code)

# --- Routes: Authentication ---

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('home'))
        
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user_res = db.execute_query("SELECT * FROM users WHERE email = %s", (email,))
        if user_res:
            user = user_res[0]
            if check_password_hash(user['password'], password):
                session['user_id'] = user['id']
                session['user_name'] = user['name']
                session['user_role'] = user['role']
                
                # Fetch cart count
                count_res = db.execute_query(
                    "SELECT SUM(quantity) as count FROM cart_items WHERE user_id = %s",
                    (user['id'],)
                )
                session['cart_count'] = count_res[0]['count'] if count_res and count_res[0]['count'] is not None else 0
                
                flash('Welcome back! Login successful.', 'success')
                
                if user['role'] == 'admin':
                    return redirect(url_for('admin_dashboard'))
                return redirect(request.args.get('next') or url_for('home'))
                
        flash('Invalid email address or password. Please try again.', 'error')
        return redirect(url_for('login'))
        
    return render_template('login_register.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        password = request.form.get('password')
        address = request.form.get('address')
        
        exists = db.execute_query("SELECT * FROM users WHERE email = %s", (email,))
        if exists:
            flash('This email address is already registered. Please login instead.', 'error')
            return redirect(url_for('login', tab='register'))
            
        hashed_password = generate_password_hash(password)
        db.execute_query(
            "INSERT INTO users (name, email, phone, password, address, role) VALUES (%s, %s, %s, %s, %s, 'customer')",
            (name, email, phone, hashed_password, address),
            is_select=False
        )
        
        flash('Account created successfully! Please sign in using your credentials.', 'success')
        return redirect(url_for('login'))
        
    return redirect(url_for('login', tab='register'))

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('home'))

# --- Routes: Cart Operations ---

@app.route('/cart')
@login_required
def cart():
    user_id = session['user_id']
    items = db.execute_query("""
        SELECT c.id, c.medicine_id, c.quantity, m.name, m.generic_name, m.price, m.stock, m.dosage_form, m.manufacturer
        FROM cart_items c
        JOIN medicines m ON c.medicine_id = m.id
        WHERE c.user_id = %s
    """, (user_id,))
    
    subtotal = sum(item['price'] * item['quantity'] for item in items)
    tax = subtotal * 0.05
    total = subtotal + tax
    savings = (subtotal * 4)
    
    return render_template('cart.html', items=items, subtotal=subtotal, tax=tax, total=total, savings=savings)

@app.route('/checkout', methods=['GET', 'POST'])
@login_required
def checkout():
    user_id = session['user_id']
    user = db.execute_query("SELECT * FROM users WHERE id = %s", (user_id,))[0]
    
    items = db.execute_query("""
        SELECT c.id, c.medicine_id, c.quantity, m.name, m.generic_name, m.price, m.stock, m.dosage_form, m.manufacturer, m.image_url
        FROM cart_items c
        JOIN medicines m ON c.medicine_id = m.id
        WHERE c.user_id = %s
    """, (user_id,))
    
    if not items and request.method == 'POST':
        flash('Your shopping cart is empty.', 'error')
        return redirect(url_for('catalog'))
        
    subtotal = sum(item['price'] * item['quantity'] for item in items)
    tax = subtotal * 0.05
    total = subtotal + tax
    savings = (subtotal * 4)
    
    if request.method == 'POST':
        name = request.form.get('name')
        phone = request.form.get('phone')
        address = request.form.get('address')
        payment_method = request.form.get('payment_method')
        
        # Verify stocks
        for item in items:
            if item['quantity'] > item['stock']:
                flash(f"Insufficient stock for {item['name']}. Available stock: {item['stock']}.", "error")
                return redirect(url_for('cart'))
                
        # Insert Order
        order_id = db.execute_query("""
            INSERT INTO orders (user_id, total_amount, status, shipping_address, phone, payment_method)
            VALUES (%s, %s, 'Pending', %s, %s, %s)
        """, (user_id, total, address, phone, payment_method), is_select=False)
        
        # Insert items and decrement stocks
        for item in items:
            db.execute_query("""
                INSERT INTO order_items (order_id, medicine_id, quantity, price)
                VALUES (%s, %s, %s, %s)
            """, (order_id, item['medicine_id'], item['quantity'], item['price']), is_select=False)
            
            db.execute_query("""
                UPDATE medicines SET stock = stock - %s WHERE id = %s
            """, (item['quantity'], item['medicine_id']), is_select=False)
            
        db.execute_query("DELETE FROM cart_items WHERE user_id = %s", (user_id,), is_select=False)
        session['cart_count'] = 0
        
        return render_template('checkout.html', success=True, order_id=order_id, 
                               name=name, phone=phone, address=address, 
                               payment_method=payment_method, total=total, savings=savings)
                               
    return render_template('checkout.html', success=False, user=user, items=items, 
                           subtotal=subtotal, tax=tax, total=total, savings=savings)

# --- Routes: API / AJAX Endpoints ---

@app.route('/api/medicine/<int:med_id>')
def get_medicine_details(med_id):
    results = db.execute_query("SELECT * FROM medicines WHERE id = %s", (med_id,))
    if results:
        return jsonify(results[0])
    return jsonify({'error': 'Medicine formulation not found.'}), 404

@app.route('/api/cart/add', methods=['POST'])
@login_required
def api_add_to_cart():
    user_id = session['user_id']
    data = request.get_json()
    med_id = data.get('medicine_id')
    qty = int(data.get('quantity', 1))
    
    med_res = db.execute_query("SELECT * FROM medicines WHERE id = %s", (med_id,))
    if not med_res:
        return jsonify({'error': 'Medicine not found.'}), 404
        
    medicine = med_res[0]
    if medicine['stock'] <= 0:
        return jsonify({'error': 'Medicine is currently out of stock.'}), 400
        
    existing = db.execute_query(
        "SELECT * FROM cart_items WHERE user_id = %s AND medicine_id = %s",
        (user_id, med_id)
    )
    
    if existing:
        new_qty = existing[0]['quantity'] + qty
        if new_qty > medicine['stock']:
            return jsonify({'error': f"Cannot add quantity. Max available stock is {medicine['stock']}."}), 400
            
        db.execute_query(
            "UPDATE cart_items SET quantity = %s WHERE id = %s",
            (new_qty, existing[0]['id']),
            is_select=False
        )
    else:
        if qty > medicine['stock']:
            return jsonify({'error': f"Cannot add quantity. Max available stock is {medicine['stock']}."}), 400
            
        db.execute_query(
            "INSERT INTO cart_items (user_id, medicine_id, quantity) VALUES (%s, %s, %s)",
            (user_id, med_id, qty),
            is_select=False
        )
        
    count_res = db.execute_query("SELECT SUM(quantity) as count FROM cart_items WHERE user_id = %s", (user_id,))
    cart_count = count_res[0]['count'] if count_res and count_res[0]['count'] is not None else 0
    session['cart_count'] = cart_count
    
    return jsonify({'success': True, 'cart_count': cart_count})

@app.route('/api/cart/update', methods=['POST'])
@login_required
def api_update_cart_quantity():
    user_id = session['user_id']
    data = request.get_json()
    item_id = data.get('item_id')
    qty = int(data.get('quantity'))
    
    item_res = db.execute_query("""
        SELECT c.*, m.stock, m.name 
        FROM cart_items c 
        JOIN medicines m ON c.medicine_id = m.id 
        WHERE c.id = %s AND c.user_id = %s
    """, (item_id, user_id))
    
    if not item_res:
        return jsonify({'error': 'Cart item not found.'}), 404
        
    item = item_res[0]
    if qty > item['stock']:
        return jsonify({'error': f"Only {item['stock']} units of {item['name']} are available in stock."}), 400
        
    if qty < 1:
        qty = 1
        
    db.execute_query(
        "UPDATE cart_items SET quantity = %s WHERE id = %s",
        (qty, item_id),
        is_select=False
    )
    
    items = db.execute_query("""
        SELECT c.id, c.medicine_id, c.quantity, m.price
        FROM cart_items c
        JOIN medicines m ON c.medicine_id = m.id
        WHERE c.user_id = %s
    """, (user_id,))
    
    cart_count = sum(item['quantity'] for item in items)
    session['cart_count'] = cart_count
    
    return jsonify({'success': True, 'items': items, 'cart_count': cart_count})

@app.route('/api/cart/delete', methods=['POST'])
@login_required
def api_delete_cart_item():
    user_id = session['user_id']
    data = request.get_json()
    item_id = data.get('item_id')
    
    exists = db.execute_query("SELECT * FROM cart_items WHERE id = %s AND user_id = %s", (item_id, user_id))
    if not exists:
        return jsonify({'error': 'Item not found in cart.'}), 404
        
    db.execute_query("DELETE FROM cart_items WHERE id = %s", (item_id,), is_select=False)
    
    items = db.execute_query("""
        SELECT c.id, c.medicine_id, c.quantity, m.price
        FROM cart_items c
        JOIN medicines m ON c.medicine_id = m.id
        WHERE c.user_id = %s
    """, (user_id,))
    
    cart_count = sum(item['quantity'] for item in items)
    session['cart_count'] = cart_count
    
    return jsonify({'success': True, 'items': items, 'cart_count': cart_count})

# --- Routes: Admin Management ---

@app.route('/admin')
@admin_required
def admin_dashboard():
    # 1. Stats and metrics calculations matching Google Stitch overview dashboard (Image 5 & Image 1)
    sales_res = db.execute_query("SELECT SUM(total_amount) as total_sales FROM orders WHERE status != 'Cancelled'")
    total_sales = sales_res[0]['total_sales'] if sales_res and sales_res[0]['total_sales'] is not None else 0.0
    
    orders_count_res = db.execute_query("SELECT COUNT(*) as total_orders FROM orders")
    total_orders = orders_count_res[0]['total_orders'] if orders_count_res else 0
    
    customers_count_res = db.execute_query("SELECT COUNT(*) as total_customers FROM users WHERE role = 'customer'")
    total_customers = customers_count_res[0]['total_customers'] if customers_count_res else 0
    
    # Stock count: total count of distinct medicine types
    total_meds_res = db.execute_query("SELECT COUNT(*) as total_meds FROM medicines")
    total_meds = total_meds_res[0]['total_meds'] if total_meds_res else 0
    
    # Low stock alert count
    low_stock_res = db.execute_query("SELECT COUNT(*) as low_stock_count FROM medicines WHERE stock <= 20")
    low_stock_count = low_stock_res[0]['low_stock_count'] if low_stock_res else 0
    
    # In Stock Value: sum of price * stock
    stock_val_res = db.execute_query("SELECT SUM(price * stock) as total_val FROM medicines")
    in_stock_value = stock_val_res[0]['total_val'] if stock_val_res and stock_val_res[0]['total_val'] is not None else 0.0
    
    # Expired soon (mocked to 12 as seen in mockup Image 1)
    expired_soon = 12
    
    stats = {
        'total_sales': total_sales,
        'total_orders': total_orders,
        'total_customers': total_customers,
        'total_meds': total_meds,
        'low_stock_count': low_stock_count,
        'in_stock_value': in_stock_value,
        'expired_soon': expired_soon
    }
    
    # 2. Get Medicines
    medicines = db.execute_query("SELECT * FROM medicines ORDER BY name ASC")
    
    # 3. Get Orders
    orders_query = """
        SELECT o.id, o.user_id, o.total_amount, o.status, o.shipping_address, o.phone, o.payment_method, o.created_at,
               u.name as customer_name, u.email as customer_email
        FROM orders o
        JOIN users u ON o.user_id = u.id
        ORDER BY o.created_at DESC
    """
    orders = db.execute_query(orders_query)
    
    # 4. Get Customers
    customers = db.execute_query("SELECT id, name, email, phone, address, role FROM users ORDER BY id ASC")
    
    return render_template('admin.html', stats=stats, medicines=medicines, orders=orders, customers=customers)

@app.route('/admin/medicine/add', methods=['POST'])
@admin_required
def admin_add_medicine():
    sku = request.form.get('sku')
    name = request.form.get('name')
    generic_name = request.form.get('generic_name')
    category = request.form.get('category')
    dosage_form = request.form.get('dosage_form')
    price = float(request.form.get('price'))
    stock = int(request.form.get('stock'))
    manufacturer = request.form.get('manufacturer')
    description = request.form.get('description')
    
    # Generate image search keyword url
    image_url = "https://images.unsplash.com/photo-1587854692152-cbe660dbde88?q=80&w=150&auto=format&fit=crop"
    if "amoxicillin" in name.lower() or "syrup" in dosage_form.lower():
        image_url = "https://images.unsplash.com/photo-1550572017-edd951b55104?q=80&w=150&auto=format&fit=crop"
    elif "metformin" in name.lower():
        image_url = "https://images.unsplash.com/photo-1607619056574-7b8f304b3c93?q=80&w=150&auto=format&fit=crop"
    elif "omeprazole" in name.lower() or "pantoprazole" in name.lower():
        image_url = "https://images.unsplash.com/photo-1471864190281-a93a3070b6de?q=80&w=150&auto=format&fit=crop"
        
    db.execute_query("""
        INSERT INTO medicines (sku, name, generic_name, category, price, stock, description, image_url, dosage_form, manufacturer)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (sku, name, generic_name, category, price, stock, description, image_url, dosage_form, manufacturer), is_select=False)
    
    flash(f"Medicine '{name}' added successfully to inventory.", "success")
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/medicine/edit', methods=['POST'])
@admin_required
def admin_edit_medicine():
    med_id = request.form.get('med_id')
    sku = request.form.get('sku')
    name = request.form.get('name')
    generic_name = request.form.get('generic_name')
    category = request.form.get('category')
    dosage_form = request.form.get('dosage_form')
    price = float(request.form.get('price'))
    stock = int(request.form.get('stock'))
    manufacturer = request.form.get('manufacturer')
    description = request.form.get('description')
    
    db.execute_query("""
        UPDATE medicines 
        SET sku = %s, name = %s, generic_name = %s, category = %s, price = %s, stock = %s, description = %s, dosage_form = %s, manufacturer = %s
        WHERE id = %s
    """, (sku, name, generic_name, category, price, stock, description, dosage_form, manufacturer, med_id), is_select=False)
    
    flash(f"Medicine '{name}' formulation details updated.", "success")
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/medicine/delete/<int:med_id>')
@admin_required
def admin_delete_medicine(med_id):
    med_res = db.execute_query("SELECT name FROM medicines WHERE id = %s", (med_id,))
    if med_res:
        name = med_res[0]['name']
        db.execute_query("DELETE FROM medicines WHERE id = %s", (med_id,), is_select=False)
        flash(f"Medicine '{name}' removed from database.", "info")
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/order/status/<int:order_id>', methods=['POST'])
@admin_required
def admin_update_order_status(order_id):
    status = request.form.get('status')
    
    order = db.execute_query("SELECT id FROM orders WHERE id = %s", (order_id,))
    if order:
        db.execute_query("UPDATE orders SET status = %s WHERE id = %s", (status, order_id), is_select=False)
        flash(f"Order #JA-{order_id} status updated to {status}.", "success")
        
    return redirect(url_for('admin_dashboard'))

# --- Server Start ---
if __name__ == '__main__':
    app.run()
