import streamlit as st
import requests
import urllib.parse
import base64
import json

# ==========================================
# ⚙️ CONFIGURATION
# ==========================================
CLIENT_ID = "a29275f0-c21e-49a3-8e78-5a6659524631" 
CLIENT_SECRET = "RSO8Q~zDrTM~PkNIzAqytp7xU_-hzfrOF18-3ble"

# Ensure this matches your Azure App Registration exactly
REDIRECT_URI = "https://evdemo.streamlit.app/" 

# 🚨 THE BARE MINIMUM SCOPE
# We bypass MSAL to strictly ask ONLY for openid and email.
# We explicitly drop "profile" (Name) and "offline_access" (Maintain access).
SCOPE = "openid email"

AUTH_URL = "https://login.microsoftonline.com/common/oauth2/v2.0/authorize"
TOKEN_URL = "https://login.microsoftonline.com/common/oauth2/v2.0/token"

# ==========================================
# 🛠️ HELPER FUNCTIONS
# ==========================================
def decode_jwt(token):
    # JWTs have 3 parts separated by dots. The middle part is the data payload.
    payload = token.split('.')[1]
    # Add padding if required by base64
    payload += '=' * (-len(payload) % 4)
    decoded_bytes = base64.urlsafe_b64decode(payload)
    return json.loads(decoded_bytes)

# ==========================================
# 🎨 UI & APP LOGIC
# ==========================================
st.set_page_config(page_title="Axis Bank EV Demo", page_icon="🏦")

st.title("Axis Bank - Employment Verification")
st.write("Verify your corporate email to continue.")

query_params = st.query_params

if "code" in query_params:
    auth_code = query_params["code"]
    
    # Manually exchange the code for a token (Bypassing MSAL entirely)
    token_data = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "code": auth_code,
        "redirect_uri": REDIRECT_URI,
        "grant_type": "authorization_code",
    }
    
    response = requests.post(TOKEN_URL, data=token_data)
    
    if response.status_code == 200:
        result = response.json()
        id_token = result.get("id_token")
        
        # Decode the token payload
        claims = decode_jwt(id_token)
        email = claims.get("email") or claims.get("preferred_username", "Not Provided")
        tenant_id = claims.get("tid", "Unknown Tenant")
        
        st.success("✅ Email Verified!")
        st.divider()
        st.write(f"**Verified Email:** {email}")
        st.write(f"**Tenant ID:** {tenant_id}")
        st.write("*(Notice: Name is not fetched because 'profile' scope was dropped)*")
        st.divider()
        
        if st.button("Restart Demo"):
            st.query_params.clear()
            st.rerun()
    else:
        st.error(f"Authentication failed: {response.text}")

else:
    # Manually construct the login URL
    auth_params = {
        "client_id": CLIENT_ID,
        "response_type": "code",
        "redirect_uri": REDIRECT_URI,
        "response_mode": "query",
        "scope": SCOPE,
    }
    login_url = f"{AUTH_URL}?{urllib.parse.urlencode(auth_params)}"
    
    st.link_button("Verify Corporate Email", login_url, type="primary")

st.caption("🔒 Lowest invasive request prototype. No persistent access requested.")
