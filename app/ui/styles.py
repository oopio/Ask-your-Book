"""
All CSS for the app — injected once via st.markdown().
Dark/light mode is resolved at call time from session state.
"""

import streamlit as st


def inject():
    """Inject the full CSS block into the current Streamlit page."""
    dark = st.session_state.get("dark_mode", True)

    # CSS variable values that differ between modes
    primary_bg    = "linear-gradient(135deg,#0f172a 0%,#1e293b 100%)" if dark else "linear-gradient(135deg,#f8fafc 0%,#e2e8f0 100%)"
    secondary_bg  = "rgba(30,41,59,0.8)"   if dark else "rgba(255,255,255,0.8)"
    glass_bg      = "rgba(30,41,59,0.1)"   if dark else "rgba(255,255,255,0.1)"
    text_primary  = "#f8fafc"  if dark else "#1e293b"
    text_secondary= "#94a3b8"  if dark else "#64748b"
    border_color  = "rgba(148,163,184,0.2)" if dark else "rgba(100,116,139,0.2)"
    shadow_light  = "0 4px 20px rgba(0,0,0,0.3)"  if dark else "0 4px 20px rgba(0,0,0,0.1)"
    shadow_heavy  = "0 8px 40px rgba(0,0,0,0.4)"  if dark else "0 8px 40px rgba(0,0,0,0.15)"
    active_card_bg= "rgba(16,185,129,0.1)" if dark else "rgba(16,185,129,0.05)"
    badge_tag_bg  = "rgba(148,163,184,0.2)" if dark else "rgba(100,116,139,0.1)"
    shimmer_bg    = "linear-gradient(90deg,#374151 25%,#4b5563 50%,#374151 75%)" if dark else "linear-gradient(90deg,#f1f5f9 25%,#e2e8f0 50%,#f1f5f9 75%)"
    btn_secondary_bg = secondary_bg

    st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

:root {{
  --primary-bg:    {primary_bg};
  --secondary-bg:  {secondary_bg};
  --glass-bg:      {glass_bg};
  --text-primary:  {text_primary};
  --text-secondary:{text_secondary};
  --border-color:  {border_color};
  --accent-primary:#3b82f6;
  --accent-secondary:#8b5cf6;
  --success:       #10b981;
  --shadow-light:  {shadow_light};
  --shadow-heavy:  {shadow_heavy};
}}

.main {{
  padding:0.5rem; background:var(--primary-bg); min-height:100vh;
  font-family:'Inter',-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;
  transition:all 0.3s cubic-bezier(0.4,0,0.2,1);
}}

/* ── Book cards ── */
.book-card {{
  background:var(--secondary-bg); backdrop-filter:blur(20px);
  border-radius:16px; padding:1.5rem; margin-bottom:1rem;
  border:1px solid var(--border-color); cursor:pointer;
  transition:all 0.4s cubic-bezier(0.4,0,0.2,1); position:relative; overflow:hidden;
}}
.book-card::after {{
  content:''; position:absolute; top:0; left:0; width:4px; height:100%;
  background:linear-gradient(180deg,var(--accent-primary) 0%,var(--accent-secondary) 100%);
  transition:width 0.3s ease;
}}
.book-card:hover {{ transform:translateY(-6px) scale(1.02); box-shadow:var(--shadow-heavy); border-color:var(--accent-primary); }}
.book-card:hover::after {{ width:8px; }}
.book-card.active {{
  border-color:var(--success); background:{active_card_bg};
  animation:pulse-glow 3s ease-in-out infinite;
}}
@keyframes pulse-glow {{
  0%,100% {{ box-shadow:0 0 20px rgba(16,185,129,0.3); }}
  50%      {{ box-shadow:0 0 30px rgba(16,185,129,0.5); }}
}}
.book-title {{ font-size:1rem; font-weight:600; color:var(--text-primary); margin-bottom:0.5rem; transition:all 0.3s ease; }}
.book-card:hover .book-title {{ color:var(--accent-primary); transform:translateX(4px); }}
.book-meta  {{ font-size:0.85rem; color:var(--text-secondary); }}

/* ── Status badges ── */
.status-badge {{
  display:inline-block; padding:0.3rem 0.8rem; border-radius:12px;
  font-size:0.75rem; font-weight:600; margin-top:0.75rem;
  text-transform:uppercase; letter-spacing:0.5px;
}}
.status-active    {{ background:linear-gradient(135deg,var(--success) 0%,#059669 100%); color:white; box-shadow:0 4px 15px rgba(16,185,129,0.3); }}
.status-available {{ background:rgba(59,130,246,0.2); color:var(--accent-primary); border:1px solid var(--accent-primary); }}

/* ── Category / tag badges ── */
.badge-category {{
  background:linear-gradient(135deg,var(--accent-primary) 0%,var(--accent-secondary) 100%);
  color:white; padding:0.3rem 0.8rem; border-radius:12px; font-size:0.7rem;
  font-weight:600; margin-right:0.5rem; margin-top:0.5rem; display:inline-block;
  text-transform:uppercase; letter-spacing:0.5px;
}}
.badge-tag {{
  background:{badge_tag_bg}; color:var(--text-secondary);
  padding:0.25rem 0.7rem; border-radius:10px; font-size:0.65rem; font-weight:500;
  margin-right:0.4rem; margin-top:0.4rem; display:inline-block;
  border:1px solid var(--border-color);
}}

/* ── Source passages ── */
.source-passage {{
  background:var(--secondary-bg); backdrop-filter:blur(10px);
  border:1px solid var(--border-color); border-radius:12px;
  padding:1rem; margin:0.75rem 0; font-size:0.9rem;
  transition:all 0.3s cubic-bezier(0.4,0,0.2,1);
}}
.source-passage:hover {{ transform:translateX(8px) scale(1.02); box-shadow:var(--shadow-light); border-color:var(--accent-primary); }}
.source-header {{ display:flex; justify-content:space-between; margin-bottom:0.75rem; font-weight:600; color:var(--text-primary); font-size:0.85rem; }}
.source-similarity {{
  background:linear-gradient(135deg,var(--accent-primary) 0%,var(--accent-secondary) 100%);
  color:white; padding:0.2rem 0.6rem; border-radius:8px; font-size:0.75rem; font-weight:600;
}}

/* ── Buttons ── */
.stButton > button {{
  border-radius:16px !important; font-weight:600 !important;
  transition:all 0.3s cubic-bezier(0.4,0,0.2,1) !important;
  border:1px solid var(--border-color) !important;
  text-transform:uppercase !important; letter-spacing:0.5px !important;
  font-size:0.85rem !important;
}}
.stButton > button[kind="primary"] {{
  background:linear-gradient(135deg,var(--accent-primary) 0%,var(--accent-secondary) 100%) !important;
  color:white !important; box-shadow:0 4px 20px rgba(59,130,246,0.3) !important;
  border-color:var(--accent-primary) !important;
}}
.stButton > button[kind="secondary"] {{
  background:{btn_secondary_bg} !important; color:var(--text-secondary) !important;
}}
.stButton > button[kind="secondary"]:hover {{
  color:var(--text-primary) !important; border-color:var(--accent-primary) !important;
  box-shadow:0 4px 15px rgba(59,130,246,0.2) !important;
}}

/* ── Shimmer / animations ── */
@keyframes shimmer-loading {{
  0%   {{ background-position:-200px 0; }}
  100% {{ background-position:calc(200px + 100%) 0; }}
}}
.shimmer {{
  background:{shimmer_bg}; background-size:200px 100%;
  animation:shimmer-loading 1.5s infinite; border-radius:8px; height:20px; margin:0.5rem 0;
}}

/* ── Scrollbar ── */
::-webkit-scrollbar {{ width:8px; }}
::-webkit-scrollbar-track {{ background:var(--glass-bg); border-radius:10px; }}
::-webkit-scrollbar-thumb {{
  background:linear-gradient(135deg,var(--accent-primary) 0%,var(--accent-secondary) 100%);
  border-radius:10px;
}}

/* ── Hide Streamlit chrome ── */
#MainMenu {{ visibility:hidden; }}
footer    {{ visibility:hidden; }}
.stDeployButton {{ display:none; }}

.single-view-container {{ max-width:100% !important; padding:0 1rem !important; }}
</style>
""", unsafe_allow_html=True)
