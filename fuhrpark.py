import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Fuhrpark Wartungs-Planer", layout="wide")

# DATEN LADEN
try:
    df_autos = pd.read_csv(st.secrets["url_autos"])
    df_services = pd.read_csv(st.secrets["url_services"])
    
    df_autos.columns = [c.lower().strip() for c in df_autos.columns]
    df_services.columns = [c.lower().strip() for c in df_services.columns]
    
    # Kosten & KM bereinigen
    for col in ['kosten', 'km_stand']:
        if col in df_services.columns:
            df_services[col] = pd.to_numeric(df_services[col].astype(str).str.replace('€','').str.replace('.','').str.replace(',','.').str.strip(), errors='coerce').fillna(0)
    
    if 'intervall' in df_autos.columns:
        df_autos['intervall'] = pd.to_numeric(df_autos['intervall'], errors='coerce').fillna(20000)
except Exception as e:
    st.error("Fehler beim Laden der Daten.")
    st.stop()

st.title("🚗 Fuhrpark Wartungs-Ampel")

# --- AMPEL LOGIK ---
st.subheader("Status-Check")
cols = st.columns(len(df_autos) if len(df_autos) > 0 else 1)

for idx, row in df_autos.iterrows():
    kz = row['kennzeichen']
    intervall = row['intervall']
    
    # Letzten Service finden
    auto_services = df_services[df_services['kennzeichen'] == kz]
    
    if not auto_services.empty:
        # Sortieren nach Datum oder KM, um den letzten Stand zu kriegen
        letzter_stand = auto_services['km_stand'].max()
        # Wir nehmen an, der KM-Stand im Blatt 'autos' ist der AKTUELLSTE (den musst du dort pflegen)
        # Wenn du im Blatt 'autos' eine Spalte 'km_aktuell' hast, nutze diese:
        km_aktuell = row['km_aktuell'] if 'km_aktuell' in row else letzter_stand 
        
        diff = km_aktuell - letzter_stand
        rest = intervall - diff
        
        with cols[idx % len(cols)]:
            if diff >= intervall:
                st.error(f"🚨 **{kz}**\n\nSERVICE FÄLLIG!\n({int(diff)} km seit Service)")
            elif diff >= (intervall * 0.8):
                st.warning(f"⚠️ **{kz}**\n\nBald fällig\n(Noch {int(rest)} km)")
            else:
                st.success(f"✅ **{kz}**\n\nAlles OK\n(Noch {int(rest)} km)")
    else:
        with cols[idx % len(cols)]:
            st.info(f"ℹ️ **{kz}**\n\nKeine Service-Daten")

st.divider()

# --- DER REST DER APP (ANALYSE ETC.) ---
auswahl = st.selectbox("Fahrzeug Details", df_autos["kennzeichen"].unique())
# ... hier folgt dein restlicher Analyse-Code ...
