import pandas as pd
import plotly.express as px

# Data
data = [
    {"Stock": "XRO", "Market Value": 2761.28},
    {"Stock": "NXT", "Market Value": 2599.68},
    {"Stock": "BHP", "Market Value": 2582.45},
    {"Stock": "SDR", "Market Value": 2371.64},
    {"Stock": "LNW", "Market Value": 1907.23},
    {"Stock": "CSL", "Market Value": 1932.80},
    {"Stock": "HLI", "Market Value": 1776.41},
    {"Stock": "YMAX", "Market Value": 1996.80},
    {"Stock": "WAM", "Market Value": 1506.05},
    {"Stock": "DTR", "Market Value": 1641.42},
    {"Stock": "CBA", "Market Value": 1429.76},
    {"Stock": "WOW", "Market Value": 1240.00},
    {"Stock": "WAX", "Market Value": 1033.32}
]
df = pd.DataFrame(data)

# Sort by Market Value descending
df = df.sort_values(by="Market Value", ascending=False)

# Abbreviate Market Value for y-axis ticks and hover

def abbreviate(val):
    if val >= 1_000_000_000:
        return f"{val/1_000_000_000:.2f}b"
    elif val >= 1_000_000:
        return f"{val/1_000_000:.2f}m"
    elif val >= 1_000:
        return f"{val/1_000:.2f}k"
    else:
        return f"{val:.2f}"

# Custom y-tick labels
y_tickvals = df["Market Value"].tolist()
y_ticktext = [abbreviate(v) for v in y_tickvals]

# Brand colors
colors = ['#1FB8CD', '#FFC185', '#ECEBD5', '#5D878F', '#D2BA4C', '#B4413C', '#964325', '#944454', '#13343B', '#DB4545']

fig = px.bar(
    df,
    x="Stock",
    y="Market Value",
    color_discrete_sequence=colors,
    labels={"Stock": "Ticker", "Market Value": "Mkt Val (AUD)"},
    title="Portfolio Mkt Value by Ticker"
)

fig.update_yaxes(
    title_text="Mkt Val (AUD)",
    tickvals=y_tickvals,
    ticktext=y_ticktext
)
fig.update_xaxes(title_text="Ticker")

fig.update_layout(
    legend=dict(orientation='h', yanchor='bottom', y=1.05, xanchor='center', x=0.5)
)

fig.write_image('portfolio_market_value.png')