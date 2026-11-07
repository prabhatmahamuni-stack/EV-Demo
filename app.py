import streamlit as st
import requests
import uuid
import streamlit.components.v1 as components

st.set_page_config(page_title="Axis Bank EV Demo", page_icon="🏦")

# ==========================================
# ⚙️ CONFIGURATION
# ==========================================
# Use your original "Default - Full access" Secret Key (ending in cfa6).
NANGO_SECRET_KEY = ""

MICROSOFT_INTEGRATION_ID = "microsoft-entra-id"
GOOGLE_INTEGRATION_ID = "google-oauth"

if 'connection_id' not in st.session_state:
    st.session_state.connection_id = f"axis-{uuid.uuid4().hex[:6]}"

query_params = st.query_params

# ==========================================
# 🔑 1. GENERATE SESSION TOKEN (BACKEND)
# ==========================================
@st.cache_data(ttl=1500)
def fetch_session_token(secret_key, connection_id):
    url = "https://api.nango.dev/connect/sessions"
    headers = {
        "Authorization": f"Bearer {secret_key}",
        "Content-Type": "application/json"
    }
    
    # THE FIX 1: We cryptographically bind the connection_id to the token
    # Change this block inside your fetch_session_token function:
    payload = {
        "end_user": {
            "id": connection_id
        },
        # THE FIX: Remove GOOGLE_INTEGRATION_ID so Nango doesn't crash looking for it
        "allowed_integrations": [MICROSOFT_INTEGRATION_ID]
    }
    
    response = requests.post(url, headers=headers, json=payload)
    if response.status_code in [200, 201]:
        data = response.json()
        return data.get("token") or data.get("data", {}).get("token")
    else:
        st.error(f"Failed to generate session token: {response.text}")
        return None

session_token = fetch_session_token(NANGO_SECRET_KEY, st.session_state.connection_id)

# ==========================================
# 📥 2. SUCCESS & AUTO-FETCH
# ==========================================
if "nango_success" in query_params:
    provider = query_params["provider"]
    provider_id = GOOGLE_INTEGRATION_ID if provider == "google" else MICROSOFT_INTEGRATION_ID
    
    proxy_url = "https://api.nango.dev/proxy/oauth2/v3/userinfo" if provider == "google" else "https://api.nango.dev/proxy/v1.0/me"
    
    headers = {
        "Authorization": f"Bearer {NANGO_SECRET_KEY}",
        "Connection-Id": st.session_state.connection_id,
        "Provider-Config-Key": provider_id
    }
    
    with st.spinner("Securing connection..."):
        response = requests.get(proxy_url, headers=headers)
        
    if response.status_code == 200:
        data = response.json()
        
        email = data.get("email") or data.get("userPrincipalName", "Not Provided")
        name = data.get("name") or data.get("displayName", "Not Provided")
        domain = email.split("@")[-1] if email and "@" in email else "Unknown"
        
        st.success(f"✅ Verified via {provider.capitalize()}!")
        st.write(f"**Verified Name:** {name}")
        st.write(f"**Verified Email:** {email}")
        st.write(f"**Detected Domain:** `{domain}`")
        
        st.divider()
        st.write("#### 🛠️ Raw Nango Payload")
        st.json(data)
        
        if st.button("Restart Demo"):
            st.query_params.clear()
            st.rerun()
            
    else:
        st.error(f"Failed to fetch data from Nango: {response.text}")

# ==========================================
# 🎨 3. NANGO BUTTONS (PRE-LOGIN)
# ==========================================
else:
    st.title("Axis Bank - Employment Verification")
    st.write("Select your corporate identity provider to instantly verify your employment.")
    
    if session_token:
        html_code = f"""
            <div style="display: flex; gap: 10px; font-family: sans-serif;">
                <button onclick="window.login('microsoft')" style="flex: 1; padding: 12px; background-color: #2F2F2F; color: white; border: none; border-radius: 8px; cursor: pointer; font-size: 16px; font-weight: bold;">🏢 Verify with Microsoft</button>
                <button onclick="window.login('google')" style="flex: 1; padding: 12px; background-color: #1A73E8; color: white; border: none; border-radius: 8px; cursor: pointer; font-size: 16px; font-weight: bold;">🌐 Verify with Google</button>
            </div>

            <script type="module">
                import Nango from 'https://cdn.jsdelivr.net/npm/@nangohq/frontend@latest/+esm';
                
                const nango = new Nango({{ connectSessionToken: '{session_token}' }});
                
                window.login = function(provider) {{
                    const provider_id = provider === 'google' ? '{GOOGLE_INTEGRATION_ID}' : '{MICROSOFT_INTEGRATION_ID}';
                    
                    // THE FIX 2: We completely remove the connection_id from the frontend call.
                    nango.auth(provider_id)
                        .then(() => {{
                            const baseUrl = window.parent.location.protocol + "//" + window.parent.location.host + window.parent.location.pathname;
                            window.parent.location.href = baseUrl + "?nango_success=true&provider=" + provider;
                        }})
                        .catch((err) => {{
                            console.error('Nango Error:', err);
                            alert("Authentication failed or was cancelled.");
                        }});
                }}
            </script>
        """
        
        components.html(html_code, height=80)
        st.caption("🔒 Powered by Nango Verified Infrastructure.")
