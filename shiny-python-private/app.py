from shiny import App, render, ui, reactive
import pandas as pd
import matplotlib.pyplot as plt
from my_custom_package import DataProcessor, generate_sample_data, format_number

# Generate sample data using our custom package
sample_data = generate_sample_data(200)

app_ui = ui.page_fluid(
    ui.h1("Shiny App with Custom Package"),
    ui.page_sidebar(
        ui.sidebar(
            ui.input_slider("n_rows", "Number of rows:", min=10, max=200, value=100),
            ui.input_selectize("category", "Filter by category:",
                             choices=["All"] + list(sample_data["category"].unique()),
                             selected="All"),
            ui.input_numeric("min_value", "Minimum value:", value=None),
            ui.input_numeric("max_value", "Maximum value:", value=None),
            ui.hr(),
            ui.h4("Data Statistics"),
            ui.output_text_verbatim("stats")
        ),
        ui.h3("Filtered Data"),
        ui.output_data_frame("data_table"),
        ui.h3("Value Distribution"),
        ui.output_plot("value_plot")
    )
)

def server(input, output, session):
    @reactive.Calc
    def filtered_data():
        # Use our custom DataProcessor
        processor = DataProcessor()

        # Start with sample data limited by slider
        data_subset = sample_data.head(input.n_rows())
        processor.load_data(data_subset)

        # Apply category filter
        if input.category() != "All":
            processor.data = processor.data[processor.data["category"] == input.category()]

        # Apply value filters using our custom method
        processor.filter_data("value", input.min_value(), input.max_value())

        return processor

    @output
    @render.data_frame
    def data_table():
        data = filtered_data().data
        # Format the value column using our custom function
        data_display = data.copy()
        data_display["value"] = data_display["value"].apply(lambda x: format_number(x, 2))
        return data_display

    @output
    @render.text
    def stats():
        stats = filtered_data().calculate_stats()
        if not stats:
            return "No data available"

        output_lines = [f"Total records: {stats['count']}"]

        if "value" in stats["mean"]:
            output_lines.extend([
                f"Value mean: {format_number(stats['mean']['value'])}",
                f"Value median: {format_number(stats['median']['value'])}",
                f"Value std: {format_number(stats['std']['value'])}"
            ])

        if "score" in stats["mean"]:
            output_lines.extend([
                f"Score mean: {format_number(stats['mean']['score'])}",
                f"Score median: {format_number(stats['median']['score'])}"
            ])

        return "\n".join(output_lines)

    @output
    @render.plot
    def value_plot():
        data = filtered_data().data
        if data.empty:
            fig, ax = plt.subplots()
            ax.text(0.5, 0.5, "No data to display", ha="center", va="center")
            return fig

        fig, ax = plt.subplots(figsize=(10, 6))
        ax.hist(data["value"], bins=20, alpha=0.7, edgecolor="black")
        ax.set_xlabel("Value")
        ax.set_ylabel("Frequency")
        ax.set_title("Distribution of Values")
        ax.grid(True, alpha=0.3)

        return fig

app = App(app_ui, server)
