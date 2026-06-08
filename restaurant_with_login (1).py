import sqlite3 as s3
import datetime as dt
import csv
import os
import hashlib

def safe_password_input(prompt):
    """Works in VS Code, PyCharm, CMD, and all terminals."""
    try:
        import getpass
        pwd = getpass.getpass(prompt)
        # getpass returns empty string silently in some IDEs
        if pwd == "":
            pwd = input(prompt + " (visible mode): ").strip()
        return pwd
    except Exception:
        return input(prompt + " (visible mode): ").strip()

DB_NAME = "Restaurant2.db"

# ─────────────────────────────────────────────
#  DB HELPERS
# ─────────────────────────────────────────────

def get_connection():
    return s3.connect(DB_NAME)

def dml_operations(query, params=()):
    con = get_connection()
    con.execute(query, params)
    con.commit()
    con.close()

def fetch_all(query, params=()):
    con = get_connection()
    cur = con.cursor()
    cur.execute(query, params)
    rows = cur.fetchall()
    cur.close()
    con.close()
    return rows

def get_date():
    return dt.date.today().strftime("%d-%m-%Y")


# ─────────────────────────────────────────────
#  LOGIN TABLE SETUP
# ─────────────────────────────────────────────

def setup_login_table():
    """Create users table and insert default admin if not exists."""
    con = get_connection()
    con.execute("""
        CREATE TABLE IF NOT EXISTS users (
            uid       INTEGER PRIMARY KEY AUTOINCREMENT,
            username  TEXT UNIQUE NOT NULL,
            password  TEXT NOT NULL,
            role      TEXT NOT NULL CHECK(role IN ('admin','staff')),
            created   TEXT
        )
    """)
    con.commit()

    # Check if admin already exists
    cur = con.cursor()
    cur.execute("SELECT uid FROM users WHERE username='admin'")
    if not cur.fetchone():
        hashed = hash_password("admin123")
        con.execute(
            "INSERT INTO users(username, password, role, created) VALUES(?,?,?,?)",
            ("admin", hashed, "admin", get_date())
        )
        con.commit()
        print("\n  ℹ️  Default admin created  →  username: admin  |  password: admin123")
        print("  ⚠️  Please change the password after first login!\n")

    cur.close()
    con.close()


# ─────────────────────────────────────────────
#  PASSWORD HASHING
# ─────────────────────────────────────────────

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password, hashed):
    return hash_password(password) == hashed


# ─────────────────────────────────────────────
#  DISPLAY HELPERS
# ─────────────────────────────────────────────

def print_line(char="─", width=60):
    print(char * width)

def print_header(title):
    print_line("═")
    print(f"  {title}")
    print_line("═")

def pause():
    input("\n  Press Enter to continue...")

def clear():
    os.system("cls" if os.name == "nt" else "clear")


# ─────────────────────────────────────────────
#  LOGIN / AUTH
# ─────────────────────────────────────────────

def login():
    """Show login screen. Returns (username, role) on success."""
    MAX_ATTEMPTS = 3
    attempt = 0

    while attempt < MAX_ATTEMPTS:
        clear()
        print_line("═")
        print("       🍽️   RESTAURANT MANAGEMENT SYSTEM  🍽️")
        print_line("═")
        print("                    🔐  LOGIN")
        print_line()

        username = input("  Username : ").strip()
        password = safe_password_input("  Password : ")

        rows = fetch_all("SELECT password, role FROM users WHERE username=?", (username,))

        if rows and verify_password(password, rows[0][0]):
            role = rows[0][1]
            clear()
            print_line("═")
            print(f"  ✅ Welcome, {username}!  [ Role: {role.upper()} ]")
            print_line("═")
            pause()
            return username, role
        else:
            attempt += 1
            remaining = MAX_ATTEMPTS - attempt
            print(f"\n  ❌ Invalid username or password. {remaining} attempt(s) left.")
            if remaining > 0:
                pause()

    print("\n  🚫 Too many failed attempts. Exiting.\n")
    exit(0)


# ─────────────────────────────────────────────
#  USER MANAGEMENT  (Admin only)
# ─────────────────────────────────────────────

def add_user():
    print_header("➕ ADD NEW USER")
    username = input("  Username : ").strip()
    if not username:
        print("  ❌ Username cannot be empty."); pause(); return

    existing = fetch_all("SELECT uid FROM users WHERE username=?", (username,))
    if existing:
        print(f"  ❌ Username '{username}' already exists."); pause(); return

    try:
        password = safe_password_input("  Password : ")
        confirm  = safe_password_input("  Confirm  : ")
    except Exception:
        password = input("  Password : ").strip()
        confirm  = input("  Confirm  : ").strip()

    if password != confirm:
        print("  ❌ Passwords do not match."); pause(); return
    if len(password) < 4:
        print("  ❌ Password must be at least 4 characters."); pause(); return

    print("  Role: 1 - Admin   2 - Staff")
    role_ch = input("  Choose Role: ").strip()
    role = "admin" if role_ch == "1" else "staff"

    dml_operations(
        "INSERT INTO users(username, password, role, created) VALUES(?,?,?,?)",
        (username, hash_password(password), role, get_date())
    )
    print(f"  ✅ User '{username}' added as [{role.upper()}]")
    pause()

def remove_user(current_user):
    print_header("🗑️  REMOVE USER")
    rows = fetch_all("SELECT uid, username, role FROM users ORDER BY uid")
    if not rows:
        print("  No users found."); pause(); return

    print(f"  {'ID':<6} {'Username':<20} {'Role'}")
    print_line()
    for r in rows:
        print(f"  {r[0]:<6} {r[1]:<20} {r[2]}")
    print_line()

    username = input("  Enter username to remove: ").strip()
    if username == current_user:
        print("  ❌ You cannot remove your own account."); pause(); return
    if username == "admin":
        print("  ❌ Cannot remove the main admin account."); pause(); return

    existing = fetch_all("SELECT uid FROM users WHERE username=?", (username,))
    if not existing:
        print("  ❌ User not found."); pause(); return

    confirm = input(f"  Remove '{username}'? (y/n): ").strip().lower()
    if confirm == "y":
        dml_operations("DELETE FROM users WHERE username=?", (username,))
        print(f"  ✅ User '{username}' removed.")
    else:
        print("  Cancelled.")
    pause()

def view_all_users():
    print_header("👥 ALL USERS")
    rows = fetch_all("SELECT uid, username, role, created FROM users ORDER BY uid")
    if not rows:
        print("  No users found.")
    else:
        print(f"  {'ID':<6} {'Username':<20} {'Role':<10} {'Created'}")
        print_line()
        for r in rows:
            print(f"  {r[0]:<6} {r[1]:<20} {r[2]:<10} {r[3] or '-'}")
    pause()

def change_password(current_user):
    print_header("🔑 CHANGE PASSWORD")
    try:
        old_pass = safe_password_input("  Current Password : ")
        new_pass = safe_password_input("  New Password     : ")
        confirm  = safe_password_input("  Confirm New      : ")
    except Exception:
        old_pass = input("  Current Password : ").strip()
        new_pass = input("  New Password     : ").strip()
        confirm  = input("  Confirm New      : ").strip()

    rows = fetch_all("SELECT password FROM users WHERE username=?", (current_user,))
    if not rows or not verify_password(old_pass, rows[0][0]):
        print("  ❌ Current password is incorrect."); pause(); return
    if new_pass != confirm:
        print("  ❌ New passwords do not match."); pause(); return
    if len(new_pass) < 4:
        print("  ❌ Password must be at least 4 characters."); pause(); return

    dml_operations("UPDATE users SET password=? WHERE username=?",
                   (hash_password(new_pass), current_user))
    print("  ✅ Password changed successfully!")
    pause()

def user_management_menu(current_user):
    while True:
        print_header("🔐 USER MANAGEMENT  [Admin Only]")
        print("  1 - Add New User")
        print("  2 - Remove User")
        print("  3 - View All Users")
        print("  4 - Change My Password")
        print("  0 - Back")
        ch = input("  Choice: ").strip()
        if   ch == "1": add_user()
        elif ch == "2": remove_user(current_user)
        elif ch == "3": view_all_users()
        elif ch == "4": change_password(current_user)
        elif ch == "0": break
        else: print("  Invalid choice.")


# ─────────────────────────────────────────────
#  BILL OPERATIONS
# ─────────────────────────────────────────────

def create_new_bill():
    print_header("CREATE NEW BILL")
    try:
        bill_id    = int(input("  Bill ID        : "))
        table_no   = int(input("  Table Number   : "))
        cust_name  = input("  Customer Name  : ").strip()
        item       = input("  Item Name      : ").strip()
        price      = float(input("  Price (₹)      : "))
        qty        = int(input("  Quantity       : "))
        order_date = input(f"  Order Date (DD-MM-YYYY) [Enter for today {get_date()}]: ").strip()
        if not order_date:
            order_date = get_date()

        total = qty * price
        existing = fetch_all("SELECT bill_id FROM all_bills WHERE bill_id=?", (bill_id,))
        if existing:
            print(f"\n  ❌ Bill ID {bill_id} already exists."); pause(); return

        dml_operations(
            "INSERT INTO all_bills(bill_id,table_no,cust_name,item,qty,price,order_date,total) VALUES(?,?,?,?,?,?,?,?)",
            (bill_id, table_no, cust_name, item, qty, price, order_date, total)
        )
        print_line()
        print(f"  ✅ Bill Created!  Customer: {cust_name}  |  Total: ₹{total:.2f}")
    except ValueError:
        print("  ❌ Invalid input.")
    pause()

def search_bill():
    print_header("SEARCH BILL")
    print("  1 - By Customer Name  2 - By Table No  3 - By Bill ID")
    ch = input("  Choice: ").strip()
    rows = []
    if   ch == "1":
        n = input("  Customer Name: ").strip()
        rows = fetch_all("SELECT * FROM all_bills WHERE cust_name LIKE ?", (f"%{n}%",))
    elif ch == "2":
        t = input("  Table Number: ").strip()
        rows = fetch_all("SELECT * FROM all_bills WHERE table_no=?", (t,))
    elif ch == "3":
        b = input("  Bill ID: ").strip()
        rows = fetch_all("SELECT * FROM all_bills WHERE bill_id=?", (b,))
    else:
        print("  Invalid."); pause(); return

    if not rows:
        print("  No records found.")
    else:
        print_line()
        print(f"  {'BillID':<8} {'Table':<7} {'Customer':<18} {'Item':<18} {'Qty':<5} {'Price':<8} {'Date':<13} {'Total'}")
        print_line()
        for r in rows:
            print(f"  {r[0]:<8} {r[1]:<7} {r[2]:<18} {r[3]:<18} {r[4]:<5} {r[5]:<8} {r[6]:<13} ₹{r[7]}")
    pause()

def view_all_bills():
    print_header("ALL BILLS")
    rows = fetch_all("SELECT * FROM all_bills ORDER BY bill_id")
    if not rows:
        print("  No bills found.")
    else:
        print(f"  {'BillID':<8} {'Table':<7} {'Customer':<18} {'Item':<18} {'Qty':<5} {'Price':<8} {'Date':<13} {'Total'}")
        print_line()
        for r in rows:
            print(f"  {r[0]:<8} {r[1]:<7} {r[2]:<18} {r[3]:<18} {r[4]:<5} {r[5]:<8} {r[6]:<13} ₹{r[7]}")
    pause()


# ─────────────────────────────────────────────
#  DISH OPERATIONS
# ─────────────────────────────────────────────

def add_new_dish():
    print_header("ADD NEW DISH")
    try:
        did    = int(input("  Dish ID    : "))
        dname  = input("  Dish Name  : ").strip()
        dprice = float(input("  Dish Price : "))
        existing = fetch_all("SELECT did FROM dishes WHERE did=?", (did,))
        if existing:
            print(f"  ❌ Dish ID {did} already exists."); pause(); return
        dml_operations("INSERT INTO dishes(did, dname, dprice) VALUES(?,?,?)", (did, dname, dprice))
        print(f"  ✅ Dish '{dname}' added at ₹{dprice}")
    except ValueError:
        print("  ❌ Invalid input.")
    pause()

def update_dish_price():
    print_header("UPDATE DISH PRICE")
    try:
        did    = int(input("  Dish ID       : "))
        nprice = float(input("  New Price (₹) : "))
        existing = fetch_all("SELECT dname FROM dishes WHERE did=?", (did,))
        if not existing:
            print(f"  ❌ Dish ID {did} not found."); pause(); return
        dml_operations("UPDATE dishes SET dprice=? WHERE did=?", (nprice, did))
        print(f"  ✅ '{existing[0][0]}' price updated → ₹{nprice}")
    except ValueError:
        print("  ❌ Invalid input.")
    pause()

def delete_dish():
    print_header("DELETE DISH")
    try:
        did = int(input("  Dish ID: "))
        existing = fetch_all("SELECT dname FROM dishes WHERE did=?", (did,))
        if not existing:
            print("  ❌ Dish not found."); pause(); return
        if input(f"  Delete '{existing[0][0]}'? (y/n): ").strip().lower() == 'y':
            dml_operations("DELETE FROM dishes WHERE did=?", (did,))
            print("  ✅ Dish deleted.")
        else:
            print("  Cancelled.")
    except ValueError:
        print("  ❌ Invalid input.")
    pause()

def view_all_dish():
    print_header("ALL DISHES")
    rows = fetch_all("SELECT * FROM dishes ORDER BY dprice")
    if not rows:
        print("  No dishes found.")
    else:
        print(f"  {'ID':<8} {'Dish Name':<25} {'Price (₹)'}")
        print_line()
        for r in rows:
            print(f"  {r[0]:<8} {r[1]:<25} ₹{r[2]}")
    pause()


# ─────────────────────────────────────────────
#  EMPLOYEE OPERATIONS
# ─────────────────────────────────────────────

def add_new_employee():
    print_header("ADD NEW EMPLOYEE")
    try:
        empid     = int(input("  Employee ID : "))
        empname   = input("  Name        : ").strip()
        empemail  = input("  Email       : ").strip()
        empmob    = input("  Mobile      : ").strip()
        empsalary = float(input("  Salary (₹)  : "))
        existing  = fetch_all("SELECT empid FROM Employees WHERE empid=?", (empid,))
        if existing:
            print(f"  ❌ Employee ID {empid} already exists."); pause(); return
        dml_operations(
            "INSERT INTO Employees(empid,empname,empemail,empmob,empsalary) VALUES(?,?,?,?,?)",
            (empid, empname, empemail, empmob, empsalary)
        )
        print(f"  ✅ Employee '{empname}' added.")
    except ValueError:
        print("  ❌ Invalid input.")
    pause()

def remove_employee():
    print_header("REMOVE EMPLOYEE")
    try:
        empid    = int(input("  Employee ID: "))
        existing = fetch_all("SELECT empname FROM Employees WHERE empid=?", (empid,))
        if not existing:
            print("  ❌ Employee not found."); pause(); return
        if input(f"  Remove '{existing[0][0]}'? (y/n): ").strip().lower() == 'y':
            dml_operations("DELETE FROM Employees WHERE empid=?", (empid,))
            print("  ✅ Employee removed.")
        else:
            print("  Cancelled.")
    except ValueError:
        print("  ❌ Invalid input.")
    pause()

def view_all_employees():
    print_header("ALL EMPLOYEES")
    rows = fetch_all("SELECT * FROM Employees ORDER BY empid")
    if not rows:
        print("  No employees found.")
    else:
        print(f"  {'ID':<8} {'Name':<20} {'Email':<28} {'Mobile':<15} {'Salary (₹)'}")
        print_line()
        for r in rows:
            print(f"  {r[0]:<8} {r[1]:<20} {r[2]:<28} {str(r[3]):<15} ₹{r[4]}")
    pause()

def update_employee_salary():
    print_header("UPDATE SALARY")
    try:
        empid   = int(input("  Employee ID    : "))
        nsalary = float(input("  New Salary (₹) : "))
        existing = fetch_all("SELECT empname FROM Employees WHERE empid=?", (empid,))
        if not existing:
            print("  ❌ Employee not found."); pause(); return
        dml_operations("UPDATE Employees SET empsalary=? WHERE empid=?", (nsalary, empid))
        print(f"  ✅ Salary updated for '{existing[0][0]}' → ₹{nsalary}")
    except ValueError:
        print("  ❌ Invalid input.")
    pause()


# ─────────────────────────────────────────────
#  COLLECTION REPORTS
# ─────────────────────────────────────────────

def view_todays_collection():
    print_header("TODAY'S COLLECTION")
    tday = get_date()
    rows = fetch_all("SELECT total FROM all_bills WHERE order_date=?", (tday,))
    coll = sum(r[0] for r in rows)
    print(f"  Date   : {tday}")
    print(f"  Orders : {len(rows)}")
    print(f"  Total  : ₹{coll}")
    pause()

def view_collection_on_date():
    print_header("COLLECTION ON DATE")
    sdate = input("  Date (DD-MM-YYYY): ").strip()
    rows  = fetch_all("SELECT * FROM all_bills WHERE order_date=?", (sdate,))
    coll  = sum(r[7] for r in rows)
    print(f"\n  Date: {sdate}  |  Orders: {len(rows)}  |  Total: ₹{coll}")
    if rows:
        print_line()
        for r in rows:
            print(f"  Bill {r[0]} | {r[2]:<18} | {r[3]:<18} | ₹{r[7]}")
    pause()

def view_collection_bet_dates():
    print_header("COLLECTION BETWEEN DATES")
    date1 = input("  Start Date (DD-MM-YYYY): ").strip()
    date2 = input("  End Date   (DD-MM-YYYY): ").strip()
    try:
        d1 = dt.datetime.strptime(date1, "%d-%m-%Y").strftime("%Y-%m-%d")
        d2 = dt.datetime.strptime(date2, "%d-%m-%Y").strftime("%Y-%m-%d")
        rows = fetch_all(
            """SELECT * FROM all_bills
               WHERE substr(order_date,7,4)||'-'||substr(order_date,4,2)||'-'||substr(order_date,1,2)
               BETWEEN ? AND ?""", (d1, d2)
        )
        coll = sum(r[7] for r in rows)
        print(f"\n  From {date1} to {date2}  |  Orders: {len(rows)}  |  Total: ₹{coll}")
        if rows:
            print_line()
            for r in rows:
                print(f"  {r[6]:<13} | Bill {r[0]} | {r[2]:<18} | {r[3]:<18} | ₹{r[7]}")
    except ValueError:
        print("  ❌ Invalid date format. Use DD-MM-YYYY")
    pause()


# ─────────────────────────────────────────────
#  EDA & ANALYTICS
# ─────────────────────────────────────────────

def eda_most_ordered_dishes():
    print_header("📊 MOST ORDERED DISHES")
    rows = fetch_all("SELECT item, COUNT(*) as orders, SUM(qty) as total_qty, SUM(total) as revenue FROM all_bills GROUP BY item ORDER BY orders DESC")
    if not rows:
        print("  No data."); pause(); return
    print(f"  {'Rank':<6} {'Item':<22} {'Orders':<9} {'Total Qty':<12} {'Revenue (₹)'}")
    print_line()
    for i, r in enumerate(rows, 1):
        print(f"  {i:<6} {r[0]:<22} {r[1]:<9} {r[2]:<12} ₹{r[3]}")
    pause()

def eda_revenue_by_date():
    print_header("📈 REVENUE BY DATE")
    rows = fetch_all("SELECT order_date, COUNT(*) as orders, SUM(total) as revenue FROM all_bills GROUP BY order_date ORDER BY order_date")
    if not rows:
        print("  No data."); pause(); return
    total_rev = sum(r[2] for r in rows)
    max_day   = max(rows, key=lambda x: x[2])
    print(f"  {'Date':<15} {'Orders':<10} {'Revenue (₹)':<15} {'Bar'}")
    print_line()
    for r in rows:
        bar = "█" * (r[2] // 10)
        print(f"  {r[0]:<15} {r[1]:<10} ₹{r[2]:<14} {bar}")
    print_line()
    print(f"  Total Revenue : ₹{total_rev}  |  Best Day: {max_day[0]} (₹{max_day[2]})")
    pause()

def eda_top_customers():
    print_header("🏆 TOP CUSTOMERS")
    rows = fetch_all("SELECT cust_name, COUNT(*) as visits, SUM(total) as spent FROM all_bills GROUP BY cust_name ORDER BY spent DESC LIMIT 10")
    if not rows:
        print("  No data."); pause(); return
    print(f"  {'Rank':<6} {'Customer':<22} {'Visits':<10} {'Total Spent (₹)'}")
    print_line()
    for i, r in enumerate(rows, 1):
        print(f"  {i:<6} {r[0]:<22} {r[1]:<10} ₹{r[2]}")
    pause()

def eda_summary_stats():
    print_header("📋 BUSINESS SUMMARY")
    bills    = fetch_all("SELECT total FROM all_bills")
    totals   = [r[0] for r in bills]
    emp_cnt  = fetch_all("SELECT COUNT(*) FROM Employees")[0][0]
    dish_cnt = fetch_all("SELECT COUNT(*) FROM dishes")[0][0]
    user_cnt = fetch_all("SELECT COUNT(*) FROM users")[0][0]
    if totals:
        avg_bill  = sum(totals) / len(totals)
        top_item  = fetch_all("SELECT item, COUNT(*) c FROM all_bills GROUP BY item ORDER BY c DESC LIMIT 1")
        peak_tbl  = fetch_all("SELECT table_no, COUNT(*) c FROM all_bills GROUP BY table_no ORDER BY c DESC LIMIT 1")
        print(f"  Total Bills       : {len(totals)}")
        print(f"  Total Revenue     : ₹{sum(totals)}")
        print(f"  Average Bill      : ₹{avg_bill:.2f}")
        print(f"  Highest Bill      : ₹{max(totals)}")
        print(f"  Lowest Bill       : ₹{min(totals)}")
        print(f"  Total Employees   : {emp_cnt}")
        print(f"  Total Dishes      : {dish_cnt}")
        print(f"  System Users      : {user_cnt}")
        if top_item:  print(f"  Most Ordered      : {top_item[0][0]} ({top_item[0][1]} orders)")
        if peak_tbl:  print(f"  Busiest Table     : Table {peak_tbl[0][0]} ({peak_tbl[0][1]} visits)")
    else:
        print("  No bill data available.")
    pause()

def eda_dish_popularity():
    print_header("🍽️  DISH POPULARITY")
    rows = fetch_all("SELECT item, SUM(qty) as total_qty, SUM(total) as revenue FROM all_bills GROUP BY item ORDER BY total_qty DESC")
    if not rows:
        print("  No data."); pause(); return
    max_qty = rows[0][1] if rows else 1
    print(f"  {'Item':<22} {'Qty Sold':<12} {'Revenue':<12} {'Popularity'}")
    print_line()
    for r in rows:
        bar = "▓" * int((r[1] / max_qty) * 20)
        print(f"  {r[0]:<22} {r[1]:<12} ₹{r[2]:<11} {bar}")
    pause()


# ─────────────────────────────────────────────
#  EXPORT TO CSV
# ─────────────────────────────────────────────

def export_to_csv():
    print_header("📁 EXPORT TO CSV")
    print("  1 - Export All Bills")
    print("  2 - Export All Employees")
    print("  3 - Export All Dishes")
    print("  4 - Export Revenue Summary by Date")
    ch = input("  Choice: ").strip()

    exports = {
        "1": ("all_bills",  ["BillID","Table","Customer","Item","Qty","Price","Date","Total"],  "bills_export.csv"),
        "2": ("Employees",  ["EmpID","Name","Email","Mobile","Salary"],                         "employees_export.csv"),
        "3": ("dishes",     ["DishID","Name","Price"],                                          "dishes_export.csv"),
    }

    if ch in exports:
        table, headers, fname = exports[ch]
        rows = fetch_all(f"SELECT * FROM {table}")
        with open(fname, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            writer.writerows(rows)
        print(f"  ✅ Exported {len(rows)} records to '{fname}'")
    elif ch == "4":
        rows = fetch_all("SELECT order_date, COUNT(*) as orders, SUM(total) as revenue FROM all_bills GROUP BY order_date ORDER BY order_date")
        fname = "revenue_summary.csv"
        with open(fname, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["Date", "Orders", "Revenue"])
            writer.writerows(rows)
        print(f"  ✅ Revenue summary exported to '{fname}'")
    else:
        print("  Invalid choice.")
    pause()


# ─────────────────────────────────────────────
#  SUB MENUS
# ─────────────────────────────────────────────

def bills_menu():
    while True:
        print_header("🧾 BILLS MENU")
        print("  1 - Create New Bill")
        print("  2 - Search Bill")
        print("  3 - View All Bills")
        print("  0 - Back")
        ch = input("  Choice: ").strip()
        if   ch == "1": create_new_bill()
        elif ch == "2": search_bill()
        elif ch == "3": view_all_bills()
        elif ch == "0": break
        else: print("  Invalid choice.")

def dishes_menu(role):
    while True:
        print_header("🍛 DISHES MENU")
        print("  1 - View All Dishes")
        if role == "admin":
            print("  2 - Add New Dish")
            print("  3 - Update Dish Price")
            print("  4 - Delete Dish")
        print("  0 - Back")
        ch = input("  Choice: ").strip()
        if   ch == "1": view_all_dish()
        elif ch == "2" and role == "admin": add_new_dish()
        elif ch == "3" and role == "admin": update_dish_price()
        elif ch == "4" and role == "admin": delete_dish()
        elif ch == "0": break
        else: print("  Invalid choice or insufficient permissions.")

def employees_menu(role):
    while True:
        print_header("👨‍💼 EMPLOYEES MENU")
        print("  1 - View All Employees")
        if role == "admin":
            print("  2 - Add New Employee")
            print("  3 - Remove Employee")
            print("  4 - Update Salary")
        print("  0 - Back")
        ch = input("  Choice: ").strip()
        if   ch == "1": view_all_employees()
        elif ch == "2" and role == "admin": add_new_employee()
        elif ch == "3" and role == "admin": remove_employee()
        elif ch == "4" and role == "admin": update_employee_salary()
        elif ch == "0": break
        else: print("  Invalid choice or insufficient permissions.")

def collections_menu():
    while True:
        print_header("💰 COLLECTIONS MENU")
        print("  1 - Today's Collection")
        print("  2 - Collection on Specific Date")
        print("  3 - Collection Between Dates")
        print("  0 - Back")
        ch = input("  Choice: ").strip()
        if   ch == "1": view_todays_collection()
        elif ch == "2": view_collection_on_date()
        elif ch == "3": view_collection_bet_dates()
        elif ch == "0": break
        else: print("  Invalid choice.")

def analytics_menu():
    while True:
        print_header("📊 ANALYTICS MENU")
        print("  1 - Business Summary")
        print("  2 - Most Ordered Dishes")
        print("  3 - Dish Popularity Ranking")
        print("  4 - Revenue by Date")
        print("  5 - Top Customers")
        print("  0 - Back")
        ch = input("  Choice: ").strip()
        if   ch == "1": eda_summary_stats()
        elif ch == "2": eda_most_ordered_dishes()
        elif ch == "3": eda_dish_popularity()
        elif ch == "4": eda_revenue_by_date()
        elif ch == "5": eda_top_customers()
        elif ch == "0": break
        else: print("  Invalid choice.")


# ─────────────────────────────────────────────
#  MAIN
# ─────────────────────────────────────────────

def main():
    setup_login_table()
    current_user, role = login()

    while True:
        clear()
        print_line("═")
        print("       🍽️   RESTAURANT MANAGEMENT SYSTEM  🍽️")
        print_line("═")
        print(f"  👤 Logged in as : {current_user}  [ {role.upper()} ]")
        print(f"  📅 Date         : {get_date()}")
        print_line()
        print("  1 - 🧾  Bills")
        print("  2 - 🍛  Dishes")
        print("  3 - 👨‍💼  Employees")
        print("  4 - 💰  Collections")
        print("  5 - 📊  Analytics & EDA")
        if role == "admin":
            print("  6 - 📁  Export to CSV")
            print("  7 - 🔐  User Management")
        print("  8 - 🔑  Change My Password")
        print("  0 - 🚪  Logout & Exit")
        print_line()
        ch = input("  Select Menu: ").strip()

        if   ch == "1": bills_menu()
        elif ch == "2": dishes_menu(role)
        elif ch == "3": employees_menu(role)
        elif ch == "4": collections_menu()
        elif ch == "5": analytics_menu()
        elif ch == "6" and role == "admin": export_to_csv()
        elif ch == "7" and role == "admin": user_management_menu(current_user)
        elif ch == "8": change_password(current_user)
        elif ch == "0":
            print(f"\n  👋 Goodbye, {current_user}!\n")
            break
        else:
            print("  ❌ Invalid choice or insufficient permissions.")
            pause()

if __name__ == "__main__":
    main()
