import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta

# Fungsi untuk membaca file Excel dari Google Drive
def load_google_drive_excel(file_url):
    try:
        # Ubah URL Google Drive menjadi URL unduhan langsung
        file_id = file_url.split("/d/")[1].split("/")[0]
        download_url = f"https://drive.google.com/uc?export=download&id={file_id}"
        
        # Baca file Excel menggunakan pandas dengan engine openpyxl
        df = pd.read_excel(download_url, engine='openpyxl')
        
        # Periksa apakah kolom 'Ticker' ada di file Excel
        if 'Ticker' not in df.columns:
            st.error("The 'Ticker' column is missing in the Excel file.")
            return None
        
        # Informasi keberhasilan pembacaan file
        st.success(f"Successfully loaded data from Google Drive!")
        st.info(f"Number of rows read: {len(df)}")
        st.info(f"Columns in the Excel file: {', '.join(df.columns)}")
        
        return df
    except Exception as e:
        st.error(f"Error loading Excel file from Google Drive: {e}")
        return None

# Fungsi untuk mendeteksi pola Mat Hold
def detect_mat_hold(data):
    if len(data) >= 5:
        # Candle 1: Bullish dengan body besar
        candle1 = data.iloc[0]
        is_candle1_bullish = candle1['Close'] > candle1['Open']
        is_candle1_large_body = (candle1['Close'] - candle1['Open']) > 0.02 * candle1['Open']  # Body besar > 2%
        
        # Candle 2: Bearish dan ditutup lebih rendah dari candle 1
        candle2 = data.iloc[1]
        is_candle2_bearish = candle2['Close'] < candle2['Open']
        is_candle2_lower_than_candle1 = candle2['Close'] < candle1['Close']
        
        # Candle 3 dan 4: Bearish
        candle3 = data.iloc[2]
        candle4 = data.iloc[3]
        is_candle3_bearish = candle3['Close'] < candle3['Open']
        is_candle4_bearish = candle4['Close'] < candle4['Open']
        
        # Candle 5: Open gap atau sama dengan close candle 4
        candle5 = data.iloc[4]
        is_candle5_gap_or_equal = candle5['Open'] >= candle4['Close']
        
        # Pastikan pola muncul di tren naik (harga candle 5 lebih tinggi dari candle 1)
        is_uptrend = candle5['Close'] > candle1['Close']
        
        # Semua kondisi harus terpenuhi
        return (
            is_candle1_bullish and
            is_candle1_large_body and
            is_candle2_bearish and
            is_candle2_lower_than_candle1 and
            is_candle3_bearish and
            is_candle4_bearish and
            is_candle5_gap_or_equal and
            is_uptrend
        )
    return False

# Main function
def main():
    st.title("Stock Screening - Mat Hold Pattern")
    
    # URL file Excel di Google Drive
    file_url = "https://docs.google.com/spreadsheets/d/1t6wgBIcPEUWMq40GdIH1GtZ8dvI9PZ2v/edit?usp=drive_link&ouid=106044501644618784207&rtpof=true&sd=true"
    
    # Load data dari Google Drive
    st.info("Loading data from Google Drive...")
    df = load_google_drive_excel(file_url)
    if df is None or 'Ticker' not in df.columns:
        st.error("Failed to load data or 'Ticker' column is missing.")
        return
    
    tickers = [f"{ticker}.JK" for ticker in df['Ticker'].tolist()]  # Tambahkan ".JK" untuk saham Indonesia
    total_tickers = len(tickers)
    
    # Date input
    analysis_date = st.date_input("Analysis Date", value=datetime.today())
    
    # Analyze button
    if st.button("Analyze Stocks"):
        results = []
        progress_bar = st.progress(0)
        progress_text = st.empty()  # Placeholder untuk menampilkan persentase
        
        # Proses setiap ticker
        for i, ticker in enumerate(tickers):
            ticker_clean = ticker.replace(".JK", "")  # Hapus ".JK" untuk hasil akhir
            
            # Ambil data selama 30 hari sebelum tanggal analisis untuk memastikan mendapatkan 5 data perdagangan
            start_date = analysis_date - timedelta(days=30)
            end_date = analysis_date
            
            try:
                stock = yf.Ticker(ticker)
                data = stock.history(start=start_date, end=end_date)
                
                # Filter hanya 5 data terakhir
                if len(data) >= 5:
                    data = data.tail(5)
                else:
                    st.warning(f"Not enough trading data for {ticker_clean} in the given date range.")
                    continue
                
                # Deteksi pola Mat Hold
                if detect_mat_hold(data):
                    results.append({
                        "Ticker": ticker_clean,
                        "Last Close": data['Close'][-1],
                        "Pattern Detected": "Mat Hold"
                    })
            except Exception as e:
                st.error(f"Error fetching data for {ticker_clean}: {str(e)}")
            
            # Update progress bar
            progress = (i + 1) / total_tickers
            progress_bar.progress(progress)
            progress_text.text(f"Progress: {int(progress * 100)}%")
        
        # Display results
        if results:
            st.subheader("Results: Stocks Meeting Criteria")
            results_df = pd.DataFrame(results)
            st.dataframe(results_df)
        else:
            st.info("No stocks match the Mat Hold pattern.")

if __name__ == "__main__":
    main()
