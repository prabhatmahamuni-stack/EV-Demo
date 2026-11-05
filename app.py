import streamlit as st
import requests
import streamlit.components.v1 as components
import uuid

# ==========================================
# ⚙️ CONFIGURATION
# ==========================================
# 🚨 Paste your keys from the Nango Environment Settings here
NANGO_PUBLIC_KEY = "8cada06d-dfa1-47b1-be93-3b28e084ee1f"
NANGO_SECRET_KEY = "51b311fe-57b9-4a14-b142-44900773cfa6"

# Based on your screenshot, this must be "microsoft-entra-id"
MICROSOFT_INTEGRATION_ID = "microsoft-entra-id"
GOOGLE_INTEGRATION_ID = "google-oauth"

# Generate a unique session ID for the applicant so data doesn't overlap
if 'connection_id' not in st.session_state:
    st.session_state.connection_id = f"axis-applicant-{uuid.uuid4().hex[:6]}"

# ==========================================
# 🛠️ NANGO FRONTEND UI (JAVASCRIPT COMPONENT)
# ==========================================
def render_nango_button(provider_id, button_text, color):
    components.html(f"""
        <script src="https://cdn.jsdelivr.net/npm/@nangohq/frontend@latest"></script>
        <button id="auth-btn" style="padding: 12px; background-color: {color}; color: white; border: none; border-radius: 8px; cursor: pointer; width: 100%; font-family: sans-serif; font-weight: bold; font-size: 16px;">
            {button_text}
        </button>
        <script>
            const nango = new Nango('{NANGO_PUBLIC_KEY}');
            document.getElementById('auth-btn').addEventListener('click', function() {{
                nango.auth('{provider_id}', '{st.session_state.connection_id}')
                    .then((result) => console.log('Auth Success!'))
                    .catch((err) => console.log('Error:', err));
            }});
        </script>
    """, height=60)

# ==========================================
# 🎨 UI & APP LOGIC
# ==========================================
st.set_page_config(page_title="Axis Bank EV", page_icon="🏦")
st.title("Axis Bank - Employment Verification")
st.write("Select your corporate identity provider to instantly verify your employment.")

# 1. SHOW THE BUTTONS IMMEDIATELY
col1, col2 = st.columns(2)
with col1:
    render_nango_button(MICROSOFT_INTEGRATION_ID, "🏢 Verify with Microsoft", "#2F2F2F")
with col2:
    render_nango_button(GOOGLE_INTEGRATION_ID, "🌐 Verify with Google", "#1A73E8")

st.caption("🔒 Verified secure connection.")
st.divider()

# ==========================================
# 📥 NANGO BACKEND DATA FETCH (THE "DETECTION")
# ==========================================
st.write("### 2. View Verified Identity")
st.write("*(Click this button ONLY AFTER you complete the popup login above)*")

provider_to_test = st.radio("Which provider did you just use?", ["Microsoft", "Google"], horizontal=True)

if st.button("Fetch My Employee Data", type="primary"):
    with st.spinner("Securely fetching verified data via Nango..."):
        
        provider_id = GOOGLE_INTEGRATION_ID if provider_to_test == "Google" else MICROSOFT_INTEGRATION_ID
        
        # We use Nango's Proxy API to fetch data without handling tokens ourselves
        headers = {
            "Authorization": f"Bearer {NANGO_SECRET_KEY}",
            "Connection-Id": st.session_state.connection_id,
            "Provider-Config-Key": provider_id
        }
        
        proxy_url = "https://api.nango.dev/proxy/oauth2/v3/userinfo" if provider_to_test == "Google" else "https://api.nango.dev/proxy/v1.0/me"

        response = requests.get(proxy_url, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            
            # Detect email automatically
            email = data.get("email") or data.get("userPrincipalName", "Not Found")
            name = data.get("name") or data.get("displayName", "Not Found")
            
            st.success("✅ Employment Identity Verified!")
            
            st.write(f"**Verified Name:** {name}")
            st.write(f"**Verified Email:** {email}")
            
            # Auto-detect domain from the fetched email
            if "@" in email:
                domain = email.split("@")[-1]
                st.write(f"**Detected Enterprise Domain:** `{domain}`")
                
            with st.expander("🛠️ View Raw Nango Proxy Payload"):
                st.json(data)
        else:
            st.error("⚠️ Could not fetch data. Ensure you completed the popup login before clicking this button.")
