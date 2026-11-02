import streamlit as st
import msal

# ==========================================
# ⚙️ CONFIGURATION
# ==========================================
# Your exact Client ID from the Entra dashboard
CLIENT_ID = "a29275f0-c21e-49a3-8e78-5a6659524631" 
# Paste the Secret Value you just generated below
CLIENT_SECRET = "RSO8Q~zDrTM~PkNIzAqytp7xU_-hzfrOF18-3ble"

AUTHORITY = "https://login.microsoftonline.com/common"
REDIRECT_URI = "http://localhost:8501/" 

# 🚨 KEY CHANGE: We dropped "User.Read" completely.
# We now ONLY request OpenID Connect (OIDC) authentication scopes.
# This prevents Microsoft from asking for Graph API directory access, 
# drastically reducing the chance of triggering an IT Admin block.
SCOPE = ["email", "profile", "openid"]

def build_auth_app():
    return msal.ConfidentialClientApplication(
        CLIENT_ID, authority=AUTHORITY, client_credential=CLIENT_SECRET
    )

# ==========================================
# 🎨 UI & APP LOGIC
# ==========================================
st.set_page_config(page_title="Axis Bank EV Demo", page_icon="🏦")

st.title("Axis Bank - Employment Verification")
st.write("Verify your corporate identity to continue with your personal loan application.")

# Streamlit catches the callback code from Microsoft in the URL
query_params = st.query_params

if "code" in query_params:
    auth_code = query_params["code"]
    auth_app = build_auth_app()
    
    # Exchange the code for the cryptographic token
    result = auth_app.acquire_token_by_authorization_code(
        auth_code, scopes=SCOPE, redirect_uri=REDIRECT_URI
    )
    
    # Fallback to checking id_token_claims directly if access_token isn't prominent
    if "access_token" in result or "id_token_claims" in result:
        claims = result.get("id_token_claims", {})
        email = claims.get("preferred_username") or claims.get("email", "Not Provided")
        name = claims.get("name", "Not Provided")
        tenant_id = claims.get("tid", "Personal Account (No Tenant ID)")
        
        st.success("✅ Identity Verified!")
        st.divider()
        st.write(f"**Name:** {name}")
        st.write(f"**Verified Email:** {email}")
        st.write(f"**Tenant ID:** {tenant_id}")
        st.divider()
        
        if st.button("Restart Demo"):
            st.query_params.clear()
            st.rerun()
    else:
        st.error(f"Authentication failed: {result.get('error_description', 'Unknown Error')}")

else:
    auth_app = build_auth_app()
    auth_url = auth_app.get_authorization_request_url(SCOPE, redirect_uri=REDIRECT_URI)
    st.link_button("Sign in with Microsoft", auth_url, type="primary")

st.caption("🔒 Your password is never shared with Axis Bank. This is an illustrative prototype.")
