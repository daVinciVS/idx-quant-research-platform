from pathlib import Path


def test_public_ticker_dashboard_does_not_import_private_broker_modules():
    source = Path(
        "src/presentation/public_ticker_dashboard.py"
    ).read_text(encoding="utf-8")

    assert "broker_flow" not in source
    assert "manual_broker" not in source
    assert "mirae_broker" not in source
    assert "broker_summary" not in source


def test_demo_dashboard_excludes_private_flow_and_exposes_flat_renderers():
    source = Path(
        "src/presentation/demo_dashboard.py"
    ).read_text(encoding="utf-8")

    assert "render_manual_broker_flow_workspace" not in source
    assert "Manual broker flow" not in source
    assert "def render_demo_sidebar() -> DemoCase" in source
    assert "def render_demo_research(case: DemoCase) -> None" in source
    assert "def render_demo_sandbox(case: DemoCase) -> None" in source


def test_streamlit_launcher_adds_project_root_before_src_imports():
    source = Path("apps/streamlit_app.py").read_text(encoding="utf-8")

    assert "PROJECT_ROOT = Path(__file__).resolve().parents[1]" in source
    assert "sys.path.insert(0, str(PROJECT_ROOT))" in source


def test_streamlit_launcher_uses_flat_public_navigation():
    source = Path("apps/streamlit_app.py").read_text(encoding="utf-8")

    assert '"Analyze ticker"' in source
    assert '"Public demo"' in source
    assert '"Paper portfolio sandbox"' in source
    assert "render_demo_dashboard" not in source
    assert source.count("render_demo_sidebar()") == 1