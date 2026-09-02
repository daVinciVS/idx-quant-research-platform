from __future__ import annotations

from src.presentation.demo_dashboard import render_demo_dashboard
from src.presentation.theme import configure_page, inject_institutional_theme

configure_page()
inject_institutional_theme()
render_demo_dashboard()