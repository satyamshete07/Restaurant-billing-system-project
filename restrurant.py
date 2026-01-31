import sqlite3 as s3
import datetime as dt

def dml_operations(query):
    con = s3.connect("Restaurant2.db")
    con.execute(query)
    con.commit()
    con.close()

def get_date():
    date_obj = dt.date.today()
    d = str( date_obj.day )
    m = str( date_obj.month )
    y = str( date_obj.year )
    curr_date = d + "-" + m + "-" + y
    return curr_date

def create_new_bill():
    bill_id =input("Enter Bill ID: ")
    table_no =input("Enter Table Number: ")
    cust_name = input("Enter Customer Name: ")
    item = input("Enter Item Name: ")
    price = float(input("Enter Price:"))
    qty = int(input("Enter Quantity: "))
    order_date = input("Enter Order Date (DD-MM-YYYY): ")

    total = qty * price
    q= """ insert into
        all_bills(bill_id,table_no,cust_name,item,qty,price,order_date,total)
        values({0},{1},'{2}','{3}',{4},{5},'{6}',{7})
       """.format(bill_id,table_no,cust_name,item,qty,price,order_date,total)

    dml_operations(q)
    print("New bill created...")
    input()

def add_new_dish():
    did=input("Enter Dish Id:")
    dname=input("Enter Dish Name:") 

    dml_operations(q)
    print("New Dish Added...")
    input()

def update_dish_price():
    did=input("Enter Dish Id:")
    nprice=input("Enter new price for the Dish:")

    q= """ update dishes
           set dprice={0}
           where did={1} 
       """.format(nprice,did)

    dml_operations(q)
    print("Dish Price Updated:")
    input()
def add_new_employee():
   empid=input("Enter new Employee Id:")
   empname=input("Enter Employee Name:")
   empemail=input("Enter Employee Email:")
   empmob=input("Enter Mobile number:")
   empsalary=input("Enter Employee Salary:")

   q=""" insert into Employees
         (empid,empname,empemail,empmob,empsalary)
         values({0},'{1}','{2}',{3},{4}) 
     """.format(empid,empname,empemail,empmob,empsalary)

   dml_operations(q)
   print("New Employee Added")
   input()
 
def remove_employee():
    empid=input("Enter Employee Id:")

    q=""" delete from Employees 
    where empid={0} 
      """.format(empid)

    dml_operations(q)
    print("Employee removed")
    input()

def view_all_dish():
    q=""" select * from dishes
      """
    con = s3.connect("Restaurant2.db")
    cur = con.cursor()
    cur.execute(q)
    all_rec = cur.fetchall()
    for one_rec in all_rec:
        print(one_rec[0], one_rec[1], one_rec[2], sep="\t")
    cur.close()
    con.close()
    input()

def view_todays_collection():
    tday=dt.date.today()

    q="""select total from all_bills where order_date='{0}'
      """.format(tday)
    con = s3.connect("Restaurant2.db")
    cur = con.cursor()
    cur.execute(q)
    all_rec = cur.fetchall()
    coll = 0
    i = 0
    for one_rec in all_rec:
        coll = coll + one_rec[0]

    print("Total Collection of:", tday, "is:", coll)
    cur.close()
    con.close()
    input()

def view_collection_on_date():
    sdate=input("Enter Specific Date:")
    q=""" select total from all_bills where order_date='{0}'
      """.format(sdate)
    con = s3.connect("Restaurant2.db")
    cur = con.cursor()
    cur.execute(q)
    all_rec = cur.fetchall()
    coll=0

    for one_rec in all_rec:
        #print(one_rec[0],sep="\t")
        coll= coll + one_rec[0]

    print("Total Collection on:",sdate,"is",coll)
    cur.close()
    con.close()
    input()

def view_collection_bet_dates():
    date1=input("Enter Start date:")
    date2=input("Enter End Date:")

    q=""" select total from all_bills where  order_date between '{0}' AND '{1}'  
      """.format(date1,date2)

    con = s3.connect("Restaurant2.db")
    cur = con.cursor()
    cur.execute(q)
    all_rec = cur.fetchall()
    coll = 0
    i = 0
    for one_rec in all_rec:
        # print(one_rec[0],sep="\t")
        coll = coll + one_rec[0]

    print("Total Collection from:",date1,"to",date2,"is", coll)
    cur.close()
    con.close()
    input()


while True:
    print("Select Operation")
    print("1 - Create New Bill")
    print("2 - Add New Dish")
    print("3 - Update Dish Price")
    print("4 - Add New Employee")
    print("5 - Remove Employee")
    print("6 - View All Dish")
    print("7 - View Today' s Total Collection")
    print("8 - View Total Collection on Specific Date")
    print("9 - View Total Collection Between Specific Dates")
    print("0 - Exit")
    ch = int( input("Provide your choice : ") )
    if ch==1: create_new_bill()
    elif ch==2: add_new_dish()
    elif ch==3: update_dish_price()
    elif ch==4: add_new_employee()
    elif ch==5: remove_employee()
    elif ch==6: view_all_dish()
    elif ch==7: view_todays_collection()
    elif ch==8: view_collection_on_date()
    elif ch==9: view_collection_bet_dates()
    elif ch==0: exit(0) 