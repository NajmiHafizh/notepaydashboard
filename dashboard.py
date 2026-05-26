import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import requests
import re
from collections import Counter
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# ============================================================================
# KONFIGURASI HALAMAN & CSS NEO-BRUTALISM
# ============================================================================
st.set_page_config(
    page_title="NotePay Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS untuk Neo-Brutalism
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Public+Sans:wght@400;700;900&display=swap');

    html, body, [data-testid="stAppViewContainer"] {
        font-family: 'Public Sans', sans-serif;
        background-color: #F3F4F6;
    }

    /* Sidebar Styling */
    [data-testid="stSidebar"] {
        background-color: #FFD700 !important;
        border-right: 4px solid #000000 !important;
    }
    [data-testid="stSidebar"] [data-testid="stVerticalBlock"] {
        padding: 2rem 1rem;
    }

    /* Metric Styling */
    [data-testid="stMetric"] {
        background-color: #FFFFFF !important;
        border: 3px solid #000000 !important;
        padding: 1rem !important;
        box-shadow: 6px 6px 0px #000000 !important;
        border-radius: 0px !important;
    }
    [data-testid="stMetricLabel"] p {
        font-weight: 800 !important;
        color: #000000 !important;
        text-transform: uppercase;
        font-size: 0.9rem !important;
    }
    [data-testid="stMetricValue"] div {
        font-weight: 900 !important;
        color: #000000 !important;
    }

    /* Tab Styling */
    [data-testid="stTabBar"] {
        background-color: transparent !important;
        gap: 10px !important;
    }
    button[data-baseweb="tab"] {
        border: 3px solid #000000 !important;
        background-color: #FFFFFF !important;
        border-radius: 0px !important;
        padding: 0.5rem 1.5rem !important;
        font-weight: 800 !important;
        box-shadow: 4px 4px 0px #000000 !important;
        transition: all 0.2s ease;
    }
    button[data-baseweb="tab"]:hover {
        transform: translate(-2px, -2px);
        box-shadow: 6px 6px 0px #000000 !important;
    }
    button[data-baseweb="tab"][aria-selected="true"] {
        background-color: #FF6B6B !important;
        color: white !important;
    }

    /* Header & Container Styling */
    .neo-container {
        border: 3px solid #000000;
        padding: 1.5rem;
        background-color: #FFFFFF;
        box-shadow: 8px 8px 0px #000000;
        margin-bottom: 2rem;
    }
    .neo-header {
        background-color: #A78BFA;
        border: 4px solid #000000;
        padding: 2rem;
        box-shadow: 10px 10px 0px #000000;
        margin-bottom: 2.5rem;
    }

    /* Global Title Adjustments */
    h1, h2, h3 {
        font-weight: 900 !important;
        color: #000000 !important;
        text-transform: uppercase;
        letter-spacing: -1px;
    }
    
    /* Expander Styling */
    [data-testid="stExpander"] {
        border: 3px solid #000000 !important;
        border-radius: 0px !important;
        box-shadow: 4px 4px 0px #000000 !important;
        background-color: white !important;
    }
    
    /* Button Styling */
    .stButton > button {
        border: 3px solid #000000 !important;
        border-radius: 0px !important;
        background-color: #4ECDC4 !important;
        color: black !important;
        font-weight: 800 !important;
        box-shadow: 4px 4px 0px #000000 !important;
        text-transform: uppercase;
    }
    .stButton > button:hover {
        background-color: #45B7D1 !important;
        box-shadow: 6px 6px 0px #000000 !important;
        transform: translate(-2px, -2px);
    }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# KONEKSI SUPABASE
# ============================================================================
SUPABASE_URL = 'https://eefmonebltpdrmdmbpuc.supabase.co'
SUPABASE_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImVlZm1vbmVibHRwZHJtZG1icHVjIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3OTMwNzg5NCwiZXhwIjoyMDk0ODgzODk0fQ.O0O2AyzmbYp6K6A9GxkZXVdnczlMzzMur1L7p2FvwWA'

@st.cache_data(ttl=3600)
def load_data():
    """Load data from Supabase using REST API"""
    try:
        SUPABASE_URL = 'https://eefmonebltpdrmdmbpuc.supabase.co'
        SUPABASE_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImVlZm1vbmVibHRwZHJtZG1icHVjIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3OTMwNzg5NCwiZXhwIjoyMDk0ODgzODk0fQ.O0O2AyzmbYp6K6A9GxkZXVdnczlMzzMur1L7p2FvwWA'
        
        headers = {
            'apikey': SUPABASE_KEY,
            'Authorization': f'Bearer {SUPABASE_KEY}'
        }
        
        # Ambil semua data dengan pagination
        all_rows = []
        offset = 0
        page_size = 1000
        
        with st.spinner('Mengambil data dari Supabase...'):
            while True:
                url = f"{SUPABASE_URL}/rest/v1/ocr_labels?select=id,filename,label,class,updated_at,updated_by&verified=eq.true&order=id.asc&offset={offset}&limit={page_size}"
                response = requests.get(url, headers=headers)
                
                if response.status_code != 200:
                    st.error(f"Error fetching data: {response.status_code}")
                    break
                
                batch = response.json()
                if not batch:
                    break
                    
                all_rows.extend(batch)
                
                if len(batch) < page_size:
                    break
                    
                offset += page_size
        
        if not all_rows:
            st.warning("Tidak ada data ditemukan")
            return None, None
        
        df_raw = pd.DataFrame(all_rows)
        
        # Data cleaning
        df = df_raw.copy()
        df['class'] = df['class'].astype(str).str.strip().str.lower()
        df['label'] = df['label'].astype(str).str.strip()
        df = df.drop_duplicates(subset=['label', 'class'], keep='last')
        df = df[df['label'].notna() & (df['label'].str.len() >= 3)]
        df['label_clean'] = df['label'].str.replace(r'[^\w\s\.\,\-\:\(\)\&\@\#\%]', '', regex=True)
        
        df['updated_at'] = pd.to_datetime(df['updated_at'], utc=True, errors='coerce')
        df['tanggal'] = df['updated_at'].dt.date
        df['jam'] = df['updated_at'].dt.hour
        df['hari'] = df['updated_at'].dt.day_name()
        
        # Deteksi mata uang
        df['mata_uang'] = 'Tidak Terdeteksi'
        df.loc[df['label'].str.contains(r'\$', na=False, regex=True), 'mata_uang'] = 'USD ($)'
        df.loc[df['label'].str.contains(r'Rp|rp|IDR', na=False, regex=True), 'mata_uang'] = 'IDR (Rp)'
        
        st.success(f"Berhasil memuat {len(df):,} baris data!")
        return df, df_raw
        
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return None, None

# ============================================================================
# FUNGSI ANALISIS
# ============================================================================
def get_error_analysis(df_raw):
    """Analisis error rate per kelas"""
    def detect_error(row):
        text = str(row['label'])
        if row['class'] == 'tanggal_waktu':
            return len(text) < 8
        elif row['class'] == 'total_belanja':
            return not any(char.isdigit() for char in text)
        elif row['class'] == 'nama_toko':
            return len(text) < 4
        elif row['class'] == 'line_item':
            return len(text) < 3
        return False
    
    df = df_raw.copy()
    df['is_error'] = df.apply(detect_error, axis=1)
    error_analysis = df.groupby('class')['is_error'].mean().mul(100).reset_index(name='error_rate (%)')
    return error_analysis, df  # ← Kembalikan 2 nilai

def get_category_distribution(df):
    """Distribusi kategori pengeluaran"""
    kategori_map = {
        'beras': 'Makanan Pokok', 'mie': 'Makanan Pokok', 'nasi': 'Makanan Pokok',
        'ayam': 'Makanan', 'chicken': 'Makanan', 'goreng': 'Makanan',
        'air mineral': 'Minuman', 'kopi': 'Minuman', 'tea': 'Minuman', 'teh': 'Minuman', 'coffee': 'Minuman',
        'sabun': 'Perawatan Diri', 'shampoo': 'Perawatan Diri'
    }
    
    def kategori_item(item):
        item = str(item).lower()
        for key, value in kategori_map.items():
            if key in item:
                return value
        return 'Lainnya'
    
    line_items = df[df['class'] == 'line_item'].copy()
    if len(line_items) > 0:
        line_items['kategori'] = line_items['label'].apply(kategori_item)
        kategori_dist = line_items['kategori'].value_counts(normalize=True).mul(100).reset_index()
        kategori_dist.columns = ['kategori', 'persentase']
        return kategori_dist, len(line_items)
    return pd.DataFrame(), 0

def get_anomaly_analysis(df_raw):
    """Analisis anomali data"""
    dup_label = df_raw.duplicated(subset=['label', 'class']).sum()
    dollar = df_raw['label'].str.contains(r'\$', na=False).sum()
    bracket = df_raw['label'].str.contains(r'\]|\[', na=False).sum()
    
    anomali = pd.DataFrame({
        'Jenis Anomali': ['Duplikat label+kelas', 'Mata uang USD', 'Karakter bracket'],
        'Jumlah': [dup_label, dollar, bracket],
        'Persen (%)': [dup_label/len(df_raw)*100, dollar/len(df_raw)*100, bracket/len(df_raw)*100]
    })
    return anomali

def get_store_analysis(df):
    """Analisis rata-rata total belanja per toko"""
    store_df = df[df['class'] == 'nama_toko'].copy().reset_index(drop=True)
    total_df = df[df['class'] == 'total_belanja'].copy().reset_index(drop=True)
    
    if len(store_df) > 0 and len(total_df) > 0:
        analysis_df = pd.DataFrame({
            'nama_toko': store_df['label'],
            'total_belanja': total_df['label']
        })
        analysis_df['total_belanja'] = analysis_df['total_belanja'].astype(str).str.replace(r'[^0-9]', '', regex=True)
        analysis_df['total_belanja'] = pd.to_numeric(analysis_df['total_belanja'], errors='coerce')
        store_stats = analysis_df.groupby('nama_toko')['total_belanja'].mean().sort_values(ascending=False).head(10)
        return store_stats
    return pd.Series()

def get_keywords_analysis(df):
    """Analisis kata kunci pada line item"""
    line_items = df[df['class'] == 'line_item'].copy()
    if len(line_items) > 0:
        text = ' '.join(line_items['label'].astype(str).tolist()).lower()
        words = re.findall(r'\b[a-zA-Z]+\b', text)
        words = [word for word in words if len(word) > 2]
        common_words = Counter(words).most_common(15)
        return pd.DataFrame(common_words, columns=['kata', 'frekuensi'])
    return pd.DataFrame()

def get_temporal_analysis(df):
    """Analisis temporal transaksi"""
    transaksi = df[df['class'] == 'tanggal_waktu'].copy()
    if len(transaksi) > 0:
        transaksi['datetime'] = pd.to_datetime(transaksi['label'], errors='coerce')
        transaksi['jam'] = transaksi['datetime'].dt.hour
        transaksi['hari'] = transaksi['datetime'].dt.day_name()
        
        jam_dist = transaksi['jam'].value_counts().sort_index()
        hari_dist = transaksi['hari'].value_counts()
        
        return jam_dist, hari_dist, len(transaksi)
    return pd.Series(), pd.Series(), 0

def get_class_distribution(df):
    """Distribusi kelas data"""
    class_dist = df['class'].value_counts()
    return class_dist

# ============================================================================
# SMART INSIGHTS GENERATOR
# ============================================================================
def generate_smart_insights(df, df_raw):
    """Generate dynamic insights based on data"""
    insights = {}
    
    # 1. Overview Insights
    if len(df) > 0:
        top_class = df['class'].value_counts().idxmax()
        top_class_pct = (df['class'].value_counts().max() / len(df)) * 100
        insights['overview'] = f"Dataset Anda didominasi oleh kelas <b>{top_class.upper()}</b> sebesar <b>{top_class_pct:.1f}%</b>. Total terdapat <b>{df['filename'].nunique()}</b> file unik yang telah diproses."
    else:
        insights['overview'] = "Tidak ada data untuk dianalisis."

    # 2. Accuracy Insights
    error_analysis, _ = get_error_analysis(df_raw)
    avg_error = error_analysis['error_rate (%)'].mean()
    worst_class = error_analysis.loc[error_analysis['error_rate (%)'].idxmax()]
    insights['accuracy'] = f"Rata-rata error rate OCR adalah <b>{avg_error:.2f}%</b>. Perhatian khusus diperlukan pada kelas <b>{worst_class['class'].upper()}</b> dengan tingkat error <b>{worst_class['error_rate (%)']:.2f}%</b>."

    # 3. Category Insights
    kategori_dist, total_items = get_category_distribution(df)
    if not kategori_dist.empty:
        top_cat = kategori_dist.iloc[0]
        insights['category'] = f"Kategori pengeluaran terbanyak adalah <b>{top_cat['kategori'].upper()}</b> (<b>{top_cat['persentase']:.1f}%</b>). Dari total <b>{total_items}</b> item, sistem berhasil mengklasifikasikan pola belanja Anda secara otomatis."
    else:
        insights['category'] = "Data item belanja tidak mencukupi untuk analisis kategori."

    # 4. Anomaly Insights
    anomali = get_anomaly_analysis(df_raw)
    total_anomali = anomali['Jumlah'].sum()
    insights['anomaly'] = f"Terdeteksi total <b>{total_anomali}</b> anomali dalam dataset. Anomali terbanyak adalah <b>{anomali.loc[anomali['Jumlah'].idxmax()]['Jenis Anomali']}</b>. Validasi manual sangat disarankan untuk data ini."

    # 5. Store Insights
    store_stats = get_store_analysis(df)
    if not store_stats.empty:
        top_store = store_stats.index[0]
        insights['store'] = f"Toko dengan rata-rata belanja tertinggi adalah <b>{top_store.upper()}</b>. Analisis ini membantu Anda mengidentifikasi di mana pengeluaran besar biasanya terjadi."
    else:
        insights['store'] = "Data toko atau total belanja tidak lengkap."

    # 6. Temporal Insights
    jam_dist, hari_dist, _ = get_temporal_analysis(df)
    if not jam_dist.empty and not hari_dist.empty:
        peak_hour = jam_dist.idxmax()
        busiest_day = hari_dist.idxmax()
        insights['temporal'] = f"Waktu transaksi terpadat Anda adalah pada pukul <b>{peak_hour}:00</b>, dengan hari tersibuk <b>{busiest_day.upper()}</b>. Gunakan info ini untuk mengatur jadwal belanja yang lebih efisien."
    else:
        insights['temporal'] = "Data waktu transaksi tidak tersedia."

    return insights

# ============================================================================
# MAIN DASHBOARD
# ============================================================================
def main():
    # Header Neo-Brutalism
    st.markdown("""
    <div class='neo-header'>
        <h1 style='margin: 0; font-size: 3rem;'>📊 NotePay Dashboard</h1>
        <p style='margin: 10px 0 0 0; font-weight: 700; color: #000;'>TRANSFORMASI FINTECH UNTUK GENERASI MUDA</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class='neo-container' style='background-color: #4ECDC4;'>
        <p style='margin: 0; font-weight: 800;'>TEAM ID: CC26-PSU410 | PROGRAM: Coding Camp 2026 powered by DBS Foundation</p>
        <p style='margin: 5px 0 0 0;'><b>DATA SCIENTISTS:</b> Firdhania Nur Rizky Setyarini & Najmi Hafizh Mauludan Zain</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Load data
    df, df_raw = load_data()
    
    if df is None:
        st.error("Gagal memuat data. Silakan periksa koneksi Supabase Anda.")
        return
    
    # Generate Smart Insights
    insights = generate_smart_insights(df, df_raw)
    
    # Sidebar untuk filter
    with st.sidebar:
        st.markdown("""
        <div style='background-color: #FFFFFF; border: 3px solid #000; padding: 15px; box-shadow: 4px 4px 0px #000; margin-bottom: 20px; text-align: center;'>
            <img src="https://img.icons8.com/color/96/000000/receipt.png" width="80">
            <h2 style='margin: 10px 0 0 0;'>NOTEPAY</h2>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("### 🔍 FILTER DATA")
        
        # Filter berdasarkan kata kunci
        search_query = st.text_input("CARI LABEL / ITEM", "").strip().lower()
        
        # Filter berdasarkan rentang tanggal
        valid_dates = df['tanggal'].dropna()
        if not valid_dates.empty:
            min_date = min(valid_dates)
            max_date = max(valid_dates)
            date_range = st.date_input(
                "RENTANG TANGGAL",
                value=(min_date, max_date),
                min_value=min_date,
                max_value=max_date
            )
        else:
            date_range = None

        # Filter berdasarkan kelas
        classes = df['class'].unique()
        selected_classes = st.multiselect(
            "PILIH KELAS DATA",
            options=classes,
            default=classes.tolist()
        )
        
        # Filter berdasarkan mata uang
        currencies = df['mata_uang'].unique()
        selected_currencies = st.multiselect(
            "PILIH MATA UANG",
            options=currencies,
            default=currencies.tolist()
        )
        
        # Apply Filters
        filtered_df = df.copy()
        
        if search_query:
            filtered_df = filtered_df[filtered_df['label'].str.lower().str.contains(search_query, na=False)]
            
        if date_range and len(date_range) == 2:
            filtered_df = filtered_df[(filtered_df['tanggal'] >= date_range[0]) & (filtered_df['tanggal'] <= date_range[1])]
            
        filtered_df = filtered_df[filtered_df['class'].isin(selected_classes)]
        filtered_df = filtered_df[filtered_df['mata_uang'].isin(selected_currencies)]
        
        st.markdown("---")
        st.metric("TOTAL DATA", f"{len(filtered_df):,}")
        st.metric("TERFILTER", f"{len(filtered_df):,}")
    
    # Tab layout untuk dashboard
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📈 OVERVIEW", 
        "🎯 AKURASI OCR", 
        "🛒 KATEGORI", 
        "⚠️ ANOMALI", 
        "🏪 TOKO", 
        "⏰ WAKTU"
    ])
    
    # ========================================================================
    # TAB 1: OVERVIEW
    # ========================================================================
    with tab1:
        st.markdown(f"""
        <div class='neo-container' style='background-color: #FFD700; border-style: dashed;'>
            <h3 style='margin:0;'>🧠 SMART INSIGHT</h3>
            <p style='margin:10px 0 0 0; font-weight:bold;'>{insights['overview']}</p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<div class='neo-container'>", unsafe_allow_html=True)
        st.header("📊 Overview Dataset")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Records", f"{len(filtered_df):,}")
        with col2:
            st.metric("Unique Files", f"{filtered_df['filename'].nunique():,}")
        with col3:
            st.metric("Unique Labels", f"{filtered_df['label'].nunique():,}")
        with col4:
            st.metric("Unique Classes", f"{filtered_df['class'].nunique()}")
        
        st.markdown("---")
        
        # Distribusi Kelas
        st.subheader("Distribusi Kelas Data")
        fig, ax = plt.subplots(figsize=(10, 5))
        fig.patch.set_facecolor('#F3F4F6')
        ax.set_facecolor('#FFFFFF')
        
        class_dist = get_class_distribution(filtered_df)
        colors = ['#FF6B6B', '#4ECDC4', '#A78BFA', '#FFD700', '#FF9F43']
        bars = ax.bar(class_dist.index, class_dist.values, color=colors[:len(class_dist)], edgecolor='black', linewidth=2)
        
        ax.set_title('DISTRIBUSI LABEL PER KELAS', fontsize=14, fontweight='black')
        ax.set_xlabel('KELAS', fontweight='bold')
        ax.set_ylabel('JUMLAH DATA', fontweight='bold')
        ax.tick_params(axis='x', rotation=45)
        
        # Remove top and right spines
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_linewidth(2)
        ax.spines['bottom'].set_linewidth(2)
        
        for bar, val in zip(bars, class_dist.values):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 5, 
                   str(val), ha='center', va='bottom', fontweight='black')
        st.pyplot(fig)
        plt.close()
        
        # Sample data
        with st.expander("LIHAT SAMPLE DATA"):
            st.dataframe(filtered_df[['label', 'class', 'mata_uang']].head(100), use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)
    
    # ========================================================================
    # TAB 2: AKURASI OCR
    # ========================================================================
    with tab2:
        st.markdown(f"""
        <div class='neo-container' style='background-color: #FFD700; border-style: dashed;'>
            <h3 style='margin:0;'>🧠 SMART INSIGHT</h3>
            <p style='margin:10px 0 0 0; font-weight:bold;'>{insights['accuracy']}</p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<div class='neo-container'>", unsafe_allow_html=True)
        st.header("🎯 Analisis Akurasi OCR")
        
        error_analysis, df_error = get_error_analysis(df_raw.copy())
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Error Rate per Kelas")
            fig, ax = plt.subplots(figsize=(8, 5))
            fig.patch.set_facecolor('#F3F4F6')
            
            colors = ['#FF6B6B' if x > 20 else '#4ECDC4' for x in error_analysis['error_rate (%)']]
            bars = ax.bar(error_analysis['class'], error_analysis['error_rate (%)'], color=colors, edgecolor='black', linewidth=2)
            ax.axhline(20, linestyle='--', color='black', linewidth=2, label='Threshold 20%')
            
            ax.set_title('ERROR RATE OCR PER KELAS', fontweight='black')
            ax.set_ylabel('PERSENTASE ERROR (%)', fontweight='bold')
            ax.tick_params(axis='x', rotation=45)
            
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.spines['left'].set_linewidth(2)
            ax.spines['bottom'].set_linewidth(2)
            
            for bar, val in zip(bars, error_analysis['error_rate (%)']):
                ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5, 
                       f'{val:.2f}%', ha='center', va='bottom', fontweight='black')
            ax.legend()
            st.pyplot(fig)
            plt.close()
        
        with col2:
            st.subheader("Insight & Rekomendasi")
            
            high_error = error_analysis[error_analysis['error_rate (%)'] > 20]
            if len(high_error) > 0:
                st.markdown("""
                <div style='background-color: #FF6B6B; padding: 15px; border: 3px solid #000; box-shadow: 4px 4px 0px #000;'>
                    <h4 style='margin:0; color:white;'>⚠️ PERINGATAN!</h4>
                    <p style='margin:10px 0 0 0; color:white; font-weight:bold;'>Kelas dengan error rate > 20%:</p>
                """, unsafe_allow_html=True)
                for _, row in high_error.iterrows():
                    st.write(f"- **{row['class'].upper()}**: {row['error_rate (%)']:.2f}%")
                st.markdown("</div>", unsafe_allow_html=True)
            else:
                st.markdown("""
                <div style='background-color: #4ECDC4; padding: 15px; border: 3px solid #000; box-shadow: 4px 4px 0px #000;'>
                    <h4 style='margin:0;'>✅ AMAN!</h4>
                    <p style='margin:10px 0 0 0; font-weight:bold;'>Semua kelas memiliki error rate di bawah 20%.</p>
                </div>
                """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Detail error per kelas
        st.subheader("Detail Analisis Error")
        
        if df_error is not None:
            error_detail = df_error[df_error['is_error'] == True].groupby('class').size().reset_index(name='jumlah_error')
            st.dataframe(error_detail, use_container_width=True)
            
            st.markdown("""
            <div style='background-color: #FFD700; padding: 10px; border: 2px solid #000; margin-top: 10px;'>
                <p style='margin:0; font-weight:800;'>📌 KETERANGAN ERROR:</p>
                <ul style='margin:5px 0 0 0; font-size: 0.9rem;'>
                    <li><b>TANGGAL_WAKTU:</b> Format tidak valid (< 8 karakter)</li>
                    <li><b>TOTAL_BELANJA:</b> Tidak mengandung angka</li>
                    <li><b>NAMA_TOKO:</b> Terlalu pendek (< 4 karakter)</li>
                    <li><b>LINE_ITEM:</b> Item terlalu pendek (< 3 karakter)</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
    
    # ========================================================================
    # TAB 3: KATEGORI BELANJA
    # ========================================================================
    with tab3:
        st.markdown(f"""
        <div class='neo-container' style='background-color: #FFD700; border-style: dashed;'>
            <h3 style='margin:0;'>🧠 SMART INSIGHT</h3>
            <p style='margin:10px 0 0 0; font-weight:bold;'>{insights['category']}</p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<div class='neo-container'>", unsafe_allow_html=True)
        st.header("🛒 Analisis Kategori Pengeluaran")
        
        kategori_dist, total_items = get_category_distribution(filtered_df)
        
        col1, col2 = st.columns(2)
        
        with col1:
            if len(kategori_dist) > 0:
                st.subheader(f"Distribusi Kategori (Total {total_items} items)")
                fig, ax = plt.subplots(figsize=(8, 5))
                fig.patch.set_facecolor('#F3F4F6')
                
                colors = ['#FF6B6B' if p < 10 else '#4ECDC4' for p in kategori_dist['persentase']]
                bars = ax.bar(kategori_dist['kategori'], kategori_dist['persentase'], color=colors, edgecolor='black', linewidth=2)
                ax.axhline(10, linestyle='--', color='black', linewidth=2, label='Threshold 10%')
                
                ax.set_title('DISTRIBUSI KATEGORI PENGELUARAN', fontweight='black')
                ax.set_ylabel('PERSENTASE (%)', fontweight='bold')
                ax.tick_params(axis='x', rotation=45)
                
                ax.spines['top'].set_visible(False)
                ax.spines['right'].set_visible(False)
                ax.spines['left'].set_linewidth(2)
                ax.spines['bottom'].set_linewidth(2)
                
                for bar, val in zip(bars, kategori_dist['persentase']):
                    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5, 
                           f'{val:.1f}%', ha='center', va='bottom', fontweight='black')
                ax.legend()
                st.pyplot(fig)
                plt.close()
        
        with col2:
            st.subheader("Rekomendasi Pengembangan")
            
            if not kategori_dist.empty and 'persentase' in kategori_dist.columns:
                low_categories = kategori_dist[kategori_dist['persentase'] < 10]
                if len(low_categories) > 0:
                    st.markdown("""
                    <div style='background-color: #FFD700; padding: 15px; border: 3px solid #000; box-shadow: 4px 4px 0px #000;'>
                        <h4 style='margin:0;'>⚠️ PERHATIAN</h4>
                        <p style='margin:10px 0 0 0; font-weight:bold;'>Kategori dengan proporsi < 10%:</p>
                    """, unsafe_allow_html=True)
                    for _, row in low_categories.iterrows():
                        st.write(f"- **{row['kategori'].upper()}**: {row['persentase']:.1f}%")
                    st.markdown("""
                        <p style='margin-top:10px; font-size:0.9rem;'>📌 Rekomendasi: Perkuat dengan data tambahan sebelum implementasi klasifikasi otomatis.</p>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.success("✅ Semua kategori memiliki proporsi di atas 10%")
            else:
                st.markdown("""
                <div style='background-color: #F3F4F6; padding: 15px; border: 2px solid #000;'>
                    <p style='margin:0; font-weight:bold;'>ℹ️ DATA TIDAK TERSEDIA</p>
                    <p style='margin:5px 0 0 0; font-size: 0.9rem;'>Tidak ada data kategori (line_item) yang ditemukan pada filter ini.</p>
                </div>
                """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Rekomendasi konten literasi keuangan
        st.subheader("📖 Literasi Keuangan")
        
        st.markdown("""
        <div style='background-color: #A78BFA; padding: 1.5rem; border: 3px solid #000; box-shadow: 6px 6px 0px #000;'>
            <h4 style='margin:0; color:white; text-transform:uppercase; font-weight:900;'>🎯 Rekomendasi Berdasarkan Pengeluaran:</h4>
            <ul style='margin:10px 0 0 0; color:white; font-weight:bold;'>
                <li>🍔 MAKAN & MINUM: "Kendalikan Budget Makan: Tips Hemat Makan di Luar"</li>
                <li>🛒 BELANJA BULANAN: "Atur Anggaran Belanja Bulanan dengan Metode 50/30/20"</li>
                <li>📊 TRACKING: "Pantau Pengeluaran Harian dengan NotePay"</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        
        # Kata kunci populer
        st.markdown("<br>", unsafe_allow_html=True)
        st.subheader("Top Kata Kunci pada Line Item")
        keywords_df = get_keywords_analysis(filtered_df)
        if len(keywords_df) > 0:
            fig, ax = plt.subplots(figsize=(10, 6))
            fig.patch.set_facecolor('#F3F4F6')
            
            bars = ax.barh(keywords_df['kata'][:10], keywords_df['frekuensi'][:10], color='#4ECDC4', edgecolor='black', linewidth=2)
            ax.set_xlabel('FREKUENSI', fontweight='bold')
            ax.set_title('TOP 10 KATA KUNCI PADA LINE ITEM', fontweight='black', fontsize=13)
            ax.invert_yaxis()
            
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.spines['left'].set_linewidth(2)
            ax.spines['bottom'].set_linewidth(2)
            
            for bar, count in zip(bars, keywords_df['frekuensi'][:10]):
                ax.text(bar.get_width() + 0.5, bar.get_y() + bar.get_height()/2,
                       str(count), va='center', fontweight='black')
            st.pyplot(fig)
            plt.close()
        st.markdown("</div>", unsafe_allow_html=True)
    
    # ========================================================================
    # TAB 4: ANOMALI DATA
    # ========================================================================
    with tab4:
        st.markdown(f"""
        <div class='neo-container' style='background-color: #FFD700; border-style: dashed;'>
            <h3 style='margin:0;'>🧠 SMART INSIGHT</h3>
            <p style='margin:10px 0 0 0; font-weight:bold;'>{insights['anomaly']}</p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<div class='neo-container'>", unsafe_allow_html=True)
        st.header("⚠️ Analisis Anomali Data")
        
        anomali = get_anomaly_analysis(df_raw)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Frekuensi Anomali")
            fig, ax = plt.subplots(figsize=(8, 5))
            fig.patch.set_facecolor('#F3F4F6')
            
            colors = ['#FF6B6B' if p >= 5 else '#A78BFA' for p in anomali['Persen (%)']]
            bars = ax.barh(anomali['Jenis Anomali'], anomali['Persen (%)'], color=colors, edgecolor='black', linewidth=2, height=0.6)
            ax.axvline(5, color='black', linestyle='--', linewidth=2, label='Threshold 5%')
            
            ax.set_xlabel('PERSENTASE DARI TOTAL DATA (%)', fontweight='bold')
            ax.set_title('FREKUENSI ANOMALI PADA DATA OCR', fontweight='black', fontsize=13)
            ax.legend(loc='lower right')
            
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.spines['left'].set_linewidth(2)
            ax.spines['bottom'].set_linewidth(2)
            
            for bar, pct in zip(bars, anomali['Persen (%)']):
                ax.text(bar.get_width() + 0.5, bar.get_y() + bar.get_height()/2,
                       f'{pct:.2f}%', va='center', fontweight='black')
            st.pyplot(fig)
            plt.close()
        
        with col2:
            st.subheader("Rekomendasi Penanganan")
            
            anomali_prioritas = anomali[anomali['Persen (%)'] >= 5]
            if len(anomali_prioritas) > 0:
                st.markdown("""
                <div style='background-color: #FF6B6B; padding: 15px; border: 3px solid #000; box-shadow: 4px 4px 0px #000;'>
                    <h4 style='margin:0; color:white;'>⚠️ PRIORITAS PENANGANAN</h4>
                    <p style='margin:10px 0 0 0; color:white; font-weight:bold;'>Anomali yang perlu ditangani segera:</p>
                """, unsafe_allow_html=True)
                for _, row in anomali_prioritas.iterrows():
                    st.write(f"- **{row['Jenis Anomali'].upper()}**: {row['Persen (%)']:.2f}%")
                st.markdown("""
                    <p style='margin-top:10px; color:white; font-size:0.9rem;'>📌 Rekomendasi: Tambahkan mekanisme konfirmasi pengguna untuk anomali ini.</p>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.success("✅ Semua anomali < 5%, tidak prioritas untuk ditangani")
        
        st.markdown("---")
        
        # Outlier total belanja
        st.subheader("Deteksi Outlier Total Belanja")
        
        total_df = filtered_df[filtered_df['class'] == 'total_belanja'].copy()
        if len(total_df) > 0:
            total_df['numeric_total'] = total_df['label'].astype(str).str.replace(r'[^0-9]', '', regex=True)
            total_df['numeric_total'] = pd.to_numeric(total_df['numeric_total'], errors='coerce')
            total_df = total_df.dropna(subset=['numeric_total'])
            
            if len(total_df) > 0:
                fig, ax = plt.subplots(figsize=(10, 4))
                fig.patch.set_facecolor('#F3F4F6')
                
                box = ax.boxplot(total_df['numeric_total'], patch_artist=True)
                for patch in box['boxes']:
                    patch.set_facecolor('#4ECDC4')
                    patch.set_edgecolor('black')
                    patch.set_linewidth(2)
                for whisker in box['whiskers']:
                    whisker.set_color('black')
                    whisker.set_linewidth(2)
                for median in box['medians']:
                    median.set_color('black')
                    median.set_linewidth(3)
                
                ax.set_title('BOXPLOT TOTAL BELANJA', fontweight='black')
                ax.set_ylabel('NILAI (RUPIAH)', fontweight='bold')
                
                ax.spines['top'].set_visible(False)
                ax.spines['right'].set_visible(False)
                ax.spines['left'].set_linewidth(2)
                ax.spines['bottom'].set_linewidth(2)
                
                st.pyplot(fig)
                plt.close()
                
                Q1 = total_df['numeric_total'].quantile(0.25)
                Q3 = total_df['numeric_total'].quantile(0.75)
                IQR = Q3 - Q1
                outliers = total_df[(total_df['numeric_total'] < Q1 - 1.5*IQR) | (total_df['numeric_total'] > Q3 + 1.5*IQR)]
                st.metric("JUMLAH OUTLIER", f"{len(outliers)} data")
        st.markdown("</div>", unsafe_allow_html=True)
    
    # ========================================================================
    # TAB 5: ANALISIS TOKO
    # ========================================================================
    with tab5:
        st.markdown(f"""
        <div class='neo-container' style='background-color: #FFD700; border-style: dashed;'>
            <h3 style='margin:0;'>🧠 SMART INSIGHT</h3>
            <p style='margin:10px 0 0 0; font-weight:bold;'>{insights['store']}</p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<div class='neo-container'>", unsafe_allow_html=True)
        st.header("🏪 Analisis Nama Toko")
        
        store_stats = get_store_analysis(filtered_df)
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            if len(store_stats) > 0:
                st.subheader("Top 10 Toko - Rata-rata Belanja")
                fig, ax = plt.subplots(figsize=(10, 6))
                fig.patch.set_facecolor('#F3F4F6')
                
                colors = plt.cm.spring(np.linspace(0.2, 0.8, len(store_stats)))
                bars = ax.barh(store_stats.index, store_stats.values, color='#A78BFA', edgecolor='black', linewidth=2)
                
                ax.set_xlabel('RATA-RATA TOTAL BELANJA (RUPIAH)', fontweight='bold')
                ax.set_title('RATA-RATA TOTAL BELANJA PER TOKO', fontweight='black', fontsize=13)
                ax.invert_yaxis()
                
                ax.spines['top'].set_visible(False)
                ax.spines['right'].set_visible(False)
                ax.spines['left'].set_linewidth(2)
                ax.spines['bottom'].set_linewidth(2)
                
                for bar, val in zip(bars, store_stats.values):
                    ax.text(bar.get_width() + val*0.01, bar.get_y() + bar.get_height()/2,
                           f'Rp {val:,.0f}', va='center', fontweight='black', fontsize=9)
                st.pyplot(fig)
                plt.close()
        
        with col2:
            st.subheader("Insight Dashboard")
            st.markdown("""
            <div style='background-color: #FFFFFF; padding: 1.5rem; border: 3px solid #000; box-shadow: 4px 4px 0px #000;'>
                <p style='margin:0; font-weight:900;'>📌 POLA PRIORITAS:</p>
                <ul style='margin:10px 0 0 0; font-weight:700;'>
                    <li>Selisih belanja antar toko > 50%</li>
                    <li>Toko Dominan: <b>TOBAKU</b></li>
                    <li>Layak divisualisasikan dalam dashboard pengeluaran harian.</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
        
        # Perbandingan nilai belanja
        if len(store_stats) >= 2:
            max_val = store_stats.iloc[0]
            min_val = store_stats.iloc[-1]
            diff_pct = ((max_val - min_val) / min_val) * 100
            
            st.markdown("---")
            st.subheader("Perbandingan Nilai Belanja")
            
            col_a, col_b, col_c = st.columns(3)
            with col_a:
                st.metric("TOKO TERTINGGI", store_stats.index[0], f"Rp {max_val:,.0f}")
            with col_b:
                st.metric("TOKO TERENDAH", store_stats.index[-1], f"Rp {min_val:,.0f}")
            with col_c:
                st.metric("SELISIH", f"{diff_pct:.1f}%", 
                         delta=">50%" if diff_pct > 50 else "<50%",
                         delta_color="inverse" if diff_pct > 50 else "off")
        st.markdown("</div>", unsafe_allow_html=True)
    
    # ========================================================================
    # TAB 6: POLA WAKTU
    # ========================================================================
    with tab6:
        st.markdown(f"""
        <div class='neo-container' style='background-color: #FFD700; border-style: dashed;'>
            <h3 style='margin:0;'>🧠 SMART INSIGHT</h3>
            <p style='margin:10px 0 0 0; font-weight:bold;'>{insights['temporal']}</p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<div class='neo-container'>", unsafe_allow_html=True)
        st.header("⏰ Pola Waktu Transaksi")
        
        jam_dist, hari_dist, total_transaksi = get_temporal_analysis(filtered_df)
        
        col1, col2 = st.columns(2)
        
        with col1:
            if len(jam_dist) > 0:
                st.subheader("Distribusi Jam")
                fig, ax = plt.subplots(figsize=(10, 5))
                fig.patch.set_facecolor('#F3F4F6')
                
                ax.plot(jam_dist.index, jam_dist.values, marker='o', linewidth=4, color='#000000', markerfacecolor='#FF6B6B', markersize=8)
                ax.fill_between(jam_dist.index, jam_dist.values, alpha=0.5, color='#4ECDC4', edgecolor='black', linewidth=2)
                
                ax.set_title('DISTRIBUSI JAM TRANSAKSI', fontweight='black')
                ax.set_xlabel('JAM', fontweight='bold')
                ax.set_ylabel('JUMLAH TRANSAKSI', fontweight='bold')
                ax.grid(True, alpha=0.3, linestyle='--')
                
                ax.spines['top'].set_visible(False)
                ax.spines['right'].set_visible(False)
                ax.spines['left'].set_linewidth(2)
                ax.spines['bottom'].set_linewidth(2)
                
                st.pyplot(fig)
                plt.close()
        
        with col2:
            if len(hari_dist) > 0:
                st.subheader("Distribusi Hari")
                fig, ax = plt.subplots(figsize=(8, 5))
                fig.patch.set_facecolor('#F3F4F6')
                
                days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
                hari_dist = hari_dist.reindex([d for d in days_order if d in hari_dist.index])
                bars = ax.bar(hari_dist.index, hari_dist.values, color='#FFD700', edgecolor='black', linewidth=2)
                
                ax.set_title('DISTRIBUSI HARI TRANSAKSI', fontweight='black')
                ax.set_xlabel('HARI', fontweight='bold')
                ax.set_ylabel('JUMLAH TRANSAKSI', fontweight='bold')
                ax.tick_params(axis='x', rotation=45)
                
                ax.spines['top'].set_visible(False)
                ax.spines['right'].set_visible(False)
                ax.spines['left'].set_linewidth(2)
                ax.spines['bottom'].set_linewidth(2)
                
                for bar, val in zip(bars, hari_dist.values):
                    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
                           str(val), ha='center', va='bottom', fontweight='black')
                st.pyplot(fig)
                plt.close()
        
        st.markdown("---")
        
        # Insight pola waktu
        st.subheader("Insight Pola Transaksi")
        
        if len(jam_dist) > 0:
            mean_transaction = jam_dist.mean()
            peak_hours = jam_dist[jam_dist > mean_transaction * 1.3]
            
            col_a, col_b, col_c = st.columns(3)
            with col_a:
                st.metric("RATA-RATA/JAM", f"{mean_transaction:.1f}")
            with col_b:
                if len(peak_hours) > 0:
                    st.metric("JAM PUNCAK", f"{peak_hours.index[0]}:00 - {peak_hours.index[-1]}:00")
            with col_c:
                st.metric("TOTAL TRANSAKSI", f"{total_transaksi}")
            
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("""
            <div style='background-color: #4ECDC4; padding: 1.5rem; border: 3px solid #000; box-shadow: 6px 6px 0px #000;'>
                <h4 style='margin:0; text-transform:uppercase; font-weight:900;'>🎯 Rekomendasi NotePay:</h4>
                <ul style='margin:10px 0 0 0; font-weight:bold;'>
                    <li>Prioritaskan notifikasi pengingat pada JAM PUNCAK.</li>
                    <li>Tampilkan summary harian di hari dengan transaksi tertinggi.</li>
                    <li>Sediakan fitur laporan mingguan otomatis.</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
    
    # Footer Neo-Brutalism
    st.markdown("""
    <div style='text-align: center; padding: 2rem; background-color: #000000; color: #FFFFFF; border: 4px solid #FFD700; box-shadow: 0px -10px 0px #FFD700;'>
        <h3 style='color: #FFD700; margin: 0;'>© 2026 NOTEPAY | CC26-PSU410</h3>
        <p style='margin: 10px 0 0 0; font-weight: bold;'>POWERED BY STREAMLIT & SUPABASE</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
