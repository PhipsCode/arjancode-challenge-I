import dash
from dash import dcc, html, Input, Output, State
import pandas as pd
from dash import dash_table
import plotly.graph_objects as go
from alpha_vantage_api.operations import (
    AssetType,
    Interval,
    create_crypto_request_params,
    create_forex_request_params,
    create_stock_request_params,
    create_symbol_search_params,
    request_data,
)
from alpha_vantage_api.models import (
    SymbolMarketSearchResults,
    AssetHistoryData,
    MarketMetaData,
)
from alpha_vantage_api.config import API_KEY
from alpha_vantage_api.limit_count import get_api_count
from db.engine_av_search import alpha_vantage_db
from db.av_search.operations import (
    save_search_results,
    get_search_results,
)


assert API_KEY is not None, "API_KEY is not set"

# left column
ASSET_TYPE_DROPDOWN = "asset-type-dropdown"

INPUT_FIELD_1 = "input-field-1"
INPUT_FIELD_1_LABEL = "input-field-1-label"
INPUT_FIELD_2 = "input-field-2"
INPUT_FIELD_2_LABEL = "input-field-2-label"

INTERVAL_DROPDOWN = "interval-dropdown"
DAILY_OUTPUTSIZE_DROPDOWN = "daily-outputsize-dropdown"

GET_TIMEDATA_BUTTON = "get-timedata-button"
TIME_DATA_STORE = "time-data-store"

# right column
SEARCH_INPUT_FIELD = "search-input-field"
SEARCH_BUTTON = "search-button"
SEARCH_RESULT_TABLE = "search-result-table"
SEARCH_RESULT_STORE = "search-result-store"


# graph area
TIME_DATA_GRAPH = "graph"

# below display area
API_COUNT_STORE = "api-count-store"
OUTPUT_REMAINING_API_CALLS = "api-calls-remaining"
DEBUG_OUTPUT_TEXT_FIELD = "debug-output-text-field"
UPDATE_DB_BUTTON = "update-db-button"
# def load_example_df() -> pd.DataFrame:
#     example = Path(r"alpha_vantage_examples\meta_data_search\TSLA_search_result.json")

#     search_results = SymbolMarketSearchResults.model_validate_json(example.read_text())
#     return pd.DataFrame(
#         best_match.model_dump() for best_match in search_results.best_matches
#     )


app = dash.Dash(__name__, suppress_callback_exceptions=True)

import dash
from dash import html, dcc

app = dash.Dash(__name__)


app.layout = html.Div(
    [
        dcc.Store(id=API_COUNT_STORE, data=get_api_count().remaining),
        dcc.Store(id=TIME_DATA_STORE),
        # upper display area with two columns
        html.Div(
            children=[
                # left column
                html.Div(
                    children=[
                        html.H2("Alpha Vantage Time Data Request"),
                        html.Div(
                            children=[
                                dcc.Dropdown(
                                    id=ASSET_TYPE_DROPDOWN,
                                    options=[
                                        {"label": asset.name, "value": asset.value}
                                        for asset in AssetType
                                    ],
                                    value=AssetType.FOREX,  # default value
                                    style={"width": "100%"},
                                ),
                                dcc.Dropdown(
                                    id=INTERVAL_DROPDOWN,
                                    options=[
                                        {
                                            "label": interval.name,
                                            "value": interval.value,
                                        }
                                        for interval in Interval
                                    ],
                                    value=Interval.DAILY,  # default value
                                    style={"width": "100%"},
                                ),
                            ],
                            style={
                                "display": "flex",
                                "justify-content": "space-between",
                                "space-between": "100%",
                            },
                        ),
                        html.Div(
                            id="input-fields-container",
                            children=[
                                html.Div(
                                    style={
                                        "display": "flex",
                                        "alignItems": "center",
                                        "marginBottom": "10px",
                                    },
                                    children=[
                                        html.Label(
                                            "initial label",
                                            id=field_lable_id,
                                            style={
                                                "width": "150px",
                                                "fontWeight": "bold",
                                            },
                                        ),
                                        dcc.Input(
                                            id=field_input_id,
                                            type="text",
                                            placeholder="initial placeholder",  # Placeholder dient jetzt als Beispiel
                                            style={"flex": "1"},
                                        ),
                                    ],
                                )
                                for field_lable_id, field_input_id in [
                                    (INPUT_FIELD_1_LABEL, INPUT_FIELD_1),
                                    (INPUT_FIELD_2_LABEL, INPUT_FIELD_2),
                                ]
                            ],
                        ),
                        html.Button(
                            "Daten abrufen", id=GET_TIMEDATA_BUTTON, n_clicks=0
                        ),
                    ],
                    style={
                        "flex": 1,
                        "padding": "10px",
                        "border": "1px solid #ccc",
                    },
                ),
                # right column
                html.Div(
                    children=[
                        html.H2("Alpha Vantage Symbol Marked Search"),
                        dcc.Input(
                            id=SEARCH_INPUT_FIELD,
                            type="text",
                            placeholder="Enter search term",
                        ),
                        html.Button(SEARCH_BUTTON, id="search-button", n_clicks=0),
                        dash_table.DataTable(
                            id=SEARCH_RESULT_TABLE,
                            columns=[
                                {"name": field_name, "id": field_name}
                                for field_name in MarketMetaData.model_fields.keys()
                            ],
                            style_table={"marginTop": "10px", "overflowX": "auto"},
                            row_selectable="single",
                        ),
                    ],
                    style={
                        "flex": 1,
                        "padding": "10px",
                        "border": "1px solid #ccc",
                    },
                ),
            ],
            style={
                "display": "flex",
                "justify-content": "space-between",
                "marginBottom": "10px",
            },
        ),
        # middle display area with graph
        html.Div(
            children=[
                dcc.Graph(id=TIME_DATA_GRAPH),
            ],
            style={
                "padding": "10px",
                "border": "1px solid #ccc",
                "width": "100%",
            },
        ),
        # lower display area with two columns
        html.Div(
            children=[
                html.Div(
                    children=[
                        dcc.Input(
                            id="new-input-field",
                            type="text",
                            placeholder="Enter new input",
                            style={"margin-right": "10px"},
                        ),
                        html.Button(
                            "Submit",
                            id="new-submit-button",
                            n_clicks=0,
                        ),
                    ],
                    style={
                        "flex": 1,
                        "padding": "10px",
                        "border": "1px solid #ccc",
                    },
                    # # graph
                    # html.Div(
                    #     children=[
                    #         dcc.Graph(id=TIME_DATA_GRAPH),
                    #     ],
                    #     style={
                    #         "padding": "20px",
                    #         "border": "1px solid #ccc",
                    #         "width": "100%",
                    #     },
                ),
                # lower display area -> will be changed to a detailed interface to save the data in the database
                html.Div(
                    children=[
                        html.Div(
                            children=[
                                html.Div(
                                    id=OUTPUT_REMAINING_API_CALLS,
                                    children=f"remaining api calls: ",
                                    style={"margin-right": "20px"},
                                ),
                                html.Button(
                                    "Update DB with remaining API calls",
                                    id=UPDATE_DB_BUTTON,
                                ),
                            ],
                            style={"display": "flex", "align-items": "center"},
                        ),
                        dcc.Textarea(
                            id=DEBUG_OUTPUT_TEXT_FIELD,
                            style={
                                "margin-left": "20px",
                                "width": "100%",
                                "height": "50px",
                            },
                            readOnly=True,
                            placeholder="raw data output",
                        ),
                    ],
                    # style={
                    #     "display": "flex",
                    #     "align-items": "center",
                    #     "padding": "10px",
                    #     "border": "1px solid #ccc",
                    # },
                    style={
                        "flex": 1,
                        "padding": "10px",
                        "border": "1px solid #ccc",
                    },
                ),
            ],
            # style={
            #     "width": "100%",
            #     "display": "flex",
            #     "flexDirection": "column",
            #     "marginTop": "20px",
            # },
            style={
                "display": "flex",
                "justify-content": "space-between",
                "marginBottom": "10px",
            },
        ),
    ]
)


# region: right area: search marked symbols
@app.callback(
    [
        Output(SEARCH_RESULT_TABLE, "data"),
        Output(API_COUNT_STORE, "data", allow_duplicate=True),
        Output(DEBUG_OUTPUT_TEXT_FIELD, "value", allow_duplicate=True),
    ],
    [Input(SEARCH_BUTTON, "n_clicks")],
    [State(SEARCH_INPUT_FIELD, "value")],
    prevent_initial_call=True,
)
def search_marked_symbols(n_clicks, search_term: str):

    if not n_clicks:
        return dash.no_update

    # this could be replaced by having the db as a fast api endpoint running in the background
    with alpha_vantage_db() as db:
        search_results = [
            MarketMetaData(**result) for result in get_search_results(db, search_term)
        ]
        debug_info = "from db"

    if search_results == []:
        search_results = request_data(
            create_symbol_search_params(search_term), API_KEY, SymbolMarketSearchResults
        ).best_matches
        with alpha_vantage_db() as db:
            save_search_results(db, search_term, search_results)
        debug_info = "from api"

    df = pd.DataFrame(best_match.model_dump() for best_match in search_results)
    print(df)
    return_values = df.to_dict("records")
    return (return_values, get_api_count().remaining, debug_info)


@app.callback(
    Output(DEBUG_OUTPUT_TEXT_FIELD, "value", allow_duplicate=True),
    Output(ASSET_TYPE_DROPDOWN, "value"),
    Output(INPUT_FIELD_1, "value"),
    [Input(SEARCH_RESULT_TABLE, "selected_rows"), Input(SEARCH_RESULT_TABLE, "data")],
    prevent_initial_call=True,
)
def select_marked_search(selected_rows, data):
    if not selected_rows:
        return dash.no_update
    selected_row_data = data[selected_rows[0]]

    return (
        f"Selected row: {selected_row_data}",
        AssetType.STOCK,
        selected_row_data["symbol"],  # TODO: Hardcoded dependency to creation of table!
    )


# endregion


# region: left area: fetch data

ASSET_INPUT_DISABLED = {
    AssetType.FOREX: [False, False],
    AssetType.STOCK: [False, True],
    AssetType.CRYPTO: [False, False],
}

ASSET_INPUT_LABELS = {
    AssetType.STOCK: ["Stock Symbol", "not used"],
    AssetType.FOREX: ["From Symbol", "To Symbol"],
    AssetType.CRYPTO: ["Crypto Symbol", "Market"],
}
ASSET_PLACEHOLDERS = {
    AssetType.STOCK: ["e.g. AAPL", "e.g. NASDAQ"],
    AssetType.FOREX: ["e.g. EUR", "e.g. USD"],
    AssetType.CRYPTO: ["e.g. BTC", "e.g. USD"],
}


@app.callback(
    [
        Output(INPUT_FIELD_1_LABEL, "children"),
        Output(INPUT_FIELD_2_LABEL, "children"),
        Output(INPUT_FIELD_1, "placeholder"),
        Output(INPUT_FIELD_2, "placeholder"),
        Output(INPUT_FIELD_1, "disabled"),
        Output(INPUT_FIELD_2, "disabled"),
    ],
    [Input(ASSET_TYPE_DROPDOWN, "value")],
)
def update_fields(config: AssetType):
    labels = ASSET_INPUT_LABELS[config]
    placeholders = ASSET_PLACEHOLDERS[config]
    disabled = ASSET_INPUT_DISABLED[config]
    return labels + placeholders + disabled


@app.callback(
    [
        Output(DEBUG_OUTPUT_TEXT_FIELD, "value", allow_duplicate=True),
        Output(API_COUNT_STORE, "data", allow_duplicate=True),
        Output(TIME_DATA_STORE, "data"),
    ],
    [Input(GET_TIMEDATA_BUTTON, "n_clicks")],
    [
        State(ASSET_TYPE_DROPDOWN, "value"),
        State(INTERVAL_DROPDOWN, "value"),
        State(INPUT_FIELD_1, "value"),
        State(INPUT_FIELD_2, "value"),
    ],
    prevent_initial_call=True,
)
def fetch_data(n_clicks, asset_type, interval, input_field_1, input_field_2):

    if not n_clicks:
        return dash.no_update

    match asset_type:
        case AssetType.STOCK:
            api_params = create_stock_request_params(
                interval=interval, symbol=input_field_1
            )
        case AssetType.FOREX:
            api_params = create_forex_request_params(
                interval=interval, from_symbol=input_field_1, to_symbol=input_field_2
            )
        case AssetType.CRYPTO:
            api_params = create_crypto_request_params(
                interval=interval, symbol=input_field_1, market=input_field_2
            )
        case _:
            raise ValueError("Invalid Asset Type")

    try:
        requested_data = request_data(api_params, API_KEY, AssetHistoryData)
        return_string = f"{requested_data}"
        return_json = requested_data.model_dump_json()
    except Exception as e:
        return_string = f"Error: {e}"
        return_json = ""

    return return_string, get_api_count().remaining, return_json


# endregion

# region: graph area


@app.callback(
    Output(TIME_DATA_GRAPH, "figure"),
    Input(TIME_DATA_STORE, "data"),
)
def update_graph(data):
    if not data:
        return dash.no_update

    asset_data = AssetHistoryData.model_validate_json(data)

    df = {
        "time": list(asset_data.time_series.keys()),
        "close": [ts_data.close for ts_data in asset_data.time_series.values()],
    }

    print(df)

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=df["time"],
            y=df["close"],
            mode="lines+markers",
            name="Close",
            line=dict(color="blue"),
        )
    )

    fig.update_layout(
        title="Time Series Data",
        xaxis_title="Time",
        yaxis_title="Price",
        template="plotly_white",
    )

    return fig


# endregion


# region: lower display area (info)
@app.callback(
    Output(OUTPUT_REMAINING_API_CALLS, "children"),
    Input(API_COUNT_STORE, "data"),
)
def update_remaining_calls(api_data):
    return f"Remaining API calls: {api_data}"


@app.callback(
    Output(DEBUG_OUTPUT_TEXT_FIELD, "value", allow_duplicate=True),
    Input(UPDATE_DB_BUTTON, "n_clicks"),
    prevent_initial_call=True,
)
def use_remaining_to_update_db():
    # create async function to use remaining api calls to update db

    pass


# endregion


if __name__ == "__main__":
    app.run_server(debug=True)
