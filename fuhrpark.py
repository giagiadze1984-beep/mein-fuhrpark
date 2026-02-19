import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Fuhrpark Manager Pro", layout="wide")
st.title("🚗 Mein Fuhrpark-Manager")

# Verbindung zu Google Sheets herstellen
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    # Wir laden die Daten mit ttl=0, um den Cache zu umgehen
    df_autos = conn.read(worksheet="autos", ttl=0)
    df_services = conn.read(worksheet="services", ttl=0)
    
    # Falls die Tabellen komplett leer sind (außer Header), erstellen wir leere DataFrames mit Spalten
    if df_autos.empty:
        df_autos = pd.DataFrame(columns=["Kennzeichen", "Marke", "Modell"])
    if df_services.empty:
        df_services = pd.DataFrame(columns=["Kennzeichen", "Datum", "KM_Stand", "Beschreibung"])
        
except Exception as e:
    st.error("Verbindung zu Google Sheets fehlgeschlagen!")
    st.info("Bitte prüfe, ob in Google Sheets Testdaten unter den Überschriften stehen.")
    st.code(str(e))
    st.stop()

# Sidebar Menü
menu = st.sidebar.selectbox("Menü", ["Fahrzeugübersicht", "Neuen Service eintragen", "Auto hinzufügen", "Daten verwalten"])

# --- AUTO HINZUFÜGEN ---
if menu == "Auto hinzufügen":
    st.header("Neues Fahrzeug registrieren")
    with st.form("add_car", clear_on_submit=True):
        kz = st.text_input("Kennzeichen").upper().strip()
        ma = st.text_input("Marke")
        mo = st.text_input("Modell")
        if st.form_submit_button("Fahrzeug Speichern"):
            if kz:
                new_car = pd.DataFrame([[kz, ma, mo]], columns=["Kennzeichen", "Marke", "Modell"])
                updated_df = pd.concat([df_autos, new_car], ignore_index=True)
                conn.update(worksheet="autos", data=updated_df)
                st.success(f"Auto {kz} gespeichert!")
                st.rerun()

# --- SERVICE EINTRAGEN ---
elif menu == "Neuen Service eintragen":
    st.header("Wartung dokumentieren")
    if df_autos.empty:
        st.warning("Bitte erst ein Auto anlegen!")
    else:
        with st.form("add_service", clear_on_submit=True):
            auswahl_kz = st.selectbox("Fahrzeug wählen", df_autos["Kennzeichen"].unique())
            datum = st.date_input("Datum", datetime.now())
            km = st.number_input("KM-Stand", min_value=0)
            info = st.text_area("Beschreibung")
            if st.form_submit_button("Speichern"):
                new_service = pd.DataFrame([[auswahl_kz, str(datum), km, info]], 
                                         columns=["Kennzeichen", "Datum", "KM_Stand", "Beschreibung"])
                updated_services = pd.concat([df_services, new_service], ignore_index=True)
                conn.update(worksheet="services", data=updated_services)
                st.success("Gespeichert!")

# --- ÜBERSICHT ---
elif menu == "Fahrzeugübersicht":
    st.header("Analyse")
    if not df_autos.empty:
        auswahl = st.selectbox("Fahrzeug wählen", df_autos["Kennzeichen"].unique())
        historie = df_services[df_services["Kennzeichen"] == auswahl].copy()
        if not historie.empty:
            st.subheader(f"Historie für {auswahl}")
            st.line_chart(data=historie, x='Datum', y='KM_Stand')
            st.dataframe(historie)
        else:
            st.info("Noch keine Einträge für dieses Auto.")

# --- DATEN VERWALTEN ---
elif menu == "Daten verwalten":
    st.header("🔧 Lösch-Funktionen")
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Fahrzeug löschen")
        if not df_autos.empty:
            del_kz = st.selectbox("Auto wählen", df_autos["Kennzeichen"].unique(), key="del_kz")
            if st.button("Auto jetzt löschen"):
                df_autos = df_autos[df_autos["Kennzeichen"] != del_kz]
                conn.update(worksheet="autos", data=df_autos)
                st.success("Gelöscht!")
                st.rerun()
    with col2:
        st.subheader("Service-Eintrag löschen")
        if not df_services.empty:
            df_with_id = df_services.copy()
            df_with_id['ID'] = df_with_id.index
            st.dataframe(df_with_id[['ID', 'Kennzeichen', 'Datum', 'Beschreibung']])
            id_to_del = st.number_input("ID eingeben", min_value=0, max_value=len(df_services)-1)
            if st.button("Eintrag jetzt löschen"):
                df_services = df_services.drop(id_to_del)
                conn.update(worksheet="services", data=df_services)
                st.success("Eintrag entfernt!")
                st.rerun()
