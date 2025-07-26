import pandas as pd

def load_data_from_csv(filepath):
    data = pd.read_csv(filepath, parse_dates=['Date'], index_col='Date')
    return data

def main():
    # فرض کن دیتای تاریخی XRPUSDT رو داری به شکل CSV
    filepath = 'data/XRPUSDT_15m.csv'  # مسیر رو به مسیر واقعی تغییر بده
    data = load_data_from_csv(filepath)
    
    print("داده‌ها با موفقیت بارگذاری شدند. 5 ردیف آخر:")
    print(data.tail())
    
if __name__ == '__main__':
    main()
