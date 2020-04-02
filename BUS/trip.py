import sys
import json
import heapq
import pandas as pd
import numpy as np
import osmnx as ox
from osmnx import settings 
import networkx as nx
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
from math import sin, cos, sqrt, atan2, radians, acos

def create_graph(response_jsons, name='unnamed', retain_all=False, bidirectional=False):
# create the graph as a MultiDiGraph and set the original CRS to default_crs
    G = nx.MultiDiGraph(name=name, crs=settings.default_crs)

    # extract nodes and paths from the downloaded osm data
    nodes = {}
    paths = {}
    nodes_temp, paths_temp = ox.parse_osm_nodes_paths(response_jsons)
    for key, value in nodes_temp.items():
        nodes[key] = value

    for key, value in paths_temp.items():
        paths[key] = value
        
    # add each osm node to the graph
    for node, data in nodes.items():
    
        G.add_node(node, **data)

    # add each osm way (aka, path) to the graph
    G = ox.add_paths(G, paths, bidirectional=False)

    # if not retain_all:
    #     G = geo_utils.get_largest_component(G)

    if len(G.edges) > 0:
        # asd(G)
        G = ox.add_edge_lengths(G)

    return G

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
            temp_1_distance = calculate_H(temp1_y,temp1_x,temp_y,temp_x)

            temp2_x = temp_2[0]
            temp2_y = temp_2[1]
            temp_2_distance = calculate_H(temp2_y,temp2_x,temp_y,temp_x)
            if temp_1_distance < temp_2_distance:
                return temp_nearest_edge[1]
            else:
                return temp_nearest_edge[2]

def calculate_H(s_lat,s_lon,e_lat,e_lon):
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
            R = 6371.0
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

start = sys.argv[1]
end = sys.argv[2]
current_time = int(sys.argv[3])
cost_per_stop = float(sys.argv[4])
cost_per_trans = float(sys.argv[5])

stops = json.loads(open("new_stops.json").read())
services = json.loads(open("new_services.json").read())
routes = json.loads(open("new_routes.json").read())

with open("export.json",encoding="utf-8") as a:
        ways = json.load(a)

# with open("bus_edges.json",encoding="utf-8") as a:
#         bus_edges = json.load(a)

# df = pd.read_csv("bus_stop.csv")
plotting_G = ox.load_graphml('Bus_Overpass.graphml')

G = create_graph(ways)

stop_code_map = {stop["BusStopCode"]: stop for stop in stops}

routes_map = {} 

for route in routes:
    key = (route["ServiceNo"], route["Direction"])
    if key not in routes_map:
        routes_map[key] = []
    routes_map[key] += [route]

graph = {}

"""
Creates the graph needed to run djikstra on
"""
for service, path in routes_map.items():
    path.sort(key = lambda r: r["StopSequence"])
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
Dijkstra algorithm to find the shortest path and taking into account least transfer
"""
def dijkstras(graph, start, end):

    seen = set()
    # maintain a queue of paths
    queue = []
    # push the first path into the queue
    heapq.heappush(queue, (0, 0, 0, [(start, None)]))
    while queue:
        # get the first path from the queue
        (curr_cost, curr_dist, curr_trans, path) = heapq.heappop(queue)

        # get the last node from the path
        (node, curr_service) = path[-1]

        # path found
        if node == end:
            return (curr_cost, curr_dist, curr_trans, path)

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
            new_cost += cost_per_stop

            heapq.heappush(queue, (new_cost, new_dist, new_trans, new_path))

(cost, distance, transfers, path) = dijkstras(graph, start, end)

route_coordinates=[]

"""
Generating the output and storing the the x and y coordinates in an array
"""
for code, service in path:
    if service != None:
        bus_service , b = service
        # test.append([bus_service, stop_code_map[code]["BusStopCode"],stop_code_map[code]["Latitude"], stop_code_map[code]["Longitude"]])
        route_coordinates.append([stop_code_map[code]["Latitude"], stop_code_map[code]["Longitude"]])
        print(service, stop_code_map[code]["BusStopCode"],stop_code_map[code]["RoadName"],stop_code_map[code]["Latitude"], stop_code_map[code]["Longitude"])

print(len(path), "stops")
print("cost", cost)
print("distance", distance, "km")
print("transfers", transfers)

# for bus_svc,bus_stop, lat, lng in (test):
#     for idx,y in enumerate(df["asset_ref"]):
#         if(df["asset_ref"][idx]!="None"):
#             if(int(df["asset_ref"][idx]) == int(bus_stop)):
#                 new_coordinates.append([lat,lng])
#                 coord.update({"bus_route_"+str(count):{"bus_svc":bus_svc,"y":lat, "x":lng}})
#                 count+=1


# def nearest_node(bus_stop_graph, endpoint_arr):
#         bus_stop_result = []
#         for x in endpoint_arr:
#             print(x[0])
#             print(x[1])
#             bus_stop_graph['reference_y'] = x[1]
#             bus_stop_graph['reference_x'] = x[0]
#             distances = euclidean_dist_vec(y1=bus_stop_graph['reference_y'],
#                                         x1=bus_stop_graph['reference_x'],
#                                         y2=bus_stop_graph['y'],
#                                         x2=bus_stop_graph['x'])
#             nearest_node_a = distances.idxmin()
#             bus_stop_result.append(bus_stop_graph["osmid"][nearest_node_a])
#         return bus_stop_result

print(route_coordinates)

a = ox.graph_from_point((1.3984,103.9072), distance =3000, network_type='drive')
plotting_nodes = []
for i in route_coordinates:
    plotting_nodes.append(get_nearestedge_node(i[0], i[1], a))

plotting_routes = []
lineStrings=[]
for x in range (0, len(plotting_nodes)-1):
    plotting_routes=nx.shortest_path(a, plotting_nodes[x], plotting_nodes[x+1])
print("plotting_routes",plotting_routes)

# for x in plotting_routes:
lineStrings=node_list_to_coordinate_lines(a,plotting_routes)
print("cooordinates",lineStrings)
# ox.plot_graph_routes(a, plotting_routes)
# print("plotting_nodes", plotting_nodes)