import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import numpy as np
import pandas as pd
import ast
import seaborn as sns

def plot_demand_percentage(df_demand, data_demand_special, days, clustered="Non-Clustered"):
   # Check if the 'Pattern_clear' column is not a string
    if pd.api.types.infer_dtype(df_demand['Pattern_clear']) == 'string':
        df_demand['Pattern_clear'] = df_demand['Pattern_clear'].apply(ast.literal_eval)

    for i, day in enumerate(days):
        df_demand[day] = df_demand['Pattern_clear'].apply(lambda x: x[i])


    # Calculate the average Demand per day
    demand_per_day = {}
    for day in days:
        demand_per_day[day] = df_demand[df_demand[day] == 1]['Demand'].sum()
    # Assuming you already have the average_demand_per_day dictionary calculated as mentioned in your code

    # Calculate the sum of average demand per day
    total_demand = sum(demand_per_day.values())

    # Calculate the percentage for each day's average demand
    percentage_demand_per_day = {}

    for day, average_demand in demand_per_day.items():
        percentage = round((average_demand / total_demand) * 100, 2)
        percentage_demand_per_day[day] = percentage

    percentage_demand_per_day = pd.Series(percentage_demand_per_day)
    # Plot the data
    plt.figure(figsize=(8, 4))
    plt.bar(percentage_demand_per_day.index, percentage_demand_per_day.values, color='lightgrey',width=0.5)
    plt.xlabel('Days of the Week', fontsize=12)
    plt.ylabel('Percentage Demand (%)', fontsize=12)
    plt.title(f'Percentage Demand per Day ({data_demand_special} - {clustered})', fontsize=14)
    plt.xticks(rotation=0, fontsize=10)  # To display day names horizontally
    # Create a list of tick positions and labels
    tick_positions = [0, 5, 10, 15, 20, 25]
    tick_labels = [f"{pos}%" for pos in tick_positions]

    # Set the y-axis ticks and labels
    plt.yticks(tick_positions, tick_labels, fontsize=10)
    plt.grid(axis='y', linestyle='--', alpha=0.5)
    plt.tight_layout()
    # Get the current Axes object
    ax = plt.gca()

    # Add labels above the bars
    for patch, day in zip(ax.patches, days):
        y_value = patch.get_height()
        plt.text(patch.get_x() + patch.get_width() / 2, y_value, f"{y_value:.1f}%", ha='center', va='bottom')
    print("Bar plot for demand has been saved.")

    return plt.gcf()


def plot_profile_comparison(data_profile, data_notprofile, data_demand_special, days, database, clustered="Non-Clustered"):
    # Calculate percentage Weight per day for data_profile
    sum_Weight_per_day_profile = data_profile.groupby('Weekday')['Weight'].sum()
    total_weight_profile = sum_Weight_per_day_profile.sum()
    percentage_Weight_per_day_profile = sum_Weight_per_day_profile / total_weight_profile * 100
    percentage_Weight_per_day_profile = percentage_Weight_per_day_profile.reindex([0, 1, 2, 3, 4])

    # Calculate percentage Weight per day for data_notprofile
    sum_Weight_per_day_notprofile = data_notprofile.groupby('Weekday')['Weight'].sum()
    total_weight_notprofile = sum_Weight_per_day_notprofile.sum()
    percentage_Weight_per_day_notprofile = sum_Weight_per_day_notprofile / total_weight_notprofile * 100
    percentage_Weight_per_day_notprofile = percentage_Weight_per_day_notprofile.reindex([0, 1, 2, 3, 4])

    # Convert the dictionaries to pandas Series for plotting
    percentage_profile = pd.Series(percentage_Weight_per_day_profile)
    percentage_notprofile = pd.Series(percentage_Weight_per_day_notprofile)

    # Create an array for the x-axis positions
    x = np.arange(len(days))

    # Set the width of the bars
    width = 0.35

    # Plot both sets of data side by side
    plt.figure(figsize=(10, 5))
    plt.bar(x - width/2, percentage_notprofile, width, label='Without Profiles', color='grey', align='center')
    plt.bar(x + width/2, percentage_profile, width, label='With Profiles', color='lightgrey', align='center')

     # Add labels above the bars
    # Add labels above the bars
    for i in range(len(days)):
        rounded_percentage_notprofile = round(percentage_notprofile[i], 1)
        rounded_percentage_profile = round(percentage_profile[i], 1)
        plt.text(x[i] - width/2, percentage_notprofile[i], f"{rounded_percentage_notprofile}%", ha='center', va='bottom')
        plt.text(x[i] + width/2, percentage_profile[i], f"{rounded_percentage_profile}%", ha='center', va='bottom')
    plt.xlabel('Days of the Week', fontsize=12)
    plt.ylabel('Percentage Weight (%)', fontsize=12)
    plt.title(f'Percentage Weight with and without Profiles per Day ({database} - {data_demand_special} - {clustered})', fontsize=14)
    plt.xticks(x, days, rotation=0, fontsize=10)
    tick_positions = [0, 5, 10, 15, 20, 25, 30]
    tick_labels = [f"{pos}%" for pos in tick_positions]

    # Set the y-axis ticks and labels
    plt.yticks(tick_positions, tick_labels, fontsize=10)
    plt.grid(axis='y', linestyle='--', alpha=0.5)
    plt.legend()
    plt.tight_layout()
    print("Bar plot for"+ '(' +database +')' + "has been saved.")
    return plt.gcf()
def plots(data_demand_base, data_demand_special, df_profile_base, df_full, plots_base, df_reult_path, clustered="Non-Clustered"):

    df_demand = pd.read_csv(data_demand_base+ "\\" + data_demand_special+".csv", encoding="latin_1", sep=";")
    df_profile = pd.read_csv(df_profile_base+ data_demand_special+".csv", encoding="latin_1", sep=";")
    df_result = pd.read_csv(df_reult_path, encoding="latin_1", sep=";")
    # Convert the 'Loading_Date' column to a datetime object
    df_full['Loading_Date'] = pd.to_datetime(df_full['Loading_Date'])
    # Calculate the weekday for each 'Loading_Date'
    df_full['Weekday'] = df_full['Loading_Date'].dt.weekday

    df_notprofile = pd.read_csv(df_profile_base+"withoutprofile_"+ data_demand_special+".csv", encoding="latin_1", sep=";")

    # Create a PdfPages object to save the plots
    pp = PdfPages(plots_base +'plot_'+ data_demand_special + clustered +'.pdf', keep_empty=False)
    days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri']

    # Create the plots
    fig1 = plot_demand_percentage(df_demand, data_demand_special, days, clustered)
    fig2 = plot_profile_comparison(df_profile, df_notprofile, data_demand_special, days, "Only Profiles", clustered)
    fig3 = plot_profile_comparison(df_result, df_full, data_demand_special, days, "Full Data", clustered)
    #fig3 = plot_full_data_comparison(df_full,days)

    # Add the plots to the PdfPages object
    pp.savefig(fig1, bbox_inches='tight')
    pp.savefig(fig2, bbox_inches='tight')
    pp.savefig(fig3, bbox_inches='tight')

    # Close the PdfPages object
    pp.close()
    print(f"All graphs for"+clustered+ " data have been added.")
    # Show the plots (optional)
    plt.show()

def freight_cost_comparison_plot(df_recal_clustered_freightcost,df_recal_freightcost,df_added_freightcostpath):
    # Function to calculate total cost for each day
    def calculate_total_cost(df):
        df['Freight_Cost'] = pd.to_numeric(df['Freight_Cost'], errors='coerce')  # Convert 'Freight_Cost' to numeric
        return df.groupby('Weekday')['Freight_Cost'].sum()

    df_added_freightcost = pd.read_csv(df_added_freightcostpath,
        encoding="latin_1", sep=";")

    # Calculate total cost for each dataframe
    total_cost_recal_clustered = calculate_total_cost(df_recal_clustered_freightcost)
    total_cost_recal = calculate_total_cost(df_recal_freightcost)
    total_cost_added = calculate_total_cost(df_added_freightcost)

    print("Total Freight Cost Without Profiles: " + str(total_cost_added))
    print("Total Freight Cost With Profiles: " + str(total_cost_recal))
    print("Total Freight Cost With Clustered Profiles: " + str(total_cost_recal_clustered))

    # Check if Weekday values are consistent
    assert len(total_cost_recal_clustered) == len(total_cost_recal) == len(
        total_cost_added), "Inconsistent Weekday values"

    # Calculate percentages for each dataframe
    percentage_recal_clustered = (df_recal_clustered_freightcost.groupby('Weekday')[
                                      'Freight_Cost'].sum() / total_cost_recal_clustered.sum()) * 100
    percentage_recal = (df_recal_freightcost.groupby('Weekday')['Freight_Cost'].sum() / total_cost_recal.sum()) * 100
    percentage_added = (df_added_freightcost.groupby('Weekday')['Freight_Cost'].sum() / total_cost_added.sum()) * 100

    # Plotting the bar graph with percentages
    fig, ax = plt.subplots(figsize=(10, 6))

    bar_width = 0.25
    bar_positions = range(len(total_cost_recal_clustered))

    # Plot bars for each dataframe
    ax.bar([pos - bar_width for pos in bar_positions], percentage_recal_clustered, width=bar_width,
           label='Clustered Profiles', color=sns.color_palette("Set2")[0])
    ax.bar(bar_positions, percentage_recal, width=bar_width, label='Profiles Only', color=sns.color_palette("Set2")[2])
    ax.bar([pos + bar_width for pos in bar_positions], percentage_added, width=bar_width, label='Without Profiles',
           color=sns.color_palette("Set2")[3])
    # Add percentages on each bar for each dataframe with reduced text size
    for pos, percentage in zip(bar_positions, percentage_recal_clustered):
        ax.text(pos - bar_width, total_cost_recal_clustered[pos] + 2, f'{percentage:.2f}%', ha='center', va='bottom',
                color='black', fontsize=8)

    for pos, percentage in zip(bar_positions, percentage_recal):
        ax.text(pos, total_cost_recal[pos] + 2, f'{percentage:.2f}%', ha='center', va='bottom', color='black',
                fontsize=8)

    for pos, percentage in zip(bar_positions, percentage_added):
        ax.text(pos + bar_width, total_cost_added[pos] + 2, f'{percentage:.2f}%', ha='center', va='bottom',
                color='black', fontsize=8)

    ax.set_xticks(bar_positions)
    ax.set_xticklabels(['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'])

    ax.set_xlabel('Weekday')
    ax.set_ylabel('Total Freight Cost')
    ax.set_title('Freight Cost Comparison by Weekday')

    ax.legend()
    plt.show()