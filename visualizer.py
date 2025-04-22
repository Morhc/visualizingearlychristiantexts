import pandas as pd
import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.graph_objs as go


def get_color(category):
    if category == "New Testament":
        return "rosybrown"  # #4682B4

    elif category == "Other":
        return "steelblue"  # #BC8F8F

    elif category == "Gnostics":
        return "mediumseagreen"  # #3CB371

    elif category == "Church Fathers":
        return "indianred"  # #CD5C5C

    elif category == "Apocrypha":
        return "darkkhaki"  # #BDB76

    else:
        return "lightgray"  # fallback for unknown categories

def load_data(path="data.csv"):
    data = pd.read_csv(path, header=0, sep=",")
    return data

def make_timeline_figure(df, selected_categories, selected_subcategories, year_range):
    mask = (df["early"] <= year_range[1]) & (df["late"] >= year_range[0])
    
    # Filter by categories and subcategories
    if selected_categories:
        mask &= df["category"].isin(selected_categories)
    
    if selected_subcategories:
        mask &= df["further category"].isin(selected_subcategories)

    filtered = df[mask]

    fig = go.Figure()

    for _, row in filtered.iterrows():

        color = get_color(row["category"])

        custom_link = row["link"] if row["link"] != "Filler" else ""
        hover = (
            f"{row['source']} ({row['early']})"
            if row["early"] == row["late"]
            else f"{row['source']} ({row['early']}-{row['late']})"
        )
        x_vals = [row["early"], row["late"] + 0.5] if row["early"] == row["late"] else [row["early"], row["late"]]

        fig.add_trace(go.Scatter(
            x=x_vals,
            y=[row["source"]] * 2,
            mode="lines",
            line=dict(width=10, color=color, shape="spline"),
            hovertext=hover,
            hoverinfo="text",
            name=row["source"],
            customdata=[custom_link] * 2,
            hoverlabel=dict(namelength=-1)
        ))

    fig.update_layout(
        height=900,
        xaxis_title="Year",
        showlegend=False
    )

    return fig


def run_app():
    df = load_data()
    categories = df["category"].dropna().unique()
    further_categories = df["further category"].dropna().unique()

    app = dash.Dash(__name__)
    app.title = "Timeline of Early Christian Writings"

    app.layout = html.Div([
        html.H1("Timeline of Early Christian Writings", style={"fontWeight": "bold", "marginBottom": "30px"}),

        html.Div([
            html.Label("Category Filter", style={"fontWeight": "bold"}),
            dcc.Checklist(
                id="category-filter",
                options=[{"label": cat, "value": cat} for cat in sorted(categories)],
                value=list(categories),
                inline=True,
                labelStyle={"marginRight": "20px"}
            )
        ], style={"marginBottom": "30px"}),
        html.Div([
            html.Label("Further Category Filter", style={"fontWeight": "bold"}),
            dcc.Checklist(
                id="subcategory-filter",
                options=[{"label": subcat, "value": subcat} for subcat in sorted(further_categories)],
                value=[],
                inline=True,
                labelStyle={"marginRight": "20px"}
            )
        ], style={"marginBottom": "30px"}),

        html.Div([
            html.Label("Year Range", style={"fontWeight": "bold"}),
            dcc.RangeSlider(
                id="year-slider",
                min=df["early"].min(),
                max=df["late"].max(),
                step=1,
                marks={int(y): str(y) for y in range(df["early"].min(), df["late"].max() + 1, 25)},
                value=[df["early"].min(), df["late"].max()]
            )
        ], ),

        dcc.Graph(id="timeline-graph"),

        dcc.Store(id="stored-link"),
        html.Div(id="dummy-output")  # used for triggering clientside callback
    ], style={"padding": "40px"})


    @app.callback(
        Output("timeline-graph", "figure"),
        Input("category-filter", "value"),
        Input("subcategory-filter", "value"),
        Input("year-slider", "value")
    )
    def update_graph(selected_categories, selected_subcategories, year_range):
        return make_timeline_figure(df, selected_categories, selected_subcategories, year_range)

    @app.callback(
        Output("stored-link", "data"),
        Input("timeline-graph", "clickData"),
        prevent_initial_call=True
    )
    def store_clicked_link(clickData):
        if clickData and "points" in clickData:
            link = clickData["points"][0].get("customdata", "")
            if link:
                return {"url": link}
        return dash.no_update

    app.clientside_callback(
        """
        function(data) {
            if (data && data.url) {
                window.open(data.url, "_blank");
            }
            return "";
        }
        """,
        Output("dummy-output", "children"),  # changed this to dummy-output instead of script
        Input("stored-link", "data")
    )

    app.run(debug=True)


if __name__ == "__main__":
    run_app()