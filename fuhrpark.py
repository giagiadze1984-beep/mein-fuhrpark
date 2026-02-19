import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Fuhrpark Manager Pro", layout="wide")
st.title("🚗 Mein Fuhrpark-Manager (Cloud)")
# Verbindung zu Google Sheets herstellen
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    df_autos = conn.read(worksheet="autos")
    df_services = conn.read(worksheet="services")
except Exception as e:
    st.error("Verbindung zu Google Sheets fehlgeschlagen!")
    st.info("Prüfe, ob der Link in den Secrets korrekt ist und das Sheet für 'Jeder mit dem Link' freigegeben wurde.")
    st.stop()


# Sidebar Menü
menu = st.sidebar.selectbox("Menü", ["Fahrzeugübersicht", "Neuen Service eintragen", "Auto hinzufügen"])

if menu == "Auto hinzufügen":
    st.header("Neues Fahrzeug registrieren")
    with st.form("add_car", clear_on_submit=True):
        kz = st.text_input("Kennzeichen").upper().strip()
        ma = st.text_input("Marke")
        mo = st.text_input("Modell")
        if st.form_submit_button("Fahrzeug Speichern"):
            if kz:
                # Neues Auto hinzufügen
                new_car = pd.DataFrame([[kz, ma, mo]], columns=["Kennzeichen", "Marke", "Modell"])
                updated_df = pd.concat([df_autos, new_car], ignore_index=True)
                conn.update(worksheet="autos", data=updated_df)
                st.success(f"Auto {kz} wurde in Google Sheets gespeichert!")
                st.rerun()

elif menu == "Neuen Service eintragen":
    st.header("Wartung / Service dokumentieren")
    if df_autos.empty:
        st.warning("Bitte erst ein Auto anlegen!")
    else:
        with st.form("add_service", clear_on_submit=True):
            eindeutige_autos = sorted(df_autos["Kennzeichen"].unique())
            auswahl_kz = st.selectbox("Fahrzeug wählen", eindeutige_autos)
            datum = st.date_input("Datum", datetime.now())
            km = st.number_input("Aktueller KM-Stand", min_value=0, step=1)
            info = st.text_area("Was wurde gemacht?")
            
            if st.form_submit_button("Service-Eintrag speichern"):
                new_service = pd.DataFrame([[auswahl_kz, str(datum), km, info]], 
                                         columns=["Kennzeichen", "Datum", "KM_Stand", "Beschreibung"])
                updated_services = pd.concat([df_services, new_service], ignore_index=True)
                conn.update(worksheet="services", data=updated_services)
                st.success(f"Eintrag für {auswahl_kz} wurde gespeichert!")

elif menu == "Fahrzeugübersicht":
    st.header("Dein Fuhrpark & Analyse")
    if df_autos.empty:
        st.info("Noch keine Fahrzeuge vorhanden.")
    else:
        auswahl = st.selectbox("Wähle ein Fahrzeug:", sorted(df_autos["Kennzeichen"].unique()))
        
        # Historie anzeigen (gefiltert aus Google Sheets)
        historie = df_services[df_services["Kennzeichen"] == auswahl].copy()
        if not historie.empty:
            st.subheader("Kilometer-Verlauf")
            st.line_chart(data=historie, x='Datum', y='KM_Stand')
            st.subheader("Service-Details")
            st.table(historie)
        else:
            st.info("Keine Einträge vorhanden.")

