import streamlit as st
import requests
import urllib.parse
import base64
import json

# ==========================================
# ⚙️ CONFIGURATION
# ==========================================
REDIRECT_URI = "https://evdemo.streamlit.app/" 
# Change to "http://localhost:8501/" if testing locally

# --- MICROSOFT CREDENTIALS ---
MS_CLIENT_ID = "a29275f0-c21e-49a3-8e78-5a6659524631" 
MS_CLIENT_SECRET = "RSO8Q~zDrTM~PkNIzAqytp7xU_-hzfrOF18-3ble"
MS_AUTH_URL = "https://login.microsoftonline.com/common/oauth2/v2.0/authorize"
MS_TOKEN_URL = "https://login.microsoftonline.com/common/oauth2/v2.0/token"

# --- GOOGLE CREDENTIALS ---
# 🚨 Replace these with the keys from your Google Cloud Console 🚨
GOOG_CLIENT_ID = "133119225376-8h8c1sr5fgehjb7ud3clgn8ag9l2aou0.apps.googleusercontent.com" 
GOOG_CLIENT_SECRET = "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"
GOOG_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOG_TOKEN_URL = "https://oauth2.googleapis.com/token"

# The bare minimum scopes for both platforms
SCOPE = "openid email"

# ==========================================
# 🛠️ HELPER FUNCTIONS
# ==========================================
def decode_jwt(token):
    payload = token.split('.')[1]
    payload += '=' * (-len(payload) % 4)
    decoded_bytes = base64.urlsafe_b64decode(payload)
    return json.loads(decoded_bytes)

# ==========================================
# 🎨 UI & APP LOGIC
# ==========================================
st.set_page_config(page_title="Axis Bank EV Demo", page_icon="🏦")

st.title("Axis Bank - Employment Verification")
st.write("Select your corporate identity provider to continue.")

query_params = st.query_params

# ------------------------------------------
# CALLBACK HANDLER (Post-Login)
# ------------------------------------------
if "code" in query_params and "state" in query_params:
    auth_code = query_params["code"]
    provider = query_params["state"] # Tells us if they used Google or MS
    
    if provider == "microsoft":
        token_data = {
            "client_id": MS_CLIENT_ID,
            "client_secret": MS_CLIENT_SECRET,
            "code": auth_code,
            "redirect_uri": REDIRECT_URI,
            "grant_type": "authorization_code",
        }
        token_url = MS_TOKEN_URL
        
    elif provider == "google":
        token_data = {
            "client_id": GOOG_CLIENT_ID,
            "client_secret": GOOG_CLIENT_SECRET,
            "code": auth_code,
            "redirect_uri": REDIRECT_URI,
            "grant_type": "authorization_code",
        }
        token_url = GOOG_TOKEN_URL

    # Execute the backend token swap
    response = requests.post(token_url, data=token_data)
    
    if response.status_code == 200:
        result = response.json()
        id_token = result.get("id_token")
        claims = decode_jwt(id_token)
        email = claims.get("email") or claims.get("preferred_username", "Not Provided")
        
        st.success(f"✅ Verified via {provider.capitalize()}!")
        st.divider()
        st.write(f"**Verified Email:** {email}")
        
        # Display provider-specific enterprise claims
        if provider == "microsoft":
            tenant_id = claims.get("tid", "Unknown Tenant")
            st.write(f"**Enterprise Tenant ID:** {tenant_id}")
        elif provider == "google":
            hosted_domain = claims.get("hd", "Personal Account (Failed Corporate Check)")
            st.write(f"**Hosted Domain (Company):** {hosted_domain}")
            
        st.divider()
        if st.button("Restart Demo"):
            st.query_params.clear()
            st.rerun()
    else:
        st.error(f"{provider.capitalize()} Authentication failed: {response.text}")

# ------------------------------------------
# LOGIN BUTTONS (Pre-Login)
# ------------------------------------------
else:
    col1, col2 = st.columns(2)
    
    # Microsoft Button
    ms_params = {
        "client_id": MS_CLIENT_ID,
        "response_type": "code",
        "redirect_uri": REDIRECT_URI,
        "response_mode": "query",
        "scope": SCOPE,
        "state": "microsoft", # Hidden tag
    }
    ms_login_url = f"{MS_AUTH_URL}?{urllib.parse.urlencode(ms_params)}"
    with col1:
        st.link_button("🏢 Verify with Microsoft", ms_login_url, type="secondary", use_container_width=True)

    # Google Button
    goog_params = {
        "client_id": GOOG_CLIENT_ID,
        "response_type": "code",
        "redirect_uri": REDIRECT_URI,
        "scope": SCOPE,
        "state": "google", # Hidden tag
        "prompt": "consent",
    }
    goog_login_url = f"{GOOG_AUTH_URL}?{urllib.parse.urlencode(goog_params)}"
    with col2:
        st.link_button("🌐 Verify with Google", goog_login_url, type="primary", use_container_width=True)
        
    st.caption("🔒 Lowest invasive request prototype. No persistent access requested.")
