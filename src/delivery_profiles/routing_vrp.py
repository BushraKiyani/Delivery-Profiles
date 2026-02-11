from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp
import pandas as pd
import numpy as np
import json

def create_data_model(filtered_distance_matrix):
    """Stores the data for the problem."""
    data = {}
    data["duration_matrix"] = filtered_distance_matrix
    data["num_vehicles"] = 5
    data["depot"] = 0
    return data

def print_solution1(data, manager, routing, solution, recipient_ids):
    """Prints solution on console."""
    print(f"Objective: {round(solution.ObjectiveValue(), 2)}")
    max_route_duration = 0
    for vehicle_id in range(data["num_vehicles"]):
        index = routing.Start(vehicle_id)
        plan_output = f"Route for vehicle {vehicle_id}:\n"
        route_duration = 0
        while not routing.IsEnd(index):
            node = manager.IndexToNode(index)
            if node == 0:
                plan_output += " Depot -> "
            else:
                plan_output += f" {node} (Recipient ID: {recipient_ids[node]}) -> "
            previous_index = index
            index = solution.Value(routing.NextVar(index))
            route_duration += routing.GetArcCostForVehicle(
                previous_index, index, vehicle_id
            )
        if manager.IndexToNode(index) == 0:
            plan_output += "Depot\n"
        else:
            plan_output += f"{manager.IndexToNode(index)} (Recipient ID: {recipient_ids[manager.IndexToNode(index)]})\n"
        plan_output += f"duration of the route: {round(route_duration/60, 2)}min\n"
        print(plan_output)
        max_route_duration = max(route_duration, max_route_duration)
    print(f"Maximum of the route durations: {round(max_route_duration/60, 2)}min")

def save_solution_to_json(data, manager, routing, solution, recipient_ids, filename, weekday):
    """Saves solution to a JSON file."""
    output = {"Objective": round(solution.ObjectiveValue(), 2), "Routes": [], "Weekday": weekday}
    max_route_duration = 0
    for vehicle_id in range(data["num_vehicles"]):
        index = routing.Start(vehicle_id)
        route = {"vehicle_id": vehicle_id, "route": [], "duration": 0}
        route_duration = 0
        while not routing.IsEnd(index):
            node = manager.IndexToNode(index)
            if node != 0:  # Exclude depot
                route["route"].append({"node": node, "Recipient_ID": recipient_ids[node]})
            previous_index = index
            index = solution.Value(routing.NextVar(index))
            route_duration += routing.GetArcCostForVehicle(previous_index, index, vehicle_id)
        route["duration"] = round(route_duration/60, 2)
        output["Routes"].append(route)
        max_route_duration = max(route_duration, max_route_duration)
    output["Max_route_duration"] = round(max_route_duration/60, 2)

    # Load existing data
    try:
        with open(filename, 'r') as f:
            existing_data = json.load(f)
    except FileNotFoundError:
        existing_data = []

    # Append new data
    existing_data.append(output)

    # Write back to file
    with open(filename, 'w') as f:
        json.dump(existing_data, f, indent=4)

def route(df_added_freightcost, df_assigned_profile, duration_matrix_path, output_json_path ):
    duration_df = pd.read_csv(duration_matrix_path, encoding="latin_1", sep=",", index_col=0)
    # Convert column indices of duration_df to int64
    duration_df.columns = duration_df.columns.astype('int64')
    df_added_freightcost['Recipient_ID'] = df_added_freightcost['Recipient_ID'].astype('int64')
    # First, drop duplicates and set the Recipient_id as the index for df_added_freightcost
    df_added_freightcost = df_added_freightcost.drop_duplicates(subset='Recipient_ID')
    df_added_freightcost.set_index('Recipient_ID', inplace=True)

    # Now, add the Duration column to the 0th row and 0th column of duration_df
    # Ensure that the indices match by reindexing df_added_freightcost['Duration'] to duration_df's index and columns
    duration_df.loc[0, :] = df_added_freightcost['Duration'].reindex(duration_df.columns)
    duration_df.loc[:, 0] = df_added_freightcost['Duration'].reindex(duration_df.index)

    # Reset the index for df_added_freightcost if needed
    df_added_freightcost.reset_index(inplace=True)
    duration_df.fillna(0.0, inplace=True)
    # Move the last row to the first
    duration_df = pd.concat([duration_df.iloc[-1:], duration_df.iloc[:-1]])
    # Move the last column to the first
    duration_df = pd.concat([duration_df.iloc[:, -1:], duration_df.iloc[:, :-1]], axis=1)


    # Define a mapping from numerical weekday values to weekday names
    weekday_mapping = {0: 'Monday', 1: 'Tuesday', 2: 'Wednesday', 3: 'Thursday', 4: 'Friday'}

    # Assuming df_assigned_profile has a 'Weekday' column indicating the day of the week
    unique_weekdays = df_assigned_profile['Weekday'].unique()

    for weekday in unique_weekdays:
        # Filter the data for the current weekday
        filtered_data = df_assigned_profile[df_assigned_profile['Weekday'] == weekday]

        # Get the unique IDs for the current weekday
        unique_ids = np.append([0], filtered_data['Recipient_ID'].unique())
        selected_ids = unique_ids.tolist()

        # Filter the distance matrix based on selected IDs
        filtered_distance_matrix = duration_df.loc[selected_ids, selected_ids]

        # Convert DataFrame to a list of lists (duration matrix)
        filtered_distance_matrix = [[float(value) for value in row] for row in filtered_distance_matrix.values.tolist()]

        # Create the data model for the current weekday
        data = create_data_model(filtered_distance_matrix)

        # Create the routing index manager for the current weekday
        manager = pywrapcp.RoutingIndexManager(len(data["duration_matrix"]), data["num_vehicles"], data["depot"])

        # Create the Routing Model for the current weekday
        routing = pywrapcp.RoutingModel(manager)

        # Create and register a transit callback.
        def distance_callback(from_index, to_index):
            """Returns the distance between the two nodes."""
            # Convert from routing variable Index to distance matrix NodeIndex.
            from_node = manager.IndexToNode(from_index)
            to_node = manager.IndexToNode(to_index)
            return int(data["duration_matrix"][from_node][to_node])

        # ... (Remaining code for creating and solving the routing model)
        transit_callback_index = routing.RegisterTransitCallback(distance_callback)
        # Define cost of each arc.
        routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)
        # Add Distance constraint.
        dimension_name = "Duration"
        routing.AddDimension(
            transit_callback_index,
            0,  # no slack
            28800,  # vehicle maximum travel duration 8 hours = 28,800 seconds
            True,  # start cumul to zero
            dimension_name, )
        distance_dimension = routing.GetDimensionOrDie(dimension_name)
        # distance_dimension.SetGlobalSpanCostCoefficient(100)

        search_parameters = pywrapcp.DefaultRoutingSearchParameters()
        search_parameters.first_solution_strategy = (
            routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC)
        # Solve the problem for the current weekday
        solution = routing.SolveWithParameters(search_parameters)

        # Print solution on console for the current weekday
        if solution:
            weekday_name = weekday_mapping.get(weekday, 'Unknown')
            print(f"Solution for {weekday_name}:")
            print_solution1(data, manager, routing, solution, selected_ids)
        else:
            weekday_name = weekday_mapping.get(weekday, 'Unknown')
            print(f"No solution found for {weekday_name}!")
        save_solution_to_json(data, manager, routing, solution, selected_ids, output_json_path, weekday_mapping[weekday])
