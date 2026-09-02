from __future__ import annotations

import streamlit as st


def configure_page() -> None:
    """Configure Streamlit before any UI elements are rendered."""
    st.set_page_config(
        page_title="IDX Quant Research Platform",
        layout="wide",
        initial_sidebar_state="expanded",
    )


def inject_institutional_theme() -> None:
    """Apply the shared dark research-workstation visual system."""
    st.markdown(
        """
        <style>
            :root {
                --bg: #0B0F14;
                --surface: #121922;
                --surface-raised: #18222E;
                --border: #2A3645;
                --text: #E8EDF2;
                --muted: #A9B4C0;
                --positive: #5DD39E;
                --warning: #F6C85F;
                --negative: #F26B6B;
                --info: #6DA9FF;
                --trend: #74C0FC;
            }

            .stApp {
                background: var(--bg);
            }

            [data-testid="stSidebar"] {
                background: #0E141C;
                border-right: 1px solid var(--border);
            }

            [data-testid="stSidebar"] > div:first-child {
                padding-top: 1.5rem;
            }

            .block-container {
                max-width: 1440px;
                padding-top: 3.6rem;
                padding-bottom: 3rem;
            }

            h1, h2, h3 {
                letter-spacing: -0.02em;
            }

            h1 {
                font-size: 2.25rem !important;
                margin-bottom: 0.15rem;
            }

            h2 {
                font-size: 1.25rem !important;
                margin-top: 0.5rem;
            }

            h3 {
                color: var(--muted);
                font-size: 1rem !important;
                letter-spacing: 0.08em;
                text-transform: uppercase;
            }

            .eyebrow {
                color: var(--trend);
                font-size: 0.72rem;
                font-weight: 700;
                letter-spacing: 0.12em;
                line-height: 1.4;
                margin-bottom: 0.55rem;
                padding-top: 0.2rem;
                text-transform: uppercase;
            }

            .subtle-copy {
                color: var(--muted);
                font-size: 0.92rem;
                line-height: 1.55;
            }

            .panel {
                background: var(--surface);
                border: 1px solid var(--border);
                border-radius: 10px;
                margin-bottom: 1rem;
                padding: 1.1rem 1.15rem;
            }

            .status-strip {
                align-items: center;
                background: var(--surface);
                border: 1px solid var(--border);
                border-radius: 10px;
                display: flex;
                flex-wrap: wrap;
                gap: 0.8rem;
                margin: 1.15rem 0 1rem;
                padding: 0.85rem 1rem;
            }

            .status-badge {
                border-radius: 999px;
                display: inline-block;
                font-size: 0.72rem;
                font-weight: 800;
                letter-spacing: 0.08em;
                padding: 0.34rem 0.62rem;
                white-space: nowrap;
            }

            .status-positive {
                background: rgba(93, 211, 158, 0.16);
                border: 1px solid rgba(93, 211, 158, 0.42);
                color: var(--positive);
            }

            .status-warning {
                background: rgba(246, 200, 95, 0.14);
                border: 1px solid rgba(246, 200, 95, 0.42);
                color: var(--warning);
            }

            .status-negative {
                background: rgba(242, 107, 107, 0.14);
                border: 1px solid rgba(242, 107, 107, 0.42);
                color: var(--negative);
            }

            .status-info {
                background: rgba(109, 169, 255, 0.14);
                border: 1px solid rgba(109, 169, 255, 0.42);
                color: var(--info);
            }

            .status-meta {
                color: var(--muted);
                font-size: 0.82rem;
            }

            .callout {
                background: #101A20;
                border-left: 3px solid var(--trend);
                border-radius: 6px;
                color: var(--text);
                line-height: 1.5;
                padding: 0.85rem 0.95rem;
            }

            .metric-label {
                color: var(--muted);
                font-size: 0.74rem;
                font-weight: 700;
                letter-spacing: 0.06em;
                text-transform: uppercase;
            }

            .metric-value {
                color: var(--text);
                font-size: 1.35rem;
                font-weight: 650;
                margin-top: 0.2rem;
            }

            .metric-detail {
                color: var(--muted);
                font-size: 0.78rem;
                margin-top: 0.15rem;
            }

            .sidebar-title {
                color: var(--text);
                font-size: 0.92rem;
                font-weight: 800;
                letter-spacing: 0.1em;
                margin-bottom: 0.3rem;
                text-transform: uppercase;
            }

            .sidebar-caption {
                color: var(--muted);
                font-size: 0.78rem;
                line-height: 1.5;
            }

            div[data-testid="stDataFrame"] {
                border: 1px solid var(--border);
                border-radius: 8px;
                overflow: hidden;
            }

            .footer-note {
                border-top: 1px solid var(--border);
                color: var(--muted);
                font-size: 0.78rem;
                line-height: 1.55;
                margin-top: 2rem;
                padding-top: 1rem;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )