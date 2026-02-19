import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Fuhrpark Manager Pro", layout="wide")
st.title("🚗 Mein Fuhrpark-Manager")

# Daten laden über die CSV-Links aus den Secrets
try:
    df_autos = pd.read_csv(st.secrets["url_autos"])
    df_services = pd.read_csv(st.secrets["url_services"])
    
    # Spaltennamen klein machen
    df_autos.columns = [c.lower().strip() for c in df_autos.columns]
    df_services.columns = [c.lower().strip() for c in df_services.columns]
except Exception as e:
    st.error("Fehler beim Laden der Daten!")
    st.info("Hast du die CSV-Links in den Secrets eingetragen?")
    st.stop()

menu = st.sidebar.selectbox("Menü", ["Fahrzeugübersicht", "Neuen Service eintragen", "Auto hinzufügen", "Daten verwalten"])

if menu == "Auto hinzufügen":
    st.header("Fahrzeug registrieren")
    st.info("Hinweis: In dieser Version bitte neue Autos direkt im Google Sheet eintragen.")
    st.dataframe(df_autos)

elif menu == "Neuen Service eintragen":
    st.header("Wartung eintragen")
    if not df_autos.empty:
        with st.form("add_service"):
            auswahl = st.selectbox("Auto", df_autos["kennzeichen"].unique())
            datum = st.date_input("Datum", datetime.now())
            km = st.number_input("KM-Stand", min_value=0)
            info = st.text_area("Beschreibung")
            if st.form_submit_button("Speichern"):
                st.warning("Speichern ist in der Web-Ansicht deaktiviert. Bitte trage Daten direkt im Google Sheet ein.")

elif menu == "Fahrzeugübersicht":
    st.header("Analyse")
    if not df_autos.empty:
        auswahl = st.selectbox("Fahrzeug wählen", df_autos["kennzeichen"].unique())
        sub = df_services[df_services["kennzeichen"] == auswahl].copy()
        if not sub.empty:
            st.subheader(f"Verlauf für {auswahl}")
            st.line_chart(data=sub, x='datum', y='km_stand')
            st.dataframe(sub)
        else:
            st.info("Keine Einträge vorhanden.")
