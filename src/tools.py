import json
import os
import sqlite3

import matplotlib.pyplot as plt
import networkx as nx
import pandas as pd
from matplotlib.colors import to_rgba, to_hex
from autogen import Agent, GroupChat


# Function to blend colors
def blend_colors(colors):
    if not colors:
        return "grey"  # Default color for fully defused bombs or no color
    rgba_colors = [to_rgba(color.lower()) for color in colors]
    blended_rgba = [sum(channel) / len(channel) for channel in zip(*rgba_colors)]
    return to_hex(blended_rgba)


# Draw initial graph without displaying it
def draw_initial_graph(pos, G, bomb_states):
    plt.figure(figsize=(16, 8))
    # Draw nodes and edges
    nx.draw(
        G, pos, with_labels=True, node_color="skyblue", font_size=15, font_weight="bold"
    )
    # Draw initial bomb colors
    for room, colors in bomb_states.items():
        blended_color = blend_colors(colors)
        nx.draw_networkx_nodes(
            G, pos, nodelist=[room], node_color=blended_color, node_size=500
        )
    plt.title("Initial Rooms and Bomb Locations")
    plt.close()


# Parse bomb information from obs_text
def parse_bomb_info(text):
    if pd.isna(text):
        return None
    if "Results: You inspected Bomb" in text:
        bomb_info_part = text.split("Results: You inspected Bomb")[-1]
        sequence_part = bomb_info_part.split("remaining sequence is ")[-1]
        colors = sequence_part.split(".")[0].split("-")
        return [color.lower() for color in colors]
    return None


# Function to update the graph for each round
def update_graph(
    round_number, actions_text, agent_positions, bomb_states, pos, G, output_dir
):
    plt.figure(figsize=(16, 8))
    # Draw nodes and edges
    nx.draw(
        G, pos, with_labels=True, node_color="skyblue", font_size=15, font_weight="bold"
    )
    # Update bomb colors
    for room, colors in bomb_states.items():
        blended_color = blend_colors(colors)
        nx.draw_networkx_nodes(
            G, pos, nodelist=[room], node_color=blended_color, node_size=500
        )

    # Draw agent positions with distinct offsets to avoid overlapping
    offset = 0.03
    for i, (agent, position) in enumerate(agent_positions.items()):
        agent_pos = pos[position]
        vertical_offset = (i % 3) * offset
        vertical_offset -= 0.05
        horizontal_offset = offset
        nx.draw_networkx_nodes(
            G, pos, nodelist=[position], node_color="red", node_size=600, alpha=0.0
        )
        plt.text(
            agent_pos[0] + horizontal_offset,
            agent_pos[1] + vertical_offset,
            agent,
            fontsize=12,
            color="black",
            fontweight="bold",
        )

    plt.text(
        0.05,
        0.95,
        f"Round {round_number}",
        transform=plt.gca().transAxes,
        fontsize=20,
        verticalalignment="top",
    )
    plt.title(f"Rooms, Their Connectivity, and Bomb Locations - Round {round_number}")

    # Add actions text on the side
    plt.figtext(
        0.8,
        0.5,
        actions_text,
        wrap=True,
        horizontalalignment="left",
        fontsize=14,
        bbox=dict(facecolor="white", alpha=0.5),
    )

    plt.savefig(os.path.join(output_dir, f"round_{round_number}.png"))
    plt.close()


def get_log(dbname, table="chat_completions"):
    con = sqlite3.connect(dbname)
    query = f"SELECT * from {table}"
    cursor = con.execute(query)
    rows = cursor.fetchall()
    column_names = [description[0] for description in cursor.description]
    data = [dict(zip(column_names, row)) for row in rows]
    con.close()
    return data


def str_to_dict(s):
    return json.loads(s)


def decode_actions(actions_dict, Action):
    from initial_paper.gymdragon.gym_dragon.core import Tool

    chat_agents = {}
    agents_names = actions_dict.get("agents_names", [])
    actions = actions_dict.get("agents_actions", [])
    for agent_name, action in zip(agents_names, actions):
        agent_name = agent_name.split("_")[-1]
        if action.startswith("go_to_node_"):
            room = int(action.split("_")[-1])
            chat_agents[agent_name] = Action.go_to(room)
        elif action == "inspect_bomb":
            chat_agents[agent_name] = Action.inspect_bomb
        elif action.startswith("apply"):
            tool = action.split("_")[-2]
            if tool == "red":
                chat_agents[agent_name] = Action.use_tool(Tool.red)
            elif tool == "green":
                chat_agents[agent_name] = Action.use_tool(Tool.green)
            elif tool == "blue":
                chat_agents[agent_name] = Action.use_tool(Tool.blue)

    return chat_agents


def format_messages(messages, codenames):
    # Variables to hold combined data
    round_number = None
    team_score = None
    room_info = {}
    actions = {}
    results = {}
    communication_messages = set()

    # Parsing the messages
    for i, message in enumerate(messages):
        parts = message.split(". ")

        # Extract round number and team score
        if round_number is None:
            round_number = parts[0].split(": ")[-1]
            team_score = parts[1].split(": ")[-1]

        # Extract specific information for each agent
        room_content = parts[4].replace("Room contents: ", "")
        action_taken = parts[3]
        result_info = parts[2].replace("Results: ", "")

        # Capture information specific to the agent
        room_info[codenames[i]] = room_content
        actions[codenames[i]] = action_taken
        results[codenames[i]] = result_info

        # Extract communication messages
        comm_message = (
            parts[-1]
            .replace("Communication messages sent by your teammates: ", "")
            .strip()
        )
        if comm_message:
            communication_messages.add(comm_message)

    # Construct the combined message
    combined_message = (
        f"Round: {round_number} ended. Total team score: {team_score}.\n\n"
    )

    for codename in codenames[: len(messages)]:
        combined_message += f"{codename}:\n"
        combined_message += (
            f"- Room Content: {room_info.get(codename, 'No relevant information.')}\n"
        )
        combined_message += (
            f"- Action: {actions.get(codename, 'No action recorded.')}\n"
        )
        combined_message += (
            f"- Results: {results.get(codename, 'No results recorded.')}\n\n"
        )

    if communication_messages:
        combined_message += "Communication messages sent by your teammates:\n"
        for comm_message in communication_messages:
            combined_message += f"- {comm_message}\n"
    else:
        combined_message += ""

    combined_message += f"Round {int(round_number) +1} will start."
    return combined_message


def create_unique_filename(filename):
    """
    Check if a file already exists. If it exists, add _1, _2, etc., until a unique name is found.
    Returns the unique filename.
    """
    base, extension = os.path.splitext(filename)
    counter = 1
    unique_filename = filename

    while os.path.exists(unique_filename):
        unique_filename = f"{base}_{counter}{extension}"
        counter += 1

    return unique_filename
