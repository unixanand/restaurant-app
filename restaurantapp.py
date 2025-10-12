import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
from datetime import datetime, timedelta, date
import time
import pytz
import oracledb
import os
import re
from dotenv import load_dotenv
import logging

# Define BASE_DIR for consistent file paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))


FILES_DIR = os.environ.get('FILES_DIR', os.path.join(BASE_DIR, 'Files'))
BULK_DIR = os.environ.get('BULK_DIR', os.path.join(BASE_DIR, 'Bulk_Import'))
REPORTS_DIR = os.environ.get('REPORTS_DIR', os.path.join(BASE_DIR, 'reports'))
os.makedirs(FILES_DIR, exist_ok=True)
os.makedirs(BULK_DIR, exist_ok=True)
os.makedirs(REPORTS_DIR, exist_ok=True)

load_dotenv()  # Load environment variables from .env file

def get_connection():
    """Load DB credentials from environment variables and connect to Oracle."""
    user = os.environ.get('DB_USER')
    password = os.environ.get('DB_PASSWORD')
    dsn = os.environ.get('DB_DSN')
    if not all([user, password, dsn]):
        st.error("Missing DB environment variables: DB_USER, DB_PASSWORD, DB_DSN")
        return None
    try:
        connection = oracledb.connect(user=user, password=password, dsn=dsn)
        st.success("Connected to Oracle Database!")
        return None
    except Exception as e:
        st.error(f"DB Connection Error: {e}")
        return None

# --- Inlined Functions from Original App (Adapted for Streamlit) ---



def get_connection():
    """Load DB credentials from environment variables and connect to Oracle."""
    user = os.environ.get('DB_USER')
    password = os.environ.get('DB_PASSWORD')
    dsn = os.environ.get('DB_DSN')  # e.g., 'host:port/service_name'
    
    if not all([user, password, dsn]):
        st.error("Missing DB environment variables: DB_USER, DB_PASSWORD, DB_DSN")
        return None
    
    try:
        connection = oracledb.connect(user=user, password=password, dsn=dsn)
        st.success("Connected to Oracle Database!")
        return connection
    except Exception as e:
        st.error(f"DB Connection Error: {e}")
        return None


def load_stock_txn_data(connection) :
    rec_cnt = 0
    
    
    qry = "select count(*) cnt from STOCK_MAINTENANCE_TXN_TBL where value_date=trim(sysdate)"
    ins_qry = "insert into STOCK_MAINTENANCE_TXN_TBL (value_date, item_name, avail_stock) select trim(sysdate), item_name, total_stock from STOCK_MAINTENANCE_TBL where delete_flag='N' "
    
    cursor = connection.cursor()
    cursor.execute(qry)

    for row in cursor.fetchone() :
        if row is None :
             break
        rec_cnt = row

    if rec_cnt == 0 :
        cursor.execute(ins_qry)
        connection.commit()

    
def load_tax_data(connection):
    """Load tax categories and rates."""
    cursor = connection.cursor()
    sel_tax_rec = "SELECT category_name, tax_slab FROM tax_maintenance_tbl"
    cursor.execute(sel_tax_rec)
    tax_data = {}
    while True:
        row = cursor.fetchone()
        if row is None:
            break
        tax_data[row[0]] = row[1]
    cursor.close()
    return tax_data

def get_stock_data(connection):
    """Load stock for current date."""
    cursor = connection.cursor()
    sel_qry = "select item_name, avail_stock from STOCK_MAINTENANCE_TXN_TBL where value_date=TRIM(SYSDATE)"
    cursor.execute(sel_qry)
    stock_rec = {}
    while True:
        rec = cursor.fetchone()
        if rec is None:
            break
        stock_rec[rec[0]] = int(rec[1])
    cursor.close()
    return stock_rec

def get_shortage_stock_data(connection):
    """Load shortage stock for current date."""
    cursor = connection.cursor()
    sel_qry = "select item_name, avail_stock from STOCK_MAINTENANCE_TXN_TBL where value_date=TRIM(SYSDATE) and avail_stock = 0"
    cursor.execute(sel_qry)
    stock_rec = {}
    while True:
        rec = cursor.fetchone()
        if rec is None:
            break
        stock_rec[rec[0]] = int(rec[1])
    cursor.close()
    return stock_rec

def load_shortage_stock_data(connection):
    """Load shortage stock for current date."""
    cursor = connection.cursor()
    upd_qry = "update STOCK_MAINTENANCE_TXN_TBL set avail_stock=50 where value_date=TRIM(SYSDATE) and avail_stock = 0"
    cursor.execute(upd_qry)
    connection.commit()
    cursor.close()

def update_stock_rec(connection, stock_rec):
    """Update stock in DB."""
    cursor = connection.cursor()
    upd_qry = "update STOCK_MAINTENANCE_TXN_TBL set avail_stock = :qty where value_date=trim(sysdate) and item_name = :itm"
    for itm, qty in stock_rec.items():
        cursor.execute(upd_qry, {"qty": qty, "itm": itm})
    connection.commit()
    cursor.close()

def update_tax_amt(connection,tax_category,tax_amount) :
    category = str(tax_category)
    amt = float(tax_amount)
    cursor = connection.cursor()
    
    
    upd_qry = "update TAX_MAINTENANCE_TBL set tax_slab = :amt where category_name = :category"
    try:
        
        cursor.execute(upd_qry,{"amt" : amt, "category" : category})
        connection.commit()
        
    except oracledb.DatabaseError as e:
        st.error(f"DB Update Error: {e}")
    cursor.close()


def insert_db_data(connection, tmp_lis):
    """Insert sales to DB."""
    cursor = connection.cursor()
    current_date = date.today().strftime("%d-%b-%Y").upper()
    ins_rec = []
    for idx in range(len(tmp_lis)):
        ins_rec.append([current_date, str(tmp_lis[idx][0]), str(tmp_lis[idx][1]), str(tmp_lis[idx][2])])
    insert_sales_rec = "insert into sales_dtl_tbl (value_date, item_name, quantity, sales_amt) values (:1, :2, :3, :4)"
    try:
        cursor.executemany(insert_sales_rec, ins_rec)
        connection.commit()
    except oracledb.DatabaseError as e:
        st.error(f"DB Insert Error: {e}")
    cursor.close()

def fetch_coffee_df(connection):
    """Fetch available coffee menu."""
    cursor = connection.cursor()
    sel_qry1 = "SELECT rownum, coffee_name, price, tax_category FROM coffee_menu_tbl a where a.coffee_name in (select b.item_name from STOCK_MAINTENANCE_TXN_TBL b "
    sel_qry2 = "where a.coffee_name=b.item_name and value_date=trim(sysdate) and avail_stock > 0) and delete_flag='N'"
    cursor.execute(sel_qry1 + sel_qry2)
    rows = cursor.fetchall()
    df = pd.DataFrame(rows, columns=['ItemNo', 'Name', 'Price', 'TaxCategory'])
    cursor.close()
    return df

def fetch_tea_df(connection):
    """Fetch available tea menu."""
    cursor = connection.cursor()
    sel_qry1 = "SELECT rownum, tea_name, price, tax_category FROM tea_menu_tbl a where a.tea_name in (select b.item_name from STOCK_MAINTENANCE_TXN_TBL b "
    sel_qry2 = "where a.tea_name=b.item_name and value_date=trim(sysdate) and avail_stock > 0) and delete_flag='N'"
    cursor.execute(sel_qry1 + sel_qry2)
    rows = cursor.fetchall()
    df = pd.DataFrame(rows, columns=['ItemNo', 'Name', 'Price', 'TaxCategory'])
    cursor.close()
    return df

def fetch_chat_df(connection, category):
    """Fetch chat menu (Veg/Non-Veg/Both)."""
    cursor = connection.cursor()
    if category == "VEG":
        select_rec = "SELECT rownum, chat_name, price, tax_category FROM chat_menu_tbl a WHERE category = 'VEG' and a.chat_name in (select b.item_name from STOCK_MAINTENANCE_TXN_TBL b where a.chat_name = b.item_name and value_date=trim(sysdate) and avail_stock > 0) and a.delete_flag='N'"
    elif category == "NV":
        select_rec = "SELECT rownum, chat_name, price, tax_category FROM chat_menu_tbl a WHERE category = 'NV' and a.chat_name in (select b.item_name from STOCK_MAINTENANCE_TXN_TBL b where a.chat_name = b.item_name and value_date=trim(sysdate) and avail_stock > 0) and a.delete_flag='N'"
    else : 
        select_rec = "SELECT rownum, chat_name, price, tax_category FROM chat_menu_tbl a where a.chat_name in (select b.item_name from STOCK_MAINTENANCE_TXN_TBL b where a.chat_name = b.item_name and value_date=trim(sysdate) and avail_stock > 0) and a.delete_flag='N'"
    cursor.execute(select_rec)
    rows = cursor.fetchall()
    df = pd.DataFrame(rows, columns=['ItemNo', 'Name', 'Price', 'TaxCategory'])
    cursor.close()
    return df

def check_time():
    """Check if current time is within special menu hours (17:00-19:00)."""
    local_time = datetime.now(pytz.timezone("Asia/Kolkata"))
    HH = int(local_time.strftime("%H"))
    return 1 if 17 <= HH <= 19 else 0


def fetch_spl_df(connection):
    """Fetch special snacks menu if within time."""
    
    if check_time() == 0:
        return pd.DataFrame()
    cursor = connection.cursor()
    sel_qry = "select rownum, item_name, price, tax_category from special_snacks_tbl where delete_flag='N'"
    cursor.execute(sel_qry)
    rows = cursor.fetchall()
    df = pd.DataFrame(rows, columns=['ItemNo', 'Name', 'Price', 'TaxCategory'])
    cursor.close()
    return df

def fetch_snack_df(connection):
    """Fetch special snacks menu for maintenance"""
    cursor = connection.cursor()
    sel_qry = "select rownum, item_name, price, tax_category from special_snacks_tbl where delete_flag='N'"
    cursor.execute(sel_qry)
    rows = cursor.fetchall()
    df = pd.DataFrame(rows, columns=['ItemNo', 'Name', 'Price', 'TaxCategory'])
    cursor.close()
    return df

def coffee_sales_fig(connection, period):
    """Generate coffee sales chart."""
    cursor = connection.cursor()
    if period == 'Daily':
        qry = "SELECT item_name, sum(quantity) as qty FROM sales_dtl_tbl WHERE item_name in (SELECT coffee_name FROM coffee_menu_tbl) AND value_date = trim(sysdate) group by item_name"
    elif period == 'Weekly':
        week_start = (datetime.now() - timedelta(days=datetime.now().weekday())).strftime("%d-%b-%Y").upper()
        qry = f"SELECT item_name, sum(quantity) as qty FROM sales_dtl_tbl WHERE value_date >= '{week_start}' AND item_name in (SELECT coffee_name FROM coffee_menu_tbl) group by item_name"
    else:  # monthly
        year_month = datetime.now().strftime("%Y-%m")
        qry = f"SELECT item_name, sum(quantity) as qty FROM sales_dtl_tbl WHERE to_char(value_date, 'YYYY-MM') = '{year_month}' AND item_name in (SELECT coffee_name FROM coffee_menu_tbl) group by item_name"
    cursor.execute(qry)
    rows = cursor.fetchall()
    df = pd.DataFrame(rows, columns=['Item', 'Quantity'])
    cursor.close()
    if not df.empty:
        fig, ax = plt.subplots()
        df.plot(kind='bar', x='Item', y='Quantity', ax=ax, title=f'Coffee Sales ({period.capitalize()})')
        ax.set_xlabel('Coffee Flavor')
        ax.set_ylabel('Sales Quantity')
        return fig
    return None

def tea_sales_fig(connection, period='daily'):
    """Generate tea sales chart (similar to coffee)."""
    cursor = connection.cursor()
    if period == 'Daily':
        qry = "SELECT item_name, sum(quantity) as qty FROM sales_dtl_tbl WHERE item_name in (SELECT tea_name FROM tea_menu_tbl) AND value_date = trim(sysdate) group by item_name"
    elif period == 'Weekly':
        week_start = (datetime.now() - timedelta(days=datetime.now().weekday())).strftime("%d-%b-%Y").upper()
        qry = f"SELECT item_name, sum(quantity) as qty FROM sales_dtl_tbl WHERE value_date >= '{week_start}' AND item_name in (SELECT tea_name FROM tea_menu_tbl) group by item_name"
    else:
        year_month = datetime.now().strftime("%Y-%m")
        qry = f"SELECT item_name, sum(quantity) as qty FROM sales_dtl_tbl WHERE to_char(value_date, 'YYYY-MM') = '{year_month}' AND item_name in (SELECT tea_name FROM tea_menu_tbl) group by item_name"
    cursor.execute(qry)
    rows = cursor.fetchall()
    df = pd.DataFrame(rows, columns=['Item', 'Quantity'])
    cursor.close()
    if not df.empty:
        fig, ax = plt.subplots()
        df.plot(kind='bar', x='Item', y='Quantity', ax=ax, title=f'Tea Sales ({period.capitalize()})')
        ax.set_xlabel('Tea Type')
        ax.set_ylabel('Sales Quantity')
        return fig
    return None

def chat_sales_fig(connection, period='daily'):
    """Generate chat sales chart (similar to coffee)."""
    cursor = connection.cursor()
    if period == 'Daily':
        qry = "SELECT item_name, sum(quantity) as qty FROM sales_dtl_tbl WHERE item_name in (SELECT chat_name FROM chat_menu_tbl) AND value_date = trim(sysdate) group by item_name"
    elif period == 'Weekly':
        week_start = (datetime.now() - timedelta(days=datetime.now().weekday())).strftime("%d-%b-%Y").upper()
        qry = f"SELECT item_name, sum(quantity) as qty FROM sales_dtl_tbl WHERE value_date >= '{week_start}' AND item_name in (SELECT chat_name FROM chat_menu_tbl) group by item_name"
    else:
        year_month = datetime.now().strftime("%Y-%m")
        qry = f"SELECT item_name, sum(quantity) as qty FROM sales_dtl_tbl WHERE to_char(value_date, 'YYYY-MM') = '{year_month}' AND item_name in (SELECT chat_name FROM chat_menu_tbl) group by item_name"
    cursor.execute(qry)
    rows = cursor.fetchall()
    df = pd.DataFrame(rows, columns=['Item', 'Quantity'])
    cursor.close()
    if not df.empty:
        fig, ax = plt.subplots()
        df.plot(kind='bar', x='Item', y='Quantity', ax=ax, title=f'Tea Sales ({period.capitalize()})')
        ax.set_xlabel('Tea Type')
        ax.set_ylabel('Sales Quantity')
        return fig
    return None

def Spl_sales_fig(connection, period='daily'):
    """Generate snacks sales chart (similar to coffee)."""
    cursor = connection.cursor()
    if period == 'Daily':
        qry = "SELECT item_name, sum(quantity) as qty FROM sales_dtl_tbl WHERE item_name in (SELECT item_name FROM SPECIAL_SNACKS_TBL) AND value_date = trim(sysdate) group by item_name"
    elif period == 'Weekly':
        week_start = (datetime.now() - timedelta(days=datetime.now().weekday())).strftime("%d-%b-%Y").upper()
        qry = f"SELECT item_name, sum(quantity) as qty FROM sales_dtl_tbl WHERE value_date >= '{week_start}' AND item_name in (SELECT item_name FROM SPECIAL_SNACKS_TBL) group by item_name"
    else:
        year_month = datetime.now().strftime("%Y-%m")
        qry = f"SELECT item_name, sum(quantity) as qty FROM sales_dtl_tbl WHERE to_char(value_date, 'YYYY-MM') = '{year_month}' AND item_name in (SELECT item_name FROM SPECIAL_SNACKS_TBL) group by item_name"
    cursor.execute(qry)
    rows = cursor.fetchall()
    df = pd.DataFrame(rows, columns=['Item', 'Quantity'])
    cursor.close()
    if not df.empty:
        fig, ax = plt.subplots()
        df.plot(kind='bar', x='Item', y='Quantity', ax=ax, title=f'Snacks Sales ({period.capitalize()})')
        ax.set_xlabel('Snack Type')
        ax.set_ylabel('Sales Quantity')
        return fig
    return None

def pull_week_data(connection) :
    current_date = datetime.today()
    start_of_week = current_date - timedelta(days=current_date.weekday())
    start_date = start_of_week.date()

    week_start_date = start_date.strftime("%d-%b-%Y").upper()

    sel_qry1 = "select substr(TO_CHAR(value_date, 'DD-Day'),1,6) day,item_name, quantity, sum(sales_amt) tot_sales from SALES_DTL_TBL "
    sel_qry2 = "where value_date >= :week_start_date  group by value_date,item_name, quantity order by 1,2"
    final_qry = sel_qry1 + sel_qry2

    cursor = connection.cursor()
    cursor.execute(final_qry, {"week_start_date" :week_start_date})
    rows = cursor.fetchall()
    df = pd.DataFrame(rows, columns =['Day','Item','Quantity','Tot.Sales'])
    cursor.close()
    return df

def execute_qry(connection, qry_str,column_names) :
    cursor = connection.cursor()
    cursor.execute(qry_str)
    rows = cursor.fetchall()
    df = pd.DataFrame(rows, columns = column_names)
    cursor.close()
    return df

def pull_month_data(connection):
    path = os.path.join(FILES_DIR, "week_wise_sales.txt")
    with open(path, "r") as fp:
        qry = fp.read()
    cursor = connection.cursor()
    cursor.execute(qry)
    rows = cursor.fetchall()
    df = pd.DataFrame(rows, columns=['WeekNo', 'Category', 'Item', 'Tot.Quantity', 'Tot.Sales'])
    cursor.close()
    return df

def get_month_data(connection) :
    item_lis = []
    path = os.path.join(BASE_DIR, "Files", "week_wise_sales.txt")
    fp = open(path,"r")
    cursor = connection.cursor()
    qry = fp.read()
    fp.close()
    cursor.execute(qry)
    while True:
        row = cursor.fetchone()
        if row is None:
            break
        item_lis.append(row)
        
    cursor.close()
    return item_lis
   

def overall_sales_fig(connection, period='daily'):
    """Generate overall sales chart (similar to coffee)."""
    cursor = connection.cursor()
    if period == 'Daily':
        qry = "SELECT item_name, sum(quantity) as qty FROM sales_dtl_tbl WHERE  value_date = trim(sysdate) group by item_name"
    elif period == 'Weekly':
        week_start = (datetime.now() - timedelta(days=datetime.now().weekday())).strftime("%d-%b-%Y").upper()
        qry = f"SELECT item_name, sum(quantity) as qty FROM sales_dtl_tbl WHERE value_date >= '{week_start}'  group by item_name"
    else:
        year_month = datetime.now().strftime("%Y-%m")
        qry = f"SELECT item_name, sum(quantity) as qty FROM sales_dtl_tbl WHERE to_char(value_date, 'YYYY-MM') = '{year_month}'  group by item_name"
    cursor.execute(qry)
    rows = cursor.fetchall()
    df = pd.DataFrame(rows, columns=['Item', 'Quantity'])
    cursor.close()
    if not df.empty:
        fig, ax = plt.subplots()
        df.plot(kind='bar', x='Item', y='Quantity', ax=ax, title=f'OverAll Sales ({period.capitalize()})')
        ax.set_xlabel('Item Type')
        ax.set_ylabel('Sales Quantity')
        return fig
    return None

##
def Week_sale_items(connection) :
    import numpy as np
    import matplotlib.pyplot as plt
    from datetime import datetime, timedelta

    item_lis = []
    
    current_date = datetime.today()
    start_of_week = current_date - timedelta(days=current_date.weekday())
    start_date = start_of_week.date()

    week_start_date = start_date.strftime("%d-%b-%Y").upper()
    
    cursor = connection.cursor()

    sel_qry1 = "select substr(TO_CHAR(value_date, 'DD-Mon'),1,6) day, 'Coffee' item_name, sum(sales_amt) tot_sales from SALES_DTL_TBL "
    sel_qry2 = "where value_date >= :week_start_date and item_name in (select coffee_name from coffee_menu_tbl) group by value_date,item_name UNION "
    sel_qry3 = "select substr(TO_CHAR(value_date, 'DD-Mon'),1,6) day, 'Tea' item_name, sum(sales_amt) tot_sales from SALES_DTL_TBL "
    sel_qry4 = "where value_date >= :week_start_date and item_name in (select tea_name from tea_menu_tbl) group by value_date,item_name UNION "
    sel_qry5 = "select substr(TO_CHAR(value_date, 'DD-Mon'),1,6) day, 'Chat' item_name, sum(sales_amt) tot_sales from SALES_DTL_TBL "
    sel_qry6 = "where value_date >= :week_start_date and item_name in (select chat_name from chat_menu_tbl) group by value_date,item_name UNION "
    sel_qry7 = "select substr(TO_CHAR(value_date, 'DD-Mon'),1,6) day, 'Snacks' item_name, sum(sales_amt) tot_sales from SALES_DTL_TBL "
    sel_qry8 = "where value_date >= :week_start_date and item_name in (select item_name from SPECIAL_SNACKS_TBL) group by value_date,item_name"
    
    final_qry = sel_qry1 + sel_qry2 + sel_qry3 + sel_qry4 + sel_qry5 + sel_qry6 + sel_qry7 + sel_qry8

    cursor.execute(final_qry, {"week_start_date" :week_start_date})

    while True :
        row = cursor.fetchone()
        if row is None :
            break
        rec = tuple(row)
        item_lis.append(rec)

    return item_lis
    
#

def validate_item(connection, item):
    cursor = connection.cursor()
    sel_qry = "select 1 from BULK_ORDER_TBL where item_name = :itm"
    try:
        cursor.execute(sel_qry, {"itm": item})
        row = cursor.fetchone()
        cursor.close()
        if row is None:
            logging.warning(f"Invalid item: {item}")
            return 0
        logging.info(f"Validated item: {item}")
        return 1
    except oracledb.DatabaseError as e:
        logging.error(f"DB Fetch Error for item {item}: {e}")
        st.error(f"DB Fetch Error: {e}")
        return 0


def get_item_stock(connection, item,qty) :
    chk = check_time()
    
    cursor = connection.cursor()
    chk_qry = "select spl_flag from BULK_ORDER_TBL where item_name = :item"
    cursor.execute(chk_qry,{"item" : item})
    row = cursor.fetchone()
    chk_flg = row[0]
    if chk_flg == 'Y' and chk == 0 :
        avail_stock = 0
        qty = 0
        return avail_stock, qty
                   
    
    stk_qry = "select avail_stock from STOCK_MAINTENANCE_TXN_TBL where item_name = :item and value_date= trim(sysdate)"
    cursor.execute(stk_qry, {"item" : item})
    while True :
        row = cursor.fetchone()
        if row is None:
            break
        avail_stock = row[0]
    #st.write(item, avail_stock)  
    cursor.close()
    
    if avail_stock == 0 :
        qty = 0
        return avail_stock, qty
    
    elif avail_stock >= qty :
        avail_stock -= qty
        
        cursor = connection.cursor()
        upd_qry = "update STOCK_MAINTENANCE_TXN_TBL set avail_stock = :avail_stock where item_name = :item and value_date= trim(sysdate)"
        try:
            cursor.execute(upd_qry, {"item" : item, "avail_stock" : avail_stock})
        except oracledb.DatabaseError as e:
            st.error(f"DB Update Error: {e}")
        connection.commit()
        cursor.close()
        return avail_stock, qty
        
    else :
        qty = avail_stock
        avail_stock = 0
        cursor = connection.cursor()
        try:
            upd_qry = "update STOCK_MAINTENANCE_TXN_TBL set avail_stock = 0 where item_name = :item and value_date= trim(sysdate)"
            cursor.execute(upd_qry, {"item" : item})
        except oracledb.DatabaseError as e:
            st.error(f"DB Update Error: {e}")
        connection.commit()
        cursor.close() 
        return avail_stock, qty
    



logging.basicConfig(level=logging.INFO, filename=os.path.join(BASE_DIR, 'Bulk_Import', 'bulk_order.log'))

def insert_log(connection, file, message):
    if not file:
        logging.info("No file provided for logging")
        return
    cursor = connection.cursor()
    sel_qry = "select 1 from bulk_order_log_tbl where value_date=trunc(sysdate) and log_message = :msg and file_name = :fil"
    cursor.execute(sel_qry, {"msg": message, "fil": file})
    row = cursor.fetchone()
    cursor.close()
    if row is None:
        cursor = connection.cursor()
        ins_qry = "insert into bulk_order_log_tbl(value_date, file_name, log_message) values(trunc(sysdate), :2, :3)"
        try:
            cursor.execute(ins_qry, {"2": file, "3": message})
            logging.info(f"Logged: {message} for file {file}")
        except oracledb.DatabaseError as e:
            logging.error(f"DB Insert Error: {e}")
            return
        connection.commit()
        cursor.close()
                   

def load_bulk_header(connection,file,status) :
    if len(file) == 0 :
        return
    cursor = connection.cursor()
    sel_qry = "select 1 from bulk_order_header_tbl where value_date = trunc(sysdate) and file_name = :fil"
    cursor.execute(sel_qry, {"fil" : file})
    row = cursor.fetchone()
    cursor.close()
    if row is None :
        cursor = connection.cursor()
                  
        ins_qry = "insert into bulk_order_header_tbl values(trunc(sysdate), :fil, :stat)"
        cursor.execute(ins_qry, {"fil" : file, "stat" : status})
    
        connection.commit()
        cursor.close()
    
def update_bulk_header(connection,file,status) :
    cursor = connection.cursor()
    upd_qry = "update bulk_order_header_tbl set status=:st where value_date = trunc(sysdate) and file_name = :fil"
    cursor.execute(upd_qry, {"fil" : file, "st" : status})
    connection.commit()
    cursor.close()

def check_bulk_header(connection,file) :
    if len(file) != 0 :
        cursor = connection.cursor()
        chk_qry = "select 1 from bulk_order_header_tbl where value_date = trunc(sysdate) and file_name = :fil and status='Processed' "
        cursor.execute(chk_qry, {"fil" : file})
        row = cursor.fetchone()
        cursor.close()
        if row is None :
            return 0
        return 1
    
def get_item_price(connection,item,qty) :
    cursor = connection.cursor()
    sel_qry = "select price, tax_category from BULK_ORDER_TBL where item_name = :itm"
    try :
        cursor.execute(sel_qry,{"itm" :item})
    except oracledb.DatabaseError as e:
        st.error(f"DB Fetch Error: {e}")
    while True :
        row = cursor.fetchone()
        if row is None :
            break
        if int(row[0]) > 0 :
            price = row[0] * qty
            tax_cat = row[1]
            
    cursor.close()

    tax_qry = "select tax_slab from TAX_MAINTENANCE_TBL where category_name= :tax_cat"
    cursor = connection.cursor()
    cursor.execute(tax_qry, {"tax_cat" : tax_cat})
    while True :
        row = cursor.fetchone()
        if row is None :
            break
        tax = row[0]
    tax_amt = price * tax
    
    cursor.close()
    return price, tax_amt
        
                 

##

# --- Initialize Session State ---
if 'order_menu' not in st.session_state:
    st.session_state.order_menu = {}
    st.session_state.stock_rec = {}
    st.session_state.tax_data = {}
    st.session_state.tax_lis = {}  # For item-specific tax categories

# --- Main App ---
st.set_page_config(page_title="Restaurant Dashboard", layout="wide", initial_sidebar_state="expanded")
st.title("🍽️ Interactive Restaurant Management Dashboard")

connection = get_connection()
if not connection:
    st.stop()

# Insert stock txn data
load_stock_txn_data(connection)
# Load tax and stock on startup
try:
    st.session_state.tax_data = load_tax_data(connection)
    st.session_state.stock_rec = get_stock_data(connection)
    st.success("Data loaded! Select a portal in the sidebar.")
except Exception as e:
    st.error(f"Error loading tax/stock data: {e}")
st.markdown("""
<style>
.stButton>button {
    background-color: #8b4513;
    color: white;
    border-radius: 10px;
}
</style>
""", unsafe_allow_html=True)
# Sidebar for Portal Selection
portal = st.sidebar.selectbox("Select Portal", ["Public (Order)", "Corporate (Admin)"])
if st.sidebar.button("Logout"):
    st.session_state.clear()
    st.rerun()

# --- Public Portal ---
if portal == "Public (Order)":
    st.header("🛒 Public Portal: Place Orders")
    tab1, tab2, tab3, tab4, tab_cart, tab_bill = st.tabs(["Coffee", "Tea", "Chat", "Special", "Cart", "Bill"])
    
    with tab1:  # Coffee
        st.subheader("☕ Coffee Menu")
        df_coffee = fetch_coffee_df(connection)
        
        if not df_coffee.empty:
            st.dataframe(df_coffee[['ItemNo', 'Name', 'Price']])
            with st.form("coffee_order"):
                
                item_options = df_coffee.set_index('ItemNo')['Name'].to_dict()
                selected_item_no = st.selectbox("Choose Item", options=list(item_options.keys()), format_func=lambda x: f"{x}: {item_options[x]}")
                item_name = item_options[selected_item_no]
                max_stock = st.session_state.stock_rec.get(item_name, 0)
                quantity = st.number_input(f"Quantity (Max: {max_stock})", min_value=0, max_value=max_stock, value=0)
                
                col1, col2 = st.columns(2)
                with col1:
                    
                    submitted = st.form_submit_button("Add to Order")
                    
                    if submitted :
                        
                        if quantity > 0 :
                            price = df_coffee[df_coffee['ItemNo'] == selected_item_no]['Price'].values[0]
                            tax_cat = df_coffee[df_coffee['ItemNo'] == selected_item_no]['TaxCategory'].values[0]
                            idx = len(st.session_state.order_menu)
                            st.session_state.order_menu[idx] = [item_name, quantity, price]
                            st.session_state.tax_lis[item_name] = tax_cat
                            st.session_state.stock_rec[item_name] -= quantity
                            update_stock_rec(connection, st.session_state.stock_rec)
                            st.success(f"Added {quantity} x {item_name}!")
                            st.rerun()
                            
                        else :
                           st.error("Not selected. Try Again!")
                    
                    
        else:
            st.warning("No coffee items available.")

    with tab2:  # Tea
        st.subheader("🫖 Tea Menu")
        df_tea = fetch_tea_df(connection)
        if not df_tea.empty:
            st.dataframe(df_tea[['ItemNo', 'Name', 'Price']])
            with st.form("tea_order"):
                item_options = df_tea.set_index('ItemNo')['Name'].to_dict()
                selected_item_no = st.selectbox("Choose Item", options=list(item_options.keys()), format_func=lambda x: f"{x}: {item_options[x]}")
                item_name = item_options[selected_item_no]
                max_stock = st.session_state.stock_rec.get(item_name, 0)
                quantity = st.number_input(f"Quantity (Max: {max_stock})", min_value=0, max_value=max_stock, value=0)
                submitted = st.form_submit_button("Add to Order")
                if submitted and quantity > 0:
                    price = df_tea[df_tea['ItemNo'] == selected_item_no]['Price'].values[0]
                    tax_cat = df_tea[df_tea['ItemNo'] == selected_item_no]['TaxCategory'].values[0]
                    idx = len(st.session_state.order_menu)
                    st.session_state.order_menu[idx] = [item_name, quantity, price]
                    st.session_state.tax_lis[item_name] = tax_cat
                    st.session_state.stock_rec[item_name] -= quantity
                    update_stock_rec(connection, st.session_state.stock_rec)
                    st.success(f"Added {quantity} x {item_name}!")
                    st.rerun()
        else:
            st.warning("No tea items available.")

    with tab3:  # Chat
        st.subheader("🍗🥕 Chat Menu")
        category = st.selectbox("Category", ["Both", "VEG", "NV"])
        df_chat = fetch_chat_df(connection, category)
        if not df_chat.empty:
            st.dataframe(df_chat[['ItemNo', 'Name', 'Price']])
            with st.form("chat_order"):
                item_options = df_chat.set_index('ItemNo')['Name'].to_dict()
                selected_item_no = st.selectbox("Choose Item", options=list(item_options.keys()), format_func=lambda x: f"{x}: {item_options[x]}")
                item_name = item_options[selected_item_no]
                max_stock = st.session_state.stock_rec.get(item_name, 0)
                quantity = st.number_input(f"Quantity (Max: {max_stock})", min_value=0, max_value=max_stock, value=0)
                submitted = st.form_submit_button("Add to Order")
                if submitted and quantity > 0:
                    price = df_chat[df_chat['ItemNo'] == selected_item_no]['Price'].values[0]
                    tax_cat = df_chat[df_chat['ItemNo'] == selected_item_no]['TaxCategory'].values[0]
                    idx = len(st.session_state.order_menu)
                    st.session_state.order_menu[idx] = [item_name, quantity, price]
                    st.session_state.tax_lis[item_name] = tax_cat
                    st.session_state.stock_rec[item_name] -= quantity
                    update_stock_rec(connection, st.session_state.stock_rec)
                    st.success(f"Added {quantity} x {item_name}!")
                    st.rerun()
        else:
            st.warning(f"No chat items available for {category}.")

    with tab4:  # Special
        st.subheader("🥂 Special Menu")
        df_spl = fetch_spl_df(connection)
        if not df_spl.empty:
            st.dataframe(df_spl[['ItemNo', 'Name', 'Price']])
            with st.form("spl_order"):
                item_options = df_spl.set_index('ItemNo')['Name'].to_dict()
                selected_item_no = st.selectbox("Choose Item", options=list(item_options.keys()), format_func=lambda x: f"{x}: {item_options[x]}")
                item_name = item_options[selected_item_no]
                max_stock = st.session_state.stock_rec.get(item_name, 0)
                quantity = st.number_input(f"Quantity (Max: {max_stock})", min_value=0, max_value=max_stock, value=0)
                submitted = st.form_submit_button("Add to Order")
                if submitted and quantity > 0:
                    price = df_spl[df_spl['ItemNo'] == selected_item_no]['Price'].values[0]
                    tax_cat = df_spl[df_spl['ItemNo'] == selected_item_no]['TaxCategory'].values[0]
                    idx = len(st.session_state.order_menu)
                    st.session_state.order_menu[idx] = [item_name, quantity, price]
                    st.session_state.tax_lis[item_name] = tax_cat
                    st.session_state.stock_rec[item_name] -= quantity
                    update_stock_rec(connection, st.session_state.stock_rec)
                    st.success(f"Added {quantity} x {item_name}!")
                    st.rerun()
        else:
            st.warning("Special menu unavailable (only 5-7 PM).")

    with tab_cart:
        st.subheader("🛍️ Your Cart")
        if st.session_state.order_menu:
            order_df = pd.DataFrame.from_dict(st.session_state.order_menu, orient='index', columns=['Item', 'Qty', 'Unit Price'])
            order_df['Total'] = order_df['Qty'].astype(int) * order_df['Unit Price']
            st.dataframe(order_df)
            col1, col2 = st.columns(2)
            with col1:
                cancel_idx = st.selectbox("Cancel Item #", options=list(st.session_state.order_menu.keys()))
            with col2:
                cancel_qty = st.number_input("Cancel Qty (0 for full)", min_value=0, max_value=order_df.loc[cancel_idx, 'Qty'])
            if st.button("Cancel"):
                item_name = order_df.loc[cancel_idx, 'Item']
                if cancel_qty == 0:
                    cancel_qty = order_df.loc[cancel_idx, 'Qty']
                st.session_state.stock_rec[item_name] += cancel_qty
                if cancel_qty == order_df.loc[cancel_idx, 'Qty']:
                    del st.session_state.order_menu[cancel_idx]
                else:
                    st.session_state.order_menu[cancel_idx][1] -= cancel_qty
                update_stock_rec(connection, st.session_state.stock_rec)
                st.success(f"Cancelled {cancel_qty} x {item_name}!")
                st.rerun()
            if st.button("Clear Cart"):
                for idx, row in order_df.iterrows():
                    st.session_state.stock_rec[row['Item']] += row['Qty']
                update_stock_rec(connection, st.session_state.stock_rec)
                st.session_state.order_menu = {}
                st.session_state.tax_lis = {}
                st.success("Cart cleared!")
                st.rerun()
        else:
            st.info("Cart is empty.")

    with tab_bill:
        st.subheader("💰 Generate Bill")
        if st.session_state.order_menu:
            order_df = pd.DataFrame.from_dict(st.session_state.order_menu, orient='index', columns=['Item', 'Qty', 'Unit Price'])
            order_df = order_df.groupby(['Item', 'Unit Price'])['Qty'].sum().reset_index()
            order_df['Total'] = order_df['Qty'].astype(int) * order_df['Unit Price']
            #order_df['Total'] = grouped_df['Qty'].astype(int) * order_df['Unit Price']
            subtotal = order_df['Total'].sum()
            tax_lis = st.session_state.tax_lis
            tax_amt = 0.0
            tax_set = set()
            for _, row in order_df.iterrows():
                item = row['Item']
                tax_cat = tax_lis.get(item, 'Standard')
                tax_rate = st.session_state.tax_data.get(tax_cat, 0.0)
                tax_set.add(tax_rate)
                tax_amt += row['Total'] * tax_rate
            gst = max(tax_set) if tax_set else 0.0
            gst *= 100
            cgst = tax_amt / 2
            sgst = cgst
            total_bill = subtotal + tax_amt

            st.write("**💳 Bill Statement**")
            ist = pytz.timezone("Asia/Kolkata")
            current_time = datetime.now(ist).strftime("%Y-%m-%d %I:%M %p")
            st.write(f"**Date:** {current_time}")
            st.dataframe(order_df[['Item', 'Qty', 'Total']])
            col1, col2, col3, col4, col5 = st.columns(5)
            col1.metric("Subtotal", f"Rs.{subtotal:.2f}")
            col2.metric("Tax Amount", f"Rs.{tax_amt:.2f}")
            col3.metric("CGST", f"Rs.{cgst:.2f}")
            col4.metric("SGST", f"Rs.{sgst:.2f}")
            col5.metric("Max Apllied GST", f"{gst}%")
            st.metric("**Total Bill**", f"Rs.{total_bill:.2f}")
            fig_pie, ax = plt.subplots()
            order_df.plot(kind='pie', y='Total', labels=order_df['Item'], ax=ax, autopct='%1.1f%%')
            ax.set_title('Bill Breakdown')
            st.pyplot(fig_pie)
            if st.button("Confirm & Insert Sales to DB"):
                tmp_lis = order_df[['Item', 'Qty', 'Total']].values.tolist()
                insert_db_data(connection, tmp_lis)
                st.session_state.order_menu = {}
                st.session_state.tax_lis = {}
                st.success("Sales inserted! Cart cleared.")
                st.rerun()
        else:
            st.warning("No items in cart.")

# --- Corporate Portal ---
elif portal == "Corporate (Admin)":
    user_file = "./Files/user_list.txt"
    if os.path.exists(user_file):
        with open(user_file, "r") as f:
            allowed = set(line.strip() for line in f)
    else:
        allowed = set()  # Or default users
    username = st.sidebar.text_input("Enter Username for Admin", type="password")
    st.sidebar.button("Ok")
    if username not in allowed:
        st.warning("Invalid user - Corporate access denied!")
        st.stop()
    st.sidebar.success(f"Welcome, Admin User!")
    st.header("⚙️ Corporate Portal: Admin Dashboard")
    tab_admin1, tab_admin2, tab_admin3,tab_admin4 = st.tabs(["Maintenance", "Graphs & Reports", "Dynamic Reports", "Bulk Orders"])

    with tab_admin1:
        st.subheader("1. View Current Stock")
        if st.button("Refresh & Show Stock"):
            st.session_state.stock_rec = get_stock_data(connection)
            df_stock = pd.DataFrame(list(st.session_state.stock_rec.items()), columns=['Item', 'Available Stock'])
            st.dataframe(df_stock)

        st.subheader("2. Load Shortage Stocks")
        if st.button("Get Shortage Stock"):
            st.session_state.stock_rec = get_shortage_stock_data(connection)
            df_stock = pd.DataFrame(list(st.session_state.stock_rec.items()), columns=['Item', 'Available Stock'])
            st.dataframe(df_stock)
            
        if st.button("Load Stock"):
            load_shortage_stock_data(connection)
            
        st.subheader("3. Item Addition/Deletion")
        category = st.selectbox("Category", ["Coffee", "Tea", "Chat", "Spl"])
        action = st.selectbox("Action", ["Add", "Delete"])
        with st.form("item_add_del"):
            if action != 'Delete' :
                item_name = st.text_input("Item Name")
            else : 
                match category :
                    case 'Coffee':
                        df_items = fetch_coffee_df(connection)
                    case 'Tea':
                        df_items = fetch_tea_df(connection)
                    case 'Chat':
                        category = 'Both'
                        df_items = fetch_chat_df(connection, category)
                    case 'Spl':
                        df_items = fetch_snack_df(connection)
                item_options = df_items.set_index('ItemNo')['Name'].to_dict()
                item_no = st.selectbox("Select Item", options=list(item_options.keys()), format_func=lambda x: f"{x}: {item_options[x]}")
                item_name = item_options[item_no]
            if action != 'Delete' :
                price = st.number_input("Price (for Add)", min_value=0.0, value=0.0)
            if action != 'Delete' :
                if category == "Chat"  :
                    item_category = st.text_input("Enter VEG / NV")
            if action != 'Delete' :
                tax_slab = st.text_input("Tax Tier (TIER2/3)")
            submitted = st.form_submit_button(f"{action} Item")
            if submitted:
                cursor = connection.cursor()
                if action == "Add":
                    if category == "Coffee":
                        ins_stmt = "insert into coffee_menu_tbl(coffee_name, price, tax_category) values (:1, :2, :3)"
                    elif category == "Tea":
                        ins_stmt = "insert into tea_menu_tbl(tea_name, price, tax_category) values (:1, :2, :3)"
                    elif category == "Chat":
                        ins_stmt = "insert into chat_menu_tbl(chat_name, price, tax_category, category) values (:1, :2, :3, :4)"
                    else:
                        ins_stmt = "insert into special_snacks_tbl(item_name, price, tax_category) values (:1, :2, :3)"
                    if category == "Chat" :
                        cursor.execute(ins_stmt, [item_name, price, item_category, tax_slab])
                    else :
                        cursor.execute(ins_stmt, [item_name, price, tax_slab])
                else:  # Delete
                    cursor = connection.cursor()
                    #del_item_name = st.text_input("del_Item Name")
                    if category == "Coffee":
                        del_stmt = "update coffee_menu_tbl set delete_flag='Y' where coffee_name = :1"
                    elif category == "Tea":
                        del_stmt = "update tea_menu_tbl set delete_flag='Y' where tea_name = :1"
                    elif category == "Chat":
                        del_stmt = "update chat_menu_tbl set delete_flag='Y' where chat_name = :1"
                    else:
                        del_stmt = "update special_snacks_tbl set delete_flag='Y' where item_name = :1"
                    cursor.execute(del_stmt, [item_name])
                connection.commit()
                cursor.close()
                st.success(f"{action}ed {item_name} in {category}!")
                st.rerun()

        st.subheader("4. Update Item Prices")
        category_price = st.selectbox("Category for Price Update", ["Coffee", "Tea", "Chat", "Spl"], key="price_cat")
        with st.form("price_update"):
            if category_price == "Coffee":
                df_items = fetch_coffee_df(connection)
            elif category_price == "Tea":
                df_items = fetch_tea_df(connection)
            elif category_price == "Chat":
                df_items = fetch_chat_df(connection)
            else:
                df_items = fetch_snack_df(connection)
            if not df_items.empty:
                item_options = df_items.set_index('ItemNo')['Name'].to_dict()
                item_no = st.selectbox("Select Item", options=list(item_options.keys()), format_func=lambda x: f"{x}: {item_options[x]}")
                new_price = st.number_input("New Price", min_value=0.0, value=df_items[df_items['ItemNo'] == item_no]['Price'].values[0])
                submitted = st.form_submit_button("Update Price")
                if submitted:
                    cursor = connection.cursor()
                    if category_price == "Coffee":
                        upd_stmt = "update coffee_menu_tbl set price = :1 where coffee_name = :2"
                    elif category_price == "Tea":
                        upd_stmt = "update tea_menu_tbl set price = :1 where tea_name = :2"
                    elif category_price == "Chat":
                        upd_stmt = "update chat_menu_tbl set price = :1 where chat_name = :2"
                    else:
                        upd_stmt = "update special_snacks_tbl set price = :1 where item_name = :2"
                    cursor.execute(upd_stmt, [new_price, item_options[item_no]])
                    connection.commit()
                    cursor.close()
                    st.success(f"Updated price for {item_options[item_no]} to ${new_price:.2f}!")
                    st.rerun()
            else:
                st.warning(f"No items in {category_price}.")

        st.subheader("5. Show Tax Category")
        if st.button("Get Tax Slabs"):
            st.session_state.tax_rec = load_tax_data(connection)
            df_tax = pd.DataFrame(list(st.session_state.tax_rec.items()), columns=['Tax Slab', 'Tax Amt'])
            st.dataframe(df_tax)
            
        st.subheader("6. Update Tax Amount")
        st.session_state.tax_rec = load_tax_data(connection)
        df_tax = pd.DataFrame(list(st.session_state.tax_rec.items()), columns=['Tax Slab', 'Tax Amt'])
        tax_category = st.selectbox("Select Tax Category", options=df_tax['Tax Slab'].unique())
        tax_amount = st.text_input("Tax Amount", value=0)
        if st.button("Update Tax Amount"):
            update_tax_amt(connection,tax_category,tax_amount)
            st.success("Tax Amount updated successfully!")
            st.rerun()
            
    with tab_admin2:
        st.subheader("Sales Graphs")
        period = st.selectbox("Period", ["Daily", "Weekly", "Monthly"])
        category = st.selectbox("Category", ["Coffee", "Tea", "Chat", "Spl", "Overall"])
        if st.button("Generate Chart"):
            if category == "Coffee":
                fig = coffee_sales_fig(connection, period)
                if fig:
                    st.pyplot(fig)
                else:
                    st.info("No coffee sales data.")
            elif category == "Tea":
                fig = tea_sales_fig(connection, period)
                if fig:
                    st.pyplot(fig)
                else:
                    st.info("No tea sales data.")
            elif category == "Chat":
                fig = chat_sales_fig(connection, period)
                if fig:
                    st.pyplot(fig)
                else:
                    st.info("No chat sales data.")
            elif category == "Spl":
                fig = Spl_sales_fig(connection, period)
                if fig:
                    st.pyplot(fig)
                else:
                    st.info("No snacks sales data.")
            else:
                fig = overall_sales_fig(connection, period)
                if fig:
                    st.pyplot(fig)
                else:
                    st.info("No sales data.")
                #st.warning(f"Graph for {category} not implemented yet. Add similar to coffee_sales_fig.")
        st.subheader("Excel Reports")
        st.info("Add your excel_data_prep.py functions here with st.download_button (e.g., Total_Coffee_Sales).")

    with tab_admin3:
        st.subheader("Dynamic Reports")
        tabG, tabW, tabM, tabA  = st.tabs(["Generic Report", "WeeklyReport", "Monthly Report", "Report as Your Choice"])
        with tabG:
            st.title("User Option")
            user_choice = st.radio(
                "Do you need to write excel into local dir? (Y/N)", 
                 options=["Y", "N"],
                index=None,  # This makes no option selected by default
                key="excel_radio"  # Optional: Unique key for state management
                )
            report_choice = st.radio(
                "Select Item for report generation", 
                 options=["Coffee", "Tea", "Chat", "Snacks", "All"],
                index=None,  # This makes no option selected by default
                key="item_radio"  # Optional: Unique key for state management
                )
            date_start = st.date_input("Start Date")
            date_end = st.date_input("End Date")
            query = ""
            if st.button("Generate Dynamic Report"):
                if report_choice == "All" :
                    rep_name="Overall"
                    fp = open("./Files/generic_sql.txt","r")
                    query = fp.read()
                    fp.close()
                elif report_choice == "Coffee" :
                    rep_name="Coffee"
                    fp = open("./Files/generic_coffee_sql.txt","r")
                    query = fp.read()
                    fp.close()
                elif report_choice == "Tea" :
                    rep_name="Tea"
                    fp = open("./Files/generic_Tea_sql.txt","r")
                    query = fp.read()
                    fp.close()
                elif report_choice == "Chat" :
                    rep_name="Chat"
                    fp = open("./Files/generic_chat_sql.txt","r")
                    query = fp.read()
                    fp.close()
                elif report_choice == "Snacks" :
                    rep_name="Snacks"
                    fp = open("./Files/generic_snacks_sql.txt","r")
                    query = fp.read()
                    fp.close()
                #query update required
                #st.write("before exec")
                cursor = connection.cursor()
                cursor.execute(query, {'date_start' : date_start ,'date_end' : date_end})
                rows = cursor.fetchall()
                columns = [desc[0] for desc in cursor.description]
                df_sales = pd.DataFrame(rows, columns=columns)
                st.dataframe(df_sales)
                if not df_sales.empty :
                
                    fig_pie, ax = plt.subplots()
                    #df_sales.groupby('item_name')['sales_amt'].sum().plot(kind='pie', ax=ax, autopct='%1.1f%%')
                    sales_by_item = df_sales.groupby('ITEM_NAME')['SALES_AMT'].sum()
                    sales_by_item.plot(kind='pie', ax=ax, autopct='%1.1f%%', labels=sales_by_item.index)
                    ax.set_title('Sales Breakdown by Item')
                    st.pyplot(fig_pie)
                
                    if user_choice == 'N' :
                        import io  # Add at top if missing

                        # ... (inside if not df_sales.empty:, after st.dataframe and pie chart)

                        # Generate Excel in memory
                        output = io.BytesIO()
                        with pd.ExcelWriter(output, engine='openpyxl') as writer:
                            df_sales.to_excel(writer, index=False, sheet_name='Sales Data')  # Optional: Add formatting here if needed
                            output.seek(0)  # Reset to start of file


                            st.download_button(
                                "Download Dynamic Excel", 
                                output.getvalue(), 
                                file_name='in_mem_dynamic_report.xlsx',
                                mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'  # Ensures proper Excel handling in browser
                            )

                            # Optional: Confirm generation
                            st.success("Excel ready for download (generated in memory—no file written to disk).")
                    else :
                        #file_name = f"./reports/dynamic_report_{rep_name}.xlsx"
                        file_name = os.path.join(REPORTS_DIR, f"dynamic_{item_option}_sales_report.xlsx")
                        df_sales.to_excel(file_name, index=False)
                        with open(file_name, 'rb') as f:
                            #rep_file_name = f"./reports/dynamic_sales_report_{date_start}_{date_end}.xlsx"
                            st.download_button("Download Dynamic Excel", f.read(), file_name=file_name)
                else:
                    st.info("No sales data for selected range.")
                    

        with tabW:
            if st.button("Generate Xcel Report"):
                df_sales =  pull_week_data(connection)
                st.dataframe(df_sales)
                #file_name = f"./reports/dynamic_Weekly_report.xlsx"
                file_name = os.path.join(REPORTS_DIR,"dynamic_Weekly_report.xlsx")
                df_sales.to_excel(file_name, index=False)
                with open(file_name, 'rb') as f:
                     st.download_button("Download Dynamic Excel", f.read(), file_name=file_name)
                
            
            if st.button("Show Visuals"):
                item_lis = Week_sale_items(connection)
                days = sorted(set(item[0] for item in item_lis))  
                item_types = sorted(set(item[1] for item in item_lis))
                num_days = len(days)
                


                sale_amt = np.zeros((len(days), len(item_types)))
                for day_idx, day in enumerate(days):
                    for item_idx, items in enumerate(item_types):
                        for item in item_lis:
                            
                            if item[0] == day and item[1] == items:
                                sale_amt[day_idx, item_idx] = item[2]
                    
                    
                colors = plt.cm.tab10(np.linspace(0, 1, num_days))
                
    
                bar_width = 0.8/num_days
                x = np.arange(len(item_types))
                fig, ax = plt.subplots()

                for day_idx, day in enumerate(days):
                    offset = (day_idx - (num_days - 1) / 2) * bar_width
                    ax.bar(x + offset, sale_amt[day_idx], bar_width, label=day, color=colors[day_idx])

    
    
                ax.set_xlabel('Item Type')
                ax.set_ylabel('Sales Amount')
                ax.set_title('Item Sales by Day')
                ax.set_xticks(x)
                ax.set_xticklabels(item_types, rotation=45, ha='right')
                ax.legend()
                ax.grid(True, axis='y', linestyle='--', alpha=0.7)

                
                st.pyplot(fig)

        with tabM:
            item_lis = []
            if st.button("Generate Monthly Xcel Report"):
                df_sales =  pull_month_data(connection)
                st.dataframe(df_sales)
                file_name = f"./reports/dynamic_Monthly_report.xlsx"
                df_sales.to_excel(file_name, index=False)
                with open(file_name, 'rb') as f:
                     st.download_button("Download Dynamic Excel", f.read(), file_name=file_name)

            option = st.selectbox(
                label="Choose an option",
                options=["Item & Qty", "Item & Sales"]
                )

            if st.button("Show Visual"):
                
                if option == "Item & Qty" :
                    
                    item_lis = get_month_data(connection)
                    weeks = sorted(set(item[0] for item in item_lis))  
                    item_types = sorted(set(item[1] for item in item_lis))
                    num_weeks = len(weeks)
                


                    sale_amt = np.zeros((len(weeks), len(item_types)))
                    for week_idx, week in enumerate(weeks):
                        for item_idx, items in enumerate(item_types):
                            for item in item_lis:
                            
                                if item[0] == week and item[1] == items:
                                    sale_amt[week_idx, item_idx] = item[3]
                    
                    
                    colors = plt.cm.tab10(np.linspace(0, 1, num_weeks))
                
    
                    bar_width = 0.8/num_weeks
                    x = np.arange(len(item_types))
                    fig, ax = plt.subplots()

                    for week_idx, week in enumerate(weeks):
                        offset = (week_idx - (num_weeks - 1) / 2) * bar_width
                        ax.bar(x + offset, sale_amt[week_idx], bar_width, label=week, color=colors[week_idx])

    
    
                    ax.set_xlabel('Item Type')
                    ax.set_ylabel('Sales Amount')
                    ax.set_title('Item Sales by Week')
                    ax.set_xticks(x)
                    ax.set_xticklabels(item_types, rotation=45, ha='right')
                    ax.legend()
                    ax.grid(True, axis='y', linestyle='--', alpha=0.7)

                
                    st.pyplot(fig)

                else :
                    
                    item_lis = get_month_data(connection)
                    weeks = sorted(set(item[0] for item in item_lis))  
                    item_types = sorted(set(item[1] for item in item_lis))
                    num_weeks = len(weeks)
                


                    sale_amt = np.zeros((len(weeks), len(item_types)))
                    for week_idx, week in enumerate(weeks):
                        for item_idx, items in enumerate(item_types):
                            for item in item_lis:
                            
                                if item[0] == week and item[1] == items:
                                    sale_amt[week_idx, item_idx] = item[4]
                    
                    
                    colors = plt.cm.tab10(np.linspace(0, 1, num_weeks))
                
    
                    bar_width = 0.8/num_weeks
                    x = np.arange(len(item_types))
                    fig, ax = plt.subplots()

                    for week_idx, week in enumerate(weeks):
                        offset = (week_idx - (num_weeks - 1) / 2) * bar_width
                        ax.bar(x + offset, sale_amt[week_idx], bar_width, label=week, color=colors[week_idx])

    
    
                    ax.set_xlabel('Item Type')
                    ax.set_ylabel('Sales Quantity')
                    ax.set_title('Item Sales by Week')
                    ax.set_xticks(x)
                    ax.set_xticklabels(item_types, rotation=45, ha='right')
                    ax.legend()
                    ax.grid(True, axis='y', linestyle='--', alpha=0.7)

                
                    st.pyplot(fig)

        with tabA:
            st.header("Welcome to Dynamic Report Generation")
            
            column_map = {
                1 : "trim(Value_date)",
                2 : "Item_name",
                3 : "Quantity",
                4 : "Sales_Amt"
            }
            field_name_map = {
                1 : "Sales Date",
                2 : "Item Name",
                3 : "Quantity",
                4 : "Sales_Amt"
            }
            item_map = {
                1 : "Coffee",
                2 : "Tea",
                3 : "Chat",
                4 : "Snacks"
            }

            table_map = {
                "Coffee" : "Coffee_menu_tbl",
                "Tea" : "Tea_menu_tbl",
                "Chat" : "Chat_menu_tbl",
                "Snacks" : "SPECIAL_SNACKS_TBL"
            }
    
            field_map = {
                "Coffee_menu_tbl" : "Coffee_name",
                "Tea_menu_tbl" : "Tea_name",
                "Chat_menu_tbl" : "Chat_name",
                "SPECIAL_SNACKS_TBL" : "item_name"
            }
    
            period_map = {
                1 : "Daily",
                2 : "Weekly",
                3 : "Monthly",
                4 : "Customized Date"
            }

            item_option = st.selectbox(
                label="Choose the Item",
                options=["Coffee", "Tea", "Chat", "Snacks"]
                )

            date_start = st.date_input("From Date")
            date_end = st.date_input("To Date")
            if "reset_widgets" not in st.session_state:
                st.session_state.reset_widgets = False

            # Define a reset callback
            def reset_state():
                st.session_state.reset_widgets = True

            # Initialize the dictionaries before using them
            selected_fields = {}
            aggregate_fields = {}
            order_fields = {}
            agg_fields = []
            query_fields = []
            allowed_fields = set()
            allowed_fields = ("Quantity", "Sales_Amt")
            agg_options = []
            order_option = []
            order_flds = []
            ord_fields = {}
            column_names = []

            

            

            # Section for choosing data fields
            st.write("Choose the data Fields")
            
            field_options = ["Value_Date", "Item_Name", "Quantity", "Sales_Amt"]

            for column in field_options:
                if f"selected_{column}" not in st.session_state:
                    st.session_state[f"selected_{column}"] = False
                if f"aggregate_{column}" not in st.session_state:
                    st.session_state[f"aggregate_{column}"] = False
                if f"order_{column}" not in st.session_state:
                    st.session_state[f"order_{column}"] = False

               
            for column in field_options:
                selected_fields[column] = st.checkbox(column,key=f"selected_{column}")

            for column in field_options:
                if selected_fields[column]:
                    query_fields.append(column)
                    if column in allowed_fields :
                        agg_options.append(column)

            # Section for choosing aggregate fields
            st.write("Choose Aggregate Fields")
            #agg_options = ["Quantity", "Sales Amt"]

            for field in agg_options:
                aggregate_fields[field] = st.checkbox(field, key=f"aggregate_{field}")

            
            for field in agg_options:
                if aggregate_fields[field] :
                    agg_fields.append(field)

            qry_str = "select "      
            for i in range(len(query_fields)) :
                if i == 0 :
                    qry_str += f"{query_fields[i]}"
                else :
                    if query_fields[i] in agg_fields :
                        qry_str += f",sum({query_fields[i]})"
                    else :
                        qry_str += f",{query_fields[i]}"

            for i in range(len(query_fields)) :
                if query_fields[i] in agg_fields :
                    column_names.append(f"Tot.{query_fields[i]}")
                else :
                    column_names.append(query_fields[i])
                
                
            qry_str += " from sales_dtl_tbl "
            if item_option == "Coffee" :
                qry_str += " where item_name in (select coffee_name from coffee_menu_tbl )"
            elif item_option == "Tea" :
                qry_str += " where item_name in (select tea_name from tea_menu_tbl )"
            elif item_option == "Chat" :
                qry_str += " where item_name in (select chat_name from chat_menu_tbl )"
            else :
                qry_str += " where item_name in (select item_name from SPECIAL_SNACKS_TBL )"

            qry_str += f" and value_date between to_date('{date_start}','YYYY-MM-DD') and to_date('{date_end}','YYYY-MM-DD')"
            if len(agg_fields) != 0 :
                qry_str += " group by "
                for i in range(len(query_fields)) :
                    if query_fields[i] not in agg_fields :
                        if i == 0 :
                            qry_str += f"{query_fields[i]}"
                        else :
                            qry_str += f",{query_fields[i]}"

            st.write("Choose Order by")
            for i in range(len(query_fields)) :
                if query_fields[i] not in agg_fields :
                    order_option.append(query_fields[i])

            for field in order_option:
                order_fields[field] = st.checkbox(field, key=f"order_{field}")

            for field in order_option:
                if order_fields[field] :
                    order_flds.append(order_fields[field])
            
            
            for i in range(len(order_flds)) :
                if i == 0 :
                    qry_str += f" order by {order_option[i]}"
                else :
                    qry_str += f",{order_option[i]}"
                    
            st.write("Choose asc/desc")
            if st.session_state.reset_widgets:
                st.session_state.order_radio = None
                
            order_choice = st.radio(
                "Choose data order", 
                 options=["asc", "desc"],
                index=None,  # This makes no option selected by default
                key="order_radio"  # Optional: Unique key for state management
                )

            if order_choice == "desc" :
                qry_str += f" {order_choice}"
            if order_choice == "asc" :
                qry_str += f" {order_choice}"
                
            #st.write(qry_str)
            #st.write(column_names)
            
            
            if st.button(f"Generate {item_option} Sales Xcel Report"):
                sales_rec = execute_qry(connection, qry_str,column_names)
                st.dataframe(sales_rec)
                
                file_name = f"./reports/dynamic_{item_option}_sales_report.xlsx"
                sales_rec.to_excel(file_name, index=False)
                with open(file_name, 'rb') as f:
                     st.download_button("Download Dynamic Excel", f.read(), file_name=file_name)

        with tab_admin4:
            st.subheader("Process Bulk Orders")
            order_list = {}
            tot_price = 0.0
            tot_tax = 0.0
            if 'bulk_lis' not in st.session_state:
                st.session_state.bulk_lis = []
            #bulk_lis = []
            tmp_lis = []
            log_str = ""
            
            
            #log_path = "./Bulk_Import/bulk_order.log"
            #file_path = "./Bulk_Import/loaded_file.txt"

            #log_path = os.path.join(BASE_DIR, "Bulk_Import", "bulk_order.log")
            #file_path = os.path.join(BASE_DIR, "Bulk_Import", "loaded_file.txt")

            log_path = os.path.join(BULK_DIR, "bulk_order.log")
            file_path = os.path.join(BULK_DIR, "loaded_file.txt")
            
            with open(log_path,"w+") as fp :
            
                current_date = date.today()
            
                print(f"Log date: {current_date}\n",file=fp)
                log_str += f"Log date: {current_date}\n"
            
                # Title of the Streamlit app
                st.title("Bulk menu Reader")
                fname = open(file_path,"w")

                # File uploader for Excel files
                uploaded_file = st.file_uploader("Upload the Order File", type=["xlsx", "xls"])
                print(f"Order file: {uploaded_file}\n",file=fp)
                log_str += f"Order file: {uploaded_file}\n"
                if uploaded_file is not None :
                    fname.write(log_str)
                fname.close()
                fname = open(file_path,"r")
                file=""
                pattern = r"name='([^']+)[.]"
                for line in fname.readlines():
                    match =  re.search(pattern,line)
                    if match :
                        file = match.group(1)
                dup_file = check_bulk_header(connection,file)
                
                if dup_file == 1 :
                    st.error("Duplicate file loaded!")
                status = "OPEN"
                load_bulk_header(connection,file, status)
                #check_duplicate(connection,file)
                message = "Loaded"
                insert_log(connection,file,message)
                fname.close()

                if uploaded_file is not None and dup_file == 0 :
                    try:
                        # Read the Excel file using pandas
                        df = pd.read_excel(uploaded_file)
        
                        # Check if required columns exist
                        required_columns = ["Item name", "Quantity"]
                        if all(col in df.columns for col in required_columns):
                            # Select only the required columns
                            df = df[required_columns]
            
                            # Display the data as a table
                            st.write("### Bulk Orders from File")
                            st.dataframe(df)
                            for index, row in df.iterrows():
                                item_name = row["Item name"]
                                #st.write(item_name)
                                valid = validate_item(connection,item_name)
                            
                                if valid == 0 :
                                    print(f"Invalid item- {item_name}\n",file=fp)
                                    log_str += f"Invalid item- {item_name}\n"
                                    message = f"Invalid item- {item_name}\n"
                                    insert_log(connection,file,message)
                                    continue
                            
                                quantity = row["Quantity"]
                            
                                if quantity < 0 or quantity > 100 :
                                    print(f"Invalid quantity - {item_name}\n", file=fp)
                                    log_str += f"Invalid quantity - {item_name}\n"
                                    message = f"Invalid quantity - {item_name}\n"
                                    insert_log(connection,file,message)
                                else :
                                    order_list[item_name] = quantity
                                    print(f"Feteching Item - {item_name}\n", file=fp)
                                    log_str += f"Feteching Item - {item_name}\n"
                                    message = f"Feteching Item - {item_name}\n"
                                    insert_log(connection,file,message)
                                    fp.flush()
                        
                            # Optional: Display some basic statistics
                            st.write("### Summary")
                            st.write(f"Total loaded Items: {len(df)}")
                            st.write(f"Total loaded Quantity: {df['Quantity'].sum()}")
                            #st.write(order_list)
                        
                        else:
                            st.error("The Excel file must contain 'Item name' and 'Quantity' columns.")
            
                    except Exception as e:
                        st.error(f"Error reading the Excel file: {e}")
                else:
                    st.info("Upload the bulk order file to process!")

                if st.button("Process Order") :
                
                    st.write("Processed Orders ###")
                    st.session_state.bulk_lis = []
                    for item, qty in order_list.items() :
                        avail_stock, qty = get_item_stock(connection, item, qty)
                        #st.write("qty=",qty)
                        if qty != 0 :
                            #st.write("inside")
                            price, tax = get_item_price(connection,item,qty)
                            #st.write(f"{item} {qty} {price} {tax}")
                            print(f"processing {item} and quantity : {qty}\n",file=fp)
                            log_str += f"processing {item} and quantity : {qty}\n"
                            message = f"processing {item} and quantity : {qty}\n"
                            insert_log(connection,file,message)
                            tot_price += price
                            tot_tax += tax
                            tmp_lis = [item,qty,price,tax]
                            st.session_state.bulk_lis.append(tmp_lis)
                        else :
                            print(f"{item} {qty} - Rejected due to stock shortage\n",file=fp)
                            log_str += f"{item} {qty} - Rejected due to stock shortage\n"
                            message = f"{item} {qty} - Rejected due to stock shortage\n"
                            insert_log(connection,file,message)
                            fp.flush()
                    df = pd.DataFrame(st.session_state.bulk_lis, columns = ["Item Name","Quantity","Price","Tax"])
                    st.dataframe(df)
                    col1, col2, col3 = st.columns(3)
                    col1.metric("Subtotal", f"Rs.{tot_price:.2f}")
                    col2.metric("Tax Amt", f"Rs.{tot_tax:.2f}")
                    col3.metric("Tot. Bill Amt", f"Rs.{tot_price+tot_tax:.2f}")
                    print(f"Tot. Bill Amt For current order", f"Rs.{tot_price+tot_tax:.2f}",file=fp)
                    log_str += f"Tot. Bill Amt For current order, Rs.{tot_price+tot_tax:.2f}"
                    message = f"Tot. Bill Amt For current order =  Rs.{tot_price+tot_tax:.2f}"
                    insert_log(connection,file,message)
                    fp.close()
                    status = "Processed"
                    update_bulk_header(connection,file,status)
                    insert_db_data(connection, st.session_state.bulk_lis)
                    fig_pie, ax = plt.subplots()
                    #df_sales.groupby('item_name')['sales_amt'].sum().plot(kind='pie', ax=ax, autopct='%1.1f%%')
                    sales_by_item = df.groupby('Item Name')['Quantity'].sum()
                    
                    if len(sales_by_item) > 0 :
                        sales_by_item.plot(kind='pie', ax=ax, autopct='%1.1f%%', labels=sales_by_item.index)
                        ax.set_title('Sales Breakdown by Item')
                        st.pyplot(fig_pie)

                if st.button(f"Generate Bill in Xcel Report"):
                    bill_rec = pd.DataFrame(st.session_state.bulk_lis, columns = ["Item Name","Quantity","Price","Tax"])
                                
                    file_name = f"./reports/Bill_Statement.xlsx"
                    bill_rec.to_excel(file_name, index=False)
                    with open(file_name, 'rb') as f:
                         st.download_button("Download Bill Statement", f.read(), file_name=file_name)
                         
                          

# Footer
st.sidebar.markdown("---")
st.sidebar.info("Dashboard powered by Streamlit + OracleDB")
