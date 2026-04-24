def load_css() -> str:
    return """<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=Material+Symbols+Rounded:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200&display=block');
html,body,[class*="css"]{font-family:'Inter',-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif !important;}
#MainMenu,footer,header{visibility:hidden;}
.stApp{background:#f0f4f8 !important;}
.block-container{padding:2rem 2.8rem 3rem !important;max-width:1300px !important;}
[data-testid="stSidebar"]{background:linear-gradient(165deg,#092e31 0%,#0d4a4f 45%,#145c63 80%,#1a7a82 100%) !important;border-right:none !important;box-shadow:6px 0 30px rgba(0,0,0,0.15) !important;}
[data-testid="stSidebarContent"]{padding:1.5rem 1.2rem !important;}
[data-testid="stSidebar"] p{color:rgba(255,255,255,0.80) !important;}
[data-testid="stSidebar"] label{color:rgba(255,255,255,0.72) !important;}
[data-testid="stSidebar"] span{color:rgba(255,255,255,0.80) !important;}
[data-testid="stSidebar"] .stMarkdown p{color:rgba(255,255,255,0.80) !important;}
[data-testid="stSidebar"] [data-baseweb="textarea"]{background:rgba(255,255,255,0.10) !important;border:1.5px solid rgba(255,255,255,0.22) !important;border-radius:13px !important;transition:background 0.2s,border-color 0.2s,box-shadow 0.2s !important;}
[data-testid="stSidebar"] [data-baseweb="textarea"]:focus-within{background:rgba(255,255,255,0.17) !important;border-color:rgba(255,255,255,0.58) !important;box-shadow:0 0 0 3px rgba(255,255,255,0.09),0 0 24px rgba(29,144,151,0.35) !important;}
[data-testid="stSidebar"] [data-baseweb="textarea"] [data-baseweb="base-input"]{background:transparent !important;}
[data-testid="stSidebar"] [data-baseweb="textarea"] textarea{background:transparent !important;color:rgba(255,255,255,0.92) !important;-webkit-text-fill-color:rgba(255,255,255,0.92) !important;caret-color:white !important;font-size:0.875rem !important;line-height:1.68 !important;letter-spacing:0.01em !important;}
[data-testid="stSidebar"] [data-baseweb="textarea"] textarea::placeholder{color:rgba(255,255,255,0.35) !important;-webkit-text-fill-color:rgba(255,255,255,0.35) !important;}
[data-testid="stSidebar"] [data-baseweb="input"]{background:rgba(255,255,255,0.10) !important;border:1.5px solid rgba(255,255,255,0.22) !important;border-radius:11px !important;transition:background 0.2s,border-color 0.2s,box-shadow 0.2s !important;}
[data-testid="stSidebar"] [data-baseweb="input"]:focus-within{background:rgba(255,255,255,0.17) !important;border-color:rgba(255,255,255,0.58) !important;box-shadow:0 0 0 3px rgba(255,255,255,0.09),0 0 24px rgba(29,144,151,0.35) !important;}
[data-testid="stSidebar"] [data-baseweb="input"] [data-baseweb="base-input"]{background:transparent !important;}
[data-testid="stSidebar"] [data-baseweb="input"] input{background:transparent !important;color:rgba(255,255,255,0.92) !important;-webkit-text-fill-color:rgba(255,255,255,0.92) !important;caret-color:white !important;font-size:0.875rem !important;letter-spacing:0.01em !important;}
[data-testid="stSidebar"] [data-baseweb="input"] input::placeholder{color:rgba(255,255,255,0.35) !important;-webkit-text-fill-color:rgba(255,255,255,0.35) !important;}
[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"]{background:rgba(255,255,255,0.07) !important;border:1.5px dashed rgba(255,255,255,0.28) !important;border-radius:14px !important;transition:background 0.2s,border-color 0.2s !important;}
[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"]:hover{background:rgba(255,255,255,0.13) !important;border-color:rgba(255,255,255,0.50) !important;}
[data-testid="stSidebar"] [data-testid="stFileUploaderDropzoneInstructions"]{color:rgba(255,255,255,0.58) !important;}
[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] button{background:rgba(255,255,255,0.12) !important;color:white !important;border:1px solid rgba(255,255,255,0.28) !important;border-radius:8px !important;font-size:0.82rem !important;font-weight:500 !important;transition:all 0.2s !important;}
[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] button:hover{background:rgba(255,255,255,0.22) !important;border-color:rgba(255,255,255,0.50) !important;}
[data-testid="stSidebar"] [data-testid="stFileUploaderFile"]{background:none !important;border:none !important;}
[data-testid="stSidebar"] [data-testid="stFileUploaderFile"] *{color:rgba(255,255,255,0.92) !important;-webkit-text-fill-color:rgba(255,255,255,0.92) !important;}
[data-testid="stSidebar"] [data-testid="stFileUploaderFileName"]{color:white !important;-webkit-text-fill-color:white !important;font-weight:500 !important;}
[data-testid="stSidebar"] [data-testid="stFileUploaderDeleteBtn"] button{background:none !important;color:rgba(255,255,255,0.50) !important;border:none !important;}
[data-testid="stSidebar"] [data-testid="stFileUploaderDeleteBtn"] button:hover{color:rgba(255,120,120,0.90) !important;background:none !important;}
[data-testid="stSidebar"] [data-testid="stFileUploaderDropzoneInstructions"] span{color:rgba(255,255,255,0.58) !important;}
[data-testid="stSidebar"] hr{border-color:rgba(255,255,255,0.10) !important;margin:1.1rem 0 !important;}
[data-testid="stSidebar"] .stButton>button{background:rgba(255,255,255,0.09) !important;color:rgba(255,255,255,0.85) !important;border:1px solid rgba(255,255,255,0.16) !important;border-radius:10px !important;font-weight:500 !important;font-size:0.86rem !important;transition:all 0.2s !important;}
[data-testid="stSidebar"] .stButton>button:hover{background:rgba(255,255,255,0.17) !important;border-color:rgba(255,255,255,0.30) !important;}
[data-testid="stSidebar"] .stButton>button[kind="primary"]{background:linear-gradient(135deg,#1d9097,#0f6467) !important;border:none !important;box-shadow:0 4px 16px rgba(0,0,0,0.22) !important;color:white !important;}
[data-testid="stSidebar"] .stButton>button[kind="primary"]:hover{box-shadow:0 6px 22px rgba(0,0,0,0.32) !important;transform:translateY(-1px) !important;}
[data-testid="stSidebar"] .stFormSubmitButton>button{background:rgba(255,255,255,0.10) !important;color:rgba(255,255,255,0.88) !important;border:1px solid rgba(255,255,255,0.18) !important;border-radius:10px !important;font-weight:500 !important;transition:all 0.2s !important;}
[data-testid="stSidebar"] .stFormSubmitButton>button:hover{background:rgba(255,255,255,0.19) !important;}
[data-testid="stSidebar"] .stAlert{background:rgba(255,255,255,0.10) !important;border:1px solid rgba(255,255,255,0.18) !important;color:white !important;border-radius:10px !important;}
[data-testid="stSidebar"] .stAlert p{color:white !important;}
[data-testid="stSidebar"] .section-title{color:rgba(255,255,255,0.40) !important;}
[data-testid="stSidebar"] .small-muted{color:rgba(255,255,255,0.48) !important;}
[data-testid="stSidebarCollapseButton"]{display:none !important;}
[data-testid="collapsedControl"]{display:none !important;}
.stTabs [data-baseweb="tab-list"]{background:white !important;border:1px solid #dde3ec !important;border-radius:14px !important;padding:5px 6px !important;gap:3px !important;width:fit-content !important;box-shadow:0 1px 5px rgba(0,0,0,0.05) !important;}
.stTabs [data-baseweb="tab"]{background:transparent !important;border-radius:10px !important;padding:8px 22px !important;font-size:0.855rem !important;font-weight:500 !important;color:#64748b !important;border:none !important;transition:background 0.15s,color 0.15s !important;letter-spacing:0.01em !important;}
.stTabs [data-baseweb="tab"]:not([aria-selected="true"]):hover{background:#eef2f7 !important;color:#334155 !important;}
.stTabs [data-baseweb="tab"][aria-selected="true"]{background:linear-gradient(135deg,#0f6467,#1d9097) !important;color:white !important;box-shadow:0 3px 12px rgba(15,100,103,0.38) !important;}
.stTabs [data-baseweb="tab-border"]{display:none !important;}
.stTabs [data-baseweb="tab-highlight"]{display:none !important;}
.stTabs [data-baseweb="tab-panel"]{padding-top:1.6rem !important;}
.stButton>button{border-radius:10px !important;font-family:'Inter',sans-serif !important;font-weight:500 !important;font-size:0.875rem !important;transition:all 0.18s !important;border:1.5px solid #dde3ec !important;background:white !important;color:#374151 !important;letter-spacing:0.01em !important;box-shadow:0 1px 3px rgba(0,0,0,0.05) !important;}
.stButton>button:hover{border-color:#0f6467 !important;color:#0f6467 !important;background:#f0fafa !important;box-shadow:0 3px 10px rgba(15,100,103,0.14) !important;}
.stButton>button[kind="primary"]{background:linear-gradient(135deg,#0f6467,#1d9097) !important;color:white !important;border:none !important;box-shadow:0 4px 14px rgba(15,100,103,0.34) !important;}
.stButton>button[kind="primary"]:hover{box-shadow:0 6px 22px rgba(15,100,103,0.50) !important;transform:translateY(-1px) !important;}
.stButton>button:disabled{opacity:0.42 !important;cursor:not-allowed !important;transform:none !important;}
[data-testid="metric-container"]{background:white !important;border:1px solid #e4eaf2 !important;border-radius:16px !important;padding:20px 22px !important;box-shadow:0 2px 8px rgba(0,0,0,0.05) !important;transition:box-shadow 0.2s !important;}
[data-testid="metric-container"]:hover{box-shadow:0 5px 18px rgba(0,0,0,0.09) !important;}
[data-testid="stMetricLabel"] p{font-size:0.72rem !important;font-weight:700 !important;text-transform:uppercase !important;letter-spacing:0.09em !important;color:#64748b !important;}
[data-testid="stMetricValue"]{font-size:1.9rem !important;font-weight:800 !important;color:#0f172a !important;letter-spacing:-0.6px !important;}
.stProgress>div{border-radius:99px !important;height:7px !important;background:#e4eaf2 !important;}
.stProgress>div>div{background:linear-gradient(90deg,#0f6467,#1d9097) !important;border-radius:99px !important;}
[data-testid="stChatInput"]{border-radius:14px !important;border:1.5px solid #dde3ec !important;background:white !important;box-shadow:0 2px 10px rgba(0,0,0,0.06) !important;}
[data-testid="stAlert"]{border-radius:12px !important;}
.material-symbols-rounded{font-family:'Material Symbols Rounded';font-weight:normal;font-style:normal;line-height:1;letter-spacing:normal;text-transform:none;display:inline-block;white-space:nowrap;direction:ltr;font-feature-settings:'liga';-webkit-font-feature-settings:'liga';-webkit-font-smoothing:antialiased;}
.material-symbols-rounded.icon{font-size:1.1em;vertical-align:-0.17em;}
.sidebar-brand{font-size:1.42rem;font-weight:800;color:white !important;letter-spacing:-0.5px;}
.sidebar-subtitle{font-size:0.79rem;color:rgba(255,255,255,0.52) !important;line-height:1.55;margin-top:5px;}
.section-title{font-size:0.71rem;font-weight:700;text-transform:uppercase;letter-spacing:0.13em;color:#94a3b8;margin-bottom:12px;display:flex;align-items:center;gap:7px;}
.small-muted{font-size:0.77rem;color:#94a3b8;margin:4px 0;line-height:1.55;}
.metric-card{background:rgba(255,255,255,0.10);border:1px solid rgba(255,255,255,0.12);border-radius:13px;padding:14px 16px;text-align:center;}
.metric-value{font-size:1.55rem;font-weight:800;color:white !important;letter-spacing:-0.4px;}
.metric-label{font-size:0.66rem;font-weight:700;text-transform:uppercase;letter-spacing:0.11em;color:rgba(255,255,255,0.45) !important;margin-top:4px;}
.app-hero{padding:28px 0 20px 0;}
.app-kicker{font-size:0.72rem;font-weight:700;text-transform:uppercase;letter-spacing:0.15em;color:#0f6467;margin-bottom:10px;display:flex;align-items:center;gap:6px;}
.app-title{font-size:2.15rem;font-weight:800;color:#0f172a;margin:0 0 10px 0;letter-spacing:-0.8px;line-height:1.18;}
.app-subtitle{font-size:0.97rem;color:#64748b;margin:0;line-height:1.7;}
.empty-state{text-align:center;padding:64px 28px;border:2px dashed #dde3ec;border-radius:22px;background:white;margin:16px 0;box-shadow:0 2px 10px rgba(0,0,0,0.04);}
.empty-icon{margin-bottom:18px;}
.empty-icon .material-symbols-rounded{font-size:3rem;color:#cbd5e1;}
.empty-title{font-size:1.04rem;font-weight:700;color:#374151;margin:0 0 8px;}
.empty-copy{font-size:0.87rem;color:#94a3b8;max-width:290px;margin:0 auto;line-height:1.7;}
.flashcard-shell{background:white;border:1px solid #e4eaf2;border-radius:22px;padding:30px 32px;box-shadow:0 4px 22px rgba(0,0,0,0.048);margin:12px 0;transition:all 0.22s;}
.flashcard-shell:hover{box-shadow:0 10px 36px rgba(0,0,0,0.09);transform:translateY(-2px);}
.flashcard-meta{display:flex;align-items:center;gap:10px;font-size:0.76rem;color:#94a3b8;margin-bottom:18px;}
.flashcard-question{font-size:1.12rem;font-weight:600;color:#0f172a;line-height:1.68;}
.flashcard-answer{background:linear-gradient(135deg,#f0fdf4,#ecfdf5);border:1px solid #a7f3d0;border-radius:15px;padding:20px 26px;margin:14px 0;font-size:0.95rem;color:#064e3b;line-height:1.68;}
.answer-title{font-size:0.67rem;font-weight:700;text-transform:uppercase;letter-spacing:0.13em;color:#059669;margin-bottom:8px;}
.pill{display:inline-flex;align-items:center;padding:3px 12px;border-radius:99px;font-size:0.71rem;font-weight:700;letter-spacing:0.04em;}
.pill-easy{background:#dcfce7;color:#15803d;}
.pill-medium{background:#fef3c7;color:#92400e;}
.pill-hard{background:#fee2e2;color:#991b1b;}
.chat-welcome{text-align:center;padding:60px 20px;}
.chat-welcome-icon{font-size:3rem;margin-bottom:18px;opacity:0.5;}
.chat-welcome-title{font-size:1.02rem;font-weight:700;color:#374151;margin-bottom:8px;}
.chat-welcome-sub{font-size:0.87rem;color:#94a3b8;line-height:1.7;max-width:320px;margin:0 auto;}
.summary-chip{display:inline-flex;align-items:center;background:#eff6ff;color:#1d4ed8;border-radius:99px;padding:4px 16px;font-size:0.75rem;font-weight:700;margin-bottom:18px;letter-spacing:0.04em;border:1px solid #bfdbfe;}
</style>"""
