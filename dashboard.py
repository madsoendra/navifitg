import streamlit as st
import pandas as pd
import pyrebase
from datetime import datetime

# --- KONFIGURASI HALAMAN & FIREBASE ---
st.set_page_config(
    page_title="Dashboard NaviFitG",
    page_icon="?????",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Inisialisasi Firebase menggunakan Streamlit Secrets
try:
    firebase_config = st.secrets["firebase_config"]
    firebase = pyrebase.initialize_app(firebase_config)
    db = firebase.database()
except Exception:
    st.error("Konfigurasi Firebase tidak ditemukan di Streamlit Secrets. Harap atur terlebih dahulu.", icon="??")
    st.stop()


# --- FUNGSI UTAMA UNTUK MENGAMBIL DATA ---
@st.cache_data(ttl=2) # Cache data selama 2 detik
def get_live_data():
    try:
        data = db.child("live_data").get().val()
        return data if data else {}
    except Exception as e:
        st.toast(f"Gagal mengambil data: {e}", icon="??")
        return {}


# --- JUDUL DASHBOARD ---
st.title("????? Dashboard Pemantauan NaviFitG")
st.markdown(f"Data terakhir diperbarui pada: **{datetime.now().strftime('%d %B %Y, %H:%M:%S WIB')}**")

# --- AMBIL DATA ---
data = get_live_data()

if not data:
    st.warning("Belum ada data diterima dari perangkat. Pastikan perangkat NaviFitG menyala dan terhubung ke internet.")
    st.stop()

# --- LAYOUT DASHBOARD ---
col1, col2, col3 = st.columns(3)

# Kolom 1: Status Kritis (Jarak & Detak Jantung)
with col1:
    st.subheader("?? Status Kritis")
    dist = data.get('distance_m')
    dist_text = f"{dist:.2f} m" if dist is not None else "N/A"
    if dist is not None:
        if dist < 0.5:
            st.error(f"**BAHAYA!** Rintangan sangat dekat: {dist_text}", icon="??")
        elif dist < 1.5:
            st.warning(f"**AWAS!** Rintangan di depan: {dist_text}", icon="??")
        else:
            st.success(f"Aman: {dist_text}", icon="?")
    else:
        st.info("Sensor jarak tidak aktif.", icon="?")
    
    bpm = data.get('hr', {}).get('bpm')
    bpm_text = f"{bpm:.0f} BPM" if bpm is not None else "N/A"
    st.metric("Detak Jantung (BPM)", bpm_text)

# Kolom 2: Status Lokasi & Lingkungan
with col2:
    st.subheader("?? Lokasi & Lingkungan")
    gps_data = data.get('gps', {})
    if gps_data.get('valid') and gps_data.get('lat') is not None:
        location_df = pd.DataFrame({'lat': [gps_data['lat']], 'lon': [gps_data['lon']]})
        st.map(location_df, zoom=16)
    else:
        st.info("Mencari sinyal GPS...", icon="???")
    
    detections = data.get('yolo', {}).get('detections', [])
    if detections:
        st.metric("Objek Terdeteksi", ", ".join(detections) or "Tidak ada")
    else:
        st.metric("Objek Terdeteksi", "Aman")

# Kolom 3: Tampilan Kamera & Status Sensor
with col3:
    st.subheader("?? Tampilan Kamera")
    image_url = data.get('yolo', {}).get('image_url')
    if image_url:
        st.image(image_url, caption="Live feed dari perangkat (diperbarui setiap 5 detik)", use_column_width=True)
    else:
        st.info("Menunggu gambar dari perangkat...", icon="??")
    
    with st.expander("Lihat Status Sensor Detail"):
        st.json(data.get('status', {}))

# Auto-refresh halaman setiap 3 detik
time.sleep(3)
st.rerun()
