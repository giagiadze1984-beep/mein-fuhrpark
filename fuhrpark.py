import streamlit as st
import pandas as pd
from datetime import datetime
from dateutil.relativedelta import relativedelta

st.set_page_config(page_title="Fuhrpark Profi-Manager", layout="wide")

# DATEN LADEN
try:
    df_autos = pd.read_csv(st.secrets["url_autos"])
    df_services = pd.read_csv(st.secrets["url_services"])
    
    df_autos.columns = [c.lower().strip() for c in df_autos.columns]
    df_services.columns = [c.lower().strip() for c in df_services.columns]
    
    # KM-Stand & Kosten bereinigen
    for col in ['km_stand', 'kosten']:
        if col in df_services.columns:
            df_services[col] = pd.to_numeric(df_services[col].astype(str).str.replace('€','').str.replace('.','').str.replace(',','.').str.strip(), errors='coerce').fillna(0)
    
    # Datum in echtes Datumsformat umwandeln
    df_services['datum'] = pd.to_datetime(df_services['datum'], errors='coerce')
    
except Exception as e:
    st.error("Fehler beim Laden. Prüfe deine Google Sheet Spalten!")
    st.stop()

st.title("🚗 Wartungs-Zentrale (KM & Zeit)")

if not df_autos.empty:
    cols = st.columns(len(df_autos))
    heute = datetime.now()

    for idx, row in df_autos.iterrows():
        kz = row['kennzeichen']
        
        # Einstellungen aus dem Sheet oder Standardwerte
        km_intervall = row['intervall'] if 'intervall' in df_autos.columns else 20000
        monate_intervall = row['zeit_intervall'] if 'zeit_intervall' in df_autos.columns else 24
        km_aktuell = row['km_aktuell'] if 'km_aktuell' in df_autos.columns else 0
        
        # Letzten Service suchen
        auto_services = df_services[df_services['kennzeichen'] == kz].sort_values(by='datum', ascending=False)
        
        with cols[idx]:
            if not auto_services.empty:
                letzter_service = auto_services.iloc[0]
                l_datum = letzter_service['datum']
                l_km = letzter_service['km_stand']
                
                # Berechnung KM & Zeit
                diff_km = km_aktuell - l_km
                diff_monate = (heute.year - l_datum.year) * 12 + heute.month - l_datum.month
                
                # Logik: Was ist kritischer?
                km_status = diff_km >= km_intervall
                zeit_status = diff_monate >= monate_intervall
                
                if km_status or zeit_status:
                    st.error(f"🚨 **{kz}**\n\n**SERVICE FÄLLIG!**")
                    if km_status: st.write(f"⚠️ KM-Limit erreicht: {int(diff_km)} km")
                    if zeit_status: st.write(f"⚠️ Zeit-Limit erreicht: {int(diff_monate)} Monate")
                elif diff_km >= (km_intervall * 0.8) or diff_monate >= (monate_intervall * 0.8):
                    st.warning(f"🟡 **{kz}**\n\n**Bald fällig**\n({int(diff_km)} km / {int(diff_monate)} Mon.)")
                else:
                    st.success(f"✅ **{kz}**\n\n**Alles OK**\n({int(diff_km)} km / {int(diff_monate)} Mon.)")
            else:
                st.info(f"⚪ **{kz}**\n\nKeine Daten")

st.divider()

# --- OPTIONAL: KOSTEN-DIAGRAMM ---
st.subheader("💰 Kosten-Check")
if not df_services.empty:
    kosten_pro_auto = df_services.groupby('kennzeichen')['kosten'].sum().reset_index()
    st.bar_chart(data=kosten_pro_auto, x='kennzeichen', y='kosten')
