import matplotlib.pyplot as plt
from matplotlib.colors import to_rgba, to_hex
import networkx as nx
import pandas as pd
import os


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
