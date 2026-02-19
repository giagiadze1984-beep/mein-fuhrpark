import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Fuhrpark Pro", layout="wide")

# Hier deine echten Links aus den Google Sheets einfügen (hast du ja bereits in den Secrets)
# Die Links zum ÖFFNEN des Sheets (für die Buttons):
# Kopiere einfach die normale Browser-URL deines Sheets hier rein:
SHEET_URL = "https://docs.google.com/spreadsheets/d/1k1zU3b7GUxFNqGQYkdy4RcUyKNhEbOdB1avBMJa3Yss/edit"

# Daten laden
try:
    df_autos = pd.read_csv(st.secrets["url_autos"])
    df_services = pd.read_csv(st.secrets["url_services"])
    
    # Spaltennamen säubern
    df_autos.columns = [c.lower().strip() for c in df_autos.columns]
    df_services.columns = [c.lower().strip() for c in df_services.columns]
    
    if 'kosten' in df_services.columns:
        df_services['kosten'] = pd.to_numeric(df_services['kosten'], errors='coerce').fillna(0)
except Exception as e:
    st.error("Daten-Verbindung unterbrochen. Bitte CSV-Links prüfen!")
    st.stop()

# --- NAVIGATION & EINGABE-BUTTONS ---
st.title("🚗 Mein Fuhrpark-Manager")

# Buttons für die mobile Eingabe
st.write("### 📲 Schnelleingabe per Handy")
col1, col2 = st.columns(2)
with col1:
    st.link_button("➕ Neues Auto / Service eintragen", SHEET_URL, use_container_width=True)
with col2:
    st.info("Tipp: Trage Daten im Sheet ein und lade diese Seite kurz neu.")

st.divider()

# --- DASHBOARD KACHELN ---
c1, c2, c3 = st.columns(3)
with c1:
    st.metric("Fahrzeuge", len(df_autos))
with c2:
    gesamtkosten = df_services['kosten'].sum() if 'kosten' in df_services.columns else 0
    st.metric("Gesamtkosten", f"{gesamtkosten:,.2f} €")
with c3:
    letzter = df_services['datum'].max() if not df_services.empty else "-"
    st.metric("Letzter Service", letzter)

st.divider()

# --- ANALYSE ---
if not df_autos.empty:
    auswahl = st.selectbox("Fahrzeug wählen:", df_autos["kennzeichen"].unique())
    
    # Daten für das gewählte Auto
    auto = df_autos[df_autos["kennzeichen"] == auswahl].iloc[0]
    serv = df_services[df_services["kennzeichen"] == auswahl].copy()
    
    st.subheader(f"Detailansicht: {auto['marke']} {auto['modell']}")
    
    col_left, col_right = st.columns([2, 1])
    
    with col_right:
        kosten_auto = serv['kosten'].sum() if 'kosten' in serv.columns else 0
        st.info(f"💰 **Kosten für dieses KFZ:** \n\n ## {kosten_auto:,.2f} €")
        
    with col_left:
        if not serv.empty:
            st.line_chart(data=serv, x='datum', y='km_stand')

    st.write("### 🛠 Service-Historie & Belege")
    if not serv.empty:
        for i, row in serv.iterrows():
            # Titel für den Klappentext (Expander)
            label = f"📅 {row['datum']} | {row['km_stand']} KM"
            if 'kosten' in row: label += f" | {row['kosten']} €"
            
            with st.expander(label):
                st.write(f"**Was wurde gemacht?**\n{row['beschreibung']}")
                # Button für Bilder/PDFs falls ein Link da ist
                if 'link' in row and pd.notnull(row['link']) and str(row['link']).startswith('http'):
                    st.link_button("📄 Dokument/Foto öffnen", str(row['link']))
    else:
        st.warning("Noch keine Service-Einträge im Google Sheet vorhanden.")
