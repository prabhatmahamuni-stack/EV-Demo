import streamlit as st
import requests
import streamlit.components.v1 as components

# ==========================================
# ⚙️ CONFIGURATION
# ==========================================
NANGO_PUBLIC_KEY = "8cada06d-dfa1-47b1-be93-3b28e084ee1f"
NANGO_SECRET_KEY = "51b311fe-57b9-4a14-b142-44900773cfa6"

# These must match the Integration IDs you set in the Nango Dashboard
GOOGLE_INTEGRATION_ID = "google-oauth"
MICROSOFT_INTEGRATION_ID = "microsoft-entra-id"

# In a production app, this is dynamic. For the POC, we hardcode an applicant ID.
CONNECTION_ID = "axis-applicant-001" 

st.set_page_config(page_title="Axis Bank EV", page_icon="🏦")
st.title("Axis Bank - Employment Verification")

# ==========================================
# 🛠️ NANGO FRONTEND UI (JAVASCRIPT COMPONENT)
# ==========================================
# This creates a native HTML button that triggers Nango's secure JS popup modal.
def render_nango_button(provider_id, button_text, color):
    components.html(f"""
        <script src="https://cdn.jsdelivr.net/npm/@nangohq/frontend@latest"></script>
        <button id="auth-btn" style="padding: 10px; background-color: {color}; color: white; border: none; border-radius: 5px; cursor: pointer; width: 100%; font-family: sans-serif; font-weight: bold;">
            {button_text}
        </button>
        <script>
            // Initialize Nango SDK
            const nango = new Nango('{NANGO_PUBLIC_KEY}');
            
            document.getElementById('auth-btn').addEventListener('click', function() {{
                // This opens the Nango popup to securely handle OAuth
                nango.auth('{provider_id}', '{CONNECTION_ID}')
                    .then((result) => console.log('Nango Auth Success!'))
                    .catch((err) => console.log('User cancelled or error', err));
            }});
        </script>
    """, height=50)

# ==========================================
# 🎨 THE EMAIL-FIRST ROUTING ENGINE
# ==========================================
st.write("We use domain pre-discovery to bypass strict corporate firewalls.")
user_input_email = st.text_input("Enter your corporate email to begin (e.g. prabhat@tata.com):")

if user_input_email:
    domain = user_input_email.split("@")[-1].lower()
    
    # 1. THE FIREWALL CHECK
    # Here we route known strict MDM domains to the fallback instantly.
    STRICT_MDM_DOMAINS = ["tata.com", "croma.com", "ey.com", "reliance.com"]
    
    if domain in STRICT_MDM_DOMAINS:
        st.warning(f"🔒 Our telemetry shows {domain.capitalize()} blocks SSO connections. Routing to secure fallback.")
        st.button("📄 Upload Offer Letter / Payslip (EV4)")
        
    # 2. THE HAPPY PATH (NANGO)
    else:
        st.success("⚡ Fast Verification Available!")
        
        col1, col2 = st.columns(2)
        with col1:
            render_nango_button(MICROSOFT_INTEGRATION_ID, "🏢 Verify with Microsoft", "#2F2F2F")
        with col2:
            render_nango_button(GOOGLE_INTEGRATION_ID, "🌐 Verify with Google", "#1A73E8")

# ==========================================
# 📥 NANGO BACKEND API PROXY (DATA FETCH)
# ==========================================
st.divider()
st.write("### Backend Data Verification")
st.write("*(Click this after completing the popup flow above)*")

provider_to_test = st.radio("Which provider did you just test?", ["Google", "Microsoft"], horizontal=True)

if st.button("Fetch Employee Data"):
    # 1. Setup the Nango Proxy Headers
    provider_id = GOOGLE_INTEGRATION_ID if provider_to_test == "Google" else MICROSOFT_INTEGRATION_ID
    
    headers = {
        "Authorization": f"Bearer {NANGO_SECRET_KEY}",
        "Connection-Id": CONNECTION_ID,
        "Provider-Config-Key": provider_id
    }
    
    # 2. Define the exact endpoint to hit via the proxy
    if provider_to_test == "Google":
        proxy_url = "https://api.nango.dev/proxy/oauth2/v3/userinfo"
    else:
        # Microsoft Graph API endpoint
        proxy_url = "https://api.nango.dev/proxy/v1.0/me"

    # 3. Make the API Call
    # Notice we don't send any OAuth tokens! Nango injects them silently.
    response = requests.get(proxy_url, headers=headers)
    
    if response.status_code == 200:
        st.success(f"✅ Data fetched successfully via Nango Proxy for '{CONNECTION_ID}'!")
        st.json(response.json())
    else:
        st.error("Authentication not found. Did you complete the popup flow?")
        st.json(response.json())
