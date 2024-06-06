#####################################################################################################################################################
#   Purpose:                                                                                                                                        #
#   The code creates a web application that displays a daily candlestick chart for S&P 500 stocks based on user-selected ticker and date range,     #
#   with the ability to switch between day and night modes.                                                                                         #
#   Retrieves S&P 500 company data and stock information using the Yahoo Finance API.                                                               #
#   Constructs a user interface with options to select a stock ticker, date range, and toggle between day and night modes.                          #
#   Dynamically updates the candlestick chart based on the selected stock data and theme mode.                                                      #
#   Author: Karthik Nakkeeran                                                                                                                       #
#   Date: 2024-06-05                                                                                                                                #
#####################################################################################################################################################

# Import as dependencies
from shiny import App, ui, reactive, render
import yfinance as yf
import plotly.graph_objs as go
import plotly.io as pio
import requests
import pandas as pd
from datetime import datetime, timedelta

"""
A server function that generates a stock daily candlestick chart based on input data.

Args:
    input: Input data for the stock chart.
    output: Output data for the stock chart.
    session: Session information for the server.

Returns:
    HTML: An HTML representation of the stock chart.
"""


# Function to fetch S&P 500 tickers
def get_sp500_companies():
    """
    Retrieves and returns a DataFrame containing the symbols and names of S&P 500 companies.

    Returns:
        DataFrame: DataFrame with columns 'Symbol' and 'Security' for S&P 500 companies.
    """

    url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
    html = requests.get(url).content
    df = pd.read_html(html, header=0)[0]
    return df[["Symbol", "Security"]]


# Fetch S&P 500 tickers and company names
sp500_df = get_sp500_companies()
sp500_choices = {
    row["Symbol"]: f"{row['Security']} - {row['Symbol']}"
    for _, row in sp500_df.iterrows()
}

# Added logics to enable Day and Night mode on HTML charts.
app_ui = ui.page_fluid(
    ui.tags.style(
        """
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
    """
    ),
    ui.tags.script(
        """
        function toggleMode() {
            const body = document.body;
            const button = document.getElementById('mode-toggle-btn');
            body.classList.toggle('night-mode');
            if (body.classList.contains('night-mode')) {
                button.innerText = 'Switch to Day Mode';
                button.classList.add('night-mode');
            } else {
                button.innerText = 'Switch to Night Mode';
                button.classList.remove('night-mode');
            }
        }
    """
    ),
    ui.tags.button(
        "Switch to Night Mode",
        id="mode-toggle-btn",
        class_="btn-toggle",
        onclick="toggleMode()",
    ),
    ui.h2("S&P 500 Stock - Daily Candlestick Chart", class_="text-center"),
    ui.h6(
        "This chart shows the market's open, high, low, and close prices for the day.",
        class_="text-center",
    ),
    ui.h6("This is supported by Yahoo! Finance's API.", class_="text-center"),
    ui.input_select(
        "ticker", "Select Stock Ticker:", choices=sp500_choices, selected="AAPL"
    ),
    ui.input_date_range(
        "date_range", "Select Date Range:", start=(datetime.now() - timedelta(days=5*365)).strftime("%Y-%m-%d"),
          end=datetime.now().strftime("%Y-%m-%d")
    ),
    ui.output_ui("stock_chart"),
)


# Same UI with out day/night mode logic.# app_ui = ui.page_fluid(
#     ui.h2("S&P 500 Stock - Daily Candlestick Chart", class_="text-center"),
#     ui.h6("This chart shows the market's open, high, low, and close prices for the day.", class_="text-center"),
#     ui.h6("This is supported by Yahoo Finance API.", class_="text-center"),
#     ui.input_select("ticker", "Select Stock Ticker:", choices=sp500_choices, selected="AAPL"),
#     ui.input_date_range(
#       "date_range", "Select Date Range:", start=(datetime.now() - timedelta(days=5*365)).strftime("%Y-%m-%d"),
#       end=datetime.now().strftime("%Y-%m-%d")
#       ),
#     ui.output_ui("stock_chart")
# )

def server(input, output, session):
    """
    Calculates and retrieves historical stock data based on input ticker and date range.

    Returns:
        DataFrame: Historical stock data for the specified ticker and date range.
    """

    @reactive.Calc
    def stock_data():
        """
        Calculates and retrieves historical stock data based on the input ticker and date range.

        Returns:
            DataFrame: Historical stock data for the specified ticker and date range.
        """

        ticker = input.ticker()
        start, end = input.date_range()
        stock = yf.Ticker(ticker)
        return stock.history(start=start, end=end)

    @reactive.Calc
    def company_name():
        """
        Retrieves the company name associated with the input stock ticker.

        Returns:
            str: Company name corresponding to the input stock ticker.
        """

        ticker = input.ticker()
        return sp500_df[sp500_df["Symbol"] == ticker]["Security"].values[0]

    @output
    @render.ui
    def stock_chart():
        """
        Generates a stock chart based on retrieved data.

        Returns:
            HTML: HTML representation of the stock chart.
        """

        data = stock_data()
        company = company_name()
        fig = go.Figure()
        fig.add_trace(
            go.Candlestick(
                x=data.index,
                open=data["Open"],
                high=data["High"],
                low=data["Low"],
                close=data["Close"],
                name="market data",
            )
        )
        fig.update_layout(
            title={
                "text": f"Stock Price for {company} - {input.ticker()}",
                "xanchor": "center",
                "yanchor": "top",
                "y": 0.9,
                "x": 0.5,
            },
            yaxis_title="Stock Price (USD)",
            xaxis_title="Date",
            xaxis_rangeslider_visible=False,
        )
        fig_html = pio.to_html(fig, full_html=False)
        return ui.HTML(fig_html)


app = App(app_ui, server)

if __name__ == "__main__":
    app.run()
