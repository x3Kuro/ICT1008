import json
import heapq
import pandas as pd
import osmnx as ox
from osmnx import settings
import networkx as nx
from math import sin, cos, sqrt, atan2, radians, acos

def get_nearestedge_node(temp_y, temp_x, G):
    """
    Find the nearest node available in Open street map

    Parameters
    ----------
    osm_id : node ID
    a : plotting graph
    g : bus graph

    Returns
    -------
    temp_nearest_edge[1]/temp_nearest_edge[2] : nearest node to a way ID
    """
    temp_nearest_edge = ox.get_nearest_edge(G, (temp_y, temp_x))
    temp_1 = temp_nearest_edge[0].coords[0]
    temp_2 = temp_nearest_edge[0].coords[1]
    temp1_x = temp_1[0]
    temp1_y = temp_1[1]
    temp_1_distance = calculate_H(temp1_y, temp1_x, temp_y, temp_x)

    temp2_x = temp_2[0]
    temp2_y = temp_2[1]
    temp_2_distance = calculate_H(temp2_y, temp2_x, temp_y, temp_x)
    if temp_1_distance < temp_2_distance:
        return temp_nearest_edge[1]
    else:
        return temp_nearest_edge[2]


def calculate_H(s_lat, s_lon, e_lat, e_lon):
    """
    Calculate a distance with x,y coordinates with

    Parameters
    ----------
    s_lat : float (starting lat)
    s_lon : float (starting lon)
    e_lat : float (ending lat)
    e_lon : float (ending lon)

    Returns
    -------
    distance
    """
    snlat = radians(s_lat)
    snlon = radians(s_lon)
    elat = radians(e_lat)
    elon = radians(e_lon)
    actual_dist = 6371.01 * acos(sin(snlat) * sin(elat) + cos(snlat) * cos(elat) * cos(snlon - elon))
    actual_dist = actual_dist * 1000
    return actual_dist


"""
Create coordinates from nodes and return an array of coordinates
"""
def node_list_to_coordinate_lines(G, node_list, use_geom=True):
    edge_nodes = list(zip(node_list[:-1], node_list[1:]))
    lines = []
    for u, v in edge_nodes:
        # if there are parallel edges, select the shortest in length
        data = min(G.get_edge_data(u, v).values(), key=lambda x: x['length'])

        # if it has a geometry attribute (ie, a list of line segments)
        if 'geometry' in data and use_geom:
            # add them to the list of lines to plot
            xs, ys = data['geometry'].xy
            lines.append(list(zip(xs, ys)))
        else:
            # if it doesn't have a geometry attribute, the edge is a straight
            # line from node to node
            x1 = G.nodes[u]['x']
            y1 = G.nodes[u]['y']
            x2 = G.nodes[v]['x']
            y2 = G.nodes[v]['y']
            line = [(y1, x1), (y2, x2)]
            lines.append(line)
    return lines

"""
Dijkstra algorithm to find the shortest path and taking into account least transfer
"""
def dijkstras(graph, start, end, cost_per_trans):

    seen = set()
    # maintain a queue of paths
    queue = []
    # push the first path into the queue
    heapq.heappush(queue, (0, 0, 0, [(start, None)]))
    
    while queue:
        # print(queue)
        # get the first path from the queue
        (curr_cost, curr_dist, curr_trans, path) = heapq.heappop(queue)

        # get the last node from the path
        (node, curr_service) = path[-1]

        # path found
        if node == end:
            return (curr_dist, curr_trans, path)

        if (node, curr_service) in seen:
            continue

        seen.add((node, curr_service))

        # enumerate all adjacent nodes, construct a new path and push it into the queue
        for (adjacent, service), distance in graph.get(node, {}).items():
            new_path = list(path)
            new_path.append((adjacent, service))
            new_dist = curr_dist + distance
            new_cost = distance + curr_cost
            new_trans = curr_trans
            if curr_service != service:
                new_cost += cost_per_trans
                new_trans += 1
            heapq.heappush(queue, (new_cost, new_dist, new_trans, new_path))

"""
Main function to run the bus routing algorithm
"""
def bus_route(startOsmid, endOsmid, cost_per_trans):
    
    dijkstra_result=[]
    bus_route_name_service=[]
    plotting_routes = []
    lineStrings = []
    plotting_nodes = []
    route_coordinates = []
    routes_map = {}
    graph = {}

    """
    Preparing the relevent data sets to be used
    """
    stops = json.loads(open("data/stops.json").read())
    routes = json.loads(open("data/routes.json").read())
    df = pd.read_csv("data/bus_stop.csv")
    stop_code_map = {stop["BusStopCode"]: stop for stop in stops}

    """
    Converting the osmid into bus stops code to run in the dijkstra algorithm
    """
    for idx,x in enumerate(df["osmid"]):    
        if str(startOsmid)==str(x):
            startBusStops=df["asset_ref"][idx]
        if str(endOsmid)==str(x):
            endBusStops=df["asset_ref"][idx]

    """
    Creates the graph needed to run djikstra on
    """
    for route in routes:
        key = (route["ServiceNo"], route["Direction"])
        if key not in routes_map:
            routes_map[key] = []
        routes_map[key] += [route]

    for service, path in routes_map.items():
        path.sort(key=lambda r: r["StopSequence"])
        for route_idx in range(len(path) - 1):
            key = path[route_idx]["BusStopCode"]
            if key not in graph:
                graph[key] = {}
            curr_route_stop = path[route_idx]
            next_route_stop = path[route_idx + 1]
            curr_dist = curr_route_stop["Distance"] or 0
            next_dist = next_route_stop["Distance"] or curr_dist
            dist = next_dist - curr_dist
            assert dist >= 0, (curr_route_stop, next_route_stop)
            curr_code = curr_route_stop["BusStopCode"]
            next_code = next_route_stop["BusStopCode"]
            graph[curr_code][(next_code, service)] = dist

    """
    Calling the dijkstra function and storing the result
    """
    (distance, transfers, path) = dijkstras(graph, startBusStops, endBusStops, cost_per_trans)
    dijkstra_result.append([len(path), distance, transfers])

    """
    Generating the path output and storing the the x and y coordinates in an array
    """
    for code, service in path:
        if service != None:
            bus_service, b = service
            route_coordinates.append([stop_code_map[code]["Latitude"], stop_code_map[code]["Longitude"]])
            bus_route_name_service.append([bus_service, stop_code_map[code]["Description"],stop_code_map[code]["BusStopCode"],stop_code_map[code]["Latitude"], stop_code_map[code]["Longitude"]])
            print(service, stop_code_map[code]["BusStopCode"],stop_code_map[code]["RoadName"],stop_code_map[code]["Latitude"], stop_code_map[code]["Longitude"])

    """
    Fixing inaccurate coordinates from datamall data set
    """
    for y in bus_route_name_service:    
        for idx,x in enumerate(df["asset_ref"]):    
            if str(y[2])==str(x):
                y[3]=df["y"][idx]
                y[4]=df["x"][idx]
 
    """
    Creating the graph using osmnx
    """
    a = ox.graph_from_point((1.3984, 103.9072), distance=3000, network_type='drive')
    
    """
    Generating the nodes nearest to bus stop coordinates
    """
    for i in route_coordinates:
        plotting_nodes.append(get_nearestedge_node(i[0], i[1], a))

    """
    Generating the path to plot on the map
    """
    for x in range(0, len(plotting_nodes) - 1):
        plotting_routes = nx.shortest_path(a, plotting_nodes[x], plotting_nodes[x + 1])

    """
    Converting the nodes into coordinates to plot on the GUI map
    """
    lineStrings = node_list_to_coordinate_lines(a, plotting_routes)

    return lineStrings, dijkstra_result, bus_route_name_service

# a,b,c=bus_route("65009","65469",4) 
# a,b,c=bus_route(1847853709, 3905803183, 0) # StartOsmid , stoposmid and transfer cost
a,b,c=bus_route(7276194081,410472396, 0)
print(a) #Line string
print(b) #[len(path), distance, transfers]
print(c) #bus path