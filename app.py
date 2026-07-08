import streamlit as st
import pandas as pd
import datetime
from PIL import Image
import time
import gspread
from google.oauth2.service_account import Credentials
import json

# --- 1. KONFIGURASI HALAMAN ---
st.set_page_config(page_title="018studio OS", page_icon="💎", layout="wide", initial_sidebar_state="expanded")

# --- 2. CSS KELAS DUNIA ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght=400;500;600;700;800;900&display=swap');
    html, body, .stApp { font-family: 'Montserrat', sans-serif !important; background-color: #f8fafc !important; }
    h1, h2, h3 { color: #0f172a !important; font-weight: 900 !important; letter-spacing: -0.5px; }
    p, span, div { color: #334155 !important; font-size: 16px; }
    label p { font-weight: 700 !important; color: #1e293b !important; margin-bottom: 8px !important; }
    div[data-testid="metric-container"] { background-color: #ffffff !important; border: 1px solid #e2e8f0 !important; padding: 24px 20px !important; border-radius: 12px !important; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05) !important; transition: all 0.3s ease !important; }
    div[data-testid="metric-container"]:hover { border-color: #ff512f !important; transform: translateY(-5px); box-shadow: 0 12px 25px -5px rgba(255,81,47,0.15) !important; }
    div[data-testid="stMetricValue"] { font-size: 2.8rem !important; font-weight: 900 !important; color: #000000 !important; }
    div[data-testid="stMetricDelta"] svg { fill: #ff512f !important; }
    input, select, textarea, div[data-baseweb="select"] { background-color: #ffffff !important; color: #000000 !important; font-weight: 600 !important; font-size: 16px !important; border: 2px solid #cbd5e1 !important; border-radius: 8px !important; padding: 0.2rem !important; transition: all 0.3s ease; }
    input:focus, div[data-baseweb="select"]:focus-within { border: 2px solid #ff512f !important; box-shadow: 0 0 0 3px rgba(255,81,47,0.1) !important; }
    .stButton>button { background: #0f172a !important; color: #ffffff !important; border-radius: 8px !important; border: none !important; font-size: 16px !important; font-weight: 800 !important; padding: 1rem 2rem !important; text-transform: uppercase; letter-spacing: 1px; transition: all 0.4s ease !important; }
    .stButton>button:hover { background: linear-gradient(135deg, #ff512f 0%, #dd2476 100%) !important; transform: translateY(-2px); box-shadow: 0 8px 20px rgba(255,81,47,0.3) !important; color: #ffffff !important; }
    #MainMenu {visibility: hidden;} footer {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# --- 3. MESIN DATABASE GOOGLE SHEETS (DENGAN SENSOR CLOUD) ---
@st.cache_data(ttl=10) 
def tarik_data_gudang():
    try:
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        
        # SENSOR: Kalau di awan (Streamlit Cloud), pakai jalur rahasia
        if "google_kunci" in st.secrets:
            kunci_dict = json.loads(st.secrets["google_kunci"])
            creds = Credentials.from_service_account_info(kunci_dict, scopes=scopes)
        # SENSOR: Kalau di laptop, pakai file JSON biasa
        else:
            creds = Credentials.from_service_account_file("kunci.json", scopes=scopes)
            
        client = gspread.authorize(creds)
        gsheet = client.open("DATABASE STOCK")
        tab_stok = gsheet.worksheet("stok_ready")
        
        data = tab_stok.get_all_records()
        return pd.DataFrame(data), True, client
    except Exception as e:
        return pd.DataFrame(), False, str(e)

df_stok, koneksi_sukses, client_atau_error = tarik_data_gudang()

# --- 4. PANEL SAMPING (SIDEBAR) ---
with st.sidebar:
    try:
        st.image(Image.open("logo 018.jpeg"), use_container_width=True)
    except:
        st.markdown("<h1 style='text-align: center; color: #000; font-weight: 900;'>018<br>STUDIO</h1>", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    menu = st.radio("MAIN NAVIGATION", ["📊 Executive Dashboard", "💳 Point of Sales (POS)", "⚙️ Production Pipeline"])
    st.divider()
    if koneksi_sukses:
        st.caption("🟢 G-Sheets: Connected")
    else:
        st.caption("🔴 G-Sheets: Disconnected")

if not koneksi_sukses:
    st.error(f"⚠️ Gagal nyambung ke Google Sheets. Error: {client_atau_error}")
    st.stop() 

# ==========================================
# MENU 1: EXECUTIVE DASHBOARD
# ==========================================
if menu == "📊 Executive Dashboard":
    st.markdown("<h1 style='text-transform: uppercase;'>Executive Dashboard</h1>", unsafe_allow_html=True)
    st.markdown("<p>Monitor pergerakan aset dan sirkulasi gudang 018studio secara *real-time*.</p>", unsafe_allow_html=True)
    
    total_sku = len(df_stok)
    stok_kritis = len(df_stok[df_stok['Stok Tersedia'] < 3]) if 'Stok Tersedia' in df_stok.columns else 0
    stok_kosong = len(df_stok[df_stok['Stok Tersedia'] == 0]) if 'Stok Tersedia' in df_stok.columns else 0
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(label="Total SKU Aktif", value=total_sku)
    with col2:
        st.metric(label="Stok Kritis", value=stok_kritis, delta="- Butuh Press", delta_color="inverse")
    with col3:
        st.metric(label="Aset Kosong", value=stok_kosong, delta="Sold Out", delta_color="inverse")
    with col4:
        st.metric(label="Status Server", value="Live", delta="Online")
        
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    st.markdown("<h3>📦 LIVE INVENTORY STATUS</h3>", unsafe_allow_html=True)
    st.dataframe(
        df_stok,
        column_config={
            "Stok Tersedia": st.column_config.ProgressColumn("Kapasitas Fisik", format="%d unit", min_value=0, max_value=30),
            "Harga Retail (Rp)": st.column_config.NumberColumn("Harga Retail", format="Rp %d")
        }, hide_index=True, use_container_width=True
    )

# ==========================================
# MENU 2: POS / KASIR (DENGAN SECURITY PIN)
# ==========================================
elif menu == "💳 Point of Sales (POS)":
    st.markdown("<h1 style='text-transform: uppercase;'>TERMINAL TRANSAKSI</h1>", unsafe_allow_html=True)
    st.markdown("<p>Otorisasi pergerakan barang dan kalkulasi otomatis ke Google Sheets.</p>", unsafe_allow_html=True)
    
    with st.container():
        st.markdown("<h3 style='margin-bottom: 20px;'>📝 Otorisasi Data Keluar</h3>", unsafe_allow_html=True)
        with st.form("form_transaksi", clear_on_submit=True):
            c1, c2 = st.columns(2)
            
            with c1:
                sku_pilihan = st.selectbox("Pilih Artikel Terjual:", df_stok['Artikel'].tolist())
                kanal = st.selectbox("Kanal Distribusi:", ["In-Store / Walk-in Customer", "Social Commerce (Instagram)"])
                nama_pembeli = st.text_input("Identitas Klien (Opsional):", placeholder="Misal: Budi / @klien018")
            with c2:
                qty = st.number_input("Kuantitas (Unit):", min_value=1, value=1)
                diskon = st.number_input("Potongan Diskon (Rp):", min_value=0, value=0, step=5000)
                pin_kasir = st.text_input("🔑 Masukkan PIN Otorisasi:", type="password", placeholder="***")
                
            submitted = st.form_submit_button("AUTHORIZE TRANSACTION", use_container_width=True)
            
            if submitted:
                if pin_kasir != "018":
                    st.error("❌ Otorisasi Ditolak! PIN yang Anda masukkan salah.")
                else:
                    harga_asli = int(df_stok.loc[df_stok['Artikel'] == sku_pilihan, 'Harga Retail (Rp)'].values[0])
                    sku_kode = str(df_stok.loc[df_stok['Artikel'] == sku_pilihan, 'SKU'].values[0])
                    stok_lama = int(df_stok.loc[df_stok['Artikel'] == sku_pilihan, 'Stok Tersedia'].values[0])
                    
                    sub_total = harga_asli * qty
                    total_akhir = sub_total - diskon
                    waktu_skrg = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    
                    if qty > stok_lama:
                        st.error(f"❌ Otorisasi Ditolak! Stok di gudang hanya tersisa {stok_lama} unit.")
                    else:
                        with st.spinner('Mengirim instruksi ke Google Sheets...'):
                            try:
                                gsheet = client_atau_error.open("DATABASE STOCK")
                                tab_log = gsheet.worksheet("log_penjualan")
                                tab_stok = gsheet.worksheet("stok_ready")
                                
                                tab_log.append_row([waktu_skrg, sku_kode, sku_pilihan, kanal, nama_pembeli, qty, diskon, total_akhir])
                                
                                cell_pencarian = tab_stok.find(sku_kode)
                                tab_stok.update_cell(cell_pencarian.row, 3, stok_lama - qty)
                                
                                st.cache_data.clear()
                                
                                st.toast(f"✅ Data terkirim ke awan!", icon="🚀")
                                st.success("Akses Diberikan. Gudang G-Sheets 018studio telah disesuaikan.")
                                st.info(f"**STRUK VIRTUAL:**\n* {qty}x {sku_pilihan} (Rp {harga_asli:,})\n* Sub-total: Rp {sub_total:,}\n* Diskon: - Rp {diskon:,}\n* **Total: Rp {total_akhir:,}**")
                            except Exception as e:
                                st.error(f"❌ Sistem Gagal: {e}")

# ==========================================
# MENU 3: PRODUCTION PIPELINE (LIVE REVISI)
# ==========================================
elif menu == "⚙️ Production Pipeline":
    st.markdown("<h1 style='text-transform: uppercase;'>PRODUCTION PIPELINE</h1>", unsafe_allow_html=True)
    st.markdown("<p>Pusat kendali fase produksi pesanan kustom.</p>", unsafe_allow_html=True)
    
    # Menarik data produksi terbaru
    try:
        gsheet = client_atau_error.open("DATABASE STOCK")
        tab_prod = gsheet.worksheet("data_produksi")
        df_prod = pd.DataFrame(tab_prod.get_all_records())
    except:
        df_prod = pd.DataFrame()
    
    # FORM 1: TAMBAH PROYEK BARU
    with st.expander("➕ TAMBAH PROYEK BARU", expanded=False):
        with st.form("form_produksi"):
            n_proyek = st.text_input("Nama Proyek/Klien:")
            n_jumlah = st.number_input("Jumlah (Unit):", min_value=1)
            fase = st.selectbox("Fase Sekarang:", ["🔴 Design & Approval", "🟡 Sublimation & Press", "🟢 Assembly & QC"])
            deadline = st.date_input("Deadline:")
            submit_proyek = st.form_submit_button("MASUKKAN KE PIPELINE")
            
            if submit_proyek:
                if n_proyek == "":
                    st.error("Nama proyek tidak boleh kosong!")
                else:
                    with st.spinner('Menambah proyek...'):
                        try:
                            tab_prod.append_row([n_proyek, n_jumlah, fase, str(deadline), "Aktif"])
                            st.success("Proyek berhasil ditambah!")
                            st.cache_data.clear()
                            st.rerun()
                        except Exception as e:
                            st.error(f"Gagal menyimpan. Error: {e}")

    # FORM 2: UPDATE FASE PROYEK (OTOMATIS BERPINDAH WARNA)
    if not df_prod.empty:
        with st.expander("🔄 UPDATE FASE PROYEK AKTIF", expanded=False):
            with st.form("form_update_produksi"):
                proyek_pilihan = st.selectbox("Pilih Proyek yang Akan Di-update:", df_prod['Nama Proyek'].tolist())
                fase_baru = st.selectbox("Ubah Ke Fase Baru:", ["🔴 Design & Approval", "🟡 Sublimation & Press", "🟢 Assembly & QC"])
                submit_update = st.form_submit_button("PERBARUI FASE PROYEK")
                
                if submit_update:
                    with st.spinner('Mengupdate status proyek di awan...'):
                        try:
                            cell = tab_prod.find(proyek_pilihan)
                            tab_prod.update_cell(cell.row, 3, fase_baru) # Update kolom ke-3 (Fase)
                            st.success(f"Berhasil! {proyek_pilihan} sekarang berada di fase {fase_baru}.")
                            st.cache_data.clear()
                            st.rerun()
                        except Exception as e:
                            st.error(f"Gagal mengupdate. Error: {e}")

    # TAMPILAN MONITORING UTAMA (KANBAN BOARD 3 KOLOM WARNA)
    st.markdown("---")
    st.subheader("📋 KANBAN BOARD PRODUCTION STATUS")
    
    if not df_prod.empty:
        # Bikin tata letak 3 kolom sejajar (Kiri, Tengah, Kanan)
        col_merah, col_kuning, col_hijau = st.columns(3)
        
        with col_merah:
            st.markdown("<h4 style='color: #ef4444; font-weight:800; text-align:center;'>🔴 DESIGN & APPROVAL</h4>", unsafe_allow_html=True)
            df_red = df_prod[df_prod['Fase'] == "🔴 Design & Approval"]
            if not df_red.empty:
                st.dataframe(df_red[['Nama Proyek', 'Jumlah', 'Deadline']], hide_index=True, use_container_width=True)
            else:
                st.info("Tidak ada antrean desain.")
                
        with col_kuning:
            st.markdown("<h4 style='color: #eab308; font-weight:800; text-align:center;'>🟡 SUBLIMATION & PRESS</h4>", unsafe_allow_html=True)
            df_yellow = df_prod[df_prod['Fase'] == "🟡 Sublimation & Press"]
            if not df_yellow.empty:
                st.dataframe(df_yellow[['Nama Proyek', 'Jumlah', 'Deadline']], hide_index=True, use_container_width=True)
            else:
                st.info("Mesin produksi sedang santai.")
                
        with col_hijau:
            st.markdown("<h4 style='color: #22c55e; font-weight:800; text-align:center;'>🟢 ASSEMBLY & QC</h4>", unsafe_allow_html=True)
            df_green = df_prod[df_prod['Fase'] == "🟢 Assembly & QC"]
            if not df_green.empty:
                st.dataframe(df_green[['Nama Proyek', 'Jumlah', 'Deadline']], hide_index=True, use_container_width=True)
            else:
                st.info("Belum ada barang di meja QC.")
    else:
        st.warning("⚠️ Tab 'data_produksi' kosong atau belum terdeteksi di Google Sheets.")
