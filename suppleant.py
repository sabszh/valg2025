import streamlit as st
import hashlib
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# --- Indstillinger ---
candidates = ["1", "2", "3", "4"]
sheet_name = "Suppleantvalg 2025"

# --- Funktion: Generér anonym ID ---
def get_pseudonym(email):
    salt = st.secrets["hash_salt"]
    return hashlib.sha256(f"{email}{salt}".encode()).hexdigest()

# --- Funktion: Opret forbindelse til ark via secrets ---
def get_sheet():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds_dict = st.secrets["gcp_service_account"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    return client.open(sheet_name).sheet1

# --- Funktion: Tjek om der allerede er stemt ---
def has_already_voted(pseudonym):
    sheet = get_sheet()
    records = sheet.col_values(1)
    return pseudonym in records

# --- Funktion: Gem stemmer ---
def submit_vote_to_sheet(pseudonym, votes):
    sheet = get_sheet()
    row = [pseudonym] + votes + [""] * (4 - len(votes))
    sheet.append_row(row)

# --- Start App ---
st.title("🗳️ Suppleantvalg 2025")
st.write("Velkommen til den digitale afstemning for valg af suppleanter til bestyrelsen 👋")

# --- Login UI ---
if not st.session_state.get("authenticated"):
    st.subheader("🔐 Log ind for at stemme")
    email = st.text_input("📧 Din mailadresse")
    membership_code = st.text_input("🔑 Dit medlemsnummer", type="password")

    if st.button("Log ind"):
        if email in st.secrets["users"] and st.secrets["users"][email] == membership_code:
            pseudonym = get_pseudonym(email)
            if has_already_voted(pseudonym):
                st.error("🚫 Du har allerede afgivet din stemme. Tak for din deltagelse!")
            else:
                st.session_state["authenticated"] = True
                st.session_state["pseudonym"] = pseudonym
                st.success("✅ Login godkendt – du kan nu afgive din stemme.")
                st.rerun()
        else:
            st.error("❌ Forkert mail eller medlemsnummer – prøv igen.")
    st.stop()

# --- Afstemning UI ---
st.subheader("📝 Afgiv din stemme")
st.write("Vælg op til **4 kandidater** til suppleantposten. 👇")

if "confirmed" not in st.session_state:
    st.session_state["confirmed"] = False

selection = st.multiselect("🎯 Vælg dine suppleanter", candidates, max_selections=4)

if st.button("Afgiv stemme"):
    if len(selection) == 0:
        st.warning("⚠️ Du skal vælge mindst én kandidat.")
    else:
        st.session_state["pending_vote"] = selection
        st.session_state["confirmed"] = True
        st.rerun()

if st.session_state.get("confirmed"):
    st.info(f"✅ Du har valgt: **{', '.join(st.session_state['pending_vote'])}**")
    st.write("Er du sikker på, at du vil afgive din stemme sådan? Dette kan ikke fortrydes bagefter.")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("✅ Bekræft og afgiv stemme"):
            submit_vote_to_sheet(st.session_state["pseudonym"], st.session_state["pending_vote"])
            st.success("🎉 Tak for at afgive din stemme – den er modtaget!")
            st.balloons()
            st.session_state.clear()
            st.stop()
    with col2:
        if st.button("🔄 Fortryd og vælg igen"):
            st.session_state["confirmed"] = False
            st.session_state["pending_vote"] = []
            st.rerun()
