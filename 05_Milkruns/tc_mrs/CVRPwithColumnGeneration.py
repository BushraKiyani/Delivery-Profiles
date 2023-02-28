"""Capacited Vehicles Routing Problem (CVRP)."""

from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp
import numpy as np
import glob
import pandas as pd

cols = []
sequ_array = []

def read_txt(instfile):
    num_per_vehicle_type_array = []
    timecap_per_verhicle_type_array =[]
    loadcap_per_vehicle_type_array =[]
    km_price_per_vehicle_type_array =[]
    min_price_per_vehicle_type_array = []
    charge_price_per_vehicle_type_array =[]
    servicetime_array = []

    intern_cust_ID_array =[]
    extern_cust_ID_array=[]
    x_coord_array=[]
    y_coord_array=[]
    demand_array=[]
    frequency_array =[]
    AF_price_array =[]

    with open(instfile) as openfileobject:
        c = 0
        currId = 0
        for line in openfileobject:
            l = line.split("\t")
            print(l)
            if (c==0):
                instType = int(l[0])
                numVehTypes = int(l[1])
                numOrders = int(l[2])
                numDays = int(l[3])
                c += 1
            elif (c <= numVehTypes): #Fahrzeugtypenliste erstellen
                num_per_vehicle_type_array.append(int(l[1]))
                timecap_per_verhicle_type_array.append(int(l[2]))
                loadcap_per_vehicle_type_array.append(int(l[3]))
                km_price_per_vehicle_type_array.append(float(l[4]))
                min_price_per_vehicle_type_array.append(float(l[5]))
                charge_price_per_vehicle_type_array.append(float(l[6]))
                c += 1
            else:
                intern_cust_ID_array.append(int(l[0]))
                extern_cust_ID_array.append(int(l[1]))
                x_coord_array.append(float(l[4]))
                y_coord_array.append(float(l[5]))
                demand_array.append(float(l[6]))
                servicetime_array.append(float(l[7]))
                frequency_array.append(int(l[8]))
                AF_price_array.append(float(l[13]))
                currId += 1

    return instType,numVehTypes, numOrders,numDays,num_per_vehicle_type_array,timecap_per_verhicle_type_array, loadcap_per_vehicle_type_array, km_price_per_vehicle_type_array, min_price_per_vehicle_type_array ,charge_price_per_vehicle_type_array, intern_cust_ID_array, extern_cust_ID_array,x_coord_array,y_coord_array,demand_array,frequency_array,AF_price_array, servicetime_array

def join_coords(x_coord_array,y_coord_array):
    coords_array = []
    for i in range(len(x_coord_array)):
        coords_array.append([x_coord_array[i],y_coord_array[i]])
    return np.array(coords_array)

def dist_matrix(koordianten):
    matrix =[]
    for k_1 in koordianten:
        matrix_element = []
        for k_2 in koordianten:
            matrix_element.append(round(np.linalg.norm(k_1-k_2)))
        matrix.append(matrix_element)
    #print(matrix)
    return matrix

class Column(object):
    def __init__(self, _id, _sequ, _sos, _dist, _vol):
        self.id = _id
        self.sequ = _sequ
        self.sos = _sos
        self.dist = _dist  # in km!!!!
        self.vol = _vol

def create_data_model(num_per_vehicle_type_array, instType, numOrders, loadcap_per_vehicle_type_array,timecap_per_verhicle_type_array,
                                     x_coord_array, y_coord_array,demand_array,vehicle_type, dima, tima, servicetime_array):
    """Stores the data for the problem."""

    data = {}
    if dima == None or tima == None:
        data["koordianten"] = join_coords(x_coord_array, y_coord_array)
        data['distance_matrix'] = dist_matrix(data["koordianten"])
        data["duration_matrix"] = data['distance_matrix']
    else:
        data['distance_matrix'] = dima
        data["duration_matrix"] = tima
    data["distance_matrix"][0] = list(np.zeros(len(data['distance_matrix'][0]))) #Erste Verbindung kostenlos
    data["duration_matrix"][0] = list(np.zeros(len(data['duration_matrix'][0])))  # Erste Verbindung kostenlos

    #print(data["duration_matrix"])
    print("Maximale Dauer: ",max(max(data["duration_matrix"])))

    data['demands'] = demand_array
    #print(data['demands'])

    data['vehicle_capacities'] = [int(loadcap_per_vehicle_type_array[vehicle_type]) for i in range(int(num_per_vehicle_type_array[vehicle_type]))]
    #print(data['vehicle_capacities'])
    #data["customer_number"] = [int(tour_length) for i in range(int(num_per_vehicle_type_array[vehicle_type]))]
    #print(data["customer_number"])
    data["vehicle_duration_matrix"] = [int(timecap_per_verhicle_type_array[vehicle_type]) for i in range(int(num_per_vehicle_type_array[vehicle_type]))]
    #print(data["vehicle_duration_matrix"])
    data['num_vehicles'] = int(num_per_vehicle_type_array[vehicle_type])
    #print(data['num_vehicles'])
    data['depot'] = 0

    data["servicetime"] = servicetime_array
    return data

def print_solution(data, manager, routing, solution):
    """Prints solution on console."""
    total_distance = 0
    total_load = 0
    for vehicle_id in range(data['num_vehicles']):
        index = routing.Start(vehicle_id)
        plan_output = 'Route for vehicle {}:\n'.format(vehicle_id)
        route_distance = 0
        route_load = 0
        while not routing.IsEnd(index):
            node_index = manager.IndexToNode(index)
            route_load += data['demands'][node_index]

            previous_index = index
            index = solution.Value(routing.NextVar(index))
            route_distance += routing.GetArcCostForVehicle(
                previous_index, index, vehicle_id)
            plan_output += ' {0} Load({1}) {2} -> '.format(node_index, route_load, route_distance)
        plan_output += ' {0} Load({1})\n'.format(manager.IndexToNode(index),
                                                 route_load)
        plan_output += 'Distance of the route: {}m\n'.format(route_distance)
        plan_output += 'Load of the route: {}\n'.format(route_load)
        print(plan_output)
        total_distance += route_distance
        total_load += route_load
    print('Total distance of all routes: {}m'.format(total_distance))
    print('Total load of all routes: {}'.format(total_load))
    return total_distance


def main(data, solvingtime, cols):
    """Solve the CVRP problem."""
    # Instantiate the data problem.

    # Create the routing index manager.
    manager = pywrapcp.RoutingIndexManager(len(data['distance_matrix']),
                                           data['num_vehicles'], data['depot'])

    # Create Routing Model.
    routing = pywrapcp.RoutingModel(manager)

    # Create and register a transit callback.
    def distance_callback(from_index, to_index):
        """Returns the distance between the two nodes."""
        # Convert from routing variable Index to distance matrix NodeIndex.
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        return data['distance_matrix'][from_node][to_node]

    transit_callback_index = routing.RegisterTransitCallback(distance_callback)

    # Define cost of each arc.
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)


    # Add Capacity constraint.
    def demand_callback(from_index):
        """Returns the demand of the node."""
        # Convert from routing variable Index to demands NodeIndex.
        from_node = manager.IndexToNode(from_index)
        return data['demands'][from_node]

    demand_callback_index = routing.RegisterUnaryTransitCallback(
        demand_callback)
    routing.AddDimensionWithVehicleCapacity(
        demand_callback_index,
        0,  # null capacity slack
        data['vehicle_capacities'],  # vehicle maximum capacities
        True,  # start cumul to zero
        'Capacity')

    # Drop Every Customer with bigger demand than Vehicles Capacity
    for index, demand in enumerate(data['demands']):
        if demand > data['vehicle_capacities'][0]:
            routing.AddDisjunction([manager.NodeToIndex(index)], 0)
            routing.solver().Add(routing.ActiveVar(manager.NodeToIndex(index)) == 0)


    # Add Capacity constraint.
    def duration_callback(from_index, to_index):
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        return data["duration_matrix"][from_node][to_node] + data["servicetime"][to_node]

    duration_callback_index = routing.RegisterTransitCallback(
        duration_callback)
    routing.AddDimensionWithVehicleCapacity(
        duration_callback_index,
        0,  # null capacity slack
        data["vehicle_duration_matrix"],  # tour maximum duration
        True,  # start cumul to zero
        'duration')

    class solution_found(object):
        def __init__(self, model):
            self.model = model
            self.routing = routing
            self.manager = manager

        def __call__(self):
            for vehicle_id in range(data['num_vehicles']):
                tour = []
                tour_duration_value = 0
                tour_duration = [0]
                tour_distance_value = 0
                tour_capacity_value = 0

                index = self.routing.Start(vehicle_id) #get first node

                while not self.routing.IsEnd(index): #append node if not end

                    if index == self.routing.Start(vehicle_id): #Überspringen der ersten Verbindung
                        previous_index = index
                        index = self.routing.NextVar(index).Value()  # get next node
                        continue

                    else:
                        node_index = self.manager.IndexToNode(index)

                        tour.append(node_index)

                        previous_index = index
                        index = self.routing.NextVar(index).Value()  # get next node

                        tour_duration_value += (data["duration_matrix"][manager.IndexToNode(previous_index)][manager.IndexToNode(index)]+ data["servicetime"][manager.IndexToNode(previous_index)])
                        tour_distance_value += data["distance_matrix"][manager.IndexToNode(previous_index)][manager.IndexToNode(index)]
                        tour_capacity_value += data['demands'][manager.IndexToNode(previous_index)]

                        tour_duration.append(tour_duration_value)

                tour.append(self.manager.IndexToNode(index)) #append last node

                #print(tour)
                #print(tour_duration)
                #print(tour_distance_value)
                #print(tour_capacity_value)

                if not sequ_array and cols:
                    for col in cols:
                        sequ_array.append(col.sequ)

                if tour not in sequ_array:
                    sequ_array.append(tour)
                    cols.append(Column(len(cols), tour, tour_duration, tour_distance_value, tour_capacity_value))
                    #print("Zielfunktionswert: ", self.model.CostVar().Min())
                    print(cols[-1].id, " ", cols[-1].sequ, " ", cols[-1].sos, " ", cols[-1].dist, " ", cols[-1].vol)
                else:
                    continue

    solution_callback = solution_found(routing)
    routing.AddAtSolutionCallback(solution_callback)

    # Setting first solution heuristic.
    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = (
        routing_enums_pb2.FirstSolutionStrategy.AUTOMATIC)

    search_parameters.local_search_metaheuristic = (
        routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH)
    search_parameters.time_limit.FromSeconds(solvingtime)

    # Solve the problem.
    solution = routing.SolveWithParameters(search_parameters)

    #print("___First Solution Strategy___")
    #print(routing.GetAutomaticFirstSolutionStrategy())

    # Print solution on console.
    if solution:

        total_costs = print_solution(data, manager, routing, solution)
        return int(routing.solver().WallTime())/1000, total_costs, len(cols)
    else:

        return 0,0,0

def CVRP_Column_gernation(instfile, suchzeit, dima = None, tima = None, cols = []):
    print("Start Heuristic Column generation.")
    print(len(cols))

    solvingtime_input = suchzeit

    for i in solvingtime_input:
            file = instfile
            print(file)
            instType, numVehTypes, numOrders, numDays, num_per_vehicle_type_array, timecap_per_verhicle_type_array, loadcap_per_vehicle_type_array, km_price_per_vehicle_type_array, min_price_per_vehicle_type_array, charge_price_per_vehicle_type_array, intern_cust_ID_array, extern_cust_ID_array, x_coord_array, y_coord_array, demand_array, frequency_array, AF_price_array, servicetime_array = read_txt(
                file)

            for vehicle_type in range(numVehTypes):
                    print("Create Columns for vehicletype {}".format(vehicle_type))
                    print("Volume Capacity: ", loadcap_per_vehicle_type_array[vehicle_type])
                    print("Duration Capacity: ", timecap_per_verhicle_type_array[vehicle_type])
                    print("Vehiclenumber: ", num_per_vehicle_type_array[vehicle_type])
                    print("")

                    data = create_data_model(num_per_vehicle_type_array, instType, numOrders, loadcap_per_vehicle_type_array,timecap_per_verhicle_type_array,
                                                 x_coord_array, y_coord_array,
                                                 demand_array, vehicle_type, dima, tima, servicetime_array)
                    solvingtime, total_costs, counter = main(data=data, solvingtime=i, cols=cols)
                    #try:
                        #solvingtime, total_costs, counter = main( data=data, solvingtime = i, cols = cols)
                    #except:
                        #print("Keine Lösung gefunden.")

            print("")
            print("Columgeneration found {} Columns so far".format(len(cols)))


    print("Columgeneration done, found {} Columns".format(len(cols)))

    return cols


if __name__ == '__main__':
    instfile = r'C:\Users\Thomas\PycharmProjects\Masterarbeit\Resources\Version_2\Milkruns\Instanzen -TK\TK_Instanz0.75-0.75.txt'
    cols = CVRP_Column_gernation(instfile, suchzeit=[30])