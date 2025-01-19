##
# Add your Google Sheet ID at line 41
# Python version: 3.13
##

from shiny import App, reactive, render, ui
import pandas as pd
import requests
import io
import plotly.express as px
import plotly.graph_objects as go
from shiny import ui

# Function to load data from Google Sheets


def load_google_sheet(sheet_id, sheet_name="Sheet1"):
    # Construct the export URL for the Google Sheet
    url = f"https://docs.google.com/spreadsheets/d/{
        sheet_id}/export?format=csv&sheet={sheet_name}"
    response = requests.get(url)
    if response.status_code != 200:
        raise Exception("Failed to fetch Google Sheet data.")
    return pd.read_csv(io.StringIO(response.text))


# Define the Shiny app UI
app_ui = ui.page_fluid(
    ui.h2("Data from Google Sheet"),
    ui.input_select("x_column", "Select X-axis column", []),
    ui.input_select("y_column", "Select Y-axis column", []),
    # Ensure to output interactive Plotly plots here
    ui.output_ui("data_plot"),
)

# Define the server logic


def server(input, output, session):
    # Google Sheet details
    sheet_id = "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"  # Your Google Sheet ID
    sheet_name = "Sheet1"  # Replace with the actual sheet name if different

    # Load data from the Google Sheet
    @reactive.Calc
    def data():
        df = load_google_sheet(sheet_id, sheet_name)
        # Convert only columns that are dates to datetime format
        for col in df.columns:
            # Check if the column is an object (i.e., string)
            if df[col].dtype == 'object':
                try:
                    # Attempt to convert if the string follows the date format
                    df[col] = pd.to_datetime(
                        df[col], format="%d/%m/%Y", errors="coerce")
                except Exception:
                    # Skip if it fails (this will leave numeric columns untouched)
                    pass
        return df

    # Dynamically update column choices
    @reactive.Effect
    @reactive.event(data)
    def update_column_choices():
        columns = data().columns.tolist()
        ui.update_select("x_column", choices=columns)
        ui.update_select("y_column", choices=columns)

    # Render the plot as an interactive Plotly chart
    @output
    @render.ui
    def data_plot():
        df = data()
        x_col = input.x_column()
        y_col = input.y_column()

        if x_col and y_col:
            # Create a Plotly scatter plot (for points)
            scatter_fig = go.Scatter(x=df[x_col], y=df[y_col], mode='markers', name=f"{y_col} vs {x_col}",
                                     marker=dict(size=10, opacity=0.7, line=dict(width=0.5, color='DarkSlateGrey')))

            # Create a Plotly line plot (for line graph)
            line_fig = go.Scatter(x=df[x_col], y=df[y_col], mode='lines', name=f"{y_col} Line",
                                  line=dict(color='blue'))

            # Create a layout and update both the line and scatter plot
            layout = go.Layout(
                title=f"{y_col} vs {x_col} - Scatter and Line Plot",
                xaxis=dict(
                    title=x_col,
                    tickformat="%d/%m/%Y" if pd.api.types.is_datetime64_any_dtype(
                        df[x_col]) else None,
                    # Add a range slider for the X-axis
                    rangeslider=dict(visible=True),
                    type="date" if pd.api.types.is_datetime64_any_dtype(
                        # Set type to date if X-axis is date
                        df[x_col]) else "linear"
                ),
                yaxis=dict(title=y_col),
                height=600  # Increase height of the plot
            )

            # Combine scatter and line into a single figure
            fig = go.Figure(data=[scatter_fig, line_fig], layout=layout)

            # Return the Plotly figure as HTML content wrapped in ui.HTML
            # Wrap in ui.HTML
            return ui.HTML(fig.to_html(full_html=False, include_plotlyjs="cdn"))


# Create the Shiny app
app = App(app_ui, server)
