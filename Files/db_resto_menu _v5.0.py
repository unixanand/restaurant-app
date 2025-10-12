import oracledb

x = 0
y = 0
idx = 0
index = 0
menu_opt = 0
itmNo = 0
order_length = 0
order_rec_len = 0

allowed_users = set()
del_set = set()
order_menu = {}
tax_lis = {}
tax_data = {}
coffee_menu_list = []
tea_menu_list = []
chat_menu_list = []
spl_menu_list = []
stock_rec = {}

def cls() :
    print("\n" *10)
    
def connect_DB(user, password, dsn):
    
    connection = oracledb.connect(
         user=user,  
         password=password, 
         dsn=dsn
     )
    #print("connection=",connection)
    print("Connected to Oracle Database 23ai Free!")
    return connection

def fetch_coffee_rec(connection):
    # Create a cursor
    cursor = connection.cursor()
    # Execute SELECT query
    #print("Executing SELECT query...")
    sel_qry1 = "SELECT rownum,coffee_name,price, tax_category FROM coffee_menu_tbl a where a.coffee_name in (select b.item_name from STOCK_MAINTENANCE_TXN_TBL b "
    sel_qry2 = "where a.coffee_name=b.item_name and value_date=trim(sysdate)and avail_stock > 0) and delete_flag='N'"
    final_qry = sel_qry1+sel_qry2
    
    cursor.execute(final_qry)
    while True :
        row = cursor.fetchone()
        if row is None :
            break
        tup = tuple(row)
        coffee_menu_list.append(tup)
        
    print("\t\t\t\t  -- Coffe Menu ---") 
    print("\t\t" , "=" *50)
    print("\t\t Item \t\t Coffee Name \t\t Price")
    print("\t\t","-" *50)
    
    for rec in range(len(coffee_menu_list)) :
        print("\t\t ", end = " ")
        tup = tuple(coffee_menu_list[rec])
        #print("len=",len(tup))
        for j in range(len(tup)-1) :
            #print("\t\t ", menu_list[rec][j], end = " ")
            print(f"{coffee_menu_list[rec][j]:<18}", end = " ")
        print()
    print("\t\t ","=" *50)
    
    cursor.close()
    #connection.close()
    #print("Connection closed.")

def get_coffee_order(idx, stock_rec) :

    
    while True :
        found = 0
        opt = input("\t\tChoose your order :").title()
        for i in range(len(coffee_menu_list)) :
            if int(coffee_menu_list[i][0]) == int(opt):
                #print("opted",menu_list[i][1])
                found = 1
                quantity = input("\t\tEnter the quantity : ").title()
                
                if int(quantity) > 0 and stock_rec[coffee_menu_list[i][1]] >= int(quantity) :
                    tmp_lis = []
                    tmp_lis = [coffee_menu_list[i][1],quantity,coffee_menu_list[i][2]]
                    tax_lis[coffee_menu_list[i][1]] = coffee_menu_list[i][3]
                    #tmp_lis.append(tup)
                    order_menu[idx] = tmp_lis
                    #found = 1
                    stock_rec[coffee_menu_list[i][1]] -= int(quantity)
                    break
                else :
                    idx -= 1
                    print("Invalid quantity or out of stock!")
                    
        if (found == 0) :
            print("Invalid option!")

        idx += 1
        inp = input("\n\t Want to continue with Coffee orders ?[y/n]: ").title()
        if inp.lower() != 'y' :
            break
        #idx += 1

    return(idx)
###
def fetch_tea_rec(connection):
    # Create a cursor
    cursor = connection.cursor()
    # Execute SELECT query
    #print("Executing SELECT query...")
    sel_qry1 = "SELECT rownum,tea_name,price, tax_category FROM tea_menu_tbl a where a.tea_name in (select b.item_name from STOCK_MAINTENANCE_TXN_TBL b "
    sel_qry2 = "where a.tea_name=b.item_name and value_date=trim(sysdate)and avail_stock > 0)"
    final_qry = sel_qry1+sel_qry2
    
    cursor.execute(final_qry)
    while True :
        row = cursor.fetchone()
        if row is None :
            break
        tup = tuple(row)
        tea_menu_list.append(tup)
        
    print("\t\t\t\t  -- Tea Menu ---") 
    print("\t\t" , "=" *50)
    print("\t\t Item \t\t Tea Name \t\t Price")
    print("\t\t","-" *50)
    
    for rec in range(len(tea_menu_list)) :
        print("\t\t ", end = " ")
        tup = tuple(tea_menu_list[rec])
        #print("len=",len(tup))
        for j in range(len(tup)-1) :
            #print("\t\t ", menu_list[rec][j], end = " ")
            print(f"{tea_menu_list[rec][j]:<18}", end = " ")
        print()
    print("\t\t ","=" *50)
    
    cursor.close()
    #connection.close()
    #print("Connection closed.")

def get_tea_order(idx, stock_rec) :
    
    while True :
        found = 0
        opt = input("\t\tChoose your order :").title()
        for i in range(len(tea_menu_list)) :
            if int(tea_menu_list[i][0]) == int(opt):
                #print("opted",menu_list[i][1])
                found = 1
                quantity = input("\t\tEnter the quantity : ").title()
                if int(quantity) > 0 and stock_rec[tea_menu_list[i][1]] >= int(quantity) :
                    tmp_lis = []
                    tmp_lis = [tea_menu_list[i][1],quantity,tea_menu_list[i][2]]
                    tax_lis[tea_menu_list[i][1]] = tea_menu_list[i][3]
                    #tmp_lis.append(tup)                               
                    order_menu[idx] = tmp_lis
                    #found = 1
                    stock_rec[tea_menu_list[i][1]] -= int(quantity)
                    break
                else :
                    idx -= 1
                    print("Invalid quantity or out of stock!")
                    
        if (found == 0) :
            print("Invalid option!")
            
        idx += 1
        inp = input("\n\t Want to continue with Tea orders ?[y/n]: ").title()
        if inp.lower() != 'y' :
            break
        #idx += 1

    
    #print("idx E = ", idx)
    return(idx) 

###

def fetch_chat_rec(connection):
    # Create a cursor
    cursor = connection.cursor()
    # Execute SELECT query
    #print("Executing SELECT query...")
    chat_menu_list.clear()
    
    opt = int(input("\t\t Enter your preference :: 1 - Veg / 2 - Non veg / 3 - Both :-> "))
    
    match opt :
        case 1:
            category = "VEG"
            select_rec1 = "SELECT rownum,chat_name,price,tax_category FROM chat_menu_tbl a WHERE category  = :category "
            select_rec2 = "and a.chat_name in (select b.item_name from STOCK_MAINTENANCE_TXN_TBL b "
            select_rec3 = "where a.chat_name = b.item_name and value_date=trim(sysdate) and avail_stock > 0)"
            select_rec = select_rec1+select_rec2+select_rec3
            cursor.execute(select_rec, {"category":category})
        case 2:
            category = "NV"
            select_rec1 = "SELECT rownum,chat_name,price,tax_category FROM chat_menu_tbl a WHERE category  = :category "
            select_rec2 = "and a.chat_name in (select b.item_name from STOCK_MAINTENANCE_TXN_TBL b "
            select_rec3 = "where a.chat_name = b.item_name and value_date=trim(sysdate) and avail_stock > 0)"
            select_rec = select_rec1+select_rec2+select_rec3
            cursor.execute(select_rec, {"category":category})
        case 3:
            select_rec1 = "SELECT rownum,chat_name,price,tax_category FROM chat_menu_tbl a WHERE  "
            select_rec2 = "a.chat_name in (select b.item_name from STOCK_MAINTENANCE_TXN_TBL b "
            select_rec3 = "where a.chat_name = b.item_name and value_date=trim(sysdate) and avail_stock > 0)"
            select_rec = select_rec1+select_rec2+select_rec3
            cursor.execute(select_rec)
            
        case _:
            print("Invalid option!")
            return 0
            
    while True :
        row = cursor.fetchone()
        if row is None :
            break
        tup = tuple(row)
        chat_menu_list.append(tup)
        
    print("\t\t\t\t  -- Chat Menu ---") 
    print("\t\t" , "=" *50)
    print("\t\t Item \t\t Chat Name \t\t Price")
    print("\t\t","-" *50)
    
    for rec in range(len(chat_menu_list)) :
        print("\t\t ", end = " ")
        tup = tuple(chat_menu_list[rec])
        #print("len=",len(tup))
        for j in range(len(tup)-1) :
            #print("\t\t ", menu_list[rec][j], end = " ")
            print(f"{chat_menu_list[rec][j]:<18}", end = " ")
        print()
    print("\t\t ","=" *50)
    
    cursor.close()
    #connection.close()
    #print("Connection closed.")
    return 1

def get_chat_order(idx, stock_rec) :
    
    while True :
        found = 0
        opt = input("\t\tChoose your order :").title()
        for i in range(len(chat_menu_list)) :
            if int(chat_menu_list[i][0]) == int(opt):
                #print("opted",menu_list[i][1])
                found = 1
                quantity = input("\t\tEnter the quantity : ").title()
                if int(quantity) > 0 and stock_rec[chat_menu_list[i][1]] >= int(quantity):
                    tmp_lis = []
                    tmp_lis = [chat_menu_list[i][1],quantity,chat_menu_list[i][2]]
                    tax_lis[chat_menu_list[i][1]] = chat_menu_list[i][3]
                    #tmp_lis.append(tup)                
                    order_menu[idx] = tmp_lis
                    #found = 1
                    stock_rec[chat_menu_list[i][1]] -= int(quantity)
                    break
                else :
                    idx -= 1
                    print("Invalid quantity or out of stock!")
                    
        if (found == 0) :
            print("Invalid option!")

        idx += 1
        inp = input("\n\t Want to continue with Chat orders ?[y/n]: ").title()
        if inp.lower() != 'y' :
            break
        #idx += 1

    return(idx)

        
###
##

def fetch_splMenu_rec(connection) :
    cursor = connection.cursor()

    sel_qry = "select rownum, item_name, price, tax_category from special_snacks_tbl "
    cursor.execute(sel_qry)
    while True :
        row = cursor.fetchone()
        if row is None :
            break
        tup = tuple(row)
        spl_menu_list.append(tup)
    cls()  
    print("\t\t\t\t  -- Spl Menu ---") 
    print("\t\t" , "=" *50)
    print("\t\t Item \t\t\t Item Name \t   Price")
    print("\t\t","-" *50)
    
    for rec in range(len(spl_menu_list)) :
        print("\t\t ", end = " ")
        tup = tuple(spl_menu_list[rec])
        #print("len=",len(tup))
        for j in range(len(tup)-1) :
            #print("\t\t ", menu_list[rec][j], end = " ")
            print(f"{spl_menu_list[rec][j]:<20}", end = " ")
        print()
    print("\t\t ","=" *50)
    
    cursor.close()
    
##

def get_splMenu_order(idx, stock_rec) :
    
    while True :
        found = 0
        opt = input("\t\tChoose your order :").title()
        for i in range(len(spl_menu_list)) :
            if int(spl_menu_list[i][0]) == int(opt):
                #print("opted",menu_list[i][1])
                found = 1
                quantity = input("\t\tEnter the quantity : ").title()
                if int(quantity) > 0 and stock_rec[spl_menu_list[i][1]] >= int(quantity):
                    tmp_lis = []
                    tmp_lis = [spl_menu_list[i][1],quantity,spl_menu_list[i][2]]
                    tax_lis[spl_menu_list[i][1]] = spl_menu_list[i][3]
                    #tmp_lis.append(tup)                
                    order_menu[idx] = tmp_lis
                    #found = 1
                    stock_rec[spl_menu_list[i][1]] -= int(quantity)
                    break
                else :
                    idx -= 1
                    print("Invalid quantity or out of stock!")
                    
        if (found == 0) :
            print("Invalid option!")

        idx += 1
        inp = input("\n\t Want to continue with spl orders ?[y/n]: ").title()
        if inp.lower() != 'y' :
            break
        #idx += 1

    return(idx)
    

##

def re_arrane_order_menu(order_menu, del_set, order_length) :
    tmp_menu_order = {}
    t = 0
    for i in range(len(order_menu)+1) :
        if i in del_set :
            continue
        tmp_menu_order[t] = order_menu[i]
        t += 1
    
    for i in range(len(tmp_menu_order)) :
        order_menu[i] = tmp_menu_order[i]

    lgth = len(order_menu)
    if  len(order_menu) > len(tmp_menu_order) :
        del order_menu[lgth -1]
    
    
##
def list_order(order_length, order_rec_len, del_set) :
    cls()
    tmp_menu_order = {}
    itm_no = 1
    t = 0
    if len(order_menu) == 0 :
        print("\t\t Your cart is empty!")
        return
    print("\n\n\t\t\t\t\t   -- Your orders --")
    print("\t\t", "=" *90)
    print("\t\t Item# \t\t Item \t\t\t    quantity \t\t      Price [per unit]")
    print("\t\t", "-" *90)

        
    for i in range(order_length) :
        #tup = tuple(order_menu[i])
        #tmp = list(order_rec_len)
        if i in del_set :
            continue
        print("\t\t",itm_no, end = " ")
        for j in range(order_rec_len) :
            print("\t\t",f"{order_menu[i][j]:<20}", end = " ")
        itm_no += 1
        print()
    print()       
    print("\t\t", "=" *90)
    

def generate_bill(connection,order_length, order_rec_len, stock_rec) :
    from datetime import datetime
    import pytz
    
    tax_set = set()
    tmp_lis = []
    matched = 0
    old_quantity = 0
    new_quantity = 0
    price = 0.0
    gst = 0.0
    cgst = 0.0
    sgst = 0.0
    total_bill = 0.0
    bill_amt = 0.0
    tax_amt = 0.0
    
    ist = pytz.timezone("Asia/Kolkata")
    current_time = datetime.now(ist).strftime("%Y-%m-%d %I:%M %p")
    
    cls()
    print("\n\n\t\t\t\t   -- Bill statement --\n")
    print(f"{'Date:':>55} {current_time:>10}")
    print("\t\t", "=" *60)
    print("\t\t Item \t\t\t quantity \t\t Price")
    print("\t\t", "-" *60)

    for i in range(order_length) :
         if i in del_set :
             continue
         if len(tmp_lis) == 0 :
             tmp_lis.append([order_menu[i][0], order_menu[i][1], float(order_menu[i][2]) * int(order_menu[i][1])])
             #print("val=", tmp_lis)
             continue
         
         for j in range(len(tmp_lis)) :
             if order_menu[i][0] == tmp_lis[j][0] :
                 matched = 1
                 old_quantity = int(tmp_lis[j][1])
                 new_quantity = int(order_menu[i][1])
                 new_quantity += old_quantity
                 tmp_lis[j][1] = new_quantity
                 price = float(order_menu[i][2])
                 price *= new_quantity
                 tmp_lis[j][2] = price
                 #print("price",price)
                 #print("j = ",j)
         if matched == 0 :
             tmp_lis.append([order_menu[i][0], order_menu[i][1], float(order_menu[i][2]) * int(order_menu[i][1])])
         if matched == 1 :
             #print("matched")
             #print("j = ",j)
             matched = 0

    #print("tax_list :", tax_lis)
    #print("tax data :", tax_data)
            
    for i in range(len(tmp_lis)) :
        tax_rt = tax_data[tax_lis[tmp_lis[i][0]]]
        #print("taxc = ", tax_c)
        #tax_rt = tax_data[tax_c]
        #print("tax rt = ", tax_rt)
        gst = tax_rt
        tax_set.add(gst)
        bill_amt += float(tmp_lis[i][2])
        tax_amt += float(tmp_lis[i][2]) * gst
        print("\t\t",f"{tmp_lis[i][0]:<25}", tmp_lis[i][1], "\t\t\t", f"{tmp_lis[i][2]:.2f}")

    total_bill = bill_amt
    total_bill += tax_amt
    cgst = tax_amt/2
    sgst = cgst
    gst = max(tax_set)
    
    print()
    print(" " *45, "\t Highest applied Gst=", f"{gst*100:.2f}%")
    print(" " *50, "\t sgst= Rs.",f"{sgst:.2f}")
    print(" " *50, "\t cgst= Rs.", f"{cgst:.2f}")
    print("\t\t", "-" *60)
    print(" " *40, "Total Bill [before tax] = Rs. ", f"{bill_amt:.2f}")
    print(" " *40, "\tTotal Tax Amt =  Rs. ", f"{tax_amt:.2f}")
    print(" " *40, "Total Bill [after tax] = Rs. ", f"{total_bill:.2f}")
    print("\t\t", "=" *60)
    print("\n\t\t\t\t\t\t **Thank you visit again!")

    insert_db_data(connection,tmp_lis)

def insert_db_data(connection, tmp_lis) :
    from datetime import date, datetime
    
    idx = 0
    ins_rec = []
    cursor = connection.cursor()

    current_date = date.today()
    cur_date = current_date.strftime("%d-%b-%Y").upper()
    
    for idx in range(len(tmp_lis)) :
        ins_rec.append([cur_date,tmp_lis[idx][0],tmp_lis[idx][1],tmp_lis[idx][2]])

    insert_sales_rec = "insert into sales_dtl_tbl (value_date,item_name,quantity,sales_amt) values ( :1, :2, :3, :4 )"
          

    try:
        cursor.executemany(insert_sales_rec, ins_rec)

    except oracledb.DatabaseError as e:
        error_obj, = e.args
        print(f"Oracle Error Code: {error_obj.code}")
        print(f"Oracle Error Message: {error_obj.message}")

    connection.commit()

def main_menu() :
    print("\n\t\t\t\t *** Main menu *** \n")
    print("\t\t\t","=" *50)
    print("\t\t\t\t 1. Coffee Menu -- ")
    print("\t\t\t\t 2. Tea Menu -- ")
    print("\t\t\t\t 3. Chat Menu -- ");
    print("\t\t\t\t 4. Special Menu -- ");
    print("\t\t\t","=" *50)
    menu_opt = int(input("\n\t Enter your option : "))
    return menu_opt

    
def load_tax_data(connection) :
    
    cursor = connection.cursor()
    sel_tax_rec = "SELECT category_name, tax_slab FROM tax_maintenance_tbl"
    cursor.execute(sel_tax_rec)

    while True :
        row = cursor.fetchone()
        if row is None :
            break
        #print("row = ", row)
        tax_data[row[0]] = row[1]


def get_portal_menu() :
    user_file_path = "./Files/user_list.txt"
    allowed_users = set()

    fp = open(user_file_path, "r")

    content = fp.readlines()
    for line in content :
        allowed_users.add(line.strip())
    
    
    print(" " *20, " Welcome to Restro Portal***")
    print("\t\t","=" *40)
    print("\t\t\t", "1. Public portal")
    print("\t\t\t", "2. Corporate portal")
    print("\t\t","=" *40)

    opt = int(input("Enter option : "))
    return (opt, allowed_users)


def item_wise_sales_graph_coffee(connection) :
    import pandas as pd
    item_lis = []
    qty_lis = []
    colors_lis = []
    lis_of_colors = ["red", "green", "yellow", "blue", "orange", "black", "violet","red", "green", "yellow"]
    i = 0
    
    cursor = connection.cursor()

    sel_qry1 = "SELECT item_name, sum(quantity) FROM sales_dtl_tbl "
    sel_qry2 = "WHERE item_name in (SELECT coffee_name FROM coffee_menu_tbl )"
    sel_qry3 = "AND value_date = trim(sysdate) group by item_name"

    final_qry = sel_qry1+sel_qry2+sel_qry3

    cursor.execute(final_qry)
    while True :
        row = cursor.fetchone()
        if row is None :
            break
        item_lis.append(row[0])
        qty_lis.append(row[1])
        colors_lis.append(lis_of_colors[i])
        i += 1
    
    name = "Coffee Flavour"
    quantity = "Sales Quantity"
    colors = "Colors"
    
    #item_lis = ["Hot", "Cold", "Latte", "Filter Coffee"]
    #qty_lis = [25, 40, 30, 15]

    data = pd.DataFrame({
        name: item_lis,
        quantity: qty_lis,
        colors : colors_lis
    })


    if len(item_lis) > 0 :
        import matplotlib.pyplot as plt
    
        data.plot(kind='bar', x = name, y = quantity, color=data[colors], title='Coffee Sales')
        plt.xlabel(name)
        plt.ylabel(quantity)
        #i += 1
        plt.show()
    else :
        print("No sales data found to report!")

    

def item_wise_sales_graph_coffee_ver(connection) :
    import pandas as pd
    item_lis = []
    qty_lis = []
    colors_lis = []
    lis_of_colors = ["red", "green", "yellow", "blue", "orange", "black", "violet","red", "green", "yellow"]
    i = 0
    
    
    cursor = connection.cursor()

    sel_qry1 = "SELECT item_name, sum(quantity) FROM sales_dtl_tbl "
    sel_qry2 = "WHERE item_name in (SELECT coffee_name FROM coffee_menu_tbl )"
    sel_qry3 = "AND value_date = trim(sysdate) group by item_name"

    final_qry = sel_qry1+sel_qry2+sel_qry3

    cursor.execute(final_qry)
    while True :
        row = cursor.fetchone()
        if row is None :
            break
        item_lis.append(row[0])
        qty_lis.append(row[1])
        colors_lis.append(lis_of_colors[i])
        i += 1
               
     
    name = "Coffee Flavour"
    quantity = "Sales Quantity"
    colors = "Colors"
    #item_lis = ["Hot", "Cold", "Latte", "Filter Coffee"]
    #qty_lis = [25, 40, 30, 15]

    data = pd.DataFrame({
        name: item_lis,
        quantity: qty_lis,
        colors : colors_lis
    })


    import matplotlib.pyplot as plt
    
    if len(item_lis) > 0 :
        import matplotlib.pyplot as plt
    
        data.plot(kind='barh', x = name, y = quantity, color=data[colors], title='Coffee Sales')
        plt.xlabel(quantity)
        plt.ylabel(name)
        #i += 1
        plt.show()
    else :
        print("No sales data found to report!")

    

def item_wise_sales_graph_tea(connection) :
    import pandas as pd
    item_lis = []
    qty_lis = []
    colors_lis = []
    lis_of_colors = ["red", "green", "yellow", "blue", "orange", "black", "violet","red", "green", "yellow"]
    i = 0
    
    cursor = connection.cursor()

    sel_qry1 = "SELECT item_name, sum(quantity) FROM sales_dtl_tbl "
    sel_qry2 = "WHERE item_name in (SELECT tea_name FROM tea_menu_tbl )"
    sel_qry3 = "AND value_date = trim(sysdate) group by item_name"

    final_qry = sel_qry1+sel_qry2+sel_qry3

    cursor.execute(final_qry)
    while True :
        row = cursor.fetchone()
        if row is None :
            break
        item_lis.append(row[0])
        qty_lis.append(row[1])
        colors_lis.append(lis_of_colors[i])
        i += 1
               
    
    name = "Tea Flavour"
    quantity = "Sales Quantity"
    colors = "Colors"
    
    #item_lis = ["Hot", "Cold", "Latte", "Filter Coffee"]
    #qty_lis = [25, 40, 30, 15]

    data = pd.DataFrame({
        name: item_lis,
        quantity: qty_lis,
        colors : colors_lis
    })


    if len(item_lis) > 0 :
        import matplotlib.pyplot as plt
    
        data.plot(kind='bar', x = name, y = quantity, color=data[colors], title='Tea Sales')
        plt.xlabel(name)
        plt.ylabel(quantity)
        #i += 1
        plt.show()
    else :
        print("No sales data found to report!")

    

def item_wise_sales_graph_tea_ver(connection) :
    import pandas as pd
    item_lis = []
    qty_lis = []
    colors_lis = []
    lis_of_colors = ["red", "green", "yellow", "blue", "orange", "black", "violet","red", "green", "yellow"]
    i = 0
    
    
    cursor = connection.cursor()

    sel_qry1 = "SELECT item_name, sum(quantity) FROM sales_dtl_tbl "
    sel_qry2 = "WHERE item_name in (SELECT tea_name FROM tea_menu_tbl )"
    sel_qry3 = "AND value_date = trim(sysdate) group by item_name"

    final_qry = sel_qry1+sel_qry2+sel_qry3

    cursor.execute(final_qry)
    while True :
        row = cursor.fetchone()
        if row is None :
            break
        item_lis.append(row[0])
        qty_lis.append(row[1])
        colors_lis.append(lis_of_colors[i])
        i += 1
               
    
    name = "Tea Flavour"
    quantity = "Sales Quantity"
    colors = "Colors"
    #item_lis = ["Hot", "Cold", "Latte", "Filter Coffee"]
    #qty_lis = [25, 40, 30, 15]

    data = pd.DataFrame({
        name: item_lis,
        quantity: qty_lis,
        colors : colors_lis
    })


    if len(item_lis) > 0 :
        import matplotlib.pyplot as plt
    
        data.plot(kind='bar', x = name, y = quantity, color=data[colors], title='Tea Sales')
        plt.xlabel(quantity)
        plt.ylabel(name)
        #i += 1
        plt.show()
    else :
        print("No sales data found to report!")



def item_wise_sales_graph_chat(connection) :
    import pandas as pd
    item_lis = []
    qty_lis = []
    colors_lis = []
    lis_of_colors = ["red", "green", "yellow", "blue", "orange", "black", "violet","red", "green", "yellow"]
    i = 0
    
    
    cursor = connection.cursor()

    sel_qry1 = "SELECT item_name, sum(quantity) FROM sales_dtl_tbl "
    sel_qry2 = "WHERE item_name in (SELECT chat_name FROM chat_menu_tbl )"
    sel_qry3 = "AND value_date = trim(sysdate) group by item_name"

    final_qry = sel_qry1+sel_qry2+sel_qry3

    cursor.execute(final_qry)
    while True :
        row = cursor.fetchone()
        if row is None :
            break
        item_lis.append(row[0])
        qty_lis.append(row[1])
        colors_lis.append(lis_of_colors[i])
        i += 1
               
    
    name = "Chat Variety"
    quantity = "Sales Quantity"
    colors = "Colors"
    #item_lis = ["Hot", "Cold", "Latte", "Filter Coffee"]
    #qty_lis = [25, 40, 30, 15]

    data = pd.DataFrame({
        name: item_lis,
        quantity: qty_lis,
        colors : colors_lis
    })

    if len(item_lis) > 0 :
        import matplotlib.pyplot as plt
    
        data.plot(kind='bar', x = name, y = quantity, color=data[colors], title='Chat Sales')
        plt.xlabel(name)
        plt.ylabel(quantity)
        #i += 1
        plt.show()
    else :
        print("No sales data found to report!")

def item_wise_sales_graph_chat_ver(connection) :
    import pandas as pd
    item_lis = []
    qty_lis = []
    colors_lis = []
    lis_of_colors = ["red", "green", "yellow", "blue", "orange", "black", "violet","red", "green", "yellow"]
    i = 0
    
    
    cursor = connection.cursor()

    sel_qry1 = "SELECT item_name, sum(quantity) FROM sales_dtl_tbl "
    sel_qry2 = "WHERE item_name in (SELECT chat_name FROM chat_menu_tbl )"
    sel_qry3 = "AND value_date = trim(sysdate) group by item_name"

    final_qry = sel_qry1+sel_qry2+sel_qry3

    cursor.execute(final_qry)
    while True :
        row = cursor.fetchone()
        if row is None :
            break
        item_lis.append(row[0])
        qty_lis.append(row[1])
        colors_lis.append(lis_of_colors[i])
        i += 1
               
    
    name = "Chat Variety"
    quantity = "Sales Quantity"
    colors = "Colors"
    #item_lis = ["Hot", "Cold", "Latte", "Filter Coffee"]
    #qty_lis = [25, 40, 30, 15]

    data = pd.DataFrame({
        name: item_lis,
        quantity: qty_lis,
        colors : colors_lis
    })


    if len(item_lis) > 0 :
        import matplotlib.pyplot as plt
    
        data.plot(kind='barh', x = name, y = quantity, color=data[colors], title='Chat Sales')
        plt.xlabel(quantity)
        plt.ylabel(name)
        #i += 1
        plt.show()
    else :
        print("No sales data found to report!")


def show_graph_menu() :
    cls()
    print("t\t\t\t   ~~Corporate Menu~~")
    print("\t\t","=" *50)
    print("\t\t 1. Today's Coffee sale chart")
    print("\t\t 2. Today's Tea sale chart")
    print("\t\t 3. Today's Chat sale chart")
    print("\t\t 4. View current stock availability")
    print("\t\t 5. Item addition / deletion")
    print("\t\t 6. Update item prices")
    print("\t\t 0. To Exit")
    print("\t\t","=" *50)
    opt = int(input("\n\t\t Enter the option :_ "))
    return(opt)


#
def load_stock_data(connection) :
    rec_cnt = 0
    
    
    qry = "select count(*) cnt from STOCK_MAINTENANCE_TXN_TBL where value_date=trim(sysdate)"
    ins_qry = "insert into STOCK_MAINTENANCE_TXN_TBL (value_date, item_name, avail_stock) select trim(sysdate), item_name, total_stock from STOCK_MAINTENANCE_TBL "
    
    cursor = connection.cursor()
    cursor.execute(qry)

    for row in cursor.fetchone() :
        if row is None :
             break
        rec_cnt = row

    if rec_cnt == 0 :
        cursor.execute(ins_qry)
        connection.commit()

    sel_qry = "select  item_name, avail_stock from STOCK_MAINTENANCE_TXN_TBL where value_date=trim(sysdate) "

    cursor.execute(sel_qry)
    while True :
        rec = cursor.fetchone()
        if rec is None :
            break
        stock_rec[rec[0]] = int(rec[1])

    return stock_rec

    
        
def show_available_stock(connection) :
    from datetime import datetime
    import pytz

    ist = pytz.timezone("Asia/Kolkata")
    current_time = datetime.now(ist).strftime("%Y-%m-%d %I:%M %p")

                        
                        
    stock_lis = []
    
    cursor = connection.cursor()
    sel_qry = "select  item_name, avail_stock from STOCK_MAINTENANCE_TXN_TBL where value_date=trim(sysdate) "

    cursor.execute(sel_qry)
    while True :
        rec = cursor.fetchone()
        if rec is None :
            break
        stock_lis.append(rec)
        
    cls()
    print("\t\t", "="*50)
    print("\t\t\t      Current stock availability\n")
    print("\t\t Current Time : \t\t", current_time)
    print("\t\t Item Name \t\t\t\t Stock")
    print("\t\t", "-"*50)

    for rec in range(len(stock_lis)) :
        tup = tuple(stock_lis[rec])
        for j in range(len(tup)) :
            print("\t\t ",f'{stock_lis[rec][j]:<23}', end=" ")
        print()
    '''
    for rec in range(len(stock_lis)) :
        print(stock_lis[rec][0], stock_lis[rec][1])
        stock_rec[stock_lis[rec][0]] = stock_lis[rec][1]

    print("dict=", stock_rec)
    '''
    print("\t\t", "="*50)
    print("\n\n")
    input("Press Enter to continue...")
    
    

##

def update_stock_rec(connection, stock_rec) :

    cursor = connection.cursor()
    #set_clause = ", ".join(f"{key} = {value}" for key , value in stock_rec.items())

    upd_qry = "update STOCK_MAINTENANCE_TXN_TBL set avail_stock = :qty "
    condition = " where value_date=trim(sysdate) and item_name = :itm"
    final_qry = upd_qry+condition

    for itm , qty in stock_rec.items() :
        cursor.execute(final_qry, {"qty" : qty, "itm" : itm})
        
        #final_qry = upd_qry+condition
        #print(final_qry)

    #cursor.execute(final_qry)
    #connection.commit()
    
##
def show_item_add_rem(connection) :
    cursor = connection.cursor()
    
    cls()
    print("\t\t", "="*50)
    print("\t\t\t Item Addition / Deletion menu")
    print("\t\t", "-"*50)
    print("\t\t","\t 1. Add Coffee Items")
    print("\t\t","\t 2. Add Tea Items")
    print("\t\t","\t 3. Add Chat Items")
    print("\t\t","\t 4. Add Spl Items")
    print("\t\t","\t 5. Del Coffee Items")
    print("\t\t","\t 6. Del Tea Items")
    print("\t\t","\t 7. Del Chat Items")
    print("\t\t","\t 8. Del Spl Items")
    print("\t\t","\t 9. Exit")
    print("\t\t", "="*50)

    opt = int(input("Enter the option :_"))

    match(opt):
        case 1|5:
            add_del_coffee(connection,opt)
        case 2|6:
            add_del_tea(connection,opt)
        case 3|7:
            add_del_chat(connection,opt)
        case 4|8:
            add_del_spl(connection,opt)

    

##
def add_del_coffee(connection, opt) :
    cursor = connection.cursor()
    coffee_list = []
    add_lis = []

    qry = "select rownum, coffee_name from coffee_menu_tbl where delete_flag='N' "
    cursor.execute(qry)
    cls()
    
    print("\t\t\t Coffee List")
    print("\t\t","="*50)
    print("\t\t Item# \t\t\t\t Item Name")
    print("\t\t","-"*50)

    while True :
        row = cursor.fetchone()
        if row is None :
            break
        tup = tuple(row)
        coffee_list.append(tup)

    
    
    if opt == 1 :
        
        for row in range(len(coffee_list)) :
            print("\t\t", f'{coffee_list[row][0]:<30}', f'{coffee_list[row][1]:<30}')
        print("\t\t","="*50)
        while True :
            add_lis = []
            item_name = input("Enter the coffee name :_")
            price = float(input("Enter the price :_"))
            tax_slab = input("Enter the Tax tier :_")

            add_lis.append(item_name)
            add_lis.append(price)
            add_lis.append(tax_slab)
            

            op = input("Want to add more item ?[y/n): ")
            if op.lower() != 'y' :
                break
            
        ins_stmt = "insert into coffee_menu_tbl(coffee_name,price,tax_category) values (:1, :2, :3)"
        cursor.execute(ins_stmt,add_lis)

        connection.commit()
    if opt ==  5 :
        
        for row in range(len(coffee_list)) :
            print("\t\t", f'{coffee_list[row][0]:<30}', f'{coffee_list[row][1]:<30}')
        print("\t\t","="*50)
        while True :
            op = int(input("Enter the Coffee No. to delete :_"))
            op -=1
            itm_name = coffee_list[op][1]

            del_stmt = "update coffee_menu_tbl set delete_flag='Y' where coffee_name = :itm_name"
            cursor.execute(del_stmt, { "itm_name" : itm_name})
            connection.commit()

            if input("Want to delete more Items? [y/n]: ").lower() != 'y' :
                break
            
         

##
def add_del_tea(connection, opt) :
    cursor = connection.cursor()
    tea_list = []
    add_lis = []

    qry = "select rownum, tea_name from tea_menu_tbl where delete_flag='N' "
    cursor.execute(qry)
    cls()
    
    print("\t\t\t Tea List")
    print("\t\t","="*50)
    print("\t\t Item# \t\t\t\t Item Name")
    print("\t\t","-"*50)

    while True :
        row = cursor.fetchone()
        if row is None :
            break
        tup = tuple(row)
        tea_list.append(tup)

    
    
    if opt == 2 :
        
        for row in range(len(tea_list)) :
            print("\t\t", f'{tea_list[row][0]:<30}', f'{tea_list[row][1]:<30}')
        print("\t\t","="*50)
        while True :
            add_lis = []
            item_name = input("Enter the tea name :_")
            price = float(input("Enter the price :_"))
            tax_slab = input("Enter the Tax tier :_")

            add_lis.append(item_name)
            add_lis.append(price)
            add_lis.append(tax_slab)
            

            op = input("Want to add more item ?[y/n): ")
            if op.lower() != 'y' :
                break
            
        ins_stmt = "insert into tea_menu_tbl(tea_name,price,tax_category) values (:1, :2, :3)"
        cursor.execute(ins_stmt,add_lis)

        connection.commit()
    if opt ==  6 :
        
        for row in range(len(tea_list)) :
            print("\t\t", f'{tea_list[row][0]:<30}', f'{tea_list[row][1]:<30}')
        print("\t\t","="*50)
        while True :
            op = int(input("Enter the Tea No. to delete :_"))
            op -=1
            itm_name = tea_list[op][1]

            del_stmt = "update tea_menu_tbl set delete_flag='Y' where tea_name = :itm_name"
            cursor.execute(del_stmt, { "itm_name" : itm_name})
            connection.commit()

            if input("Want to delete more Items? [y/n]: ").lower() != 'y' :
                break

           
##
def add_del_chat(connection, opt) :
    cursor = connection.cursor()
    chat_list = []
    add_lis = []

    qry = "select rownum, chat_name from chat_menu_tbl where delete_flag='N' "
    cursor.execute(qry)
    cls()
    
    print("\t\t\t Chat List")
    print("\t\t","="*50)
    print("\t\t Item# \t\t\t\t Item Name")
    print("\t\t","-"*50)

    while True :
        row = cursor.fetchone()
        if row is None :
            break
        tup = tuple(row)
        chat_list.append(tup)

    
    
    if opt == 3 :
        
        for row in range(len(chat_list)) :
            print("\t\t", f'{chat_list[row][0]:<30}', f'{chat_list[row][1]:<30}')
        print("\t\t","="*50)
        while True :
            add_lis = []
            item_name = input("Enter the chat name :_")
            price = float(input("Enter the price :_"))
            tax_slab = input("Enter the Tax tier :_")

            add_lis.append(item_name)
            add_lis.append(price)
            add_lis.append(tax_slab)
            

            op = input("Want to add more item ?[y/n): ")
            if op.lower() != 'y' :
                break
            
        ins_stmt = "insert into chat_menu_tbl(chat_name,price,tax_category) values (:1, :2, :3)"
        cursor.execute(ins_stmt,add_lis)

        connection.commit()
    if opt ==  7 :
        
        for row in range(len(chat_list)) :
            print("\t\t", f'{chat_list[row][0]:<30}', f'{chat_list[row][1]:<30}')
        print("\t\t","="*50)
        while True :
            op = int(input("Enter the Chat No. to delete :_"))
            op -=1
            itm_name = chat_list[op][1]

            del_stmt = "update chat_menu_tbl set delete_flag='Y' where chat_name = :itm_name"
            cursor.execute(del_stmt, { "itm_name" : itm_name})
            connection.commit()

            if input("Want to delete more Items? [y/n]: ").lower() != 'y' :
                break

##

def add_del_spl(connection, opt) :
    cursor = connection.cursor()
    spl_list = []
    add_lis = []

    qry = "select rownum, item_name from SPECIAL_SNACKS_TBL where delete_flag='N' "
    cursor.execute(qry)
    cls()
    
    print("\t\t\t Spl snack List")
    print("\t\t","="*50)
    print("\t\t Item# \t\t\t\t Item Name")
    print("\t\t","-"*50)

    while True :
        row = cursor.fetchone()
        if row is None :
            break
        tup = tuple(row)
        spl_list.append(tup)

    
    
    if opt == 4 :
        
        for row in range(len(spl_list)) :
            print("\t\t", f'{spl_list[row][0]:<30}', f'{spl_list[row][1]:<30}')
        print("\t\t","="*50)
        while True :
            add_lis = []
            item_name = input("Enter the snack name :_")
            price = float(input("Enter the price :_"))
            tax_slab = input("Enter the Tax tier :_")

            add_lis.append(item_name)
            add_lis.append(price)
            add_lis.append(tax_slab)
            

            op = input("Want to add more item ?[y/n): ")
            if op.lower() != 'y' :
                break
            
        ins_stmt = "insert into SPECIAL_SNACKS_TBL(item_name,price,tax_category) values (:1, :2, :3)"
        cursor.execute(ins_stmt,add_lis)

        connection.commit()
    if opt ==  8 :
        
        for row in range(len(spl_list)) :
            print("\t\t", f'{spl_list[row][0]:<30}', f'{spl_list[row][1]:<30}')
        print("\t\t","="*50)
        while True :
            op = int(input("Enter the Snack No. to delete :_"))
            op -=1
            itm_name = spl_list[op][1]

            del_stmt = "update SPECIAL_SNACKS_TBL set delete_flag='Y' where item_name = :itm_name"
            cursor.execute(del_stmt, { "itm_name" : itm_name})
            connection.commit()

            if input("Want to delete more Items? [y/n]: ").lower() != 'y' :
                break

            
##
def check_time() :
    from datetime import datetime

    local_time = datetime.now()
    HH = int(local_time.strftime("%H"))
    if HH >= 17 and HH <= 19 :
        return 1
    else :
        return 0
    
##
#main module

path = "./Files/db_prop.txt"
def main():
    ret = 0
    chk = 0
    idx = 0
    portal_opt = 0
    allowed_users = set()
    
    conn = []
    new_list = []
    
    fp = open(path,"r")
    for rec in fp :
        conn = rec.split(',')
        #rec_tup = tuple(rec)
    user = conn[0]
    password = conn[1]
    dsn = conn[2]
    connection = connect_DB(user, password, dsn)

    stock_rec = load_stock_data(connection)

    portal_opt, allowed_users = get_portal_menu()

    
    
    if portal_opt == 1 :
        load_tax_data(connection)
        
    
       
        while True :
            menu_opt = main_menu()
            match menu_opt :
                case 1:
                    fetch_coffee_rec(connection)
                    ret = get_coffee_order(idx, stock_rec)
                case 2:
                    fetch_tea_rec(connection)
                    ret = get_tea_order(idx, stock_rec)
                case 3:
                    chk = fetch_chat_rec(connection)
                    if chk == 1 :
                        ret = get_chat_order(idx, stock_rec)
                case 4:
                    flag = check_time()
                    if flag == 1 :
                        fetch_splMenu_rec(connection)
                        ret = get_splMenu_order(idx, stock_rec)
                    else :
                        print("Special items availabe between 5PM to 7PM")
                case _:
                    print("Invalid option!")

            idx = ret
        
            option = input("\n\n\t\t Would you like to order more..(view main menu)[y/n]? ").title()
            if option.lower() != 'y' :
               break

        del_set.add(99)       
        if len(order_menu) > 0 :
            order_length = len(order_menu)
            order_rec_len = len(order_menu[0])
            cls()
            list_order(order_length, order_rec_len, del_set)
        else:
            print("\n\n\t\t your cart is empty!")
        
    
        tmp_order_menu = {}
        del_set.clear()
        
        while True :
            tmp_lis = []
            if len(order_menu) == 0 :
                break
            opt = input("\n\t Would you like to cancel any order?[y/n] : ").title()
            if opt.lower() == 'y' :
                itmNo = int(input("\n\t Enter the Item # : "))
            
                if itmNo > len(order_menu) :
                    print("Invalid item, try again!")
                    continue
                if len(order_menu) == 0 :
                    print("your cart is empty!")
                    break

                if itmNo > 0 :
                    itmNo -= 1
                    #re_arrane_order_menu(order_menu, del_set, order_length)
                    tmp_lis.append(order_menu[itmNo])
                    #print(tmp_lis[0][0])
                    #print(stock_rec[tmp_lis[0][0]])
                    stock_rec[tmp_lis[0][0]] += int(tmp_lis[0][1])
                    #print(stock_rec[tmp_lis[0][0]])
                    del_set.clear()
                    del_set.add(itmNo)            
                    del order_menu[itmNo]
                    re_arrane_order_menu(order_menu, del_set, order_length)
                    del_set.clear()
                    order_length = len(order_menu)
                    list_order(order_length, order_rec_len, del_set)
                    
                else :
                    print("Invalid selection!")
            
            else :
                break
      
        if len(order_menu) > 0 :
            update_stock_rec(connection, stock_rec)
            generate_bill(connection,order_length, order_rec_len, stock_rec)
        else :
            print("No item selected to generate the bill statement !")
    
    elif portal_opt == 2 :
        
        user_val = input("\t\t Enter user name : ")
        if user_val not in allowed_users :
            print("Invalid user - not allowed to proceed ! ")
        else :
            while True :
                grp_opt = show_graph_menu()
                match grp_opt :
                    case 1:
                        sub_opt = input("Horizontal / Vertical chart? [H/V] :")
                        if sub_opt.lower() == 'h' :
                            item_wise_sales_graph_coffee_ver(connection)
                        else :
                            item_wise_sales_graph_coffee(connection)
                    case 2:
                        sub_opt = input("Horizontal / Vertical chart? [H/V] :")
                        if sub_opt.lower() == 'h' :
                            item_wise_sales_graph_tea_ver(connection)
                        else :
                            item_wise_sales_graph_tea(connection)
                    case 3:
                        sub_opt = input("Horizontal / Vertical chart? [H/V] :")
                        if sub_opt.lower() == 'h' :
                            item_wise_sales_graph_chat_ver(connection)
                        else :
                            item_wise_sales_graph_chat(connection)
                    case 4:
                        show_available_stock(connection)
                    case 5:
                        show_item_add_rem(connection)
                    case 6:
                        show_item_upd_price(connection)
                    case 0:
                        break
                    case _:
                        print("Nothing to act!")
                        break
    else :
        print("Invalid option!")
        
    connection.close()
    print("End program")

main()
