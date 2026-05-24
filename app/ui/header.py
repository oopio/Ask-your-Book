"""
Main page header — the animated hero banner at the top of the app.
"""

import streamlit as st


def render():
    st.markdown("""
<div style="text-align:center;padding:2.5rem 0;
     background:linear-gradient(135deg,#1e293b 0%,#334155 100%);
     border-radius:12px;margin-bottom:2rem;
     box-shadow:0 8px 32px rgba(0,0,0,0.15);border:1px solid #475569;">
  <h1 style="color:white;font-size:2.8rem;margin:0;
       text-shadow:2px 2px 4px rgba(0,0,0,0.3);font-weight:700;
       font-family:'Inter',sans-serif;">
    📚 ASK YOUR BOOK
  </h1>
  <p style="color:rgba(255,255,255,0.85);font-size:1.1rem;
       margin:0.5rem 0 0 0;font-weight:400;letter-spacing:0.5px;">
    Professional Document Intelligence Platform
  </p>
  <div style="margin-top:1.5rem;">
    <span style="background:rgba(255,255,255,0.15);padding:0.4rem 1.2rem;
          border-radius:8px;font-size:0.85rem;color:white;margin:0 0.5rem;
          font-weight:500;text-transform:uppercase;letter-spacing:0.5px;">
      📊 Analytics
    </span>
    <span style="background:rgba(255,255,255,0.15);padding:0.4rem 1.2rem;
          border-radius:8px;font-size:0.85rem;color:white;margin:0 0.5rem;
          font-weight:500;text-transform:uppercase;letter-spacing:0.5px;">
      🔍 Search
    </span>
    <span style="background:rgba(255,255,255,0.15);padding:0.4rem 1.2rem;
          border-radius:8px;font-size:0.85rem;color:white;margin:0 0.5rem;
          font-weight:500;text-transform:uppercase;letter-spacing:0.5px;">
      🤖 AI Insights
    </span>
  </div>
</div>

<style>
@keyframes float {
  0%   { transform: translateY(0px);  }
  50%  { transform: translateY(-8px); }
  100% { transform: translateY(0px);  }
}
</style>
""", unsafe_allow_html=True)
