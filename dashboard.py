# ======================================================================
# NAVIFITG - STREAMLIT DASHBOARD v1.0 (Handal & Real-time)
# Dijalankan di Streamlit Community Cloud, membaca data dari Firebase
# ======================================================================

import streamlit as st
import pandas as pd
import pyrebase
from datetime import datetime
import time

# --- 1. Konfigurasi Halaman & Koneksi Firebase ---

# Mengatur konfigurasi dasar halaman agar terlihat profesional
st.set_page_config(
    page_title="Dashboard Pemantauan NaviFitG",
    page_icon="🏃‍♀️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Mengambil kredensial dari Streamlit Secrets (lebih aman)
try:
    firebase_config = st.secrets["firebase_config"]
    firebase = pyrebase.initialize_app(firebase_config)
    db = firebase.database()
except Exception:
    st.error("Konfigurasi Firebase tidak ditemukan atau salah di Streamlit Secrets. Harap atur terlebih dahulu.", icon="🔥")
    st.stop() # Menghentikan eksekusi jika koneksi gagal

# --- 2. Fungsi Pengambilan Data ---

# Menggunakan cache agar tidak terlalu sering memanggil Firebase
# TTL (Time To Live) = 2 detik. Data akan diambil ulang setiap 2 detik.
@st.cache_data(ttl=2)
def get_live_data():
    """Mengambil data terbaru dari node 'live_data' di Firebase Realtime Database."""
    try:
        # Mengambil data dari path "live_data"
        data = db.child("live_data").get().val()
        return data if data else {}
    except Exception as e:
        # Menampilkan pesan sementara jika ada gangguan
        st.toast(f"Gagal mengambil data: {e}", icon="⚠️")
        return {}

# --- 3. Tampilan Antarmuka (UI) Dashboard ---

# Judul Utama
st.title("🏃‍♀️ Dashboard Pemantauan NaviFitG")

# Ambil data terbaru
data = get_live_data()

# Tampilkan timestamp terakhir data diterima
if data and 'last_update' in data:
    last_update_time = datetime.fromisoformat(data['last_update']).strftime('%d %B %Y, %H:%M:%S WIB')
    st.markdown(f"**Data terakhir diterima pada:** `{last_update_time}`")
else:
    st.warning("Menunggu data pertama dari perangkat NaviFitG...", icon="📡")
    st.stop() # Hentikan jika belum ada data sama sekali

# Membuat layout dengan 3 kolom utama
col1, col2, col3 = st.columns([1, 1.5, 1])

# --- Kolom 1: Status Kritis (Jarak & Kesehatan) ---
with col1:
    st.subheader("⚠️ Status Kritis")
    
    # Menampilkan jarak rintangan dengan status berwarna
    dist = data.get('distance_m')
    if dist is not None:
        dist_text = f"{dist:.2f} m"
        if dist < 0.5:
            st.error(f"**BAHAYA!** Rintangan sangat dekat: {dist_text}", icon="🚨")
        elif dist < 1.5:
            st.warning(f"**AWAS!** Rintangan di depan: {dist_text}", icon="⚠️")
        else:
            st.success(f"Aman: {dist_text}", icon="✅")
    else:
        st.info("Sensor jarak tidak mengirim data.", icon="❓")
    
    # Menampilkan metrik detak jantung dan SpO2
    hr_data = data.get('hr', {})
    bpm = hr_data.get('bpm')
    spo2 = hr_data.get('spo2')
    
    bpm_text = f"{int(bpm)}" if bpm is not None else "N/A"
    spo2_text = f"{int(spo2)}%" if spo2 is not None else "N/A"
    
    st.metric("Detak Jantung (BPM)", bpm_text)
    st.metric("Saturasi Oksigen (SpO2)", spo2_text)

# --- Kolom 2: Peta Lokasi & Tampilan Kamera ---
with col2:
    st.subheader("📍 Lokasi & Tampilan Lingkungan")
    
    # Menampilkan peta lokasi pengguna
    gps_data = data.get('gps', {})
    if gps_data.get('valid') and gps_data.get('lat') is not None and gps_data.get('lon') is not None:
        location_df = pd.DataFrame({'lat': [gps_data['lat']], 'lon': [gps_data['lon']]})
        st.map(location_df, zoom=16)
    else:
        st.info("Mencari sinyal GPS...", icon="🛰️")
        
    # Menampilkan gambar dari URL yang ada di Firebase
    image_url = data.get('yolo', {}).get('image_url')
    if image_url:
        st.image(image_url, caption="Tampilan dari perangkat (diperbarui secara periodik)", use_column_width=True)
    else:
        st.info("Menunggu gambar dari perangkat...", icon="📸")

# --- Kolom 3: Informasi Tambahan ---
with col3:
    st.subheader("🔍 Informasi Tambahan")
    
    # Menampilkan objek yang terdeteksi YOLO
    detections = data.get('yolo', {}).get('detections', [])
    if detections:
        st.metric("Objek Terdeteksi", ", ".join(detections) or "Tidak ada")
    else:
        st.metric("Objek Terdeteksi", "Aman")
        
    # Menampilkan kecepatan pengguna
    speed_kmh = gps_data.get('speed_kmh')
    speed_text = f"{speed_kmh:.1f} km/jam" if speed_kmh is not None else "N/A"
    st.metric("Kecepatan", speed_text)

    # Menampilkan status detail dari semua sensor dalam expander
    with st.expander("Lihat Status Sensor Perangkat"):
        st.json(data.get('status', {}))

# --- 4. Auto-Refresh ---
# Membuat halaman dimuat ulang secara otomatis setiap 3 detik
time.sleep(3)
st.rerun()
