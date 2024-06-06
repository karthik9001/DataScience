#########################################################################################################################################
#   Purpose: The code generates an interactive earthquake map that displays recent earthquakes in North America based on USGS API data, # 
#   allowing users to select regions and switch between day and night modes.                                                            #
#   Retrieves earthquake data from the USGS API and filters it for North America.                                                       #
#   Constructs the user interface with options to select regions and toggle between day and night modes.                                #
#   Dynamically updates the earthquake map based on user-selected region and theme mode.                                                #
#   Author: Karthik Nakkeeran                                                                                                           #
#   Date: 2024-06-05                                                                                                                    #
#########################################################################################################################################

# Import dependencies

import requests
import pandas as pd
from shiny import App, ui, reactive, render
import plotly.graph_objs as go
import plotly.io as pio

def get_earthquake_data():
    """
    Retrieves earthquake data from a USGS API and transforms it into a DataFrame.

    Returns:
        DataFrame: DataFrame containing earthquake data with columns for place, magnitude, time, latitude, longitude, and depth.
    """

    url = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_month.geojson"
    response = requests.get(url).json()
    data = []
    for feature in response['features']:
        properties = feature['properties']
        geometry = feature['geometry']
        data.append({
            'Place': properties['place'],
            'Magnitude': properties['mag'],
            'Time': pd.to_datetime(properties['time'], unit='ms'),
            'Latitude': geometry['coordinates'][1],
            'Longitude': geometry['coordinates'][0],
            'Depth': geometry['coordinates'][2]
        })
    return pd.DataFrame(data)

earthquake_df = get_earthquake_data()
region_choices = {row['Place']: row['Place'] for _, row in earthquake_df.iterrows()}

# Filter for North America region using latitude and longitude bounds
north_america_bounds = {
    'min_latitude': 5,
    'max_latitude': 83,
    'min_longitude': -180,
    'max_longitude': -50
}

earthquake_df = earthquake_df[
    (earthquake_df['Latitude'] >= north_america_bounds['min_latitude']) &
    (earthquake_df['Latitude'] <= north_america_bounds['max_latitude']) &
    (earthquake_df['Longitude'] >= north_america_bounds['min_longitude']) &
    (earthquake_df['Longitude'] <= north_america_bounds['max_longitude'])
]

app_ui = ui.page_fluid(
    ui.tags.style("""
        .center-text {
            text-align: center;
        }
        body.day-mode {
            background-color: white;
            color: black;
        }
        body.night-mode {
            background-color: black;
            color: white;
        }
        .btn-toggle {
            position: fixed;
            top: 10px;
            right: 10px;
            padding: 10px;
            background-color: #f0f0f0;
            border: none;
            cursor: pointer;
            border-radius: 5px;
        }
        .btn-toggle.night-mode {
            background-color: #303030;
            color: white;
        }
    """),
    ui.tags.script("""
        function toggleMode() {
            const body = document.body;
            const button = document.getElementById('mode-toggle-btn');
            const isNightMode = body.classList.toggle('night-mode');
            button.innerText = isNightMode ? 'Switch to Day Mode' : 'Switch to Night Mode';
            button.classList.toggle('night-mode', isNightMode);

            // Inform the server about the theme change
            Shiny.setInputValue('theme_mode', isNightMode ? 'night' : 'day');
        }
    """),
    ui.tags.button("Switch to Night Mode", id="mode-toggle-btn", class_="btn-toggle", onclick="toggleMode()"),
    ui.h2("Recent North America Earthquakes Tracker", class_="text-center"),
    ui.h6("This is supported by USGS API.", class_="text-center"),
    ui.input_select("region", "Select Region:", choices=region_choices, selected=""),
    ui.output_ui("earthquake_map")
)

def server(input, output, session):
    """
    A server function that generates an interactive earthquake map based on user input for region and theme mode.

    Returns:
        HTML: HTML representation of the interactive earthquake map.
    """

    @reactive.Calc
    def region_data():
        """
        Calculates and returns earthquake data for a specific region if provided, otherwise returns all earthquake data.

        Returns:
            DataFrame: DataFrame containing earthquake data filtered by the specified region.
        """

        region = input.region()
        if region:
            return earthquake_df[earthquake_df['Place'].str.contains(region, case=False)]
        return earthquake_df

    @reactive.Calc
    def theme_mode():
        """
        Calculates and returns the theme mode based on user input, defaulting to 'day' if not specified.

        Returns:
            str: The theme mode for the application.
        """

        return input.theme_mode() if 'theme_mode' in input else 'day'

    @output
    @render.ui
    def earthquake_map():
        """
        Calculates and returns earthquake data for a specific region if provided, otherwise returns all earthquake data.

        Returns:
            DataFrame: DataFrame containing earthquake data filtered by the specified region.
        """

        data = region_data()
        mode = theme_mode()
        fig = go.Figure()

        fig.add_trace(go.Scattergeo(
            lon = data['Longitude'],
            lat = data['Latitude'],
            text = data['Place'] + '<br>Magnitude: ' + data['Magnitude'].astype(str) + '<br>Depth: ' + data['Depth'].astype(str) + ' km',
            marker = dict(
                size = data['Magnitude'] * 5,
                color = data['Magnitude'],
                colorscale = 'Viridis',
                colorbar_title = "Magnitude"
            )
        ))

        geo_scope = 'north america'

        fig.update_layout(
                geo = dict(
                    scope = geo_scope,
                    projection_scale = 1 if geo_scope == 'world' else None,
                    showland = True,
                    landcolor = "rgb(243, 243, 243)",
                    subunitcolor = "rgb(217, 217, 217)",
                    countrycolor = "rgb(217, 217, 217)",
                )
            )

        fig.update_layout(
            geo = dict(
                showland = True,
                landcolor = "rgb(243, 243, 243)",
                subunitcolor = "rgb(217, 217, 217)",
                countrycolor = "rgb(217, 217, 217)"
            )
        )

        fig_html = pio.to_html(fig, full_html=False)
        return ui.HTML(fig_html)

app = App(app_ui, server)

if __name__ == "__main__":
    app.run()

