import os
import sqlite3
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash

# Load env variables
load_dotenv()

DB_TYPE = os.getenv('DB_TYPE', 'mysql').lower()
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', '3306')
DB_USER = os.getenv('DB_USER', 'root')
DB_PASSWORD = os.getenv('DB_PASSWORD', '')
DB_NAME = os.getenv('DB_NAME', 'jan_aushadhi')

is_sqlite = False

def get_connection():
    global is_sqlite
    
    if DB_TYPE == 'sqlite':
        is_sqlite = True
        conn = sqlite3.connect('database.db')
        conn.row_factory = sqlite3.Row
        return conn
        
    try:
        import mysql.connector
        conn = mysql.connector.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME
        )
        is_sqlite = False
        return conn
    except Exception as e:
        print(f"Warning: Failed to connect to MySQL ({e}). Falling back to local SQLite database.")
        is_sqlite = True
        conn = sqlite3.connect('database.db')
        conn.row_factory = sqlite3.Row
        return conn

def execute_query(query, params=None, is_select=True, commit=False):
    conn = get_connection()
    cursor = conn.cursor()
    
    if is_sqlite:
        query = query.replace('%s', '?')
        
    try:
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
            
        if is_select:
            if is_sqlite:
                rows = cursor.fetchall()
                result = [dict(row) for row in rows]
            else:
                columns = [col[0] for col in cursor.description]
                result = [dict(zip(columns, row)) for row in cursor.fetchall()]
        else:
            if commit or not is_select:
                conn.commit()
            if cursor.lastrowid:
                result = cursor.lastrowid
            else:
                result = cursor.rowcount
    except Exception as e:
        print(f"Database Query Error: {e}\nQuery: {query}\nParams: {params}")
        raise e
    finally:
        cursor.close()
        conn.close()
        
    return result

def init_db():
    global is_sqlite
    if DB_TYPE == 'mysql':
        try:
            import mysql.connector
            conn = mysql.connector.connect(
                host=DB_HOST,
                port=DB_PORT,
                user=DB_USER,
                password=DB_PASSWORD
            )
            cursor = conn.cursor()
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME}")
            cursor.close()
            conn.close()
            print(f"MySQL database '{DB_NAME}' verified/created.")
        except Exception as e:
            print(f"MySQL initialization failed ({e}). Will create local SQLite instead.")
            is_sqlite = True
            
    conn = get_connection()
    cursor = conn.cursor()
    
    if is_sqlite:
        print("Initializing SQLite tables with SKU and Image fields...")
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'customer',
            phone TEXT,
            address TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""")
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS medicines (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sku TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            generic_name TEXT NOT NULL,
            category TEXT NOT NULL,
            price REAL NOT NULL,
            stock INTEGER NOT NULL,
            description TEXT,
            image_url TEXT,
            dosage_form TEXT,
            manufacturer TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""")
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS cart_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            medicine_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL DEFAULT 1,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (medicine_id) REFERENCES medicines(id) ON DELETE CASCADE
        )""")
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            total_amount REAL NOT NULL,
            status TEXT NOT NULL DEFAULT 'Pending',
            shipping_address TEXT NOT NULL,
            phone TEXT NOT NULL,
            payment_method TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )""")
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS order_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            medicine_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            price REAL NOT NULL,
            FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
            FOREIGN KEY (medicine_id) REFERENCES medicines(id)
        )""")
    else:
        print("Initializing MySQL tables with SKU and Image fields...")
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            email VARCHAR(255) UNIQUE NOT NULL,
            password VARCHAR(255) NOT NULL,
            role VARCHAR(50) NOT NULL DEFAULT 'customer',
            phone VARCHAR(20),
            address TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB""")
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS medicines (
            id INT AUTO_INCREMENT PRIMARY KEY,
            sku VARCHAR(50) UNIQUE NOT NULL,
            name VARCHAR(255) NOT NULL,
            generic_name VARCHAR(255) NOT NULL,
            category VARCHAR(100) NOT NULL,
            price DECIMAL(10,2) NOT NULL,
            stock INT NOT NULL,
            description TEXT,
            image_url TEXT,
            dosage_form VARCHAR(100),
            manufacturer VARCHAR(255),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB""")
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS cart_items (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            medicine_id INT NOT NULL,
            quantity INT NOT NULL DEFAULT 1,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (medicine_id) REFERENCES medicines(id) ON DELETE CASCADE
        ) ENGINE=InnoDB""")
        
        # We drop and recreate or alter tables. For simplicity we assume clean init or handled.
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            total_amount DECIMAL(10,2) NOT NULL,
            status VARCHAR(50) NOT NULL DEFAULT 'Pending',
            shipping_address TEXT NOT NULL,
            phone VARCHAR(20) NOT NULL,
            payment_method VARCHAR(50) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        ) ENGINE=InnoDB""")
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS order_items (
            id INT AUTO_INCREMENT PRIMARY KEY,
            order_id INT NOT NULL,
            medicine_id INT NOT NULL,
            quantity INT NOT NULL,
            price DECIMAL(10,2) NOT NULL,
            FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
            FOREIGN KEY (medicine_id) REFERENCES medicines(id)
        ) ENGINE=InnoDB""")
        
    conn.commit()
    
    # Seed Admin User
    cursor.execute("SELECT * FROM users WHERE role = 'admin'")
    admin = cursor.fetchone()
    if not admin:
        print("Seeding admin account...")
        admin_pass = generate_password_hash("admin123")
        if is_sqlite:
            cursor.execute(
                "INSERT INTO users (name, email, password, role) VALUES (?, ?, ?, ?)",
                ("Jan Aushadhi Admin", "admin@janaushadhi.gov.in", admin_pass, "admin")
            )
        else:
            cursor.execute(
                "INSERT INTO users (name, email, password, role) VALUES (%s, %s, %s, %s)",
                ("Jan Aushadhi Admin", "admin@janaushadhi.gov.in", admin_pass, "admin")
            )
        conn.commit()
        
    # Seed Customer User (Rahul Sharma)
    cursor.execute("SELECT * FROM users WHERE email = 'rahul@gmail.com'")
    cust = cursor.fetchone()
    if not cust:
        print("Seeding customer account (Rahul Sharma)...")
        cust_pass = generate_password_hash("customer123")
        if is_sqlite:
            cursor.execute(
                "INSERT INTO users (name, email, password, role, phone, address) VALUES (?, ?, ?, ?, ?, ?)",
                ("Rahul Sharma", "rahul@gmail.com", cust_pass, "customer", "9876543210", 
                 "Flat 402, Sunshine Apartments, M.G. Road, Sector 15, Gurugram, Haryana - 122001")
            )
        else:
            cursor.execute(
                "INSERT INTO users (name, email, password, role, phone, address) VALUES (%s, %s, %s, %s, %s, %s)",
                ("Rahul Sharma", "rahul@gmail.com", cust_pass, "customer", "9876543210", 
                 "Flat 402, Sunshine Apartments, M.G. Road, Sector 15, Gurugram, Haryana - 122001")
            )
        conn.commit()
        
    # Seed Medicines
    cursor.execute("SELECT COUNT(*) FROM medicines")
    med_count = cursor.fetchone()[0]
    if med_count == 0:
        print("Seeding catalog with generic medicines and images...")
        medicines_data = [
            ("#JAA-0021", "Paracetamol 500mg", "Acetaminophen", "Analgesics", 12.50, 850, 
             "Effective for fever and mild to moderate pain relief. Generic alternative to Crocin/Calpol.", 
             "https://images.unsplash.com/photo-1584308666744-24d5c474f2ae?q=80&w=150&auto=format&fit=crop", 
             "tablet", "Jan Aushadhi Pharmaceuticals"),
            ("#JAA-0452", "Amoxicillin 250mg", "Amoxicillin Trihydrate", "Antibiotics", 45.00, 12, 
             "Broad-spectrum antibiotic used to treat bacterial infections. Generic alternative to Mox.", 
             "https://images.unsplash.com/photo-1550572017-edd951b55104?q=80&w=150&auto=format&fit=crop", 
             "syrup", "National Health Labs"),
            ("#JAA-0118", "Metformin 500mg", "Metformin Hydrochloride", "Antidiabetic", 22.00, 240, 
             "First-line medication for the treatment of type 2 diabetes. Generic alternative to Glycomet.", 
             "https://images.unsplash.com/photo-1607619056574-7b8f304b3c93?q=80&w=150&auto=format&fit=crop", 
             "tablet", "Generic Drugs Corp"),
            ("#JAA-0892", "Omeprazole 20mg", "Omeprazole", "Gastrointestinal", 18.75, 1120, 
             "Proton pump inhibitor that decreases stomach acid. Generic alternative to Omez.", 
             "https://images.unsplash.com/photo-1471864190281-a93a3070b6de?q=80&w=150&auto=format&fit=crop", 
             "tablet", "Astra Generic Care"),
            ("#JAA-0035", "Cetirizine Syrup", "Cetirizine Hydrochloride", "Antihistamine", 15.00, 320, 
             "Allergy relief syrup for running nose, sneezing, and watery eyes. Generic alternative to Okacet.", 
             "https://images.unsplash.com/photo-1550572017-edd951b55104?q=80&w=150&auto=format&fit=crop", 
             "syrup", "Pure Care Pharma"),
            ("#JAA-0044", "Atorvastatin 10mg", "Atorvastatin Calcium", "Cardiovascular", 38.00, 60, 
             "Statin medication used to prevent cardiovascular disease and lower cholesterol. Generic alternative to Lipivas.", 
             "https://images.unsplash.com/photo-1628771065518-0d82f1938462?q=80&w=150&auto=format&fit=crop", 
             "tablet", "Cardio Generic Ltd"),
            ("#JAA-0056", "Ibuprofen 400mg", "Ibuprofen", "Analgesics", 15.00, 150, 
             "Nonsteroidal anti-inflammatory drug (NSAID) used for treating pain, fever, and inflammation. Generic alternative to Brufen.", 
             "https://images.unsplash.com/photo-1584308666744-24d5c474f2ae?q=80&w=150&auto=format&fit=crop", 
             "tablet", "Jan Aushadhi Pharmaceuticals")
        ]
        
        for item in medicines_data:
            if is_sqlite:
                cursor.execute("""
                INSERT INTO medicines (sku, name, generic_name, category, price, stock, description, image_url, dosage_form, manufacturer)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, item)
            else:
                cursor.execute("""
                INSERT INTO medicines (sku, name, generic_name, category, price, stock, description, image_url, dosage_form, manufacturer)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, item)
        conn.commit()
        print("Medicines catalog seeded successfully.")
        
    # Seed Mock Order for tracking demonstration: Order ID #24 (display code JAK-882910-24)
    cursor.execute("SELECT * FROM orders WHERE id = 24")
    order = cursor.fetchone()
    if not order:
        print("Seeding demo order for tracking (#JAK-882910-24)...")
        # Fetch Rahul's user ID
        cursor.execute("SELECT id FROM users WHERE email = 'rahul@gmail.com'")
        rahul_id = cursor.fetchone()[0]
        
        # Fetch Paracetamol and Metformin IDs
        cursor.execute("SELECT id FROM medicines WHERE sku = '#JAA-0021'")
        para_id = cursor.fetchone()[0]
        cursor.execute("SELECT id FROM medicines WHERE sku = '#JAA-0118'")
        met_id = cursor.fetchone()[0]
        
        # Insert order with explicit ID 24
        # Total: Paracetamol is ₹12.00 (discounted for this order) and Metformin is ₹24.50. Total = ₹36.50
        # In SQLite, we can insert explicit ID.
        if is_sqlite:
            cursor.execute("""
            INSERT INTO orders (id, user_id, total_amount, status, shipping_address, phone, payment_method, created_at)
            VALUES (24, ?, ?, 'Shipped', ?, ?, 'Cash on Delivery', '2026-06-18 10:12:00')
            """, (rahul_id, 36.50, "Flat 402, Sunshine Apartments, M.G. Road, Sector 15, Gurugram, Haryana - 122001", "9876543210"))
            
            cursor.execute("""
            INSERT INTO order_items (order_id, medicine_id, quantity, price)
            VALUES (24, ?, 1, 12.00)
            """, (para_id,))
            
            cursor.execute("""
            INSERT INTO order_items (order_id, medicine_id, quantity, price)
            VALUES (24, ?, 1, 24.50)
            """, (met_id,))
        else:
            # For MySQL, we insert and then we can update the ID to 24 if needed, or check if we can insert it.
            # Usually MySQL supports explicit insert on AUTO_INCREMENT fields if value is provided.
            try:
                cursor.execute("""
                INSERT INTO orders (id, user_id, total_amount, status, shipping_address, phone, payment_method, created_at)
                VALUES (24, %s, %s, 'Shipped', %s, %s, 'Cash on Delivery', '2026-06-18 10:12:00')
                """, (rahul_id, 36.50, "Flat 402, Sunshine Apartments, M.G. Road, Sector 15, Gurugram, Haryana - 122001", "9876543210"))
                
                cursor.execute("""
                INSERT INTO order_items (order_id, medicine_id, quantity, price)
                VALUES (24, %s, 1, 12.00)
                """, (para_id,))
                
                cursor.execute("""
                INSERT INTO order_items (order_id, medicine_id, quantity, price)
                VALUES (24, %s, 1, 24.50)
                """, (met_id,))
            except Exception as ex:
                print(f"Failed to seed explicit MySQL order ID: {ex}. Placing normal order.")
                cursor.execute("""
                INSERT INTO orders (user_id, total_amount, status, shipping_address, phone, payment_method)
                VALUES (%s, %s, 'Shipped', %s, %s, 'Cash on Delivery')
                """, (rahul_id, 36.50, "Flat 402, Sunshine Apartments, M.G. Road, Sector 15, Gurugram, Haryana - 122001", "9876543210"))
                last_id = cursor.lastrowid
                
                cursor.execute("""
                INSERT INTO order_items (order_id, medicine_id, quantity, price)
                VALUES (%s, %s, 1, 12.00)
                """, (last_id, para_id))
                cursor.execute("""
                INSERT INTO order_items (order_id, medicine_id, quantity, price)
                VALUES (%s, %s, 1, 24.50)
                """, (last_id, met_id))
        conn.commit()
        print("Demo order seeded successfully.")
        
    cursor.close()
    conn.close()

if __name__ == "__main__":
    init_db()
