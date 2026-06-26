import json
import os
from typing import Optional

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

PLOT_IN_GRID = True


def load_data(file_path: str) -> Optional[pd.DataFrame]:
    data_list = []
    time_start = 0
    first_event_in_cycle = True

    with open(file_path, encoding="utf-8") as f:
        for line in f:
            try:
                event = json.loads(line)
                event_type = event.get("event_type")

                if event_type == "objective_progress":
                    if first_event_in_cycle:
                        time_start = event["time_elapsed"]
                        first_event_in_cycle = False

                    details = event.get("details", {})
                    data_list.append(
                        {
                            "time_elapsed": event["time_elapsed"] - time_start,
                            "progress": details.get("progress"),
                            "rate_of_change": details.get("rate_of_change"),
                            "cycle_id": details.get("cycle_id"),
                        }
                    )
                elif event_type == "Objective reached":
                    first_event_in_cycle = True

            except json.JSONDecodeError:
                print(f"Warning: Skipping malformed line: {line.strip()}")

    return pd.DataFrame(data_list).sort_values("time_elapsed")


def plot_as_grid(df: pd.DataFrame, path: str, window_size: int) -> None:
    print("Plotting mode selected: GRID.")
    os.makedirs(path, exist_ok=True)
    path_rate = os.path.join(path, "rate_of_change.png")
    path_progress = os.path.join(path, "progress.png")

    g_progress = sns.FacetGrid(
        df, col="cycle_id", col_wrap=4, height=3, aspect=1.5, sharey=True
    )
    g_progress.map(sns.scatterplot, "time_elapsed", "progress", alpha=0.4, color="gray")
    g_progress.map(
        sns.lineplot,
        "time_elapsed",
        "progress_smoothed",
        color="deepskyblue",
        linewidth=2.5,
    )
    g_progress.set_axis_labels("Elapsed Time (s)", "Progress")
    g_progress.set_titles("Cycle {col_name}")
    g_progress.fig.suptitle(
        f"Smoothed Progress (Window={window_size}) vs. Raw Data", y=1.03
    )
    plt.savefig(path_progress)
    plt.close()
    print("Successfully saved 'progress.png'")

    g_rate = sns.relplot(
        data=df,
        x="time_elapsed",
        y="rate_of_change",
        col="cycle_id",
        col_wrap=4,
        kind="line",
        color="coral",
        height=3,
        aspect=1.5,
        marker="o",
    )
    g_rate.set_axis_labels("Elapsed Time (s)", "Rate of Change (Raw)")
    g_rate.set_titles("Cycle {col_name}")
    g_rate.fig.suptitle("Raw Rate of Change Over Time", y=1.03)
    plt.savefig(path_rate)
    plt.close()
    print("Successfully saved 'rate.png'")


def plot_as_single(df: pd.DataFrame, path: str, window_size: int) -> None:
    print("Plotting mode selected: SINGLE chart with overlays.")

    os.makedirs(path, exist_ok=True)
    path_rate = os.path.join(path, "rate_of_change.png")
    path_progress = os.path.join(path, "progress.png")

    plt.figure(figsize=(12, 7))
    sns.lineplot(
        data=df,
        x="time_elapsed",
        y="progress_smoothed",
        hue="cycle_id",
        palette="viridis",
        linewidth=2.5,
    )
    sns.scatterplot(
        data=df,
        x="time_elapsed",
        y="progress",
        hue="cycle_id",
        palette="viridis",
        alpha=0.2,
        legend=False,
    )
    plt.title(f"Smoothed Progress per Cycle (Window={window_size})", fontsize=16)
    plt.xlabel("Elapsed Time (s)", fontsize=12)
    plt.ylabel("Progress", fontsize=12)
    plt.legend(title="Cycle ID")
    plt.tight_layout()
    plt.savefig(path_progress)
    plt.close()
    print("Successfully saved 'progress.png'")

    plt.figure(figsize=(12, 7))
    sns.lineplot(
        data=df,
        x="time_elapsed",
        y="rate_of_change",
        hue="cycle_id",
        palette="plasma",
        marker="o",
    )
    plt.title("Raw Rate of Change per Cycle", fontsize=16)
    plt.xlabel("Elapsed Time (s)", fontsize=12)
    plt.ylabel("Rate of Change", fontsize=12)
    plt.legend(title="Cycle ID")
    plt.tight_layout()
    plt.savefig(path_rate)
    plt.close()
    print("Successfully saved 'rate.png'")


def plot_grid(input_file, smoothing_window=3):
    path = input_file.split("/")
    path = "/".join(path[:2]) + "/"

    df = load_data(input_file)

    df["progress_smoothed"] = (
        df.groupby("cycle_id")["progress"]
        .rolling(window=smoothing_window, min_periods=1, center=True)
        .mean()
        .reset_index(level=0, drop=True)
    )

    sns.set_theme(style="whitegrid")
    if PLOT_IN_GRID:
        plot_as_grid(df, path, smoothing_window)
    else:
        plot_as_single(df, path, smoothing_window)
