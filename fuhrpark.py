import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Fuhrpark Wartungs-Ampel", layout="wide")

# DATEN LADEN
try:
    df_autos = pd.read_csv(st.secrets["url_autos"])
    df_services = pd.read_csv(st.secrets["url_services"])
    
    # Spaltennamen säubern (alles klein & ohne Leerzeichen)
    df_autos.columns = [c.lower().strip() for c in df_autos.columns]
    df_services.columns = [c.lower().strip() for c in df_services.columns]
    
    # Kosten & KM-Stand bereinigen (Text zu Zahl)
    for col in ['kosten', 'km_stand']:
        if col in df_services.columns:
            df_services[col] = pd.to_numeric(
                df_services[col].astype(str)
                .str.replace('€','')
                .str.replace('.','')
                .str.replace(',','.')
                .str.strip(), 
                errors='coerce'
            ).fillna(0)
            
except Exception as e:
    st.error("Fehler beim Laden der Daten. Prüfe die Links in den Secrets!")
    st.stop()

st.title("🚗 Fuhrpark Wartungs-Ampel")

# --- AMPEL LOGIK ---
st.subheader("Status-Check")

if not df_autos.empty:
    cols = st.columns(len(df_autos))
    
    for idx, row in df_autos.iterrows():
        kz = row['kennzeichen']
        
        # Sicherstellen, dass 'intervall' existiert, sonst 20.000 als Standard
        intervall = row['intervall'] if 'intervall' in df_autos.columns else 20000
        # Sicherstellen, dass 'km_aktuell' existiert
        km_jetzt = row['km_aktuell'] if 'km_aktuell' in df_autos.columns else 0
        
        # Letzten Service aus der Service-Tabelle finden
        auto_services = df_services[df_services['kennzeichen'] == kz]
        
        with cols[idx]:
            if not auto_services.empty:
                letzter_service_km = auto_services['km_stand'].max()
                gefahrene_km = km_jetzt - letzter_service_km
                rest_km = intervall - gefahrene_km
                
                if gefahrene_km >= intervall:
                    st.error(f"🚨 **{kz}**\n\n**SERVICE FÄLLIG!**\n\n{int(gefahrene_km)} km seit Service")
                elif gefahrene_km >= (intervall * 0.8):
                    st.warning(f"⚠️ **{kz}**\n\n**Bald fällig**\n\nNoch {int(rest_km)} km")
                else:
                    st.success(f"✅ **{kz}**\n\n**Alles OK**\n\nNoch {int(rest_km)} km")
            else:
                st.info(f"ℹ️ **{kz}**\n\nKeine Service-Daten vorhanden.")

st.divider()

# --- DATEN-ANZEIGE ---
st.write("### Aktuelle Fahrzeugliste")
st.dataframe(df_autos, use_container_width=True)
