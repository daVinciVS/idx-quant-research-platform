from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd
from src.analytics.decision import DecisionLabel, RiskCategory, TradeDecision
from src.application.public_analysis import PublicAnalysisResult
from src.presentation.public_ticker_dashboard import _relative_strength_label


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

_JAKARTA = ZoneInfo("Asia/Jakarta")


def _result(
    *,
    relative_strength_available: bool,
    relative_strength_positive: bool | None,
) -> PublicAnalysisResult:
    decision = TradeDecision(
        label=DecisionLabel.WAIT,
        confidence="Low",
        reasons=(),
        next_action="Wait.",
    )

    return PublicAnalysisResult(
        ticker="BBCA.JK",
        as_of=datetime(2026, 9, 24, 12, tzinfo=_JAKARTA),
        as_of_date="2026-09-23",
        history=pd.DataFrame(),
        latest_close=None,
        sma20=None,
        sma50=None,
        atr14=None,
        resistance_20d=None,
        six_month_high=None,
        trend_template_passed=False,
        extension_risk=False,
        relative_strength_available=relative_strength_available,
        stock_return_20d=None,
        ihsg_return_20d=None,
        relative_strength_spread_20d=None,
        relative_strength_positive=relative_strength_positive,
        risk_category=RiskCategory.UNKNOWN,
        decision=decision,
        trade_plan=None,
        data_status="Test fixture.",
    )


def test_relative_strength_label_marks_outperformance():
    assert _relative_strength_label(
        _result(
            relative_strength_available=True,
            relative_strength_positive=True,
        )
    ) == "Outperforming IHSG"


def test_relative_strength_label_marks_underperformance():
    assert _relative_strength_label(
        _result(
            relative_strength_available=True,
            relative_strength_positive=False,
        )
    ) == "Underperforming IHSG"


def test_relative_strength_label_marks_unavailable_benchmark():
    assert _relative_strength_label(
        _result(
            relative_strength_available=False,
            relative_strength_positive=None,
        )
    ) == "IHSG comparison unavailable"

def test_public_ticker_dashboard_displays_public_relative_strength_context():
    source = Path(
        "src/presentation/public_ticker_dashboard.py"
    ).read_text(encoding="utf-8")

    assert "Stock 20D return" in source
    assert "IHSG 20D return" in source
    assert "Relative-strength spread" in source
    assert "IHSG relative strength:" in source
    assert "IHSG relative strength uses aligned 20-day" in source