from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st  # noqa: E402
from src.presentation.demo_dashboard import (  # noqa: E402
    render_demo_research,
    render_demo_sandbox,
    render_demo_sidebar,
)
from src.presentation.public_ticker_dashboard import (  # noqa: E402
    render_public_ticker_dashboard,
)
from src.presentation.theme import (  # noqa: E402
    configure_page,
    inject_institutional_theme,
)

configure_page()
inject_institutional_theme()

selected_demo_case = render_demo_sidebar()

ticker_tab, demo_tab, sandbox_tab = st.tabs(
    [
        "Analyze ticker",
        "Public demo",
        "Paper portfolio sandbox",
    ]
)

with ticker_tab:
    render_public_ticker_dashboard()

with demo_tab:
    render_demo_research(selected_demo_case)

with sandbox_tab:
    render_demo_sandbox(selected_demo_case)