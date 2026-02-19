import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Fuhrpark Manager Pro", layout="wide")
st.title("🚗 Mein Fuhrpark-Manager")

# Verbindung zu Google Sheets herstellen
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    df_autos = conn.read(worksheet="autos")
    df_services = conn.read(worksheet="services")
except Exception as e:
    st.error("Verbindung zu Google Sheets fehlgeschlagen. Prüfe deine Secrets!")
    st.stop()

# Sidebar Menü
menu = st.sidebar.selectbox("Menü", ["Fahrzeugübersicht", "Neuen Service eintragen", "Auto hinzufügen", "Daten verwalten (Löschen/Bearbeiten)"])

# --- FUNKTION: AUTO HINZUFÜGEN ---
if menu == "Auto hinzufügen":
    st.header("Neues Fahrzeug registrieren")
    with st.form("add_car", clear_on_submit=True):
        kz = st.text_input("Kennzeichen (z.B. S-XY-123)").upper().strip()
        ma = st.text_input("Marke")
        mo = st.text_input("Modell")
        if st.form_submit_button("Fahrzeug Speichern"):
            if kz:
                if not df_autos.empty and kz in df_autos["Kennzeichen"].astype(str).values:
                    st.error(f"Das Kennzeichen {kz} existiert bereits!")
                else:
                    new_car = pd.DataFrame([[kz, ma, mo]], columns=["Kennzeichen", "Marke", "Modell"])
                    updated_df = pd.concat([df_autos, new_car], ignore_index=True)
                    conn.update(worksheet="autos", data=updated_df)
                    st.success(f"Auto {kz} wurde gespeichert!")
                    st.rerun()

# --- FUNKTION: SERVICE EINTRAGEN ---
elif menu == "Neuen Service eintragen":
    st.header("Wartung / Service dokumentieren")
    if df_autos.empty:
        st.warning("Bitte erst ein Auto unter 'Auto hinzufügen' anlegen!")
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
                st.success(f"Eintrag für {auswahl_kz} gespeichert!")

# --- FUNKTION: ÜBERSICHT & GRAFIK ---
elif menu == "Fahrzeugübersicht":
    st.header("Dein Fuhrpark & Analyse")
    if df_autos.empty:
        st.info("Noch keine Fahrzeuge vorhanden.")
    else:
        auswahl = st.selectbox("Wähle ein Fahrzeug für Details:", sorted(df_autos["Kennzeichen"].unique()))
        
        # Details anzeigen
        auto_daten = df_autos[df_autos["Kennzeichen"] == auswahl].iloc[0]
        st.subheader(f"Details für {auswahl}: {auto_daten['Marke']} {auto_daten['Modell']}")
        
        historie = df_services[df_services["Kennzeichen"] == auswahl].copy()
        if not historie.empty:
            historie['Datum'] = pd.to_datetime(historie['Datum'])
            historie = historie.sort_values(by="Datum")
            
            st.line_chart(data=historie, x='Datum', y='KM_Stand')
            st.write("**Service-Verlauf:**")
            st.dataframe(historie.sort_values(by="Datum", ascending=False), use_container_width=True)
        else:
            st.info("Keine Service-Einträge für dieses Fahrzeug gefunden.")

# --- NEU: DATEN VERWALTEN (LÖSCHEN / BEARBEITEN) ---
elif menu == "Daten verwalten (Löschen/Bearbeiten)":
    st.header("🔧 Daten verwalten")
    
    tab1, tab2 = st.tabs(["Fahrzeuge löschen", "Service-Einträge bearbeiten/löschen"])
    
    with tab1:
        st.subheader("Auto aus Datenbank entfernen")
        if not df_autos.empty:
            delete_kz = st.selectbox("Welches Auto soll gelöscht werden?", df_autos["Kennzeichen"].unique(), key="del_car")
            st.warning(f"Achtung: Das Löschen von {delete_kz} entfernt auch alle zugehörigen Service-Einträge!")
            if st.button(f"{delete_kz} endgültig löschen"):
                # Auto löschen
                df_autos_new = df_autos[df_autos["Kennzeichen"] != delete_kz]
                # Zugehörige Services löschen
                df_services_new = df_services[df_services["Kennzeichen"] != delete_kz]
                
                conn.update(worksheet="autos", data=df_autos_new)
                conn.update(worksheet="services", data=df_services_new)
                st.success(f"{delete_kz} wurde gelöscht.")
                st.rerun()
        else:
            st.write("Keine Autos zum Löschen vorhanden.")

    with tab2:
        st.subheader("Service-Eintrag bearbeiten oder löschen")
        if not df_services.empty:
            # Wir zeigen die Services mit einer ID (Index) an, damit man sie wählen kann
            df_temp_services = df_services.copy()
            df_temp_services['ID'] = df_temp_services.index
            
            selected_id = st.number_input("Gib die ID (Index-Nummer) des Eintrags ein, den du löschen möchtest:", 
                                         min_value=0, max_value=len(df_services)-1, step=1)
            
            st.write("Ausgewählter Eintrag:")
            st.table(df_services.iloc[[selected_id]])
            
            if st.button("Diesen Service-Eintrag löschen"):
                df_services_new = df_services.drop(selected_id)
                conn.update(worksheet="services", data=df_services_new)
                st.success("Eintrag gelöscht!")
                st.rerun()
            
            st.divider()
            st.write("**Alle aktuellen Service-Einträge (mit ID links):**")
            st.dataframe(df_temp_services[['ID', 'Kennzeichen', 'Datum', 'KM_Stand', 'Beschreibung']], use_container_width=True)
        else:
            st.write("Keine Service-Einträge vorhanden.")
