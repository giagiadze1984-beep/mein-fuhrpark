import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Fuhrpark Pro + Dokumente", layout="wide")

# Daten laden
try:
    df_autos = pd.read_csv(st.secrets["url_autos"])
    df_services = pd.read_csv(st.secrets["url_services"])
    
    # Spaltennamen säubern
    df_autos.columns = [c.lower().strip() for c in df_autos.columns]
    df_services.columns = [c.lower().strip() for c in df_services.columns]
    
    # Kosten-Spalte in Zahlen umwandeln (falls vorhanden)
    if 'kosten' in df_services.columns:
        df_services['kosten'] = pd.to_numeric(df_services['kosten'], errors='coerce').fillna(0)
except Exception as e:
    st.error("Daten konnten nicht geladen werden. Prüfe die CSV-Links!")
    st.stop()

# --- DASHBOARD OBEN ---
st.title("🚗 Fuhrpark Management")
col_a, col_b, col_c = st.columns(3)

with col_a:
    st.metric("Fahrzeuge Gesamt", len(df_autos))
with col_b:
    gesamtkosten = df_services['kosten'].sum() if 'kosten' in df_services.columns else 0
    st.metric("Gesamtkosten Fuhrpark", f"{gesamtkosten:,.2f} €")
with col_c:
    letzter_service = df_services['datum'].max() if not df_services.empty else "Keiner"
    st.metric("Letzter Service am", letzter_service)

st.divider()

# --- NAVIGATION ---
menu = st.sidebar.selectbox("Menü", ["Fahrzeug-Analyse", "Alle Daten anzeigen"])

if menu == "Fahrzeug-Analyse":
    if not df_autos.empty:
        auswahl = st.selectbox("Wähle ein Fahrzeug:", df_autos["kennzeichen"].unique())
        
        # Fahrzeug-Details
        auto_info = df_autos[df_autos["kennzeichen"] == auswahl].iloc[0]
        st.subheader(f"Details: {auto_info['marke']} {auto_info['modell']} ({auswahl})")
        
        # Kosten-Auswertung für dieses Auto
        sub_services = df_services[df_services["kennzeichen"] == auswahl].copy()
        auto_kosten = sub_services['kosten'].sum() if 'kosten' in sub_services.columns else 0
        
        c1, c2 = st.columns([2, 1])
        with c2:
            st.info(f"💰 **Gesamtkosten für dieses Auto:** \n\n ### {auto_kosten:,.2f} €")
        
        with c1:
            if not sub_services.empty:
                st.write("**Laufleistung über Zeit:**")
                st.line_chart(data=sub_services, x='datum', y='km_stand')
        
        st.write("### Service-Historie & Dokumente")
        if not sub_services.empty:
            # Tabelle mit Dokumenten-Links verschönern
            for i, row in sub_services.iterrows():
                with st.expander(f"📅 {row['datum']} - {row['km_stand']} KM - {row['kosten']} €"):
                    st.write(f"**Beschreibung:** {row['beschreibung']}")
                    # Prüfen ob ein Link (Bild/PDF) hinterlegt ist
                    if 'link' in sub_services.columns and pd.notnull(row['link']):
                        st.link_button("📂 Rechnung / Foto öffnen", str(row['link']))
                    else:
                        st.caption("Kein Dokument hinterlegt.")
        else:
            st.info("Noch keine Service-Einträge für dieses Fahrzeug.")

elif menu == "Alle Daten anzeigen":
    st.subheader("Rohdaten aus Google Sheets")
    st.write("Autos:")
    st.dataframe(df_autos, use_container_width=True)
    st.write("Services:")
    st.dataframe(df_services, use_container_width=True)
