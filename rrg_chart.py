import plotly.graph_objects as go
import json
from rrg_engine import run_rrg, TICKERS
import plotly.express as px

def get_color(ticker, idx):
    colors = [
        "#2a78d6", "#1baf7a", "#eda100", "#e34948", "#4a3aa7",
        "#eb6834", "#e87ba4", "#008300", "#BA7517", "#185FA5",
        "#3B6D11", "#A32D2D", "#534AB7", "#0F6E56", "#854F0B",
        "#639922", "#993556", "#185FA5", "#3987e5", "#199e70",
        "#c98500", "#008300", "#9085e9", "#e66767", "#d55181",
        "#d95926", "#3987e5", "#199e70", "#c98500", "#008300",
        "#9085e9", "#e66767", "#d55181", "#d95926", "#2a78d6",
        "#1baf7a", "#eda100", "#e34948", "#4a3aa7", "#eb6834",
        "#e87ba4", "#008300", "#BA7517", "#185FA5", "#3B6D11",
        "#A32D2D", "#534AB7", "#0F6E56", "#854F0B", "#639922",
        "#993556", "#185FA5", "#3987e5"
    ]
    return colors[idx % len(colors)]

def get_quadrant(x, y):
    if x >= 100 and y >= 100: return "LEADING"
    if x >= 100 and y < 100: return "WEAKENING"
    if x < 100 and y >= 100: return "IMPROVING"
    return "LAGGING"

def build_chart():
    results = run_rrg()
    fig = go.Figure()

    # Background kuadran
    fig.add_shape(type="rect", x0=100, x1=130, y0=100, y1=130,
        fillcolor="rgba(99,153,34,0.1)", line_width=0)
    fig.add_shape(type="rect", x0=70, x1=100, y0=100, y1=130,
        fillcolor="rgba(55,138,221,0.1)", line_width=0)
    fig.add_shape(type="rect", x0=100, x1=130, y0=70, y1=100,
        fillcolor="rgba(240,200,0,0.1)", line_width=0)
    fig.add_shape(type="rect", x0=70, x1=100, y0=70, y1=100,
        fillcolor="rgba(226,73,72,0.1)", line_width=0)

    # Label kuadran
    for text, x, y in [
        ("LEADING", 115, 128),
        ("WEAKENING", 115, 72),
        ("IMPROVING", 85, 128),
        ("LAGGING", 85, 72)
    ]:
        fig.add_annotation(x=x, y=y, text=text, showarrow=False,
            font=dict(size=11, color="gray"), opacity=0.6)

    # Plot tail per emiten
    for ticker, tail in results.items():
        if not tail:
            continue
        xs = [p['x'] for p in tail]
        ys = [p['y'] for p in tail]
        color = get_color(ticker, list(results.keys()).index(ticker))
        name = ticker.replace(".JK", "")
        quadrant = get_quadrant(xs[-1], ys[-1])

        # Tail
        for i in range(len(xs)-1):
            opacity = 0.2 + (i / len(xs)) * 0.6
            fig.add_trace(go.Scatter(
                x=[xs[i], xs[i+1]], y=[ys[i], ys[i+1]],
                mode='lines',
                line=dict(color=color, width=2),
                opacity=opacity,
                showlegend=False,
                hoverinfo='skip'
            ))

        # Titik akhir
        fig.add_trace(go.Scatter(
            x=[xs[-1]], y=[ys[-1]],
            mode='markers+text',
            marker=dict(size=12, color=color,
                line=dict(width=2, color='white')),
            text=[f"{name}"],
            textposition="top center",
            name=f"{name} ({quadrant})",
            hovertemplate=f"<b>{name}</b><br>X: {xs[-1]:.1f}<br>Y: {ys[-1]:.1f}<br>Kuadran: {quadrant}<extra></extra>"
        ))

    # Layout
    fig.update_layout(
        title="Psychological RRG — Market Pulse Monitor",
        xaxis=dict(title="Logika Tren (X)", range=[70, 130],
            zeroline=False, showgrid=False),
        yaxis=dict(title="Intensitas Emosi (Y)", range=[70, 130],
            zeroline=False, showgrid=False),
        shapes=[
            dict(type="line", x0=100, x1=100, y0=70, y1=130,
                line=dict(color="gray", width=1, dash="dash")),
            dict(type="line", x0=70, x1=130, y0=100, y1=100,
                line=dict(color="gray", width=1, dash="dash"))
        ],
        plot_bgcolor='white',
        paper_bgcolor='white',
        height=600,
        legend=dict(x=0.01, y=0.99)
    )

    print("Chart saved: rrg_chart.html")
    print("Chart saved: rrg_chart.html + rrg_chart.png")

if __name__ == "__main__":
    build_chart()
