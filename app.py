import sqlite3

# 這是我的書店管理程式，會用 SQLite 存資料

# 資料庫檔案名稱
database_name = "bookstore.db"

# 主程式開始
def main():
    # 連接到資料庫
    conn = sqlite3.connect(database_name)
    conn.row_factory = sqlite3.Row  # 這讓我可以用欄位名稱拿資料
    cursor = conn.cursor()

    # 先設定資料庫，創建表格和初始資料
    # 創建會員表格
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS member (
            mid TEXT PRIMARY KEY,
            mname TEXT NOT NULL,
            mphone TEXT NOT NULL,
            memail TEXT
        )
    """)
    
    # 創建書籍表格
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS book (
            bid TEXT PRIMARY KEY,
            btitle TEXT NOT NULL,
            bprice INTEGER NOT NULL,
            bstock INTEGER NOT NULL
        )
    """)
    
    # 創建銷售表格
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sale (
            sid INTEGER PRIMARY KEY AUTOINCREMENT,
            sdate TEXT NOT NULL,
            mid TEXT NOT NULL,
            bid TEXT NOT NULL,
            sqty INTEGER NOT NULL,
            sdiscount INTEGER NOT NULL,
            stotal INTEGER NOT NULL
        )
    """)
    
    # 加入初始會員資料
    cursor.execute("INSERT OR IGNORE INTO member VALUES ('M001', 'Alice', '0912-345678', 'alice@example.com')")
    cursor.execute("INSERT OR IGNORE INTO member VALUES ('M002', 'Bob', '0923-456789', 'bob@example.com')")
    cursor.execute("INSERT OR IGNORE INTO member VALUES ('M003', 'Cathy', '0934-567890', 'cathy@example.com')")
    
    # 加入初始書籍資料
    cursor.execute("INSERT OR IGNORE INTO book VALUES ('B001', 'Python Programming', 600, 50)")
    cursor.execute("INSERT OR IGNORE INTO book VALUES ('B002', 'Data Science Basics', 800, 30)")
    cursor.execute("INSERT OR IGNORE INTO book VALUES ('B003', 'Machine Learning Guide', 1200, 20)")
    
    # 加入初始銷售資料
    cursor.execute("INSERT OR IGNORE INTO sale (sdate, mid, bid, sqty, sdiscount, stotal) VALUES ('2024-01-15', 'M001', 'B001', 2, 100, 1100)")
    cursor.execute("INSERT OR IGNORE INTO sale (sdate, mid, bid, sqty, sdiscount, stotal) VALUES ('2024-01-16', 'M002', 'B002', 1, 50, 750)")
    cursor.execute("INSERT OR IGNORE INTO sale (sdate, mid, bid, sqty, sdiscount, stotal) VALUES ('2024-01-17', 'M001', 'B003', 3, 200, 3400)")
    cursor.execute("INSERT OR IGNORE INTO sale (sdate, mid, bid, sqty, sdiscount, stotal) VALUES ('2024-01-18', 'M003', 'B001', 1, 0, 600)")
    
    conn.commit()  # 儲存初始資料

    # 開始選單迴圈
    while True:
        # 顯示選單
        print("\n***************選單***************")
        print("1. 新增銷售記錄")
        print("2. 顯示銷售報表")
        print("3. 更新銷售記錄")
        print("4. 刪除銷售記錄")
        print("5. 離開")
        print("**********************************")
        
        user_choice = input("請選擇操作項目(Enter 離開)：").strip()
        
        # 如果輸入空值或選 5，就離開程式
        if user_choice == "" or user_choice == "5":
            print("程式結束！")
            break
        
        # 檢查輸入是否正確
        if user_choice not in ["1", "2", "3", "4", "5"]:
            print("錯誤！你輸入的不是1到5，請再試一次")
            continue

        # 功能 1：新增銷售記錄
        if user_choice == "1":
            # 取得使用者輸入
            input_date = input("請輸入銷售日期 (YYYY-MM-DD)：").strip()
            
            # 檢查日期格式
            if len(input_date) != 10 or input_date[4] != '-' or input_date[7] != '-':
                print("錯誤！日期格式要像 2024-01-19 這樣")
                continue
                
            input_member_id = input("請輸入會員編號：").strip()
            input_book_id = input("請輸入書籍編號：").strip()
            
            # 檢查數量輸入
            input_quantity = input("請輸入購買數量：").strip()
            try:
                quantity = int(input_quantity)
                if quantity <= 0:
                    print("錯誤！數量要大於0")
                    continue
            except:
                print("錯誤！數量要輸入數字")
                continue
                
            # 檢查折扣輸入
            input_discount = input("請輸入折扣金額：").strip()
            try:
                discount = int(input_discount)
                if discount < 0:
                    print("錯誤！折扣不能是負數")
                    continue
            except:
                print("錯誤！折扣要輸入數字")
                continue
                
            # 檢查會員是否存在
            cursor.execute("SELECT mid FROM member WHERE mid = ?", (input_member_id,))
            member_data = cursor.fetchone()
            if member_data is None:
                print("錯誤！這個會員編號不存在")
                continue
                
            # 檢查書籍是否存在並檢查庫存
            cursor.execute("SELECT bid, bprice, bstock FROM book WHERE bid = ?", (input_book_id,))
            book_data = cursor.fetchone()
            if book_data is None:
                print("錯誤！這個書籍編號不存在")
                continue
            if book_data["bstock"] < quantity:
                print("錯誤！庫存不夠，現在只有", book_data["bstock"], "本")
                continue
                
            # 計算總額
            book_price = book_data["bprice"]
            total_price = (book_price * quantity) - discount
            
            # 儲存銷售記錄
            try:
                cursor.execute("""
                    INSERT INTO sale (sdate, mid, bid, sqty, sdiscount, stotal)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (input_date, input_member_id, input_book_id, quantity, discount, total_price))
                
                # 更新庫存
                cursor.execute("UPDATE book SET bstock = bstock - ? WHERE bid = ?", 
                             (quantity, input_book_id))
                
                conn.commit()  # 儲存到資料庫
                print("成功！新增了一筆銷售記錄，總額是", f"{total_price:,}")
            except:
                conn.rollback()  # 如果出錯就取消
                print("錯誤！沒能新增銷售記錄")
                
        # 功能 2：顯示銷售報表
        elif user_choice == "2":
            # 查詢所有銷售記錄
            cursor.execute("SELECT sid, sdate, mid, bid, sqty, sdiscount, stotal FROM sale ORDER BY sid")
            all_sales = cursor.fetchall()
            
            # 顯示每一筆銷售
            for index, sale in enumerate(all_sales, 1):
                # 取得會員名稱
                cursor.execute("SELECT mname FROM member WHERE mid = ?", (sale["mid"],))
                member_name = cursor.fetchone()["mname"]
                
                # 取得書籍資訊
                cursor.execute("SELECT btitle, bprice FROM book WHERE bid = ?", (sale["bid"],))
                book_info = cursor.fetchone()
                book_title = book_info["btitle"]
                book_price = book_info["bprice"]
                
                # 顯示報表
                print("\n" + "="*50 + " 銷售報表 " + "="*50)
                print("銷售 #" + str(index))
                print("銷售編號:", sale["sid"])
                print("銷售日期:", sale["sdate"])
                print("會員姓名:", member_name)
                print("書籍標題:", book_title)
                print("-"*50)
                print("單價\t數量\t折扣\t小計")
                print("-"*50)
                print(f"{book_price:,}\t{sale['sqty']}\t{sale['sdiscount']:,}\t{sale['stotal']:,}")
                print("-"*50)
                print("銷售總額:", f"{sale['stotal']:,}")
                print("="*50)
                
        # 功能 3：更新銷售記錄
        elif user_choice == "3":
            # 查詢所有銷售記錄
            cursor.execute("SELECT sid, sdate, mid FROM sale ORDER BY sid")
            all_sales = cursor.fetchall()
            
            if len(all_sales) == 0:
                print("錯誤！目前沒有銷售記錄可以更新")
                continue
                
            # 顯示銷售列表
            print("\n======== 銷售記錄列表 ========")
            for index, sale in enumerate(all_sales, 1):
                cursor.execute("SELECT mname FROM member WHERE mid = ?", (sale["mid"],))
                member_name = cursor.fetchone()["mname"]
                print(f"{index}. 銷售編號: {sale['sid']} - 會員: {member_name} - 日期: {sale['sdate']}")
            print("="*32)
            
            # 讓使用者選擇
            input_choice = input("請選擇要更新的銷售編號 (輸入數字或按 Enter 取消): ").strip()
            if input_choice == "":
                continue
                
            # 檢查輸入是否為數字
            try:
                choice_number = int(input_choice)
                if choice_number < 1 or choice_number > len(all_sales):
                    print("錯誤！請輸入正確的數字")
                    continue
            except:
                print("錯誤！請輸入數字")
                continue
                
            # 取得選中的銷售編號
            selected_sale = all_sales[choice_number - 1]
            sale_id = selected_sale["sid"]
            
            # 輸入新折扣
            input_discount = input("請輸入新的折扣金額：").strip()
            try:
                new_discount = int(input_discount)
                if new_discount < 0:
                    print("錯誤！折扣不能是負數")
                    continue
            except:
                print("錯誤！折扣要輸入數字")
                continue
                
            # 計算新總額
            cursor.execute("SELECT bid, sqty FROM sale WHERE sid = ?", (sale_id,))
            sale_data = cursor.fetchone()
            cursor.execute("SELECT bprice FROM book WHERE bid = ?", (sale_data["bid"],))
            book_price = cursor.fetchone()["bprice"]
            new_total = (book_price * sale_data["sqty"]) - new_discount
            
            # 更新資料
            try:
                cursor.execute("UPDATE sale SET sdiscount = ?, stotal = ? WHERE sid = ?", 
                             (new_discount, new_total, sale_id))
                conn.commit()
                print("成功！銷售編號", sale_id, "已更新，新的總額是", f"{new_total:,}")
            except:
                conn.rollback()
                print("錯誤！沒能更新銷售記錄")
                
        # 功能 4：刪除銷售記錄
        elif user_choice == "4":
            # 查詢所有銷售記錄
            cursor.execute("SELECT sid, sdate, mid FROM sale ORDER BY sid")
            all_sales = cursor.fetchall()
            
            if len(all_sales) == 0:
                print("錯誤！目前沒有銷售記錄可以刪除")
                continue
                
            # 顯示銷售列表
            print("\n======== 銷售記錄列表 ========")
            for index, sale in enumerate(all_sales, 1):
                cursor.execute("SELECT mname FROM member WHERE mid = ?", (sale["mid"],))
                member_name = cursor.fetchone()["mname"]
                print(f"{index}. 銷售編號: {sale['sid']} - 會員: {member_name} - 日期: {sale['sdate']}")
            print("="*32)
            
            # 讓使用者選擇
            input_choice = input("請選擇要刪除的銷售編號 (輸入數字或按 Enter 取消): ").strip()
            if input_choice == "":
                continue
                
            # 檢查輸入是否為數字
            try:
                choice_number = int(input_choice)
                if choice_number < 1 or choice_number > len(all_sales):
                    print("錯誤！請輸入正確的數字")
                    continue
            except:
                print("錯誤！請輸入數字")
                continue
                
            # 取得選中的銷售編號
            selected_sale = all_sales[choice_number - 1]
            sale_id = selected_sale["sid"]
            
            # 刪除記錄
            try:
                cursor.execute("DELETE FROM sale WHERE sid = ?", (sale_id,))
                conn.commit()
                print("成功！銷售編號", sale_id, "已刪除")
            except:
                conn.rollback()
                print("錯誤！沒能刪除銷售記錄")
    
    # 關閉資料庫
    conn.close()

# 執行程式
if __name__ == "__main__":
    main()