import yfinance as yf

candidates = ["GLDTR.IS", "ZGOLD.IS", "GC=F"]

print("Testing Tickers History (2023+)...")
for t in candidates:
    try:
        df = yf.download(t, start="2023-01-01", progress=False)
        if not df.empty:
            print(f"FOUND: {t} - Rows: {len(df)}")
            print(df.head(2))
        else:
            print(f"Miss: {t}")
    except Exception as e:
        print(f"Error {t}: {e}")
