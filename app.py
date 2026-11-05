import streamlit as st
import requests
import uuid

st.set_page_config(page_title="Axis Bank EV", page_icon="🏦")

# ==========================================
# ⚙️ CONFIGURATION
# ==========================================
# 🚨 Paste your keys from the Nango Environment Settings here
NANGO_PUBLIC_KEY = "8cada06d-dfa1-47b1-be93-3b28e084ee1f"
NANGO_SECRET_KEY = "51b311fe-57b9-4a14-b142-44900773cfa6"

# Ensure these match your Nango dashboard exactly
MICROSOFT_INTEGRATION_ID = "microsoft-entra-id"
GOOGLE_INTEGRATION_ID = "google-oauth"

# Generate a unique connection ID per user session
if 'connection_id' not in st.session_state:
    st.session_state.connection_id = f"axis-{uuid.uuid4().hex[:6]}"

query_params = st.query_params

# ==========================================
# 📥 STATE 2: SUCCESS & AUTO-FETCH
# ==========================================
# The JavaScript below automatically appends 'nango_success' to the URL the moment the user logs in.
if "nango_success" in query_params:
    provider = query_params["provider"]
    provider_id = GOOGLE_INTEGRATION_ID if provider == "google" else MICROSOFT_INTEGRATION_ID
    
    # Setup the proxy fetch exactly like your original architecture
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
# 🎨 STATE 1: NANGO BUTTONS (PRE-LOGIN)
# ==========================================
else:
    st.title("Axis Bank - Employment Verification")
    st.write("Select your corporate identity provider to instantly verify your employment.")
    
    # We consolidate the buttons into a single HTML block. This fixes the Streamlit iframe bug
    # and allows the Javascript to instantly reload the parent window upon a successful login.
    html_code = f"""
        <script src="https://cdn.jsdelivr.net/npm/@nangohq/frontend@latest"></script>
        <div style="display: flex; gap: 10px; font-family: sans-serif;">
            <button onclick="login('microsoft')" style="flex: 1; padding: 12px; background-color: #2F2F2F; color: white; border: none; border-radius: 8px; cursor: pointer; font-size: 16px; font-weight: bold;">🏢 Verify with Microsoft</button>
            <button onclick="login('google')" style="flex: 1; padding: 12px; background-color: #1A73E8; color: white; border: none; border-radius: 8px; cursor: pointer; font-size: 16px; font-weight: bold;">🌐 Verify with Google</button>
        </div>

        <script>
            const nango = new Nango('{NANGO_PUBLIC_KEY}');
            
            function login(provider) {{
                const provider_id = provider === 'google' ? '{GOOGLE_INTEGRATION_ID}' : '{MICROSOFT_INTEGRATION_ID}';
                
                nango.auth(provider_id, '{st.session_state.connection_id}')
                    .then(() => {{
                        // THE FIX: The moment auth succeeds, forcefully reload Streamlit to the success state.
                        const baseUrl = window.parent.location.protocol + "//" + window.parent.location.host + window.parent.location.pathname;
                        window.parent.location.href = baseUrl + "?nango_success=true&provider=" + provider;
                    }})
                    .catch((err) => {{
                        console.error('Nango Error:', err);
                        alert("Authentication was blocked or cancelled. Please allow popups for this portal.");
                    }});
            }}
        </script>
    """
    
    import streamlit.components.v1 as components
    components.html(html_code, height=80)
    
    st.caption("🔒 Powered by Nango Verified Infrastructure.")
