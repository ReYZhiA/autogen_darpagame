import pandas as pd
import networkx as nx
import imageio
import os

from tools import parse_bomb_info, draw_initial_graph, update_graph

# Load the CSV file
summary_file_path = (
    "./data/gpt-4-turbo-preview/gpt-4/seed0/summary.csv"  # Change this path
)
game_summary = pd.read_csv(summary_file_path)

# Create directory for saving images
output_dir = "./graph_images/temp"
os.makedirs(output_dir, exist_ok=True)

# Extract the current room from obs_text
game_summary["current_room"] = game_summary["obs_text"].str.extract(
    r"You are currently in Room (\d+)"
)

# Remove rows where current_room is NaN
game_summary = game_summary.dropna(subset=["current_room"])
game_summary["bomb_colors"] = game_summary["obs_text"].apply(parse_bomb_info)


# Init
bomb_states = {}
G = nx.Graph()

agent_paths = game_summary.groupby("agent_id")["current_room"].apply(list).reset_index()

# Create a list of edges based on the paths, excluding self-loops
edges = []
for path in agent_paths["current_room"]:
    for i in range(len(path) - 1):
        if path[i] != path[i + 1]:
            edges.append((path[i], path[i + 1]))

G.add_edges_from(edges)

# Initialize bomb states
initial_bomb_info = game_summary.dropna(subset=["bomb_colors"]).drop_duplicates(
    subset=["current_room"]
)
for index, row in initial_bomb_info.iterrows():
    bomb_states[row["current_room"]] = row["bomb_colors"]

# Compute fixed layout
pos = nx.spring_layout(G)

draw_initial_graph(pos, G, bomb_states)


# Process each round and update the graph
for round_number in sorted(game_summary["round"].unique()):
    round_data = game_summary[game_summary["round"] == round_number]
    actions_text = ""
    agent_positions = {}
    # Update bomb states based on actions
    for index, row in round_data.iterrows():
        if row["bomb_colors"] is not None:
            bomb_states[row["current_room"]] = row["bomb_colors"]
        elif "use" in row["action"] and "tool" in row["action"]:
            room = row["current_room"]
            tool_color = row["action"].split(" ")[-2].lower()
            if room in bomb_states and bomb_states[room] is not None:
                if tool_color in bomb_states[room]:
                    bomb_states[room].remove(tool_color)
                    if not bomb_states[room]:  # If all colors are removed
                        bomb_states[room] = None  # Mark as fully defused
        # Collect actions for the text
        actions_text += (
            f"Agent {row['agent_id']} in Room {row['current_room']}: {row['action']}\n"
        )
        agent_positions[row["agent_id"]] = row["current_room"]

    # Add edges and nodes for the current round
    for path in round_data.groupby("agent_id")["current_room"].apply(list):
        for i in range(len(path) - 1):
            if path[i] != path[i + 1]:
                G.add_edge(path[i], path[i + 1])
    # Ensure all nodes have positions
    for room in bomb_states.keys():
        G.add_node(room)
    # Update the graph for the current round
    update_graph(
        round_number, actions_text, agent_positions, bomb_states, pos, G, output_dir
    )

# Create GIF
images = []
for round_number in sorted(game_summary["round"].unique()):
    images.append(
        imageio.v2.imread(os.path.join(output_dir, f"round_{round_number}.png"))
    )
imageio.mimsave(
    "./graph_images/rooms_and_bombs.gif", images, duration=4000
)  # Slower iteration

# Remove temporary images
for round_number in sorted(game_summary["round"].unique()):
    os.remove(os.path.join(output_dir, f"round_{round_number}.png"))
