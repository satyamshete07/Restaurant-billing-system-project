import sqlite3 as s3

def creating_tables(query):
    con = s3.connect("Restaurant2.db")
    con.execute(query)
    con.commit()
    con.close()

q1 = """
    create table Employees
    (
      empid number(15) primary key,
      empname varchar(30),
      empemail varchar(75),
      empmob number(15),
      empsalary varchar(10)
    )
"""

q2 = """
    create table all_bills
    (
      bill_id number(15) primary key,
      table_no number(15),
      cust_name varchar(20),
      item varchar(20),
      qty number(10),
      price number(10),
      order_date varchar(20),
      total number(10)
    )
"""

q3 = """
    create table dishes
    (
      did number(10) primary key,
      dname varchar(20),
      dprice number(10)
    )
"""

creating_tables(q1)
creating_tables(q2)
creating_tables(q3)