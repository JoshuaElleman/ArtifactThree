from dash import Dash, html, dcc, dash_table, Input, Output, State
import plotly.express as px
import pandas as pd
from datetime import date, datetime
from CRUD import BoardGamePlays

# Initialize Dash application
app = Dash(__name__)
server = app.server

# Initialize database connection using CRUD class
db = BoardGamePlays()

# -----------------------------
# Layout Definition
# -----------------------------
# Defines the structure and components of the dashboard UI
app.layout = html.Div([
    html.H1("Board Game Plays Dashboard"),

    # Hidden store used to persist selected record ID across callbacks
    dcc.Store(id="selected-record-id"),

    # Input section for creating or editing a play record
    html.Div([
        # Date picker for selecting play date
        dcc.DatePickerSingle(
            id="date-input",
            date=date.today(),
            display_format="YYYY-MM-DD"
        ),
        # Game and player inputs
        dcc.Input(id="game-input", type="text", placeholder="Game"),
        dcc.Input(
            id="player-count-input",
            type="number",
            placeholder="Player Count",
            min=2,
            max=4,
            step=1
        ),
        dcc.Input(id="player1-input", type="text", placeholder="Player 1"),
        dcc.Input(id="player2-input", type="text", placeholder="Player 2"),
        dcc.Input(id="player3-input", type="text", placeholder="Player 3"),
        dcc.Input(id="player4-input", type="text", placeholder="Player 4"),
        dcc.Input(id="winner-input", type="text", placeholder="Winner"),
    ], style={"display": "grid", "gap": "10px", "marginBottom": "20px"}),

    # Action buttons for CRUD operations
    html.Div([
        html.Button("Create", id="create-btn", n_clicks=0),
        html.Button("Delete Selected", id="delete-btn", n_clicks=0),
        html.Button("Refresh", id="refresh-btn", n_clicks=0),
        html.Button("Clear Form", id="clear-btn", n_clicks=0),
    ], style={"display": "flex", "gap": "10px", "marginBottom": "20px"}),

    # Displays feedback messages to the user
    html.Div(id="status-msg", style={"marginBottom": "20px"}),

    html.H2("Player Statistics"),

    # Dropdown used to filter statistics by exact player count
    html.Div([
        html.Label("Player Count Filter"),
        dcc.Dropdown(
            id="player-count-filter",
            options=[
                {"label": "2 Players", "value": 2},
                {"label": "3 Players", "value": 3},
                {"label": "4 Players", "value": 4},
            ],
            value=2,
            clearable=False,
            style={"width": "200px"}
        ),
    ], style={"marginBottom": "20px"}),

    # Pie chart showing win distribution
    dcc.Graph(id="win-pie-chart"),

    # Data table displaying all play records
    dash_table.DataTable(
        id="plays-table",
        columns=[],
        data=[],
        page_size=10,
        row_selectable="single",
        selected_rows=[],
        style_table={"overflowX": "auto"},
        style_cell={"textAlign": "left", "padding": "8px"},
        style_header={"fontWeight": "bold"},
        sort_action="native",
        filter_action="native"
    )
])


# -----------------------------
# Data Fetching and Cleaning
# -----------------------------
def fetch_records():
    """
    Retrieves records from MongoDB and normalizes fields for display and analysis.
    Converts ObjectId and datetime values into serializable formats.
    """
    records = db.read({})
    cleaned = []

    for record in records:
        clean = dict(record)

        # Convert MongoDB ObjectId to string for Dash compatibility
        clean["_id"] = str(clean["_id"])

        # Normalize Date field to ISO string format
        if "Date" in clean and clean["Date"]:
            if isinstance(clean["Date"], datetime):
                clean["Date"] = clean["Date"].date().isoformat()
            else:
                clean["Date"] = str(clean["Date"])

        # Ensure Player Count is always an integer
        if "Player Count" in clean and clean["Player Count"] not in (None, ""):
            try:
                clean["Player Count"] = int(clean["Player Count"])
            except (ValueError, TypeError):
                clean["Player Count"] = None

        cleaned.append(clean)

    return cleaned


# -----------------------------
# Player Statistics Builder
# -----------------------------
def build_player_stats(records):
    """
    Aggregates player statistics from records.
    Calculates total plays, wins, and win percentage per player.
    """
    player_play_counts = {}
    player_win_counts = {}

    for record in records:
        # Count appearances for each player
        for field in ["Player 1", "Player 2", "Player 3", "Player 4"]:
            player = record.get(field, "")
            if player:
                player_play_counts[player] = player_play_counts.get(player, 0) + 1

        # Count wins (excluding empty values)
        winner = record.get("Winner", "")
        if winner:
            player_win_counts[winner] = player_win_counts.get(winner, 0) + 1

    # Combine all unique players
    players = set(player_play_counts.keys()) | set(player_win_counts.keys())

    rows = []
    for player in players:
        plays = player_play_counts.get(player, 0)
        wins = player_win_counts.get(player, 0)

        # Calculate win percentage safely
        win_pct = (wins / plays * 100) if plays > 0 else 0

        rows.append({
            "Player": player,
            "Plays": plays,
            "Wins": wins,
            "Win Percentage": round(win_pct, 2)
        })

    return pd.DataFrame(rows)


# -----------------------------
# Table Update Callback
# -----------------------------
@app.callback(
    Output("plays-table", "columns"),
    Output("plays-table", "data"),
    Input("refresh-btn", "n_clicks"),
    Input("create-btn", "n_clicks"),
    Input("delete-btn", "n_clicks")
)
def load_plays(refresh_clicks, create_clicks, delete_clicks):
    """
    Loads records into the DataTable.
    Re-runs whenever data is created, deleted, or refreshed.
    """
    records = fetch_records()

    if not records:
        return [], []

    df = pd.DataFrame(records)

    # Define preferred column order for display
    preferred_order = [
        "_id", "Date", "Game", "Player Count",
        "Player 1", "Player 2", "Player 3", "Player 4", "Winner"
    ]

    # Preserve column order while including any additional fields
    existing_columns = [col for col in preferred_order if col in df.columns]
    remaining_columns = [col for col in df.columns if col not in existing_columns]
    df = df[existing_columns + remaining_columns]

    columns = [{"name": col, "id": col} for col in df.columns]
    return columns, df.to_dict("records")


# -----------------------------
# Populate Form from Selected Row
# -----------------------------
@app.callback(
    Output("selected-record-id", "data"),
    Output("date-input", "date"),
    Output("game-input", "value"),
    Output("player-count-input", "value"),
    Output("player1-input", "value"),
    Output("player2-input", "value"),
    Output("player3-input", "value"),
    Output("player4-input", "value"),
    Output("winner-input", "value"),
    Input("plays-table", "selected_rows"),
    State("plays-table", "data"),
    prevent_initial_call=True
)
def populate_form_from_selected_row(selected_rows, table_data):
    """
    Populates the input fields when a row is selected in the table.
    Enables editing or deletion of a specific record.
    """
    if not selected_rows or not table_data:
        return None, None, None, None, None, None, None, None, None

    row = table_data[selected_rows[0]]

    return (
        row.get("_id"),
        row.get("Date"),
        row.get("Game"),
        row.get("Player Count"),
        row.get("Player 1"),
        row.get("Player 2"),
        row.get("Player 3"),
        row.get("Player 4"),
        row.get("Winner"),
    )


# -----------------------------
# Create Record Callback
# -----------------------------
@app.callback(
    Output("status-msg", "children"),
    Input("create-btn", "n_clicks"),
    State("date-input", "date"),
    State("game-input", "value"),
    State("player-count-input", "value"),
    State("player1-input", "value"),
    State("player2-input", "value"),
    State("player3-input", "value"),
    State("player4-input", "value"),
    State("winner-input", "value"),
    prevent_initial_call=True
)
def create_play(n_clicks, play_date, game, player_count, player1, player2, player3, player4, winner):
    """
    Validates input and inserts a new play record into the database.
    """
    if not game or not winner:
        return "Please enter at least a game and winner."

    if player_count is None or player_count < 2 or player_count > 4:
        return "Player count must be between 2 and 4."

    players = [player1, player2, player3, player4]
    filled_players = [p for p in players if p]

    if len(filled_players) != player_count:
        return f"Please provide exactly {player_count} player names."

    # Allow 'Tie' as a valid outcome
    if winner != "Tie" and winner not in filled_players:
        return "Winner must be one of the players or 'Tie'."

    play_doc = {
        "Date": datetime.fromisoformat(play_date) if play_date else None,
        "Game": game,
        "Player Count": player_count,
        "Player 1": player1 or "",
        "Player 2": player2 or "",
        "Player 3": player3 or "",
        "Player 4": player4 or "",
        "Winner": winner
    }

    success = db.create(play_doc)
    return f"Added play for {game}." if success else "Failed to add play."


# -----------------------------
# Delete Record Callback
# -----------------------------
@app.callback(
    Output("status-msg", "children", allow_duplicate=True),
    Input("delete-btn", "n_clicks"),
    State("selected-record-id", "data"),
    prevent_initial_call=True
)
def delete_selected_play(n_clicks, record_id):
    """
    Deletes the selected record from the database using its unique ID.
    """
    if not record_id:
        return "Select a row before deleting."

    count = db.delete_one_by_id(record_id)
    return "Record deleted." if count else "No record was deleted."


# -----------------------------
# Clear Form Callback
# -----------------------------
@app.callback(
    Output("selected-record-id", "data", allow_duplicate=True),
    Output("date-input", "date", allow_duplicate=True),
    Output("game-input", "value", allow_duplicate=True),
    Output("player-count-input", "value", allow_duplicate=True),
    Output("player1-input", "value", allow_duplicate=True),
    Output("player2-input", "value", allow_duplicate=True),
    Output("player3-input", "value", allow_duplicate=True),
    Output("player4-input", "value", allow_duplicate=True),
    Output("winner-input", "value", allow_duplicate=True),
    Output("plays-table", "selected_rows"),
    Input("clear-btn", "n_clicks"),
    prevent_initial_call=True
)
def clear_form(n_clicks):
    """
    Resets all input fields and clears selected table row.
    """
    return None, date.today().isoformat(), "", None, "", "", "", "", "", []


# -----------------------------
# Graph Update Callback
# -----------------------------
@app.callback(
    Output("win-pie-chart", "figure"),
    Input("player-count-filter", "value"),
    Input("refresh-btn", "n_clicks"),
    Input("create-btn", "n_clicks"),
    Input("delete-btn", "n_clicks"),
)
def update_graphs(player_count, refresh_clicks, create_clicks, delete_clicks):
    """
    Updates the win distribution pie chart based on selected player count.
    """
    records = fetch_records()

    if not records:
        empty_df = pd.DataFrame({"Message": ["No data"], "Value": [1]})
        return px.pie(empty_df, names="Message", values="Value", title="No Data")

    # Filter records by exact player count
    filtered_records = [
        r for r in records
        if r.get("Player Count") == int(player_count)
    ]

    if not filtered_records:
        empty_df = pd.DataFrame({"Message": ["No matching games"], "Value": [1]})
        return px.pie(empty_df, names="Message", values="Value", title="No Matching Games")

    stats_df = build_player_stats(filtered_records)

    if stats_df.empty:
        empty_df = pd.DataFrame({"Message": ["No player stats"], "Value": [1]})
        return px.pie(empty_df, names="Message", values="Value", title="No Player Stats")

    # Exclude players with zero wins from pie chart
    pie_source = stats_df[stats_df["Wins"] > 0]

    if pie_source.empty:
        return px.pie(
            pd.DataFrame({"Message": ["No wins recorded"], "Value": [1]}),
            names="Message",
            values="Value",
            title=f"Win Share ({player_count}-Player Games)"
        )

    pie_fig = px.pie(
        pie_source,
        names="Player",
        values="Wins",
        title=f"Win Share ({player_count}-Player Games)"
    )

    pie_fig.update_traces(textinfo="label+percent")

    return pie_fig


# Run the application
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8050, debug=False)