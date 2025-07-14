import pandas as pd
import plotly.express as px

df = pd.read_csv('portfolio_export_20250714_172832.csv')
# Convert Market Value to numeric (remove $ and , first)
df['Market Value'] = df['Market Value'].str.replace('$', '').str.replace(',', '')
df['Market Value'] = pd.to_numeric(df['Market Value'], errors='coerce')
# Sort by Market Value descending
sorted_df = df.sort_values('Market Value', ascending=False)
# Abbreviate market values

def abbreviate_number(x):
    if x >= 1_000_000_000:
        return f"{x/1_000_000_000:.2f}b"
    elif x >= 1_000_000:
        return f"{x/1_000_000:.2f}m"
    elif x >= 1_000:
        return f"{x/1_000:.2f}k"
    else:
        return f"{x:.2f}"

sorted_df['Market Value Abbr'] = sorted_df['Market Value'].apply(abbreviate_number)

# Brand colors
colors = ['#1FB8CD', '#FFC185', '#ECEBD5', '#5D878F', '#D2BA4C', '#B4413C', '#964325', '#944454', '#13343B', '#DB4545']

fig = px.bar(
    sorted_df,
    x='Stock',
    y='Market Value',
    color_discrete_sequence=colors,
    text='Market Value Abbr'
)

fig.update_traces(textposition='outside')
fig.update_yaxes(title_text='Mkt Val (AUD)')
fig.update_xaxes(title_text='Ticker')
fig.update_layout(title_text='Portfolio Holdings 14 Jul 2025')

fig.write_image('portfolio_holdings_bar.png')
