import streamlit as st
import pandas as pd
import os
from datetime import datetime

# DATEI-PFADE
CAR_FILE = "autos.csv"
SERVICE_FILE = "services.csv"

def load_data(file, columns):
    if os.path.exists(file):
        return pd.read_csv(file)
    return pd.DataFrame(columns=columns)

def save_data(df, file):
    df.to_csv(file, index=False)

st.set_page_config(page_title="Fuhrpark Manager Pro", layout="wide")
st.title("🚗 Mein Fuhrpark-Manager")

# Daten laden
df_autos = load_data(CAR_FILE, ["Kennzeichen", "Marke", "Modell"])
df_services = load_data(SERVICE_FILE, ["Kennzeichen", "Datum", "KM_Stand", "Beschreibung"])

# --- DOPPELTE KENNZEICHEN VERHINDERN ---
# Wir stellen sicher, dass die Autoliste immer eindeutig ist
df_autos = df_autos.drop_duplicates(subset=["Kennzeichen"])

# Sidebar Menü
menu = st.sidebar.selectbox("Menü", ["Fahrzeugübersicht", "Neuen Service eintragen", "Auto hinzufügen"])

if menu == "Auto hinzufügen":
    st.header("Neues Fahrzeug registrieren")
    with st.form("add_car", clear_on_submit=True):
        kz = st.text_input("Kennzeichen").upper().strip() # Großbuchstaben & Leerzeichen weg
        ma = st.text_input("Marke")
        mo = st.text_input("Modell")
        if st.form_submit_button("Fahrzeug Speichern"):
            if kz:
                if kz in df_autos["Kennzeichen"].values:
                    st.error(f"Das Kennzeichen {kz} existiert bereits!")
                else:
                    new_car = pd.DataFrame([[kz, ma, mo]], columns=df_autos.columns)
                    df_autos = pd.concat([df_autos, new_car], ignore_index=True)
                    save_data(df_autos, CAR_FILE)
                    st.success(f"Auto {kz} wurde erfolgreich angelegt!")
                    st.rerun()

elif menu == "Neuen Service eintragen":
    st.header("Wartung / Service dokumentieren")
    if df_autos.empty:
        st.warning("Bitte erst ein Auto anlegen!")
    else:
        with st.form("add_service", clear_on_submit=True):
            # Eindeutige Liste für das Dropdown
            eindeutige_autos = sorted(df_autos["Kennzeichen"].unique())
            auswahl_kz = st.selectbox("Fahrzeug wählen", eindeutige_autos)
            datum = st.date_input("Datum", datetime.now())
            km = st.number_input("Aktueller KM-Stand", min_value=0, step=1)
            info = st.text_area("Was wurde gemacht?")
            
            if st.form_submit_button("Service-Eintrag speichern"):
                new_service = pd.DataFrame([[auswahl_kz, datum, km, info]], columns=df_services.columns)
                df_services = pd.concat([df_services, new_service], ignore_index=True)
                save_data(df_services, SERVICE_FILE)
                st.success(f"Eintrag für {auswahl_kz} gespeichert!")

elif menu == "Fahrzeugübersicht":
    st.header("Dein Fuhrpark & Analyse")
    if df_autos.empty:
        st.info("Noch keine Fahrzeuge vorhanden.")
    else:
        # Eindeutige Kennzeichen für die Auswahl
        eindeutige_kzs = sorted(df_autos["Kennzeichen"].unique())
        auswahl = st.selectbox("Wähle ein Fahrzeug für Details:", eindeutige_kzs)
        
        # Details zum gewählten Auto anzeigen
        auto_daten = df_autos[df_autos["Kennzeichen"] == auswahl].iloc[0]
        st.write(f"**Modell:** {auto_daten['Marke']} {auto_daten['Modell']}")
        
        # Historie filtern
        historie = df_services[df_services["Kennzeichen"] == auswahl].copy()
        historie['Datum'] = pd.to_datetime(historie['Datum'])
        historie = historie.sort_values(by="Datum", ascending=False)

        if not historie.empty:
            # Grafik
            st.subheader("Kilometer-Verlauf")
            chart_data = historie.sort_values(by="Datum")
            st.line_chart(data=chart_data, x='Datum', y='KM_Stand')
            
            # Tabelle
            st.subheader("Alle Service-Einträge")
            st.dataframe(historie, use_container_width=True)
            
            # --- EXPORT FUNKTION ---
            csv = historie.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="Diese Historie als Excel (CSV) exportieren",
                data=csv,
                file_name=f"Service_Historie_{auswahl}.csv",
                mime='text/csv',
            )
        else:
            st.info("Keine Service-Einträge für dieses Auto gefunden.")

    # Gesamtliste aller Autos (eindeutig)
    st.divider()
    st.subheader("Alle registrierten Fahrzeuge")
    st.table(df_autos)