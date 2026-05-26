import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import requests
import re
from collections import Counter
from datetime import datetime
from scipy import stats
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

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Public+Sans:wght@400;700;900&display=swap');
    html, body, [data-testid="stAppViewContainer"] {
        font-family: 'Public Sans', sans-serif;
        background-color: #F3F4F6;
    }
    [data-testid="stSidebar"] {
        background-color: #FFD700 !important;
        border-right: 4px solid #000000 !important;
    }
    [data-testid="stSidebar"] [data-testid="stVerticalBlock"] { padding: 2rem 1rem; }
    [data-testid="stMetric"] {
        background-color: #FFFFFF !important;
        border: 3px solid #000000 !important;
        padding: 1rem !important;
        box-shadow: 6px 6px 0px #000000 !important;
        border-radius: 0px !important;
    }
    [data-testid="stMetricLabel"] p { font-weight: 800 !important; color: #000000 !important; text-transform: uppercase; font-size: 0.9rem !important; }
    [data-testid="stMetricValue"] div { font-weight: 900 !important; color: #000000 !important; }
    [data-testid="stTabBar"] { background-color: transparent !important; gap: 10px !important; }
    button[data-baseweb="tab"] {
        border: 3px solid #000000 !important;
        background-color: #FFFFFF !important;
        border-radius: 0px !important;
        padding: 0.5rem 1.5rem !important;
        font-weight: 800 !important;
        box-shadow: 4px 4px 0px #000000 !important;
        transition: all 0.2s ease;
    }
    button[data-baseweb="tab"]:hover { transform: translate(-2px, -2px); box-shadow: 6px 6px 0px #000000 !important; }
    button[data-baseweb="tab"][aria-selected="true"] { background-color: #FF6B6B !important; color: white !important; }
    .neo-container { border: 3px solid #000000; padding: 1.5rem; background-color: #FFFFFF; box-shadow: 8px 8px 0px #000000; margin-bottom: 2rem; }
    .neo-header { background-color: #A78BFA; border: 4px solid #000000; padding: 2rem; box-shadow: 10px 10px 0px #000000; margin-bottom: 2.5rem; }
    h1, h2, h3 { font-weight: 900 !important; color: #000000 !important; text-transform: uppercase; letter-spacing: -1px; }
    [data-testid="stExpander"] { border: 3px solid #000000 !important; border-radius: 0px !important; box-shadow: 4px 4px 0px #000000 !important; background-color: white !important; }
    .stButton > button { border: 3px solid #000000 !important; border-radius: 0px !important; background-color: #4ECDC4 !important; color: black !important; font-weight: 800 !important; box-shadow: 4px 4px 0px #000000 !important; text-transform: uppercase; }
    .stButton > button:hover { background-color: #45B7D1 !important; box-shadow: 6px 6px 0px #000000 !important; transform: translate(-2px, -2px); }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# KONEKSI SUPABASE
# ============================================================================
SUPABASE_URL = 'https://eefmonebltpdrmdmbpuc.supabase.co'
SUPABASE_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImVlZm1vbmVibHRwZHJtZG1icHVjIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3OTMwNzg5NCwiZXhwIjoyMDk0ODgzODk0fQ.O0O2AyzmbYp6K6A9GxkZXVdnczlMzzMur1L7p2FvwWA'

# ============================================================================
# LOAD DATA
# ============================================================================
@st.cache_data(ttl=3600)
def load_data():
    """Load data dari Supabase menggunakan REST API dengan pagination."""
    try:
        headers = {
            'apikey': SUPABASE_KEY,
            'Authorization': f'Bearer {SUPABASE_KEY}'
        }
        all_rows = []
        offset = 0
        page_size = 1000

        with st.spinner('Mengambil data dari Supabase...'):
            while True:
                url = (
                    f"{SUPABASE_URL}/rest/v1/ocr_labels"
                    f"?select=id,filename,label,class,updated_at,updated_by"
                    f"&verified=eq.true&order=id.asc&offset={offset}&limit={page_size}"
                )
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

        # -- DATA CLEANING DASAR --
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
# FEATURE ENGINEERING
# ============================================================================
def feature_engineering(df):
    """
    Melakukan feature engineering pada dataset untuk menghasilkan fitur-fitur
    yang lebih informatif bagi model machine learning.

    Returns:
        df_fe (DataFrame): DataFrame dengan fitur-fitur baru yang siap digunakan model.
    """
    df_fe = df.copy()

    # ---- 1. FITUR TEKS ----
    # Panjang karakter label (raw dan bersih)
    df_fe['feat_label_len']       = df_fe['label'].str.len()
    df_fe['feat_label_clean_len'] = df_fe['label_clean'].str.len()

    # Jumlah token/kata
    df_fe['feat_word_count'] = df_fe['label'].str.split().str.len().fillna(0).astype(int)

    # Jumlah digit dalam label
    df_fe['feat_digit_count'] = df_fe['label'].str.count(r'\d')

    # Jumlah huruf kapital
    df_fe['feat_upper_count'] = df_fe['label'].str.count(r'[A-Z]')

    # Rasio digit terhadap panjang label (0 jika label kosong)
    df_fe['feat_digit_ratio'] = np.where(
        df_fe['feat_label_len'] > 0,
        df_fe['feat_digit_count'] / df_fe['feat_label_len'],
        0
    )

    # Apakah label mengandung tanda titik dua (indikator format jam/tanggal)
    df_fe['feat_has_colon'] = df_fe['label'].str.contains(r':', na=False).astype(int)

    # Apakah label mengandung garis miring (indikasi tanggal DD/MM/YYYY)
    df_fe['feat_has_slash'] = df_fe['label'].str.contains(r'/', na=False).astype(int)

    # Apakah label mengandung simbol mata uang
    df_fe['feat_has_currency'] = df_fe['label'].str.contains(r'Rp|rp|IDR|\$', na=False, regex=True).astype(int)

    # Apakah ada tanda kurung (lazim pada keterangan diskon/satuan)
    df_fe['feat_has_brackets'] = df_fe['label'].str.contains(r'\(|\)', na=False).astype(int)

    # Apakah label murni angka setelah stripped non-digit
    numeric_stripped = df_fe['label'].str.replace(r'[^0-9]', '', regex=True)
    df_fe['feat_is_pure_numeric'] = (
        (numeric_stripped.str.len() > 0) & (numeric_stripped == df_fe['label'].str.replace(r'[^0-9]', '', regex=True))
    ).astype(int)

    # ---- 2. FITUR VALIDASI PER KELAS ----
    # Validasi format tanggal_waktu (minimal 8 karakter)
    df_fe['feat_valid_tanggal'] = np.where(
        df_fe['class'] == 'tanggal_waktu',
        (df_fe['feat_label_len'] >= 8).astype(int),
        np.nan
    )

    # Validasi total_belanja (harus mengandung minimal 1 digit)
    df_fe['feat_valid_total'] = np.where(
        df_fe['class'] == 'total_belanja',
        (df_fe['feat_digit_count'] > 0).astype(int),
        np.nan
    )

    # Validasi nama_toko (minimal 4 karakter)
    df_fe['feat_valid_toko'] = np.where(
        df_fe['class'] == 'nama_toko',
        (df_fe['feat_label_len'] >= 4).astype(int),
        np.nan
    )

    # Validasi line_item (minimal 3 karakter)
    df_fe['feat_valid_item'] = np.where(
        df_fe['class'] == 'line_item',
        (df_fe['feat_label_len'] >= 3).astype(int),
        np.nan
    )

    # ---- 3. FITUR TEMPORAL ----
    # Sesi waktu: pagi/siang/sore/malam
    def sesi_waktu(jam):
        if pd.isna(jam):
            return 'tidak_diketahui'
        jam = int(jam)
        if 5 <= jam < 12:
            return 'pagi'
        elif 12 <= jam < 17:
            return 'siang'
        elif 17 <= jam < 21:
            return 'sore'
        else:
            return 'malam'

    df_fe['feat_sesi_waktu'] = df_fe['jam'].apply(sesi_waktu)

    # Apakah transaksi terjadi di akhir pekan
    df_fe['feat_is_weekend'] = df_fe['hari'].isin(['Saturday', 'Sunday']).astype(int)

    # ---- 4. ENCODING KATEGORIKAL ----
    # Label Encoding untuk kolom 'class'
    class_map = {c: i for i, c in enumerate(sorted(df_fe['class'].unique()))}
    df_fe['feat_class_encoded'] = df_fe['class'].map(class_map)

    # Label Encoding untuk mata_uang
    currency_map = {c: i for i, c in enumerate(sorted(df_fe['mata_uang'].unique()))}
    df_fe['feat_currency_encoded'] = df_fe['mata_uang'].map(currency_map)

    # One-Hot Encoding untuk sesi_waktu
    sesi_dummies = pd.get_dummies(df_fe['feat_sesi_waktu'], prefix='feat_sesi')
    df_fe = pd.concat([df_fe, sesi_dummies], axis=1)

    # ---- 5. NILAI NUMERIK TOTAL BELANJA ----
    # Ekstrak nilai numerik dari label total_belanja
    df_fe['feat_numeric_value'] = df_fe['label'].str.replace(r'[^0-9]', '', regex=True)
    df_fe['feat_numeric_value'] = pd.to_numeric(df_fe['feat_numeric_value'], errors='coerce')

    return df_fe, class_map, currency_map


# ============================================================================
# CEK KESIAPAN DATA UNTUK MODEL
# ============================================================================
def check_model_readiness(df_fe):
    """
    Mengecek apakah fitur-fitur hasil feature engineering sudah siap
    diproses oleh model machine learning.

    Returns:
        report (dict): Laporan kesiapan data.
    """
    feature_cols = [c for c in df_fe.columns if c.startswith('feat_')]
    df_feat = df_fe[feature_cols]

    report = {}

    # Missing values
    missing = df_feat.isnull().sum()
    missing_pct = (missing / len(df_feat) * 100).round(2)
    report['missing'] = pd.DataFrame({'jumlah_null': missing, 'persen_null (%)': missing_pct})
    report['missing'] = report['missing'][report['missing']['jumlah_null'] > 0]

    # Data types
    report['dtypes'] = df_feat.dtypes.reset_index().rename(columns={'index': 'fitur', 0: 'tipe_data'})

    # Statistik deskriptif (numerik)
    num_cols = df_feat.select_dtypes(include=[np.number]).columns.tolist()
    report['stats'] = df_feat[num_cols].describe().T

    # Distribusi fitur kelas (target encoding check)
    report['class_dist'] = df_fe['feat_class_encoded'].value_counts().reset_index()
    report['class_dist'].columns = ['class_encoded', 'count']

    # Cek class imbalance
    counts = df_fe['feat_class_encoded'].value_counts()
    imbalance_ratio = counts.max() / counts.min() if counts.min() > 0 else np.inf
    report['imbalance_ratio'] = imbalance_ratio
    report['is_balanced'] = imbalance_ratio < 3

    return report, num_cols


# ============================================================================
# A/B TESTING
# ============================================================================
def run_ab_testing(df_fe):
    """
    Melakukan A/B Testing untuk membandingkan dua kelompok pada metrik kunci:
    - Grup A: label TANPA simbol mata uang
    - Grup B: label DENGAN simbol mata uang (IDR/USD)

    Pengujian: Two-sample t-test pada panjang label dan jumlah digit.
    """
    group_a = df_fe[df_fe['feat_has_currency'] == 0].copy()
    group_b = df_fe[df_fe['feat_has_currency'] == 1].copy()

    results = []

    for metric, col in [
        ("Panjang Label (feat_label_len)", "feat_label_len"),
        ("Jumlah Digit (feat_digit_count)", "feat_digit_count"),
        ("Rasio Digit (feat_digit_ratio)", "feat_digit_ratio"),
        ("Jumlah Kata (feat_word_count)", "feat_word_count"),
    ]:
        a_vals = group_a[col].dropna()
        b_vals = group_b[col].dropna()

        if len(a_vals) < 2 or len(b_vals) < 2:
            continue

        t_stat, p_val = stats.ttest_ind(a_vals, b_vals, equal_var=False)  # Welch's t-test
        mean_a = a_vals.mean()
        mean_b = b_vals.mean()
        std_a = a_vals.std()
        std_b = b_vals.std()

        # Effect size (Cohen's d)
        pooled_std = np.sqrt((std_a**2 + std_b**2) / 2)
        cohens_d = (mean_b - mean_a) / pooled_std if pooled_std > 0 else 0

        results.append({
            'Metrik': metric,
            'Mean Grup A (Tanpa Simbol)': round(mean_a, 3),
            'Mean Grup B (Dengan Simbol)': round(mean_b, 3),
            't-statistic': round(t_stat, 4),
            'p-value': round(p_val, 6),
            "Signifikan (α=0.05)": "✅ YA" if p_val < 0.05 else "❌ TIDAK",
            "Cohen's d": round(cohens_d, 3),
            "Ukuran Efek": (
                "Besar" if abs(cohens_d) >= 0.8 else
                "Sedang" if abs(cohens_d) >= 0.5 else
                "Kecil" if abs(cohens_d) >= 0.2 else
                "Sangat Kecil"
            )
        })

    return pd.DataFrame(results), group_a, group_b


# ============================================================================
# FUNGSI ANALISIS (EXISTING - TIDAK DIUBAH)
# ============================================================================
def get_error_analysis(df_raw):
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
    return error_analysis, df


def get_category_distribution(df):
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
    dup_label = df_raw.duplicated(subset=['label', 'class']).sum()
    dollar = df_raw['label'].str.contains(r'\$', na=False).sum()
    bracket = df_raw['label'].str.contains(r'\]|\[', na=False).sum()
    anomali = pd.DataFrame({
        'Jenis Anomali': ['Duplikat label+kelas', 'Mata uang USD', 'Karakter bracket'],
        'Jumlah': [dup_label, dollar, bracket],
        'Persen (%)': [dup_label / len(df_raw) * 100, dollar / len(df_raw) * 100, bracket / len(df_raw) * 100]
    })
    return anomali


def get_store_analysis(df):
    store_df = df[df['class'] == 'nama_toko'].copy().reset_index(drop=True)
    total_df = df[df['class'] == 'total_belanja'].copy().reset_index(drop=True)
    if len(store_df) > 0 and len(total_df) > 0:
        analysis_df = pd.DataFrame({'nama_toko': store_df['label'], 'total_belanja': total_df['label']})
        analysis_df['total_belanja'] = analysis_df['total_belanja'].astype(str).str.replace(r'[^0-9]', '', regex=True)
        analysis_df['total_belanja'] = pd.to_numeric(analysis_df['total_belanja'], errors='coerce')
        store_stats = analysis_df.groupby('nama_toko')['total_belanja'].mean().sort_values(ascending=False).head(10)
        return store_stats
    return pd.Series()


def get_keywords_analysis(df):
    line_items = df[df['class'] == 'line_item'].copy()
    if len(line_items) > 0:
        text = ' '.join(line_items['label'].astype(str).tolist()).lower()
        words = re.findall(r'\b[a-zA-Z]+\b', text)
        words = [word for word in words if len(word) > 2]
        common_words = Counter(words).most_common(15)
        return pd.DataFrame(common_words, columns=['kata', 'frekuensi'])
    return pd.DataFrame()


def get_temporal_analysis(df):
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
    return df['class'].value_counts()


# ============================================================================
# SMART INSIGHTS GENERATOR
# ============================================================================
def generate_smart_insights(df, df_raw):
    insights = {}

    if len(df) > 0:
        top_class = df['class'].value_counts().idxmax()
        top_class_pct = (df['class'].value_counts().max() / len(df)) * 100
        insights['overview'] = f"Dataset didominasi kelas <b>{top_class.upper()}</b> sebesar <b>{top_class_pct:.1f}%</b>. Total <b>{df['filename'].nunique()}</b> file unik telah diproses."
    else:
        insights['overview'] = "Tidak ada data untuk dianalisis."

    error_analysis, _ = get_error_analysis(df_raw)
    avg_error = error_analysis['error_rate (%)'].mean()
    worst_class = error_analysis.loc[error_analysis['error_rate (%)'].idxmax()]
    insights['accuracy'] = f"Rata-rata error rate OCR: <b>{avg_error:.2f}%</b>. Kelas <b>{worst_class['class'].upper()}</b> memiliki tingkat error tertinggi: <b>{worst_class['error_rate (%)']:.2f}%</b>."

    kategori_dist, total_items = get_category_distribution(df)
    if not kategori_dist.empty:
        top_cat = kategori_dist.iloc[0]
        insights['category'] = f"Kategori terbanyak: <b>{top_cat['kategori'].upper()}</b> (<b>{top_cat['persentase']:.1f}%</b>) dari <b>{total_items}</b> item."
    else:
        insights['category'] = "Data item belanja tidak mencukupi untuk analisis kategori."

    anomali = get_anomaly_analysis(df_raw)
    total_anomali = anomali['Jumlah'].sum()
    insights['anomaly'] = f"Total <b>{total_anomali}</b> anomali terdeteksi. Anomali terbanyak: <b>{anomali.loc[anomali['Jumlah'].idxmax()]['Jenis Anomali']}</b>."

    store_stats = get_store_analysis(df)
    if not store_stats.empty:
        insights['store'] = f"Toko dengan rata-rata belanja tertinggi: <b>{store_stats.index[0].upper()}</b>."
    else:
        insights['store'] = "Data toko atau total belanja tidak lengkap."

    jam_dist, hari_dist, _ = get_temporal_analysis(df)
    if not jam_dist.empty and not hari_dist.empty:
        peak_hour = jam_dist.idxmax()
        busiest_day = hari_dist.idxmax()
        insights['temporal'] = f"Waktu terpadat: pukul <b>{peak_hour}:00</b>. Hari tersibuk: <b>{busiest_day.upper()}</b>."
    else:
        insights['temporal'] = "Data waktu transaksi tidak tersedia."

    return insights


# ============================================================================
# DATA DICTIONARY
# ============================================================================
DATA_DICTIONARY = {
    "KOLOM ASLI (dari Supabase)": [
        {"Kolom": "id",           "Tipe": "integer",   "Deskripsi": "ID unik setiap record label OCR",                    "Contoh": "1, 2, 3"},
        {"Kolom": "filename",     "Tipe": "string",    "Deskripsi": "Nama file gambar struk yang di-OCR",                 "Contoh": "struk_001.jpg"},
        {"Kolom": "label",        "Tipe": "string",    "Deskripsi": "Teks hasil ekstraksi OCR dari gambar",               "Contoh": "Rp 25.000, ALFAMART, 12/05/2024"},
        {"Kolom": "class",        "Tipe": "string",    "Deskripsi": "Kelas/kategori label OCR",                           "Contoh": "total_belanja, nama_toko, line_item, tanggal_waktu"},
        {"Kolom": "updated_at",   "Tipe": "timestamp", "Deskripsi": "Waktu terakhir data diperbarui (UTC)",               "Contoh": "2024-05-12T08:30:00Z"},
        {"Kolom": "updated_by",   "Tipe": "string",    "Deskripsi": "Pengguna yang memperbarui data",                     "Contoh": "user_001"},
    ],
    "KOLOM HASIL CLEANING": [
        {"Kolom": "label_clean",  "Tipe": "string",  "Deskripsi": "Label setelah dibersihkan dari karakter khusus tidak relevan", "Contoh": "Rp 25000"},
        {"Kolom": "tanggal",      "Tipe": "date",    "Deskripsi": "Tanggal dari updated_at",                                     "Contoh": "2024-05-12"},
        {"Kolom": "jam",          "Tipe": "integer", "Deskripsi": "Jam (0–23) dari updated_at",                                  "Contoh": "8"},
        {"Kolom": "hari",         "Tipe": "string",  "Deskripsi": "Nama hari dari updated_at",                                   "Contoh": "Monday"},
        {"Kolom": "mata_uang",    "Tipe": "string",  "Deskripsi": "Deteksi mata uang dari teks label",                           "Contoh": "IDR (Rp), USD ($), Tidak Terdeteksi"},
    ],
    "FITUR TEKS (Feature Engineering)": [
        {"Kolom": "feat_label_len",       "Tipe": "integer", "Deskripsi": "Panjang karakter label mentah",                             "Contoh": "15"},
        {"Kolom": "feat_label_clean_len", "Tipe": "integer", "Deskripsi": "Panjang karakter label bersih",                            "Contoh": "12"},
        {"Kolom": "feat_word_count",      "Tipe": "integer", "Deskripsi": "Jumlah kata dalam label",                                  "Contoh": "3"},
        {"Kolom": "feat_digit_count",     "Tipe": "integer", "Deskripsi": "Jumlah karakter digit dalam label",                        "Contoh": "5"},
        {"Kolom": "feat_upper_count",     "Tipe": "integer", "Deskripsi": "Jumlah karakter kapital dalam label",                      "Contoh": "2"},
        {"Kolom": "feat_digit_ratio",     "Tipe": "float",   "Deskripsi": "Rasio digit terhadap panjang label (0–1)",                 "Contoh": "0.33"},
        {"Kolom": "feat_has_colon",       "Tipe": "int(0/1)","Deskripsi": "Flag: label mengandung ':' (indikator waktu/tanggal)",     "Contoh": "1"},
        {"Kolom": "feat_has_slash",       "Tipe": "int(0/1)","Deskripsi": "Flag: label mengandung '/' (indikator tanggal)",           "Contoh": "1"},
        {"Kolom": "feat_has_currency",    "Tipe": "int(0/1)","Deskripsi": "Flag: label mengandung simbol mata uang (Rp/IDR/$)",       "Contoh": "1"},
        {"Kolom": "feat_has_brackets",    "Tipe": "int(0/1)","Deskripsi": "Flag: label mengandung tanda kurung",                      "Contoh": "0"},
        {"Kolom": "feat_is_pure_numeric", "Tipe": "int(0/1)","Deskripsi": "Flag: label hanya berisi angka",                          "Contoh": "0"},
    ],
    "FITUR VALIDASI (Feature Engineering)": [
        {"Kolom": "feat_valid_tanggal", "Tipe": "float(0/1/NaN)", "Deskripsi": "Validitas format tanggal_waktu (len >= 8); NaN jika bukan kelas ini", "Contoh": "1.0"},
        {"Kolom": "feat_valid_total",   "Tipe": "float(0/1/NaN)", "Deskripsi": "Validitas total_belanja (ada digit); NaN jika bukan kelas ini",       "Contoh": "1.0"},
        {"Kolom": "feat_valid_toko",    "Tipe": "float(0/1/NaN)", "Deskripsi": "Validitas nama_toko (len >= 4); NaN jika bukan kelas ini",             "Contoh": "1.0"},
        {"Kolom": "feat_valid_item",    "Tipe": "float(0/1/NaN)", "Deskripsi": "Validitas line_item (len >= 3); NaN jika bukan kelas ini",             "Contoh": "1.0"},
    ],
    "FITUR TEMPORAL & ENCODING (Feature Engineering)": [
        {"Kolom": "feat_sesi_waktu",       "Tipe": "string",  "Deskripsi": "Sesi waktu input (pagi/siang/sore/malam/tidak_diketahui)",   "Contoh": "pagi"},
        {"Kolom": "feat_is_weekend",       "Tipe": "int(0/1)","Deskripsi": "Flag: transaksi pada akhir pekan",                           "Contoh": "0"},
        {"Kolom": "feat_class_encoded",    "Tipe": "integer", "Deskripsi": "Label Encoding untuk kolom 'class'",                         "Contoh": "0"},
        {"Kolom": "feat_currency_encoded", "Tipe": "integer", "Deskripsi": "Label Encoding untuk kolom 'mata_uang'",                     "Contoh": "1"},
        {"Kolom": "feat_sesi_*",           "Tipe": "int(0/1)","Deskripsi": "One-Hot Encoding sesi_waktu (feat_sesi_pagi, feat_sesi_siang, dst.)", "Contoh": "1"},
        {"Kolom": "feat_numeric_value",    "Tipe": "float",   "Deskripsi": "Nilai numerik hasil ekstraksi dari label (khusus total_belanja)", "Contoh": "25000.0"},
    ]
}


# ============================================================================
# MAIN DASHBOARD
# ============================================================================
def main():
    # Header
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
        st.error("Gagal memuat data. Periksa koneksi Supabase.")
        return

    # Feature Engineering
    df_fe, class_map, currency_map = feature_engineering(df)

    # Model Readiness
    readiness_report, numeric_feature_cols = check_model_readiness(df_fe)

    # Smart Insights
    insights = generate_smart_insights(df, df_raw)

    # Sidebar
    with st.sidebar:
        st.markdown("""
        <div style='background-color: #FFFFFF; border: 3px solid #000; padding: 15px; box-shadow: 4px 4px 0px #000; margin-bottom: 20px; text-align: center;'>
            <img src="https://img.icons8.com/color/96/000000/receipt.png" width="80">
            <h2 style='margin: 10px 0 0 0;'>NOTEPAY</h2>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("### 🔍 FILTER DATA")
        search_query = st.text_input("CARI LABEL / ITEM", "").strip().lower()

        valid_dates = df['tanggal'].dropna()
        if not valid_dates.empty:
            min_date, max_date = min(valid_dates), max(valid_dates)
            date_range = st.date_input("RENTANG TANGGAL", value=(min_date, max_date), min_value=min_date, max_value=max_date)
        else:
            date_range = None

        classes = df['class'].unique()
        selected_classes = st.multiselect("PILIH KELAS DATA", options=classes, default=classes.tolist())

        currencies = df['mata_uang'].unique()
        selected_currencies = st.multiselect("PILIH MATA UANG", options=currencies, default=currencies.tolist())

        # Apply Filters
        filtered_df = df.copy()
        filtered_fe = df_fe.copy()

        if search_query:
            mask = filtered_df['label'].str.lower().str.contains(search_query, na=False)
            filtered_df = filtered_df[mask]
            filtered_fe = filtered_fe[mask]

        if date_range and len(date_range) == 2:
            mask = (filtered_df['tanggal'] >= date_range[0]) & (filtered_df['tanggal'] <= date_range[1])
            filtered_df = filtered_df[mask]
            filtered_fe = filtered_fe[mask]

        filtered_df = filtered_df[filtered_df['class'].isin(selected_classes)]
        filtered_fe = filtered_fe[filtered_fe['class'].isin(selected_classes)]
        filtered_df = filtered_df[filtered_df['mata_uang'].isin(selected_currencies)]
        filtered_fe = filtered_fe[filtered_fe['mata_uang'].isin(selected_currencies)]

        st.markdown("---")
        st.metric("TOTAL DATA", f"{len(filtered_df):,}")
        st.metric("TERFILTER", f"{len(filtered_df):,}")

    # Tabs
    tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9 = st.tabs([
        "📈 OVERVIEW",
        "🎯 AKURASI OCR",
        "🛒 KATEGORI",
        "⚠️ ANOMALI",
        "🏪 TOKO",
        "⏰ WAKTU",
        "🔧 FEATURE ENG.",
        "🧪 A/B TESTING",
        "📚 DATA DICT."
    ])

    # ====================================================================
    # TAB 1 — OVERVIEW
    # ====================================================================
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
        with col1: st.metric("Total Records", f"{len(filtered_df):,}")
        with col2: st.metric("Unique Files", f"{filtered_df['filename'].nunique():,}")
        with col3: st.metric("Unique Labels", f"{filtered_df['label'].nunique():,}")
        with col4: st.metric("Unique Classes", f"{filtered_df['class'].nunique()}")

        st.markdown("---")
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
        for spine in ['top', 'right']: ax.spines[spine].set_visible(False)
        for spine in ['left', 'bottom']: ax.spines[spine].set_linewidth(2)
        for bar, val in zip(bars, class_dist.values):
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 5, str(val), ha='center', fontweight='black')
        st.pyplot(fig); plt.close()

        with st.expander("LIHAT SAMPLE DATA"):
            st.dataframe(filtered_df[['label', 'class', 'mata_uang']].head(100), use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # ====================================================================
    # TAB 2 — AKURASI OCR
    # ====================================================================
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
            for spine in ['top', 'right']: ax.spines[spine].set_visible(False)
            for bar, val in zip(bars, error_analysis['error_rate (%)']):
                ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.5, f'{val:.2f}%', ha='center', fontweight='black')
            ax.legend()
            st.pyplot(fig); plt.close()

        with col2:
            st.subheader("Insight & Rekomendasi")
            high_error = error_analysis[error_analysis['error_rate (%)'] > 20]
            if len(high_error) > 0:
                st.markdown("""<div style='background-color:#FF6B6B;padding:15px;border:3px solid #000;box-shadow:4px 4px 0px #000;'>
                    <h4 style='margin:0;color:white;'>⚠️ PERINGATAN!</h4>
                    <p style='color:white;font-weight:bold;'>Kelas dengan error rate > 20%:</p></div>""", unsafe_allow_html=True)
                for _, row in high_error.iterrows():
                    st.write(f"- **{row['class'].upper()}**: {row['error_rate (%)']:.2f}%")
            else:
                st.markdown("""<div style='background-color:#4ECDC4;padding:15px;border:3px solid #000;'>
                    <h4>✅ AMAN!</h4><p style='font-weight:bold;'>Semua kelas di bawah 20%.</p></div>""", unsafe_allow_html=True)

        st.markdown("---")
        st.subheader("Detail Analisis Error")
        if df_error is not None:
            error_detail = df_error[df_error['is_error']].groupby('class').size().reset_index(name='jumlah_error')
            st.dataframe(error_detail, use_container_width=True)
            st.markdown("""
            <div style='background-color:#FFD700;padding:10px;border:2px solid #000;margin-top:10px;'>
                <p style='margin:0;font-weight:800;'>📌 KETERANGAN ERROR:</p>
                <ul style='margin:5px 0 0 0;font-size:0.9rem;'>
                    <li><b>TANGGAL_WAKTU:</b> &lt; 8 karakter</li>
                    <li><b>TOTAL_BELANJA:</b> Tidak mengandung angka</li>
                    <li><b>NAMA_TOKO:</b> &lt; 4 karakter</li>
                    <li><b>LINE_ITEM:</b> &lt; 3 karakter</li>
                </ul>
            </div>""", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # ====================================================================
    # TAB 3 — KATEGORI
    # ====================================================================
    with tab3:
        st.markdown(f"""
        <div class='neo-container' style='background-color:#FFD700;border-style:dashed;'>
            <h3 style='margin:0;'>🧠 SMART INSIGHT</h3>
            <p style='margin:10px 0 0 0;font-weight:bold;'>{insights['category']}</p>
        </div>""", unsafe_allow_html=True)

        st.markdown("<div class='neo-container'>", unsafe_allow_html=True)
        st.header("🛒 Analisis Kategori Pengeluaran")
        kategori_dist, total_items = get_category_distribution(filtered_df)
        col1, col2 = st.columns(2)

        with col1:
            if len(kategori_dist) > 0:
                st.subheader(f"Distribusi Kategori (Total {total_items} items)")
                fig, ax = plt.subplots(figsize=(8, 5))
                colors = ['#FF6B6B' if p < 10 else '#4ECDC4' for p in kategori_dist['persentase']]
                bars = ax.bar(kategori_dist['kategori'], kategori_dist['persentase'], color=colors, edgecolor='black', linewidth=2)
                ax.axhline(10, linestyle='--', color='black', linewidth=2, label='Threshold 10%')
                ax.set_title('DISTRIBUSI KATEGORI PENGELUARAN', fontweight='black')
                ax.set_ylabel('PERSENTASE (%)', fontweight='bold')
                ax.tick_params(axis='x', rotation=45)
                for spine in ['top', 'right']: ax.spines[spine].set_visible(False)
                for bar, val in zip(bars, kategori_dist['persentase']):
                    ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.5, f'{val:.1f}%', ha='center', fontweight='black')
                ax.legend()
                st.pyplot(fig); plt.close()

        with col2:
            st.subheader("Rekomendasi Pengembangan")
            if not kategori_dist.empty:
                low_cat = kategori_dist[kategori_dist['persentase'] < 10]
                if len(low_cat) > 0:
                    st.markdown("""<div style='background-color:#FFD700;padding:15px;border:3px solid #000;'>
                        <h4>⚠️ PERHATIAN</h4><p style='font-weight:bold;'>Kategori < 10%:</p></div>""", unsafe_allow_html=True)
                    for _, row in low_cat.iterrows():
                        st.write(f"- **{row['kategori'].upper()}**: {row['persentase']:.1f}%")
                else:
                    st.success("✅ Semua kategori di atas 10%")
            else:
                st.info("ℹ️ Data line_item tidak ditemukan.")

        st.markdown("---")
        st.subheader("Top Kata Kunci pada Line Item")
        keywords_df = get_keywords_analysis(filtered_df)
        if len(keywords_df) > 0:
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.barh(keywords_df['kata'][:10], keywords_df['frekuensi'][:10], color='#4ECDC4', edgecolor='black', linewidth=2)
            ax.set_title('TOP 10 KATA KUNCI', fontweight='black')
            ax.invert_yaxis()
            st.pyplot(fig); plt.close()
        st.markdown("</div>", unsafe_allow_html=True)

    # ====================================================================
    # TAB 4 — ANOMALI
    # ====================================================================
    with tab4:
        st.markdown(f"""
        <div class='neo-container' style='background-color:#FFD700;border-style:dashed;'>
            <h3 style='margin:0;'>🧠 SMART INSIGHT</h3>
            <p style='margin:10px 0 0 0;font-weight:bold;'>{insights['anomaly']}</p>
        </div>""", unsafe_allow_html=True)

        st.markdown("<div class='neo-container'>", unsafe_allow_html=True)
        st.header("⚠️ Analisis Anomali Data")
        anomali = get_anomaly_analysis(df_raw)
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Frekuensi Anomali")
            fig, ax = plt.subplots(figsize=(8, 5))
            colors = ['#FF6B6B' if p >= 5 else '#A78BFA' for p in anomali['Persen (%)']]
            bars = ax.barh(anomali['Jenis Anomali'], anomali['Persen (%)'], color=colors, edgecolor='black', linewidth=2)
            ax.axvline(5, color='black', linestyle='--', linewidth=2, label='Threshold 5%')
            ax.set_title('FREKUENSI ANOMALI OCR', fontweight='black')
            ax.legend()
            for bar, pct in zip(bars, anomali['Persen (%)']):
                ax.text(bar.get_width() + 0.1, bar.get_y() + bar.get_height() / 2, f'{pct:.2f}%', va='center', fontweight='black')
            st.pyplot(fig); plt.close()

        with col2:
            st.subheader("Rekomendasi Penanganan")
            prio = anomali[anomali['Persen (%)'] >= 5]
            if len(prio) > 0:
                for _, row in prio.iterrows():
                    st.error(f"**{row['Jenis Anomali'].upper()}**: {row['Persen (%)']:.2f}%")
            else:
                st.success("✅ Semua anomali < 5%")

        st.markdown("---")
        st.subheader("Deteksi Outlier Total Belanja")
        total_df = filtered_df[filtered_df['class'] == 'total_belanja'].copy()
        if len(total_df) > 0:
            total_df['numeric_total'] = pd.to_numeric(total_df['label'].str.replace(r'[^0-9]', '', regex=True), errors='coerce')
            total_df = total_df.dropna(subset=['numeric_total'])
            if len(total_df) > 0:
                fig, ax = plt.subplots(figsize=(10, 4))
                box = ax.boxplot(total_df['numeric_total'], patch_artist=True)
                for patch in box['boxes']: patch.set_facecolor('#4ECDC4'); patch.set_edgecolor('black')
                ax.set_title('BOXPLOT TOTAL BELANJA', fontweight='black')
                st.pyplot(fig); plt.close()
                Q1, Q3 = total_df['numeric_total'].quantile(0.25), total_df['numeric_total'].quantile(0.75)
                IQR = Q3 - Q1
                outliers = total_df[(total_df['numeric_total'] < Q1 - 1.5 * IQR) | (total_df['numeric_total'] > Q3 + 1.5 * IQR)]
                st.metric("JUMLAH OUTLIER", f"{len(outliers)} data")
        st.markdown("</div>", unsafe_allow_html=True)

    # ====================================================================
    # TAB 5 — TOKO
    # ====================================================================
    with tab5:
        st.markdown(f"""
        <div class='neo-container' style='background-color:#FFD700;border-style:dashed;'>
            <h3 style='margin:0;'>🧠 SMART INSIGHT</h3>
            <p style='margin:10px 0 0 0;font-weight:bold;'>{insights['store']}</p>
        </div>""", unsafe_allow_html=True)

        st.markdown("<div class='neo-container'>", unsafe_allow_html=True)
        st.header("🏪 Analisis Nama Toko")
        store_stats = get_store_analysis(filtered_df)
        col1, col2 = st.columns([2, 1])

        with col1:
            if len(store_stats) > 0:
                st.subheader("Top 10 Toko - Rata-rata Belanja")
                fig, ax = plt.subplots(figsize=(10, 6))
                ax.barh(store_stats.index, store_stats.values, color='#A78BFA', edgecolor='black', linewidth=2)
                ax.set_title('RATA-RATA TOTAL BELANJA PER TOKO', fontweight='black')
                ax.invert_yaxis()
                for bar, val in zip(ax.patches, store_stats.values):
                    ax.text(bar.get_width() * 1.01, bar.get_y() + bar.get_height() / 2, f'Rp {val:,.0f}', va='center', fontsize=9)
                st.pyplot(fig); plt.close()

        with col2:
            st.subheader("Insight")
            if len(store_stats) >= 2:
                max_val, min_val = store_stats.iloc[0], store_stats.iloc[-1]
                diff_pct = ((max_val - min_val) / min_val) * 100
                st.metric("TOKO TERTINGGI", store_stats.index[0], f"Rp {max_val:,.0f}")
                st.metric("TOKO TERENDAH", store_stats.index[-1], f"Rp {min_val:,.0f}")
                st.metric("SELISIH", f"{diff_pct:.1f}%")
        st.markdown("</div>", unsafe_allow_html=True)

    # ====================================================================
    # TAB 6 — WAKTU
    # ====================================================================
    with tab6:
        st.markdown(f"""
        <div class='neo-container' style='background-color:#FFD700;border-style:dashed;'>
            <h3 style='margin:0;'>🧠 SMART INSIGHT</h3>
            <p style='margin:10px 0 0 0;font-weight:bold;'>{insights['temporal']}</p>
        </div>""", unsafe_allow_html=True)

        st.markdown("<div class='neo-container'>", unsafe_allow_html=True)
        st.header("⏰ Pola Waktu Transaksi")
        jam_dist, hari_dist, total_transaksi = get_temporal_analysis(filtered_df)
        col1, col2 = st.columns(2)

        with col1:
            if len(jam_dist) > 0:
                st.subheader("Distribusi Jam")
                fig, ax = plt.subplots(figsize=(10, 5))
                ax.plot(jam_dist.index, jam_dist.values, marker='o', linewidth=4, color='#000', markerfacecolor='#FF6B6B', markersize=8)
                ax.fill_between(jam_dist.index, jam_dist.values, alpha=0.5, color='#4ECDC4')
                ax.set_title('DISTRIBUSI JAM TRANSAKSI', fontweight='black')
                st.pyplot(fig); plt.close()

        with col2:
            if len(hari_dist) > 0:
                st.subheader("Distribusi Hari")
                fig, ax = plt.subplots(figsize=(8, 5))
                days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
                hari_dist = hari_dist.reindex([d for d in days_order if d in hari_dist.index])
                ax.bar(hari_dist.index, hari_dist.values, color='#FFD700', edgecolor='black', linewidth=2)
                ax.tick_params(axis='x', rotation=45)
                ax.set_title('DISTRIBUSI HARI TRANSAKSI', fontweight='black')
                st.pyplot(fig); plt.close()

        st.markdown("</div>", unsafe_allow_html=True)

    # ====================================================================
    # TAB 7 — FEATURE ENGINEERING
    # ====================================================================
    with tab7:
        st.markdown("<div class='neo-container'>", unsafe_allow_html=True)
        st.header("🔧 Feature Engineering & Model Readiness")

        st.markdown("""
        <div style='background-color:#A78BFA;padding:1rem;border:3px solid #000;box-shadow:4px 4px 0px #000;margin-bottom:1rem;'>
            <h4 style='margin:0;color:white;'>📌 Deskripsi Proses</h4>
            <p style='color:white;font-weight:bold;margin:8px 0 0 0;'>
            Feature engineering dilakukan untuk menghasilkan representasi numerik yang lebih informatif dari teks OCR,
            sehingga model ML dapat membedakan kelas label secara lebih akurat.
            </p>
        </div>
        """, unsafe_allow_html=True)

        # Tampilkan sample fitur hasil
        feat_cols_display = [c for c in filtered_fe.columns if c.startswith('feat_') and 'sesi_' not in c]
        st.subheader("📋 Sample Fitur Hasil Feature Engineering")
        st.dataframe(
            filtered_fe[['label', 'class'] + feat_cols_display[:10]].head(50),
            use_container_width=True
        )

        st.markdown("---")
        st.subheader("📊 Statistik Fitur Numerik")
        num_feat_cols = [c for c in filtered_fe.columns if c.startswith('feat_') and filtered_fe[c].dtype in [np.float64, np.int64]]
        if num_feat_cols:
            st.dataframe(filtered_fe[num_feat_cols].describe().T.style.format("{:.3f}"), use_container_width=True)

        st.markdown("---")
        st.subheader("🚦 Laporan Kesiapan Data untuk Model")

        col1, col2, col3 = st.columns(3)
        total_feat = len([c for c in df_fe.columns if c.startswith('feat_')])
        with col1: st.metric("TOTAL FITUR DIHASILKAN", f"{total_feat}")
        with col2: st.metric("FITUR NUMERIK SIAP", f"{len(num_feat_cols)}")
        imbalance = readiness_report.get('imbalance_ratio', 0)
        with col3: st.metric("CLASS IMBALANCE RATIO", f"{imbalance:.2f}x", delta="✅ Seimbang" if imbalance < 3 else "⚠️ Imbalanced")

        st.markdown("---")
        if not readiness_report['missing'].empty:
            st.subheader("⚠️ Fitur dengan Missing Values")
            st.dataframe(readiness_report['missing'], use_container_width=True)
            st.info("💡 Fitur validasi (feat_valid_*) ber-NaN secara by-design karena hanya berlaku untuk kelas tertentu. Isi dengan 0 atau -1 saat training model.")
        else:
            st.success("✅ Tidak ada missing values pada fitur numerik utama!")

        st.markdown("---")
        st.subheader("📈 Distribusi Fitur Kunci per Kelas")
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        fig.patch.set_facecolor('#F3F4F6')
        key_feats = ['feat_label_len', 'feat_digit_count', 'feat_digit_ratio', 'feat_word_count']
        for ax, feat in zip(axes.flat, key_feats):
            if feat in filtered_fe.columns:
                for cls in filtered_fe['class'].unique():
                    vals = filtered_fe[filtered_fe['class'] == cls][feat].dropna()
                    if len(vals) > 1:
                        ax.hist(vals, bins=20, alpha=0.5, label=cls, edgecolor='black', linewidth=0.5)
                ax.set_title(feat.upper(), fontweight='black')
                ax.legend(fontsize=7)
                ax.spines['top'].set_visible(False)
                ax.spines['right'].set_visible(False)
        plt.tight_layout()
        st.pyplot(fig); plt.close()
        st.markdown("</div>", unsafe_allow_html=True)

    # ====================================================================
    # TAB 8 — A/B TESTING
    # ====================================================================
    with tab8:
        st.markdown("<div class='neo-container'>", unsafe_allow_html=True)
        st.header("🧪 A/B Testing")

        st.markdown("""
        <div style='background-color:#FFD700;padding:1rem;border:3px solid #000;box-shadow:4px 4px 0px #000;margin-bottom:1rem;'>
            <h4 style='margin:0;'>📌 Hipotesis Pengujian</h4>
            <p style='font-weight:bold;margin:8px 0 0 0;'>
            <b>Grup A</b>: Label OCR <u>TANPA</u> simbol mata uang (Rp/IDR/$)<br>
            <b>Grup B</b>: Label OCR <u>DENGAN</u> simbol mata uang<br><br>
            <b>H₀</b>: Tidak ada perbedaan signifikan antara Grup A dan Grup B.<br>
            <b>H₁</b>: Terdapat perbedaan signifikan pada metrik teks (panjang, digit, dll.).<br><br>
            Metode: <b>Welch's Two-Sample t-test</b> (α = 0.05) + <b>Cohen's d</b> untuk ukuran efek.
            </p>
        </div>
        """, unsafe_allow_html=True)

        ab_results, group_a, group_b = run_ab_testing(filtered_fe)

        col1, col2, col3 = st.columns(3)
        with col1: st.metric("UKURAN GRUP A (Tanpa Simbol)", f"{len(group_a):,}")
        with col2: st.metric("UKURAN GRUP B (Dengan Simbol)", f"{len(group_b):,}")
        with col3:
            sig_count = (ab_results["Signifikan (α=0.05)"] == "✅ YA").sum() if not ab_results.empty else 0
            st.metric("METRIK SIGNIFIKAN", f"{sig_count} / {len(ab_results)}")

        st.markdown("---")
        st.subheader("📊 Hasil Uji Statistik")
        if not ab_results.empty:
            st.dataframe(ab_results.style.applymap(
                lambda v: 'background-color: #d4edda' if v == '✅ YA' else ('background-color: #f8d7da' if v == '❌ TIDAK' else ''),
                subset=["Signifikan (α=0.05)"]
            ), use_container_width=True)
        else:
            st.warning("Data tidak cukup untuk A/B Testing.")

        st.markdown("---")
        st.subheader("📈 Visualisasi Distribusi per Grup")

        viz_metrics = ['feat_label_len', 'feat_digit_count', 'feat_digit_ratio', 'feat_word_count']
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        fig.patch.set_facecolor('#F3F4F6')

        for ax, metric in zip(axes.flat, viz_metrics):
            a_vals = group_a[metric].dropna()
            b_vals = group_b[metric].dropna()
            ax.hist(a_vals, bins=25, alpha=0.6, color='#4ECDC4', label='Grup A (Tanpa Simbol)', edgecolor='black', linewidth=0.5)
            ax.hist(b_vals, bins=25, alpha=0.6, color='#FF6B6B', label='Grup B (Dengan Simbol)', edgecolor='black', linewidth=0.5)
            ax.axvline(a_vals.mean(), color='#4ECDC4', linestyle='--', linewidth=2)
            ax.axvline(b_vals.mean(), color='#FF6B6B', linestyle='--', linewidth=2)
            ax.set_title(metric.upper(), fontweight='black')
            ax.legend(fontsize=8)
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)

        plt.tight_layout()
        st.pyplot(fig); plt.close()

        st.markdown("---")
        st.subheader("🔍 Interpretasi Hasil")
        if not ab_results.empty:
            sig_rows = ab_results[ab_results["Signifikan (α=0.05)"] == "✅ YA"]
            if len(sig_rows) > 0:
                st.markdown("""
                <div style='background-color:#FF6B6B;padding:1rem;border:3px solid #000;box-shadow:4px 4px 0px #000;'>
                    <h4 style='color:white;'>⚠️ H₀ DITOLAK pada metrik berikut:</h4>
                """, unsafe_allow_html=True)
                for _, row in sig_rows.iterrows():
                    cohens_val = row["Cohen's d"]
                    st.write(f"- **{row['Metrik']}** — p={row['p-value']}, Cohen's d={cohens_val} ({row['Ukuran Efek']})")
                st.markdown("""
                    <p style='color:white;font-weight:bold;margin-top:10px;'>
                    📌 Artinya: label berformat mata uang (IDR/Rp/$) memiliki karakteristik teks yang BERBEDA SIGNIFIKAN
                    dibanding label tanpa simbol. Fitur ini penting dan informatif untuk model klasifikasi.
                    </p>
                </div>""", unsafe_allow_html=True)
            else:
                st.success("✅ H₀ GAGAL DITOLAK — Tidak ada perbedaan signifikan pada semua metrik.")
        st.markdown("</div>", unsafe_allow_html=True)

    # ====================================================================
    # TAB 9 — DATA DICTIONARY
    # ====================================================================
    with tab9:
        st.markdown("<div class='neo-container'>", unsafe_allow_html=True)
        st.header("📚 Data Dictionary")

        st.markdown("""
        <div style='background-color:#4ECDC4;padding:1rem;border:3px solid #000;box-shadow:4px 4px 0px #000;margin-bottom:1.5rem;'>
            <h4 style='margin:0;'>📌 Tentang Data Dictionary</h4>
            <p style='font-weight:bold;margin-top:8px;'>
            Dokumen ini mendeskripsikan seluruh kolom dan fitur dalam pipeline data NotePay OCR,
            mencakup kolom asli dari Supabase, kolom hasil cleaning, hingga fitur-fitur hasil
            feature engineering yang digunakan untuk pelatihan model ML.
            </p>
        </div>
        """, unsafe_allow_html=True)

        for section, entries in DATA_DICTIONARY.items():
            st.subheader(f"📂 {section}")
            df_dict = pd.DataFrame(entries)
            st.dataframe(df_dict, use_container_width=True)
            st.markdown("<br>", unsafe_allow_html=True)

        st.markdown("---")

        st.markdown("</div>", unsafe_allow_html=True)

    # Footer
    st.markdown("""
    <div style='text-align:center;padding:2rem;background-color:#000;color:#FFF;border:4px solid #FFD700;box-shadow:0px -10px 0px #FFD700;'>
        <h3 style='color:#FFD700;margin:0;'>© 2026 NOTEPAY | CC26-PSU410</h3>
        <p style='margin:10px 0 0 0;font-weight:bold;'>POWERED BY STREAMLIT & SUPABASE</p>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
