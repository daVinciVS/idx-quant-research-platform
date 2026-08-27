import math
from datetime import datetime
from pathlib import Path
from typing import Any
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

NAVY = colors.HexColor("#102A43")
BLUE = colors.HexColor("#1F4E78")
MID_BLUE = colors.HexColor("#D9EAF7")
LIGHT_BLUE = colors.HexColor("#EDF4FA")
LIGHT_GRAY = colors.HexColor("#F4F6F8")
MEDIUM_GRAY = colors.HexColor("#D9E1E8")
DARK_GRAY = colors.HexColor("#334E68")
WHITE = colors.white

GREEN_FILL = colors.HexColor("#E2F0D9")
GREEN_TEXT = colors.HexColor("#276749")

YELLOW_FILL = colors.HexColor("#FFF2CC")
YELLOW_TEXT = colors.HexColor("#8A5A00")

RED_FILL = colors.HexColor("#FCE4D6")
RED_TEXT = colors.HexColor("#9B2C2C")


def safe_text(value: Any, fallback: str = "N/A") -> str:
    if value is None:
        return fallback

    text = str(value).strip()

    if not text or text.lower() == "nan":
        return fallback

    return text


def format_number(value: Any, decimals: int = 2) -> str:
    try:
        number = float(value)

        if math.isnan(number) or math.isinf(number):
            return "N/A"

        return f"{number:,.{decimals}f}"

    except (TypeError, ValueError):
        return "N/A"


def get_status_colors(status: str) -> tuple:
    normalized = safe_text(status).upper()

    if any(
        keyword in normalized
        for keyword in [
            "STRONG BUY",
            "BUY CANDIDATE",
            "PASSED",
            "CONNECTED",
            "NORMAL",
            "MARKUP",
            "CONFIRMED",
        ]
    ):
        return GREEN_FILL, GREEN_TEXT

    if any(
        keyword in normalized
        for keyword in [
            "HOLD",
            "WATCHLIST",
            "EXTENDED",
            "MODERATE",
            "WAIT",
            "PARTIAL",
        ]
    ):
        return YELLOW_FILL, YELLOW_TEXT

    return RED_FILL, RED_TEXT


def p(value: Any, style: ParagraphStyle) -> Paragraph:
    return Paragraph(
        escape(safe_text(value)),
        style,
    )


def metric_box(
    label: str,
    value: str,
    width: float,
    label_style: ParagraphStyle,
    value_style: ParagraphStyle,
) -> Table:
    box = Table(
        [
            [p(label, label_style)],
            [p(value, value_style)],
        ],
        colWidths=[width],
    )

    box.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), LIGHT_BLUE),
                ("BOX", (0, 0), (-1, -1), 0.35, MEDIUM_GRAY),
                ("LINEBELOW", (0, 0), (-1, 0), 0.25, MEDIUM_GRAY),
                ("TOPPADDING", (0, 0), (-1, 0), 5),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 3),
                ("TOPPADDING", (0, 1), (-1, 1), 3),
                ("BOTTOMPADDING", (0, 1), (-1, 1), 6),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]
        )
    )

    return box


def section_header(title: str, style: ParagraphStyle) -> Table:
    header = Table(
        [[p(title, style)]],
        colWidths=[18.8 * cm],
    )

    header.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), NAVY),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("LEFTPADDING", (0, 0), (-1, -1), 7),
                ("RIGHTPADDING", (0, 0), (-1, -1), 7),
            ]
        )
    )

    return header


def generate_pdf_report(
    output_path: str | Path,
    ticker: str,
    company_name: str,
    latest_close: float,
    metrics: dict[str, Any],
) -> Path:
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    document = SimpleDocTemplate(
        str(output_path),
        pagesize=A4,
        rightMargin=1.1 * cm,
        leftMargin=1.1 * cm,
        topMargin=0.9 * cm,
        bottomMargin=0.8 * cm,
    )

    styles = getSampleStyleSheet()

    report_title_style = ParagraphStyle(
        "ReportTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=15,
        leading=18,
        textColor=WHITE,
        alignment=TA_LEFT,
    )

    report_subtitle_style = ParagraphStyle(
        "ReportSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=7.5,
        leading=9,
        textColor=colors.HexColor("#D9EAF7"),
        alignment=TA_LEFT,
    )

    small_label_style = ParagraphStyle(
        "SmallLabel",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=6.8,
        leading=8,
        textColor=colors.HexColor("#627D98"),
        alignment=TA_CENTER,
    )

    metric_value_style = ParagraphStyle(
        "MetricValue",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=9.2,
        leading=11,
        textColor=NAVY,
        alignment=TA_CENTER,
    )

    recommendation_label_style = ParagraphStyle(
        "RecommendationLabel",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=7,
        leading=8,
        textColor=colors.HexColor("#627D98"),
        alignment=TA_LEFT,
    )

    recommendation_value_style = ParagraphStyle(
        "RecommendationValue",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=15,
        leading=17,
        alignment=TA_LEFT,
    )

    section_title_style = ParagraphStyle(
        "SectionTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8,
        leading=10,
        textColor=WHITE,
        alignment=TA_LEFT,
    )

    body_style = ParagraphStyle(
        "Body",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.2,
        leading=11,
        textColor=DARK_GRAY,
        alignment=TA_LEFT,
    )

    body_bold_style = ParagraphStyle(
        "BodyBold",
        parent=body_style,
        fontName="Helvetica-Bold",
    )

    table_label_style = ParagraphStyle(
        "TableLabel",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=7.6,
        leading=9,
        textColor=DARK_GRAY,
        alignment=TA_LEFT,
    )

    table_value_style = ParagraphStyle(
        "TableValue",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=7.6,
        leading=9,
        textColor=DARK_GRAY,
        alignment=TA_RIGHT,
    )

    footer_style = ParagraphStyle(
        "Footer",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=6.5,
        leading=8,
        textColor=colors.HexColor("#7B8794"),
        alignment=TA_CENTER,
    )

    decision = safe_text(metrics.get("decision"))
    normalized_score = format_number(
        metrics.get("normalized_score"),
        1,
    )

    wyckoff_phase = safe_text(
        metrics.get("wyckoff_phase")
    )

    extension_status = safe_text(
        metrics.get("extension_risk_status")
    )

    extension_reason = safe_text(
        metrics.get("extension_risk_reason")
    )

    risk_label = safe_text(
        metrics.get("risk_label")
    )

    minervini_passed = bool(
        metrics.get("minervini_passed")
    )

    minervini_status = (
        "Passed"
        if minervini_passed
        else "Failed"
    )

    minervini_checks = (
        f"{safe_text(metrics.get('minervini_passed_checks'))}"
        f"/{safe_text(metrics.get('minervini_total_checks'))}"
    )

    broker_available = bool(
        metrics.get("broker_data_available")
    )

    foreign_available = bool(
        metrics.get("foreign_flow_data_available")
    )

    flow_status = (
        "Confirmed"
        if broker_available and foreign_available
        else "Partial / unavailable"
    )

    pullback_rrr = format_number(
        metrics.get("pullback_rrr"),
        2,
    )

    breakout_rrr = format_number(
        metrics.get("breakout_rrr"),
        2,
    )

    pullback_entry_low = format_number(
        metrics.get("pullback_entry_low"),
        2,
    )

    pullback_entry_high = format_number(
        metrics.get("pullback_entry_high"),
        2,
    )

    pullback_stop_loss = format_number(
        metrics.get("pullback_stop_loss"),
        2,
    )

    pullback_target_1 = format_number(
        metrics.get("pullback_target_1"),
        2,
    )

    pullback_target_2 = format_number(
        metrics.get("pullback_target_2"),
        2,
    )

    breakout_entry = format_number(
        metrics.get("breakout_entry"),
        2,
    )

    breakout_stop_loss = format_number(
        metrics.get("breakout_stop_loss"),
        2,
    )

    breakout_target_1 = format_number(
        metrics.get("breakout_target_1"),
        2,
    )

    breakout_target_2 = format_number(
        metrics.get("breakout_target_2"),
        2,
    )

    pullback_rrr_value = metrics.get("pullback_rrr")
    breakout_rrr_value = metrics.get("breakout_rrr")

    try:
        pullback_valid = (
            not math.isnan(float(pullback_rrr_value))
            and float(pullback_rrr_value) >= 2.0
        )
    except (TypeError, ValueError):
        pullback_valid = False

    try:
        breakout_valid = (
            not math.isnan(float(breakout_rrr_value))
            and float(breakout_rrr_value) >= 2.0
        )
    except (TypeError, ValueError):
        breakout_valid = False

    pullback_status = (
        "VALID SETUP"
        if pullback_valid
        else "WAIT — RRR BELOW 2.00"
    )

    breakout_status = (
        "VALID IF CONFIRMED"
        if breakout_valid
        else "WAIT — RRR BELOW 2.00"
    )

    pullback_entry_zone = (
        f"Rp {pullback_entry_low} – Rp {pullback_entry_high}"
        if pullback_entry_low != "N/A"
        and pullback_entry_high != "N/A"
        else "N/A"
    )

    decision_fill, decision_text = get_status_colors(
        decision
    )

    extension_fill, extension_text = get_status_colors(
        extension_status
    )

    story = []

    header = Table(
        [
            [
                p(
                    "IDX EQUITY RESEARCH — SWING TRADING NOTE",
                    report_title_style,
                ),
            ],
            [
                p(
                    (
                        f"{safe_text(ticker)}  |  "
                        f"{safe_text(company_name)}  |  "
                        f"Published "
                        f"{datetime.now().strftime('%d %b %Y, %H:%M')}"
                    ),
                    report_subtitle_style,
                ),
            ],
        ],
        colWidths=[18.8 * cm],
    )

    header.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), NAVY),
                ("TOPPADDING", (0, 0), (-1, 0), 8),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 2),
                ("TOPPADDING", (0, 1), (-1, 1), 1),
                ("BOTTOMPADDING", (0, 1), (-1, 1), 8),
                ("LEFTPADDING", (0, 0), (-1, -1), 9),
                ("RIGHTPADDING", (0, 0), (-1, -1), 9),
            ]
        )
    )

    story.append(header)
    story.append(Spacer(1, 0.20 * cm))

    recommendation_table = Table(
        [
            [
                p("TRADING RECOMMENDATION", recommendation_label_style),
                p("LAST CLOSE", recommendation_label_style),
                p("MODEL SCORE", recommendation_label_style),
                p("RISK CLASSIFICATION", recommendation_label_style),
            ],
            [
                p(decision, recommendation_value_style),
                p(
                    f"Rp {format_number(latest_close, 2)}",
                    metric_value_style,
                ),
                p(
                    f"{normalized_score} / 100",
                    metric_value_style,
                ),
                p(risk_label, metric_value_style),
            ],
        ],
        colWidths=[
            7.2 * cm,
            3.6 * cm,
            3.6 * cm,
            4.4 * cm,
        ],
    )

    recommendation_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), LIGHT_GRAY),
                ("BACKGROUND", (0, 1), (0, 1), decision_fill),
                ("BACKGROUND", (1, 1), (-1, 1), WHITE),
                ("TEXTCOLOR", (0, 1), (0, 1), decision_text),
                ("BOX", (0, 0), (-1, -1), 0.45, MEDIUM_GRAY),
                ("INNERGRID", (0, 0), (-1, -1), 0.25, MEDIUM_GRAY),
                ("TOPPADDING", (0, 0), (-1, 0), 5),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 4),
                ("TOPPADDING", (0, 1), (-1, 1), 6),
                ("BOTTOMPADDING", (0, 1), (-1, 1), 7),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]
        )
    )

    story.append(recommendation_table)
    story.append(Spacer(1, 0.18 * cm))

    kpi_strip = Table(
        [
            [
                metric_box(
                    "WYCKOFF PHASE",
                    wyckoff_phase,
                    3.62 * cm,
                    small_label_style,
                    metric_value_style,
                ),
                metric_box(
                    "MINERVINI",
                    f"{minervini_status} ({minervini_checks})",
                    3.62 * cm,
                    small_label_style,
                    metric_value_style,
                ),
                metric_box(
                    "FLOW",
                    flow_status,
                    3.62 * cm,
                    small_label_style,
                    metric_value_style,
                ),
                metric_box(
                    "ENTRY TIMING",
                    extension_status,
                    3.62 * cm,
                    small_label_style,
                    metric_value_style,
                ),
                metric_box(
                    "PULLBACK RRR",
                    pullback_rrr,
                    3.62 * cm,
                    small_label_style,
                    metric_value_style,
                ),
            ]
        ],
        colWidths=[3.72 * cm] * 5,
    )

    kpi_strip.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 1),
                ("RIGHTPADDING", (0, 0), (-1, -1), 1),
                ("TOPPADDING", (0, 0), (-1, -1), 1),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
            ]
        )
    )

    story.append(kpi_strip)
    story.append(Spacer(1, 0.22 * cm))

    story.append(
        section_header(
            "INVESTMENT VIEW",
            section_title_style,
        )
    )

    if "EXTENDED" in extension_status.upper():
        action_text = (
            "The broader technical structure remains constructive, "
            "but the current price is extended from the preferred "
            "short-term entry area. Do not chase; wait for either a "
            "controlled pullback or a fresh volume-confirmed breakout."
        )
    elif minervini_passed:
        action_text = (
            "Trend structure meets the model's long-term requirements. "
            "Evaluate entry only if price action, volume, and defined "
            "risk parameters remain aligned with the trade plan."
        )
    else:
        action_text = (
            "The long-term trend structure does not meet the model's "
            "minimum requirements. Avoid initiating a new swing "
            "position until the technical structure improves."
        )

    view_table = Table(
        [
            [
                p("ANALYST VIEW", body_bold_style),
                p("KEY WATCH ITEM", body_bold_style),
            ],
            [
                p(action_text, body_style),
                p(
                    (
                        f"Extension status: {extension_status}. "
                        f"{extension_reason}"
                    ),
                    body_style,
                ),
            ],
        ],
        colWidths=[9.35 * cm, 9.35 * cm],
    )

    view_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), LIGHT_GRAY),
                ("BACKGROUND", (0, 1), (-1, 1), WHITE),
                ("BOX", (0, 0), (-1, -1), 0.35, MEDIUM_GRAY),
                ("INNERGRID", (0, 0), (-1, -1), 0.25, MEDIUM_GRAY),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("LEFTPADDING", (0, 0), (-1, -1), 7),
                ("RIGHTPADDING", (0, 0), (-1, -1), 7),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
        )
    )

    story.append(view_table)
    story.append(Spacer(1, 0.22 * cm))

    story.append(
        section_header(
            "TRADE PLAN & EXECUTION PARAMETERS",
            section_title_style,
        )
    )

    trade_plan_header_style = ParagraphStyle(
        "TradePlanHeader",
        parent=table_label_style,
        fontName="Helvetica-Bold",
        textColor=WHITE,
        alignment=TA_CENTER,
    )

    trade_plan_value_style = ParagraphStyle(
        "TradePlanValue",
        parent=table_value_style,
        alignment=TA_CENTER,
    )

    trade_plan_rows = [
        [
            p("PARAMETER", trade_plan_header_style),
            p("PULLBACK SCENARIO", trade_plan_header_style),
            p("CONFIRMED BREAKOUT SCENARIO", trade_plan_header_style),
        ],
        [
            p("Execution status", table_label_style),
            p(pullback_status, trade_plan_value_style),
            p(breakout_status, trade_plan_value_style),
        ],
        [
            p("Entry condition", table_label_style),
            p(
                "Wait for price to trade within the preferred zone.",
                trade_plan_value_style,
            ),
            p(
                "Daily close above trigger with volume ratio above 1.20x.",
                trade_plan_value_style,
            ),
        ],
        [
            p("Preferred entry", table_label_style),
            p(pullback_entry_zone, trade_plan_value_style),
            p(
                f"Rp {breakout_entry}",
                trade_plan_value_style,
            ),
        ],
        [
            p("Stop-loss / invalidation", table_label_style),
            p(
                f"Rp {pullback_stop_loss}",
                trade_plan_value_style,
            ),
            p(
                f"Rp {breakout_stop_loss}",
                trade_plan_value_style,
            ),
        ],
        [
            p("Target 1", table_label_style),
            p(
                f"Rp {pullback_target_1}",
                trade_plan_value_style,
            ),
            p(
                f"Rp {breakout_target_1}",
                trade_plan_value_style,
            ),
        ],
        [
            p("Target 2", table_label_style),
            p(
                f"Rp {pullback_target_2}",
                trade_plan_value_style,
            ),
            p(
                f"Rp {breakout_target_2}",
                trade_plan_value_style,
            ),
        ],
        [
            p("Reward / risk ratio", table_label_style),
            p(
                f"{pullback_rrr}x",
                trade_plan_value_style,
            ),
            p(
                f"{breakout_rrr}x",
                trade_plan_value_style,
            ),
        ],
    ]

    trade_plan_table = Table(
        trade_plan_rows,
        colWidths=[
            4.1 * cm,
            7.35 * cm,
            7.35 * cm,
        ],
    )

    trade_plan_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), NAVY),
                ("BACKGROUND", (0, 1), (-1, -1), WHITE),
                (
                    "BACKGROUND",
                    (0, 1),
                    (0, -1),
                    LIGHT_GRAY,
                ),
                (
                    "ROWBACKGROUNDS",
                    (1, 1),
                    (-1, -1),
                    [WHITE, LIGHT_BLUE],
                ),
                ("BOX", (0, 0), (-1, -1), 0.35, MEDIUM_GRAY),
                ("INNERGRID", (0, 0), (-1, -1), 0.25, MEDIUM_GRAY),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]
        )
    )

    story.append(trade_plan_table)
    story.append(Spacer(1, 0.22 * cm))

    story.append(
        section_header(
            "TECHNICAL SETUP & DATA VALIDATION",
            section_title_style,
        )
    )

    technical_rows = [
        [
            p("Trend structure", table_label_style),
            p(wyckoff_phase, table_value_style),
            p("Minervini template", table_label_style),
            p(
                f"{minervini_status} ({minervini_checks})",
                table_value_style,
            ),
        ],
        [
            p("Entry timing", table_label_style),
            p(extension_status, table_value_style),
            p("Pullback RRR", table_label_style),
            p(pullback_rrr, table_value_style),
        ],
        [
            p("Broker summary", table_label_style),
            p(
                "Connected" if broker_available else "Unavailable",
                table_value_style,
            ),
            p("Foreign flow", table_label_style),
            p(
                "Connected" if foreign_available else "Unavailable",
                table_value_style,
            ),
        ],
    ]

    technical_table = Table(
        technical_rows,
        colWidths=[
            4.7 * cm,
            4.7 * cm,
            4.7 * cm,
            4.7 * cm,
        ],
    )

    technical_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), WHITE),
                ("ROWBACKGROUNDS", (0, 0), (-1, -1), [WHITE, LIGHT_GRAY]),
                ("BOX", (0, 0), (-1, -1), 0.35, MEDIUM_GRAY),
                ("INNERGRID", (0, 0), (-1, -1), 0.25, MEDIUM_GRAY),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("LEFTPADDING", (0, 0), (-1, -1), 7),
                ("RIGHTPADDING", (0, 0), (-1, -1), 7),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]
        )
    )

    story.append(technical_table)
    story.append(Spacer(1, 0.26 * cm))

    story.append(
        Paragraph(
            (
                "Source: Yahoo Finance market data; broker summary "
                "and foreign-flow data from the selected system source. "
                "This report is generated for educational market-analysis "
                "purposes only and is not investment advice."
            ),
            footer_style,
        )
    )

    document.build(story)

    return output_path