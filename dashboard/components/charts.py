import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from ..config import COLOR_MAP, TOP_N

DARK_LAYOUT = dict(
    template="plotly_dark",
    paper_bgcolor="rgba(18,18,36,0.7)",
    plot_bgcolor="rgba(18,18,36,0.3)",
    font=dict(color="#9494B8", family="Noto Sans SC, sans-serif"),
    title=dict(font=dict(color="#EDEDF5", size=14)),
    legend=dict(font=dict(color="#9494B8")),
    margin=dict(l=0, r=0, t=40, b=0),
    xaxis=dict(gridcolor="rgba(255,255,255,0.04)", zerolinecolor="rgba(255,255,255,0.06)"),
    yaxis=dict(gridcolor="rgba(255,255,255,0.04)", zerolinecolor="rgba(255,255,255,0.06)"),
)


def _dark_fig(fig, height=None):
    fig.update_layout(**DARK_LAYOUT)
    if height:
        fig.update_layout(height=height)
    return fig


def bar_chart_top(df, x, y, title, color=None, orientation="h", top_n=TOP_N, color_discrete_map=None):
    top_df = df.nlargest(top_n, x) if orientation == "h" else df.nlargest(top_n, y)
    if orientation == "h":
        top_df = top_df.sort_values(x, ascending=True)

    fig = px.bar(
        top_df, x=x, y=y, orientation=orientation, title=title,
        color=color, color_discrete_map=color_discrete_map or COLOR_MAP,
    )
    return _dark_fig(fig, height=max(400, top_n * 25))


def pie_chart(df, names, values, title, color_map=None):
    fig = px.pie(
        df, names=names, values=values, title=title,
        color=names, color_discrete_map=color_map or COLOR_MAP, hole=0.35,
    )
    return _dark_fig(fig)


def line_chart(df, x, y, color=None, title="", color_discrete_map=None):
    fig = px.line(df, x=x, y=y, color=color, title=title,
                  color_discrete_map=color_discrete_map or COLOR_MAP)
    return _dark_fig(fig)


def scatter_chart(df, x, y, color=None, title="", hover_name=None, size=None, color_discrete_map=None):
    fig = px.scatter(df, x=x, y=y, color=color, title=title,
                     hover_name=hover_name, size=size,
                     color_discrete_map=color_discrete_map or COLOR_MAP)
    return _dark_fig(fig)


def histogram(df, x, color=None, title="", barmode="overlay", color_discrete_map=None):
    fig = px.histogram(df, x=x, color=color, title=title, barmode=barmode,
                       color_discrete_map=color_discrete_map or COLOR_MAP)
    return _dark_fig(fig)


def box_chart(df, x, y, color=None, title="", color_discrete_map=None):
    fig = px.box(df, x=x, y=y, color=color, title=title,
                 color_discrete_map=color_discrete_map or COLOR_MAP)
    return _dark_fig(fig)


def density_heatmap(df, x, y, z=None, title=""):
    fig = px.density_heatmap(
        df, x=x, y=y, z=z, title=title,
        color_continuous_scale="Teal",
    )
    return _dark_fig(fig)


def stacked_area(df, x, y, color, title="", top_n=5, color_discrete_map=None):
    top_categories = df.groupby(color)[y].sum().nlargest(top_n).index.tolist()
    plot_df = df[df[color].isin(top_categories)]
    fig = px.area(plot_df, x=x, y=y, color=color, title=title,
                  color_discrete_map=color_discrete_map or COLOR_MAP)
    return _dark_fig(fig)


def wordcloud_figure(words_dict, title=""):
    try:
        from wordcloud import WordCloud
        import matplotlib.pyplot as plt
        wc = WordCloud(width=800, height=400, background_color="#0C0C1A",
                       colormap="viridis", max_words=100)
        wc.generate_from_frequencies(words_dict)
        fig, ax = plt.subplots(figsize=(10, 5), facecolor="#0C0C1A")
        ax.imshow(wc, interpolation="bilinear")
        ax.axis("off")
        ax.set_title(title, fontsize=14, color="#EDEDF5")
        plt.tight_layout()
        return fig
    except ImportError:
        return None


def empty_chart(message="No data available"):
    fig = go.Figure()
    fig.add_annotation(
        text=message, xref="paper", yref="paper", x=0.5, y=0.5,
        showarrow=False, font=dict(size=16, color="#5C5C80"),
    )
    fig.update_layout(
        height=300, margin=dict(l=0, r=0, t=0, b=0),
        xaxis=dict(showgrid=False, zeroline=False, visible=False),
        yaxis=dict(showgrid=False, zeroline=False, visible=False),
        paper_bgcolor="rgba(18,18,36,0.3)", plot_bgcolor="rgba(18,18,36,0.3)",
    )
    return fig
