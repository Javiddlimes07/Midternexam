import sqlite3
from typing import Tuple
from datetime import datetime

# 常數：資料庫名稱和日期格式
DATABASE_NAME = "bookstore.db"
DATE_FORMAT = "%Y-%m-%d"

def connect_db() -> sqlite3.Connection:
    """連接到資料庫並設定可以用欄位名稱拿資料"""
    connection = sqlite3.connect(DATABASE_NAME)
    connection.row_factory = sqlite3.Row
    return connection

def initialize_db(connection: sqlite3.Connection) -> None:
    """檢查資料表是否存在，若沒有就創建並加入初始資料"""
    with connection:
        cursor = connection.cursor()
        cursor.executescript("""
            CREATE TABLE IF NOT EXISTS member (
                mid TEXT PRIMARY KEY,
                mname TEXT NOT NULL,
                mphone TEXT NOT NULL,
                memail TEXT
            );
            
            CREATE TABLE IF NOT EXISTS book (
                bid TEXT PRIMARY KEY,
                btitle TEXT NOT NULL,
                bprice INTEGER NOT NULL,
                bstock INTEGER NOT NULL
            );
            
            CREATE TABLE IF NOT EXISTS sale (
                sid INTEGER PRIMARY KEY AUTOINCREMENT,
                sdate TEXT NOT NULL,
                mid TEXT NOT NULL,
                bid TEXT NOT NULL,
                sqty INTEGER NOT NULL,
                sdiscount INTEGER NOT NULL,
                stotal INTEGER NOT NULL
            );
            
            INSERT OR IGNORE INTO member VALUES 
                ('M001', 'Alice', '0912-345678', 'alice@example.com'),
                ('M002', 'Bob', '0923-456789', 'bob@example.com'),
                ('M003', 'Cathy', '0934-567890', 'cathy@example.com');
                
            INSERT OR IGNORE INTO book VALUES 
                ('B001', 'Python Programming', 600, 50),
                ('B002', 'Data Science Basics', 800, 30),
                ('B003', 'Machine Learning Guide', 1200, 20);
                
            INSERT OR IGNORE INTO sale (sdate, mid, bid, sqty, sdiscount, stotal) VALUES 
                ('2024-01-15', 'M001', 'B001', 2, 100, 1100),
                ('2024-01-16', 'M002', 'B002', 1, 50, 750),
                ('2024-01-17', 'M001', 'B003', 3, 200, 3400),
                ('2024-01-18', 'M003', 'B001', 1, 0, 600);
        """)

def check_date_format(date_string: str) -> bool:
    """檢查日期是不是 YYYY-MM-DD 格式"""
    if len(date_string) != 10 or date_string[4] != '-' or date_string[7] != '-':
        return False
    try:
        datetime.strptime(date_string, DATE_FORMAT)
        return True
    except ValueError:
        return False

def add_sale(connection: sqlite3.Connection, sale_date: str, member_id: str, 
             book_id: str, quantity: int, discount: int) -> Tuple[bool, str]:
    """新增一筆銷售記錄並更新庫存"""
    if not check_date_format(sale_date):
        return False, "錯誤！日期格式要像 2024-01-19 這樣"

    with connection:
        cursor = connection.cursor()
        
        # 檢查會員是否存在
        cursor.execute("SELECT mid FROM member WHERE mid = ?", (member_id,))
        if not cursor.fetchone():
            return False, "錯誤！會員編號或書籍編號不存在"
            
        # 檢查書籍和庫存
        cursor.execute("SELECT bprice, bstock FROM book WHERE bid = ?", (book_id,))
        book_data = cursor.fetchone()
        if not book_data:
            return False, "錯誤！會員編號或書籍編號不存在"
        if book_data['bstock'] < quantity:
            return False, f"錯誤！庫存不夠，現在只有 {book_data['bstock']} 本"
            
        # 計算總額
        total_price = (book_data['bprice'] * quantity) - discount
        
        try:
            # 儲存銷售記錄
            cursor.execute("""
                INSERT INTO sale (sdate, mid, bid, sqty, sdiscount, stotal)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (sale_date, member_id, book_id, quantity, discount, total_price))
            
            # 更新庫存
            cursor.execute("UPDATE book SET bstock = bstock - ? WHERE bid = ?", 
                         (quantity, book_id))
            connection.commit()
            return True, f"成功！新增銷售記錄，總額是 {total_price:,}"
        except (sqlite3.OperationalError, sqlite3.DatabaseError):
            connection.rollback()
            return False, "錯誤！無法儲存到資料庫"

def print_sale_report(connection: sqlite3.Connection) -> None:
    """顯示所有銷售記錄的報表"""
    with connection:
        cursor = connection.cursor()
        cursor.execute("""
            SELECT s.sid, s.sdate, m.mname, b.btitle, b.bprice, 
                   s.sqty, s.sdiscount, s.stotal
            FROM sale s
            JOIN member m ON s.mid = m.mid
            JOIN book b ON s.bid = b.bid
            ORDER BY s.sid
        """)
        
        all_sales = cursor.fetchall()
        for index, sale in enumerate(all_sales, 1):
            print(f"\n{'='*50} 銷售報表 {'='*50}")
            print(f"銷售 #{index}")
            print(f"銷售編號: {sale['sid']}")
            print(f"銷售日期: {sale['sdate']}")
            print(f"會員姓名: {sale['mname']}")
            print(f"書籍標題: {sale['btitle']}")
            print("-"*50)
            print("單價\t數量\t折扣\t小計")
            print("-"*50)
            print(f"{sale['bprice']:,}\t{sale['sqty']}\t{sale['sdiscount']:,}\t{sale['stotal']:,}")
            print("-"*50)
            print(f"銷售總額: {sale['stotal']:,}")
            print("="*50)

def update_sale(connection: sqlite3.Connection) -> None:
    """更新一筆銷售記錄的折扣和總額"""
    with connection:
        cursor = connection.cursor()
        cursor.execute("""
            SELECT s.sid, m.mname, s.sdate
            FROM sale s
            JOIN member m ON s.mid = m.mid
            ORDER BY s.sid
        """)
        all_sales = cursor.fetchall()
        
        if not all_sales:
            print("沒有銷售記錄可以更新！")
            return
            
        print("\n======== 銷售記錄列表 ========")
        for index, sale in enumerate(all_sales, 1):
            print(f"{index}. 銷售編號: {sale['sid']} - 會員: {sale['mname']} - 日期: {sale['sdate']}")
        print("="*32)
        
        user_choice = input("請選擇要更新的銷售編號 (輸入數字或按 Enter 取消): ").strip()
        if not user_choice:
            return
            
        try:
            choice_number = int(user_choice)
            if choice_number < 1 or choice_number > len(all_sales):
                print("錯誤！請輸入正確的數字")
                return
        except ValueError:
            print("錯誤！請輸入數字")
            return
            
        selected_sale_id = all_sales[choice_number-1]['sid']
        
        try:
            new_discount = int(input("請輸入新的折扣金額："))
            if new_discount < 0:
                print("錯誤！折扣不能是負數")
                return
        except ValueError:
            print("錯誤！折扣要輸入數字")
            return
        
        try:
            cursor.execute("""
                SELECT b.bprice, s.sqty
                FROM sale s
                JOIN book b ON s.bid = b.bid
                WHERE s.sid = ?
            """, (selected_sale_id,))
            sale_data = cursor.fetchone()
            
            new_total = (sale_data['bprice'] * sale_data['sqty']) - new_discount
            
            cursor.execute("""
                UPDATE sale 
                SET sdiscount = ?, stotal = ?
                WHERE sid = ?
            """, (new_discount, new_total, selected_sale_id))
            
            connection.commit()
            print(f"成功！銷售編號 {selected_sale_id} 已更新，新的總額是 {new_total:,}")
        except (sqlite3.OperationalError, sqlite3.DatabaseError):
            connection.rollback()
            print("錯誤！無法更新資料庫")

def delete_sale(connection: sqlite3.Connection) -> None:
    """刪除一筆銷售記錄"""
    with connection:
        cursor = connection.cursor()
        cursor.execute("""
            SELECT s.sid, m.mname, s.sdate
            FROM sale s
            JOIN member m ON s.mid = m.mid
            ORDER BY s.sid
        """)
        all_sales = cursor.fetchall()
        
        if not all_sales:
            print("沒有銷售記錄可以刪除！")
            return
            
        print("\n======== 銷售記錄列表 ========")
        for index, sale in enumerate(all_sales, 1):
            print(f"{index}. 銷售編號: {sale['sid']} - 會員: {sale['mname']} - 日期: {sale['sdate']}")
        print("="*32)
        
        user_choice = input("請選擇要刪除的銷售編號 (輸入數字或按 Enter 取消): ").strip()
        if not user_choice:
            return
            
        try:
            choice_number = int(user_choice)
            if choice_number < 1 or choice_number > len(all_sales):
                print("錯誤！請輸入正確的數字")
                return
        except ValueError:
            print("錯誤！請輸入數字")
            return
            
        selected_sale_id = all_sales[choice_number-1]['sid']
        
        try:
            cursor.execute("DELETE FROM sale WHERE sid = ?", (selected_sale_id,))
            connection.commit()
            print(f"成功！銷售編號 {selected_sale_id} 已刪除")
        except (sqlite3.OperationalError, sqlite3.DatabaseError):
            connection.rollback()
            print("錯誤！無法刪除資料庫記錄")

def main() -> None:
    """主程式，顯示選單並讓使用者選擇功能"""
    connection = connect_db()
    initialize_db(connection)
    
    while True:
        print("\n***************選單***************")
        print("1. 新增銷售記錄")
        print("2. 顯示銷售報表")
        print("3. 更新銷售記錄")
        print("4. 刪除銷售記錄")
        print("5. 離開")
        print("**********************************")
        
        user_choice = input("請選擇操作項目(Enter 離開)：").strip()
        
        if user_choice == "" or user_choice == "5":
            print("程式結束！")
            break
        
        if user_choice not in ["1", "2", "3", "4", "5"]:
            print("錯誤！請輸入 1 到 5 的選項")
            continue
            
        if user_choice == "1":
            input_date = input("請輸入銷售日期 (YYYY-MM-DD)：").strip()
            input_member_id = input("請輸入會員編號：").strip()
            input_book_id = input("請輸入書籍編號：").strip()
            
            try:
                input_quantity = int(input("請輸入購買數量："))
                if input_quantity <= 0:
                    print("錯誤！數量要大於 0")
                    continue
            except ValueError:
                print("錯誤！數量要輸入數字")
                continue
                
            try:
                input_discount = int(input("請輸入折扣金額："))
                if input_discount < 0:
                    print("錯誤！折扣不能是負數")
                    continue
            except ValueError:
                print("錯誤！折扣要輸入數字")
                continue
                
            success, message = add_sale(connection, input_date, input_member_id, 
                                     input_book_id, input_quantity, input_discount)
            print(message)
            
        elif user_choice == "2":
            print_sale_report(connection)
            
        elif user_choice == "3":
            update_sale(connection)
            
        elif user_choice == "4":
            delete_sale(connection)
    
    connection.close()

if __name__ == "__main__":
    main()