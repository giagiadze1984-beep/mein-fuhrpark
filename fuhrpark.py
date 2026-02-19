import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Fuhrpark Manager Pro", layout="wide")
st.title("🚗 Mein Fuhrpark-Manager")

# Verbindung mit Fehlertoleranz
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    # Daten laden
    df_autos = conn.read(worksheet="autos", ttl=0)
    df_services = conn.read(worksheet="services", ttl=0)
    
    # Sicherstellen, dass Spaltennamen klein sind für die Logik
    df_autos.columns = [c.lower() for c in df_autos.columns]
    df_services.columns = [c.lower() for c in df_services.columns]
except Exception as e:
    st.error("Verbindung zu Google Sheets hakt noch!")
    st.info("💡 Tipp: Prüfe, ob der Link in den Secrets auf '/edit' endet.")
    st.code(str(e))
    st.stop()

menu = st.sidebar.selectbox("Menü", ["Fahrzeugübersicht", "Neuen Service eintragen", "Auto hinzufügen", "Daten verwalten"])

if menu == "Auto hinzufügen":
    st.header("Fahrzeug registrieren")
    with st.form("add_car", clear_on_submit=True):
        kz = st.text_input("Kennzeichen").upper().strip()
        ma = st.text_input("Marke")
        mo = st.text_input("Modell")
        if st.form_submit_button("Speichern"):
            if kz:
                new_car = pd.DataFrame([[kz, ma, mo]], columns=["kennzeichen", "marke", "modell"])
                updated = pd.concat([df_autos, new_car], ignore_index=True)
                conn.update(worksheet="autos", data=updated)
                st.success("Erfolgreich gespeichert!")
                st.rerun()

elif menu == "Neuen Service eintragen":
    st.header("Service dokumentieren")
    if not df_autos.empty:
        with st.form("add_service", clear_on_submit=True):
            auswahl = st.selectbox("Auto wählen", df_autos["kennzeichen"].unique())
            datum = st.date_input("Datum", datetime.now())
            km = st.number_input("KM-Stand", min_value=0)
            info = st.text_area("Beschreibung")
            if st.form_submit_button("Speichern"):
                new_s = pd.DataFrame([[auswahl, str(datum), km, info]], 
                                     columns=["kennzeichen", "datum", "km_stand", "beschreibung"])
                updated = pd.concat([df_services, new_s], ignore_index=True)
                conn.update(worksheet="services", data=updated)
                st.success("Service-Eintrag gespeichert!")

elif menu == "Fahrzeugübersicht":
    st.header("Analyse")
    if not df_autos.empty:
        auswahl = st.selectbox("Fahrzeug", df_autos["kennzeichen"].unique())
        sub = df_services[df_services["kennzeichen"] == auswahl].copy()
        if not sub.empty:
            st.line_chart(data=sub, x='datum', y='km_stand')
            st.dataframe(sub)
        else:
            st.info("Keine Einträge für dieses Auto.")

elif menu == "Daten verwalten":
    st.header("🔧 Lösch-Bereich")
    if not df_autos.empty:
        del_kz = st.selectbox("Welches Auto löschen?", df_autos["kennzeichen"].unique())
        if st.button("Jetzt löschen"):
            df_autos = df_autos[df_autos["kennzeichen"] != del_kz]
            conn.update(worksheet="autos", data=df_autos)
            st.success("Auto gelöscht!")
            st.rerun()
