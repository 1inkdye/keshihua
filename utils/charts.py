import streamlit as st

# =========================
# 尺寸
# =========================
CHART_H_SM = 280
CHART_H_MD = 320
CHART_H_LG = 380
CHART_H_XL = 420

# =========================
# 主题色
# =========================
CARD_BG = "#FFFFFF"
GRID_COLOR = "#E7EEF7"
TEXT_COLOR = "#16324F"        # 深蓝色，白底可见
SUB_TEXT_COLOR = "#6B7A90"    # 灰色
BORDER_COLOR = "#E5EAF3"
HOVER_BG = "#EEF4FB"

COLOR_PRIMARY = "#3B5998"
COLOR_SECOND = "#7BCFA6"
COLOR_WARN = "#FF9900"
COLOR_DANGER = "#B36D61"
COLOR_NEUTRAL = "#7F8EA3"


# =========================
# 全局 CSS
# =========================
def inject_chart_css():
    st.markdown("""
    <style>
    @keyframes chartCardReveal {
        0% {
            opacity: 0;
            transform: translateY(22px) scale(0.965);
        }
        60% {
            opacity: 1;
            transform: translateY(-2px) scale(1.01);
        }
        100% {
            opacity: 1;
            transform: translateY(0) scale(1);
        }
    }

    @keyframes chartHeadingReveal {
        0% {
            opacity: 0;
            transform: translateY(10px);
        }
        100% {
            opacity: 1;
            transform: translateY(0);
        }
    }

    @keyframes pieGrowIn {
        0% {
            opacity: 0;
            transform: scale(0.12) rotate(-18deg);
        }
        55% {
            opacity: 1;
            transform: scale(0.92) rotate(4deg);
        }
        78% {
            opacity: 1;
            transform: scale(1.08) rotate(-1deg);
        }
        100% {
            opacity: 1;
            transform: scale(1) rotate(0deg);
        }
    }

    @keyframes pieSliceReveal {
        0% {
            opacity: 0;
            transform: scale(0.3);
        }
        65% {
            opacity: 1;
            transform: scale(1.06);
        }
        100% {
            opacity: 1;
            transform: scale(1);
        }
    }

    @keyframes barGrowIn {
        0% {
            opacity: 0;
            transform: scaleY(0.04);
        }
        58% {
            opacity: 1;
            transform: scaleY(0.88);
        }
        78% {
            opacity: 1;
            transform: scaleY(1.07);
        }
        100% {
            opacity: 1;
            transform: scaleY(1);
        }
    }

    @keyframes barGrowInHorizontal {
        0% {
            opacity: 0;
            transform: scaleX(0.04);
        }
        58% {
            opacity: 1;
            transform: scaleX(0.88);
        }
        78% {
            opacity: 1;
            transform: scaleX(1.07);
        }
        100% {
            opacity: 1;
            transform: scaleX(1);
        }
    }

    @keyframes chartGlowSweep {
        0% {
            opacity: 0;
            transform: translateX(-125%) skewX(-18deg);
        }
        28% {
            opacity: 0.55;
        }
        100% {
            opacity: 0;
            transform: translateX(145%) skewX(-18deg);
        }
    }

    .chart-title {
        color: #16324F;
        font-size: 15px;
        font-weight: 700;
        line-height: 1.3;
        margin: 0 0 6px 0;
        opacity: 0;
        animation: chartHeadingReveal 0.5s ease-out 0.08s forwards;
    }

    .chart-subtitle {
        color: #6B7A90;
        font-size: 12px;
        line-height: 1.35;
        margin: -2px 0 8px 0;
        opacity: 0;
        animation: chartHeadingReveal 0.5s ease-out 0.14s forwards;
    }

    div[data-testid="stPlotlyChart"] {
        position: relative;
        background: #FFFFFF;
        border: 1px solid #E5EAF3;
        border-radius: 16px;
        padding: 8px 10px 4px 10px;
        margin-bottom: 12px;
        overflow: hidden;
        transition: transform 0.22s ease, box-shadow 0.22s ease, border-color 0.22s ease;
        box-shadow: 0 10px 28px rgba(15, 23, 42, 0.08);
        will-change: transform, box-shadow;
        transform-origin: center center;
        z-index: 1;
        animation: chartCardReveal 0.55s cubic-bezier(0.22, 1, 0.36, 1) both;
    }

    div[data-testid="stPlotlyChart"]:nth-of-type(1) { animation-delay: 0.02s; }
    div[data-testid="stPlotlyChart"]:nth-of-type(2) { animation-delay: 0.08s; }
    div[data-testid="stPlotlyChart"]:nth-of-type(3) { animation-delay: 0.14s; }
    div[data-testid="stPlotlyChart"]:nth-of-type(4) { animation-delay: 0.20s; }
    div[data-testid="stPlotlyChart"]:nth-of-type(5) { animation-delay: 0.26s; }
    div[data-testid="stPlotlyChart"]:nth-of-type(6) { animation-delay: 0.32s; }

    div[data-testid="stPlotlyChart"]::before {
        content: "";
        position: absolute;
        inset: 0;
        background: linear-gradient(
            105deg,
            rgba(255,255,255,0) 0%,
            rgba(80, 130, 190, 0.04) 42%,
            rgba(123, 207, 166, 0.12) 50%,
            rgba(80, 130, 190, 0.03) 58%,
            rgba(255,255,255,0) 100%
        );
        pointer-events: none;
        z-index: 2;
        opacity: 0;
        animation: chartGlowSweep 1.1s ease-out 0.18s both;
    }

    div[data-testid="stPlotlyChart"]:hover {
        transform: translateY(-4px);
        border-color: rgba(123, 207, 166, 0.22);
        box-shadow: 0 18px 38px rgba(15, 23, 42, 0.14);
        z-index: 3;
    }

    div[data-testid="stPlotlyChart"] > div {
        border-radius: 12px;
        overflow: hidden;
    }

    div[data-testid="stPlotlyChart"] .js-plotly-plot,
    div[data-testid="stPlotlyChart"] .plot-container,
    div[data-testid="stPlotlyChart"] .svg-container {
        overflow: hidden !important;
        transition: filter 0.22s ease;
        transform-origin: center center;
    }

    div[data-testid="stPlotlyChart"] .main-svg,
    div[data-testid="stPlotlyChart"] .main-svg {
        overflow: hidden !important;
    }

    div[data-testid="stPlotlyChart"] .hoverlayer,
    div[data-testid="stPlotlyChart"] .hoverlayer * {
        overflow: visible !important;
    }

    div[data-testid="stPlotlyChart"]:hover .js-plotly-plot,
    div[data-testid="stPlotlyChart"]:hover .plot-container,
    div[data-testid="stPlotlyChart"]:hover .svg-container {
        filter: saturate(1.08) brightness(1.04);
    }

    div[data-testid="stPlotlyChart"] .pielayer,
    div[data-testid="stPlotlyChart"] .sunburstlayer {
        transform-origin: 50% 50%;
        transform-box: fill-box;
        animation: pieGrowIn 1.05s cubic-bezier(0.16, 0.84, 0.24, 1) 0.08s both;
    }

    div[data-testid="stPlotlyChart"] .pielayer .trace {
        transform-origin: 50% 50%;
        transform-box: fill-box;
        transition: opacity 0.28s ease;
        animation: pieSliceReveal 0.72s cubic-bezier(0.22, 1, 0.36, 1) both;
    }

    div[data-testid="stPlotlyChart"] .pielayer .trace path,
    div[data-testid="stPlotlyChart"] .sunburstlayer .trace path {
        transition: transform 0.34s cubic-bezier(0.22, 1, 0.36, 1),
                    filter 0.34s cubic-bezier(0.22, 1, 0.36, 1),
                    opacity 0.28s ease;
        transform-origin: 50% 50%;
        transform-box: fill-box;
    }

    div[data-testid="stPlotlyChart"] .pielayer:hover .trace,
    div[data-testid="stPlotlyChart"] .sunburstlayer:hover .trace {
        opacity: 0.82;
    }

    div[data-testid="stPlotlyChart"] .pielayer .trace:hover,
    div[data-testid="stPlotlyChart"] .sunburstlayer .trace:hover {
        opacity: 1;
    }

    div[data-testid="stPlotlyChart"] .pielayer .trace:hover path,
    div[data-testid="stPlotlyChart"] .sunburstlayer .trace:hover path {
        transform: scale(1.045) translateY(-2px);
        filter: brightness(1.08) saturate(1.1) drop-shadow(0 10px 20px rgba(123, 207, 166, 0.16));
    }

    div[data-testid="stPlotlyChart"] .pielayer .trace:nth-child(1) { animation-delay: 0.18s; }
    div[data-testid="stPlotlyChart"] .pielayer .trace:nth-child(2) { animation-delay: 0.26s; }
    div[data-testid="stPlotlyChart"] .pielayer .trace:nth-child(3) { animation-delay: 0.34s; }
    div[data-testid="stPlotlyChart"] .pielayer .trace:nth-child(4) { animation-delay: 0.42s; }
    div[data-testid="stPlotlyChart"] .pielayer .trace:nth-child(5) { animation-delay: 0.50s; }
    div[data-testid="stPlotlyChart"] .pielayer .trace:nth-child(6) { animation-delay: 0.58s; }
    div[data-testid="stPlotlyChart"] .pielayer .trace:nth-child(7) { animation-delay: 0.66s; }
    div[data-testid="stPlotlyChart"] .pielayer .trace:nth-child(8) { animation-delay: 0.74s; }

    div[data-testid="stPlotlyChart"] .barlayer .trace,
    div[data-testid="stPlotlyChart"] .waterfalllayer .trace,
    div[data-testid="stPlotlyChart"] .funnellayer .trace {
        transform-origin: center bottom;
        transform-box: fill-box;
        transition: opacity 0.24s ease;
        animation: barGrowIn 0.9s cubic-bezier(0.16, 0.84, 0.24, 1) both;
    }

    div[data-testid="stPlotlyChart"] .barlayer .bars .point,
    div[data-testid="stPlotlyChart"] .waterfalllayer .point,
    div[data-testid="stPlotlyChart"] .funnellayer .point {
        transition: transform 0.28s cubic-bezier(0.22, 1, 0.36, 1),
                    filter 0.28s cubic-bezier(0.22, 1, 0.36, 1),
                    opacity 0.22s ease;
        transform-box: fill-box;
        transform-origin: center bottom;
    }

    div[data-testid="stPlotlyChart"] .barlayer:hover .point,
    div[data-testid="stPlotlyChart"] .waterfalllayer:hover .point,
    div[data-testid="stPlotlyChart"] .funnellayer:hover .point {
        opacity: 0.76;
    }

    div[data-testid="stPlotlyChart"] .barlayer .point:hover,
    div[data-testid="stPlotlyChart"] .waterfalllayer .point:hover,
    div[data-testid="stPlotlyChart"] .funnellayer .point:hover {
        opacity: 1;
        transform: translateY(-4px) scale(1.018);
        filter: brightness(1.1) saturate(1.08) drop-shadow(0 12px 22px rgba(15, 23, 42, 0.28));
    }

    div[data-testid="stPlotlyChart"] g.horizontal .barlayer .trace,
    div[data-testid="stPlotlyChart"] g.horizontal .waterfalllayer .trace,
    div[data-testid="stPlotlyChart"] g.horizontal .funnellayer .trace {
        transform-origin: left center;
        animation-name: barGrowInHorizontal;
    }

    div[data-testid="stPlotlyChart"] g.horizontal .barlayer .point:hover,
    div[data-testid="stPlotlyChart"] g.horizontal .waterfalllayer .point:hover,
    div[data-testid="stPlotlyChart"] g.horizontal .funnellayer .point:hover {
        transform: translateX(4px) scale(1.018);
    }

    div[data-testid="stPlotlyChart"] .scatterlayer .trace .points path,
    div[data-testid="stPlotlyChart"] .scatterlayer .trace .lines path {
        transition: transform 0.24s cubic-bezier(0.22, 1, 0.36, 1),
                    filter 0.24s cubic-bezier(0.22, 1, 0.36, 1),
                    opacity 0.2s ease;
    }

    div[data-testid="stPlotlyChart"] .scatterlayer .trace .points path:hover {
        transform: scale(1.12);
        filter: brightness(1.08) drop-shadow(0 8px 16px rgba(15, 23, 42, 0.24));
    }

    div[data-testid="stPlotlyChart"] .barlayer .trace:nth-child(1),
    div[data-testid="stPlotlyChart"] .funnellayer .trace:nth-child(1) { animation-delay: 0.04s; }
    div[data-testid="stPlotlyChart"] .barlayer .trace:nth-child(2),
    div[data-testid="stPlotlyChart"] .funnellayer .trace:nth-child(2) { animation-delay: 0.08s; }
    div[data-testid="stPlotlyChart"] .barlayer .trace:nth-child(3),
    div[data-testid="stPlotlyChart"] .funnellayer .trace:nth-child(3) { animation-delay: 0.12s; }
    div[data-testid="stPlotlyChart"] .barlayer .trace:nth-child(4),
    div[data-testid="stPlotlyChart"] .funnellayer .trace:nth-child(4) { animation-delay: 0.16s; }
    div[data-testid="stPlotlyChart"] .barlayer .trace:nth-child(5),
    div[data-testid="stPlotlyChart"] .funnellayer .trace:nth-child(5) { animation-delay: 0.20s; }
    div[data-testid="stPlotlyChart"] .barlayer .trace:nth-child(6),
    div[data-testid="stPlotlyChart"] .funnellayer .trace:nth-child(6) { animation-delay: 0.24s; }
    div[data-testid="stPlotlyChart"] .barlayer .trace:nth-child(7),
    div[data-testid="stPlotlyChart"] .funnellayer .trace:nth-child(7) { animation-delay: 0.28s; }
    div[data-testid="stPlotlyChart"] .barlayer .trace:nth-child(8),
    div[data-testid="stPlotlyChart"] .funnellayer .trace:nth-child(8) { animation-delay: 0.32s; }
    div[data-testid="stPlotlyChart"] .barlayer .trace:nth-child(9),
    div[data-testid="stPlotlyChart"] .funnellayer .trace:nth-child(9) { animation-delay: 0.36s; }
    div[data-testid="stPlotlyChart"] .barlayer .trace:nth-child(10),
    div[data-testid="stPlotlyChart"] .funnellayer .trace:nth-child(10) { animation-delay: 0.40s; }
    div[data-testid="stPlotlyChart"] .barlayer .trace:nth-child(11),
    div[data-testid="stPlotlyChart"] .funnellayer .trace:nth-child(11) { animation-delay: 0.44s; }
    div[data-testid="stPlotlyChart"] .barlayer .trace:nth-child(12),
    div[data-testid="stPlotlyChart"] .funnellayer .trace:nth-child(12) { animation-delay: 0.48s; }
    @keyframes customPanelReveal {
        0% {
            opacity: 0;
            transform: translateY(18px) scale(0.98);
        }
        100% {
            opacity: 1;
            transform: translateY(0) scale(1);
        }
    }

    @keyframes customBarFill {
        0% {
            width: 0;
            opacity: 0.35;
        }
        100% {
            opacity: 1;
        }
    }

    .custom-analytic-card {
        animation: customPanelReveal 0.55s cubic-bezier(0.22, 1, 0.36, 1) both;
        transition: transform 0.28s cubic-bezier(0.22, 1, 0.36, 1),
                    box-shadow 0.28s cubic-bezier(0.22, 1, 0.36, 1),
                    border-color 0.28s ease,
                    filter 0.28s ease;
        transform-origin: center center;
        will-change: transform, box-shadow, filter;
    }

    .custom-analytic-card:hover {
        transform: translateY(-6px) scale(1.025);
        box-shadow: 0 20px 42px rgba(15, 23, 42, 0.14);
        border-color: rgba(123, 207, 166, 0.18) !important;
        filter: brightness(1.04) saturate(1.04);
    }

    .task-type-summary-card {
        animation-delay: 0.06s;
    }

    .task-penetration-card {
        animation-delay: 0.12s;
    }

    .task-penetration-row {
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 8px 0;
        transition: transform 0.24s cubic-bezier(0.22, 1, 0.36, 1), opacity 0.22s ease;
    }

    .task-penetration-row:hover {
        transform: translateX(4px);
    }

    .task-penetration-track {
        flex:1;
        position:relative;
        height:28px;
        background:#EDF3F9;
        border-radius:999px;
        overflow:hidden;
    }

    .task-penetration-row:hover .task-penetration-track {
        background: #E3ECF6 !important;
    }

    .task-penetration-fill {
        position: absolute;
        left: 0;
        top: 0;
        height: 100%;
        border-radius: 999px;
        display: flex;
        align-items: center;
        padding-left: 10px;
        min-width: 52px;
        animation: customBarFill 0.95s cubic-bezier(0.16, 0.84, 0.24, 1) both;
        transition: transform 0.24s cubic-bezier(0.22, 1, 0.36, 1),
                    filter 0.24s cubic-bezier(0.22, 1, 0.36, 1),
                    box-shadow 0.24s ease;
        transform-origin: left center;
    }

    .task-penetration-row:hover .task-penetration-fill {
        filter: brightness(1.08) saturate(1.08);
        box-shadow: 0 10px 20px rgba(15, 23, 42, 0.12);
    }

    .metric-summary-card {
        animation-delay: 0.04s;
    }

    .metric-board-card {
        animation: customPanelReveal 0.5s cubic-bezier(0.22, 1, 0.36, 1) both;
        transition: transform 0.24s cubic-bezier(0.22, 1, 0.36, 1),
                    background 0.24s ease,
                    box-shadow 0.24s ease,
                    border-color 0.24s ease,
                    filter 0.24s ease;
        position: relative;
        z-index: 1;
        will-change: transform, box-shadow, filter;
    }

    .metric-board-card:hover {
        transform: translateY(-10px) scale(1.06);
        box-shadow: 0 24px 44px rgba(15, 23, 42, 0.16);
        border-color: rgba(123, 207, 166, 0.26) !important;
        filter: brightness(1.08) saturate(1.08);
    }

    .rank-board-card {
        animation: customPanelReveal 0.55s cubic-bezier(0.22, 1, 0.36, 1) both;
        transition: transform 0.26s cubic-bezier(0.22, 1, 0.36, 1),
                    box-shadow 0.26s ease,
                    border-color 0.26s ease,
                    filter 0.26s ease;
        transform-origin: center center;
        will-change: transform, box-shadow, filter;
    }

    .rank-board-card:hover {
        transform: translateY(-6px) scale(1.02);
        box-shadow: 0 18px 36px rgba(15, 23, 42, 0.14);
        border-color: rgba(123, 207, 166, 0.18) !important;
        filter: brightness(1.04);
    }

    .rank-board-row {
        transition: transform 0.22s cubic-bezier(0.22, 1, 0.36, 1),
                    background-color 0.22s ease;
        border-radius: 10px;
    }

    .rank-board-row:hover {
        transform: translateX(4px);
        background-color: #F5F9FD;
    }
    </style>
    """, unsafe_allow_html=True)


# =========================
# 基础样式层
# =========================
def style_figure(
    fig,
    x_title=None,
    y_title=None,
    legend_title=None,
    height=CHART_H_MD,
    margin=None,
    legend_top=True
):
    if margin is None:
        margin = dict(l=34, r=28, t=26, b=26)

    fig.update_layout(
        xaxis_title=x_title,
        yaxis_title=y_title,
        legend_title=legend_title,
        plot_bgcolor=CARD_BG,
        paper_bgcolor=CARD_BG,
        font=dict(color=TEXT_COLOR, size=11),
        height=height,
        margin=margin,
        transition=dict(duration=650, easing="cubic-in-out"),
        hovermode="closest",
        hoverdistance=36,
        spikedistance=1000,
        hoverlabel=dict(
            bgcolor=HOVER_BG,
            font_color=TEXT_COLOR,
            bordercolor=HOVER_BG
        )
    )

    if legend_top:
            fig.update_layout(
                legend=dict(
                    orientation="h",
                    y=1.02,
                    x=0,
                    xanchor="left",
                    yanchor="bottom",
                    font=dict(size=11),
                    bgcolor="rgba(0,0,0,0)"
                )
            )
    else:
        fig.update_layout(
            legend=dict(
                orientation="h",
                y=-0.18,
                x=0.5,
                xanchor="center",
                yanchor="top",
                font=dict(size=11),
                bgcolor="rgba(0,0,0,0)"
            )
        )

    fig.update_xaxes(
        showgrid=False,
        zeroline=False,
        tickfont=dict(color=SUB_TEXT_COLOR, size=11),
        title_font=dict(color=TEXT_COLOR, size=12),
        showline=False,
        automargin=True,
        showspikes=True,
        spikesnap="cursor",
        spikemode="across",
        spikecolor="rgba(123, 207, 166, 0.45)",
        spikethickness=1
    )

    fig.update_yaxes(
        showgrid=True,
        gridcolor=GRID_COLOR,
        zeroline=False,
        tickfont=dict(color=SUB_TEXT_COLOR, size=11),
        title_font=dict(color=TEXT_COLOR, size=12),
        showline=False,
        automargin=True,
        showspikes=True,
        spikesnap="cursor",
        spikemode="across",
        spikecolor="rgba(123, 207, 166, 0.26)",
        spikethickness=1
    )

    return fig


# =========================
# 各图类型美化
# =========================
def beautify_bar_chart(fig, horizontal=False):
    fig.update_traces(
        marker_line_width=0,
        opacity=0.96,
        cliponaxis=False
    )

    try:
        fig.update_layout(barcornerradius=999)
    except Exception:
        pass

    fig.update_layout(
        bargap=0.18 if not horizontal else 0.22,
        bargroupgap=0.10
    )

    if horizontal:
        fig.update_xaxes(showgrid=False)
        fig.update_yaxes(showgrid=False)

    return fig


def beautify_diverging_bar_chart(fig):
    fig.update_traces(
        marker_line_width=0,
        opacity=0.96,
        textfont=dict(size=11, color=TEXT_COLOR),
        textposition="outside",
        cliponaxis=False
    )

    try:
        fig.update_layout(barcornerradius=999)
    except Exception:
        pass

    fig.update_layout(
        bargap=0.38,
        bargroupgap=0.08,
        showlegend=True,
        legend=dict(
            orientation="h",
            y=1.03,
            x=0.02,
            xanchor="left",
            yanchor="bottom",
            bgcolor="rgba(0,0,0,0)",
            font=dict(size=11, color=TEXT_COLOR)
        )
    )

    fig.update_xaxes(
        showgrid=False,
        zeroline=True,
            zerolinecolor="rgba(22, 50, 79, 0.16)",
        zerolinewidth=1.2,
        tickfont=dict(color=SUB_TEXT_COLOR, size=11),
        title_font=dict(color=TEXT_COLOR, size=12)
    )

    fig.update_yaxes(
        showgrid=False,
        tickfont=dict(color=TEXT_COLOR, size=11),
        title_font=dict(color=TEXT_COLOR, size=12),
        categoryorder="total ascending",
        automargin=True
    )

    return fig


def beautify_progress_like_bar(fig):
    fig.update_traces(
        marker_line_width=0,
        opacity=0.98,
        textposition="outside",
        cliponaxis=False
    )

    try:
        fig.update_layout(barcornerradius=999)
    except Exception:
        pass

    fig.update_layout(
        bargap=0.18,
        bargroupgap=0.08
    )

    fig.update_xaxes(showgrid=False, zeroline=False)
    fig.update_yaxes(showgrid=False, zeroline=False)

    return fig


def beautify_line_chart(fig):
    fig.update_layout(hovermode="x unified")
    fig.update_traces(
        mode="lines+markers",
        line=dict(width=3),
        marker=dict(size=7),
        connectgaps=True
    )
    return fig


def beautify_scatter_chart(fig):
    fig.update_layout(hovermode="closest")
    fig.update_traces(
        marker=dict(
            size=11,
            line=dict(width=1, color="rgba(22, 50, 79, 0.14)")
        ),
        cliponaxis=False
    )

    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(showgrid=False)
    return fig


def beautify_pie_chart(fig):
    fig.update_traces(
        textposition="inside",
        textinfo="percent",
        marker=dict(
            line=dict(color="#FFFFFF", width=2)
        )
    )
    return fig


def fix_pie(fig, height=CHART_H_SM):
    fig.update_layout(
        plot_bgcolor=CARD_BG,
        paper_bgcolor=CARD_BG,
        font=dict(color=TEXT_COLOR, size=11),
        height=height,
        margin=dict(l=12, r=12, t=10, b=34),
        transition=dict(duration=650, easing="cubic-in-out"),
        hoverlabel=dict(
            bgcolor=HOVER_BG,
            font_color=TEXT_COLOR,
            bordercolor=HOVER_BG
        ),
        legend=dict(
            orientation="h",
            y=-0.10,
            x=0.5,
            xanchor="center",
            font=dict(size=10),
            bgcolor="rgba(0,0,0,0)"
        )
    )

    fig = beautify_pie_chart(fig)
    fig.update_traces(hole=0.55)

    return fig


# =========================
# 统一加工入口
# =========================
def make_chart_pretty(
    fig,
    chart_type="bar",
    height=None,
    x_title=None,
    y_title=None,
    legend_title=None,
    legend_top=True,
    margin=None
):
    if height is None:
        if chart_type == "pie":
            height = CHART_H_SM
        elif chart_type in ["line", "scatter"]:
            height = CHART_H_LG
        else:
            height = CHART_H_MD

    if chart_type == "pie":
        return fix_pie(fig, height=height)

    fig = style_figure(
        fig,
        x_title=x_title,
        y_title=y_title,
        legend_title=legend_title,
        height=height,
        margin=margin,
        legend_top=legend_top
    )

    if chart_type == "bar":
        fig = beautify_bar_chart(fig, horizontal=False)
    elif chart_type == "hbar":
        fig = beautify_bar_chart(fig, horizontal=True)
    elif chart_type == "diverging":
        fig = beautify_diverging_bar_chart(fig)
    elif chart_type == "progress":
        fig = beautify_progress_like_bar(fig)
    elif chart_type == "line":
        fig = beautify_line_chart(fig)
    elif chart_type == "scatter":
        fig = beautify_scatter_chart(fig)

    return fig


# =========================
# 渲染层
# =========================
def render_chart_card(
    fig,
    title=None,
    subtitle=None,
    use_container_width=True,
    config=None
):
    if config is None:
        config = {
            "displayModeBar": False,
            "displaylogo": False,
            "responsive": True
        }

    if title:
        st.markdown(f'<div class="chart-title">{title}</div>', unsafe_allow_html=True)

    if subtitle:
        st.markdown(f'<div class="chart-subtitle">{subtitle}</div>', unsafe_allow_html=True)

    st.plotly_chart(fig, use_container_width=use_container_width, config=config)


# =========================
# 标准调用入口
# =========================
def show_chart(
    fig,
    chart_type="bar",
    title=None,
    subtitle=None,
    height=None,
    x_title=None,
    y_title=None,
    legend_title=None,
    legend_top=True,
    margin=None,
    use_container_width=True,
    config=None
):
    fig = make_chart_pretty(
        fig=fig,
        chart_type=chart_type,
        height=height,
        x_title=x_title,
        y_title=y_title,
        legend_title=legend_title,
        legend_top=legend_top,
        margin=margin
    )

    render_chart_card(
        fig=fig,
        title=title,
        subtitle=subtitle,
        use_container_width=use_container_width,
        config=config
    )
