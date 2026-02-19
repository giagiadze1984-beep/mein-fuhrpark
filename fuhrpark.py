import streamlit as st
import pandas as pd
from datetime import datetime
from dateutil.relativedelta import relativedelta

st.set_page_config(page_title="Fuhrpark Management Pro", layout="wide")

# DEIN LINK ZUM BEARBEITEN (Browser-URL deines Sheets)
SHEET_EDIT_URL = "https://docs.google.com/spreadsheets/d/1k1zU3b7GUxFNqGQYkdy4RcUyKNhEbOdB1avBMJa3Yss/edit"

# DATEN LADEN
try:
    df_autos = pd.read_csv(st.secrets["url_autos"])
    df_services = pd.read_csv(st.secrets["url_services"])
    
    df_autos.columns = [c.lower().strip() for c in df_autos.columns]
    df_services.columns = [c.lower().strip() for c in df_services.columns]
    
    # KM & Kosten säubern
    for col in ['km_stand', 'kosten']:
        if col in df_services.columns:
            df_services[col] = pd.to_numeric(df_services[col].astype(str).str.replace('€','').str.replace('.','').str.replace(',','.').str.strip(), errors='coerce').fillna(0)
    
    if 'km_aktuell' in df_autos.columns:
        df_autos['km_aktuell'] = pd.to_numeric(df_autos['km_aktuell'], errors='coerce').fillna(0)

    df_services['datum'] = pd.to_datetime(df_services['datum'], errors='coerce')
except Exception as e:
    st.error("Daten konnten nicht geladen werden.")
    st.stop()

# --- NAVIGATION & TOOLS ---
st.title("🚗 Mein Fuhrpark-Manager")

with st.expander("🛠️ Verwaltung & Eingabe (Hier klicken)"):
    col1, col2, col3 = st.columns(3)
    with col1:
        st.write("**Hinzufügen / Bearbeiten**")
        st.link_button("📝 Google Sheet öffnen", SHEET_EDIT_URL)
        st.caption("Einfach in die nächste freie Zeile schreiben oder Werte ändern.")
    with col2:
        st.write("**Löschen**")
        st.info("Im Google Sheet die ganze Zeile markieren -> Rechtsklick -> Zeile löschen.")
    with col3:
        st.write("**Bilder/PDFs**")
        st.write("Link von Google Drive in die Spalte 'Link' kopieren.")

st.divider()

# --- WARTUNGS-AMPEL ---
st.subheader("⚠️ Wartungs-Status")
if not df_autos.empty:
    ampel_cols = st.columns(len(df_autos))
    heute = datetime.now()

    for idx, row in df_autos.iterrows():
        kz = row['kennzeichen']
        km_int = row['intervall'] if 'intervall' in df_autos.columns else 20000
        zeit_int = row['zeit_intervall'] if 'zeit_intervall' in df_autos.columns else 24
        km_jetzt = row['km_aktuell'] if 'km_aktuell' in df_autos.columns else 0
        
        serv = df_services[df_services['kennzeichen'] == kz].sort_values(by='datum', ascending=False)
        
        with ampel_cols[idx]:
            if not serv.empty:
                l_serv = serv.iloc[0]
                diff_km = km_jetzt - l_serv['km_stand']
                diff_mon = (heute.year - l_serv['datum'].year) * 12 + heute.month - l_serv['datum'].month
                
                if diff_km >= km_int or diff_mon >= zeit_int:
                    st.error(f"**{kz}**\n\nFÄLLIG!")
                elif diff_km >= (km_int * 0.8) or diff_mon >= (zeit_int * 0.8):
                    st.warning(f"**{kz}**\n\nBald fällig")
                else:
                    st.success(f"**{kz}**\n\nOK")
                st.caption(f"{int(diff_km)} km / {int(diff_mon)} Mon. seit Service")
            else:
                st.info(f"**{kz}**\n\nKeine Daten")

st.divider()

# --- KOSTEN-CHECK ---
col_graph, col_stats = st.columns([2, 1])
with col_graph:
    st.subheader("💰 Kosten je Fahrzeug")
    if not df_services.empty:
        kosten_chart = df_services.groupby('kennzeichen')['kosten'].sum().reset_index()
        st.bar_chart(data=kosten_chart, x='kennzeichen', y='kosten')
with col_stats:
    st.subheader("Gesamt-Fuhrpark")
    st.metric("Gesamtkosten", f"{df_services['kosten'].sum():,.2f} €")
    st.metric("Anzahl Autos", len(df_autos))

# --- DETAIL-ANSICHT ---
st.divider()
if not df_autos.empty:
    auto_wahl = st.selectbox("Fahrzeug-Details & Dokumente:", df_autos["kennzeichen"].unique())
    sub_serv = df_services[df_services['kennzeichen'] == auto_wahl].sort_values(by='datum', ascending=False)
    
    if not sub_serv.empty:
        for i, r in sub_serv.iterrows():
            datum_str = r['datum'].strftime('%d.%m.%Y') if pd.notnull(r['datum']) else "Unbekannt"
            with st.expander(f"🛠️ {datum_str} — {r['kosten']:.2f} €"):
                st.write(f"**Beschreibung:** {r['beschreibung']}")
                if 'link' in r and pd.notnull(r['link']) and str(r['link']).startswith('http'):
                    st.link_button("📄 Dokument öffnen", str(r['link']))
