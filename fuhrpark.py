import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Fuhrpark Pro", layout="wide")

# Link zum Bearbeiten für den Button
SHEET_URL = "https://docs.google.com/spreadsheets/d/1k1zU3b7GUxFNqGQYkdy4RcUyKNhEbOdB1avBMJa3Yss/edit"

# DATEN LADEN & BEREINIGEN
try:
    df_autos = pd.read_csv(st.secrets["url_autos"])
    df_services = pd.read_csv(st.secrets["url_services"])
    
    # Spaltennamen säubern (alles klein, keine Leerzeichen)
    df_autos.columns = [c.lower().strip() for c in df_autos.columns]
    df_services.columns = [c.lower().strip() for c in df_services.columns]
    
    # Kosten-Logik: Wandelt Text wie "350,00 €" in berechenbare Zahlen um
    if 'kosten' in df_services.columns:
        # Wir machen alles zu Text, entfernen €, Punkte und machen Komma zu Punkt
        df_services['kosten'] = (
            df_services['kosten']
            .astype(str)
            .str.replace('€', '', regex=False)
            .str.replace(' ', '', regex=False)
            .str.replace('.', '', regex=False) 
            .str.replace(',', '.', regex=False)
        )
        # Jetzt in echte Zahlen umwandeln
        df_services['kosten'] = pd.to_numeric(df_services['kosten'], errors='coerce').fillna(0)
except Exception as e:
    st.error("Daten-Verbindung hakt. Hast du die CSV-Links in den Secrets?")
    st.stop()

# --- APP LAYOUT ---
st.title("🚗 Mein Fuhrpark-Manager")

# Schnellzugriff
st.write("### 📲 Verwaltung")
col_link, col_info = st.columns([1, 1])
with col_link:
    st.link_button("➕ Daten im Google Sheet bearbeiten", SHEET_URL, use_container_width=True)
with col_info:
    st.info("Nach Änderungen im Sheet: In der App 'Clear Cache' klicken oder 1 Min. warten.")

st.divider()

# --- DASHBOARD ---
c1, c2, c3 = st.columns(3)
with c1:
    st.metric("Fahrzeuge", len(df_autos))
with c2:
    total_costs = df_services['kosten'].sum()
    st.metric("Gesamtkosten", f"{total_costs:,.2f} €")
with c3:
    last_service = df_services['datum'].max() if not df_services.empty else "-"
    st.metric("Letzter Service", last_service)

st.divider()

# --- EINZELANSICHT ---
if not df_autos.empty:
    all_cars = df_autos["kennzeichen"].unique()
    auswahl = st.selectbox("Wähle ein Fahrzeug für Details:", all_cars)
    
    auto_data = df_autos[df_autos["kennzeichen"] == auswahl].iloc[0]
    service_data = df_services[df_services["kennzeichen"] == auswahl].copy()
    
    st.subheader(f"Details: {auto_data['marke']} {auto_data['modell']} ({auswahl})")
    
    col_l, col_r = st.columns([2, 1])
    
    with col_r:
        car_costs = service_data['kosten'].sum()
        st.success(f"💰 **Kosten für dieses Auto:** \n\n ## {car_costs:,.2f} €")
        
    with col_l:
        if not service_data.empty:
            st.write("**Kilometerstand-Verlauf:**")
            st.line_chart(data=service_data, x='datum', y='km_stand')

    st.write("### 🛠 Service-Einträge & Anhänge")
    if not service_data.empty:
        service_data = service_data.sort_values(by='datum', ascending=False)
        
        for i, row in service_data.iterrows():
            with st.expander(f"📅 {row['datum']} — {row['kosten']:,.2f} €"):
                st.write(f"**Beschreibung:** {row['beschreibung']}")
                st.write(f"**KM-Stand:** {row['km_stand']}")
                
                if 'link' in row and pd.notnull(row['link']) and str(row['link']).startswith('http'):
                    st.link_button("📄 Bild/PDF öffnen", str(row['link']))
    else:
        st.info("Keine Einträge für dieses Fahrzeug gefunden.")
