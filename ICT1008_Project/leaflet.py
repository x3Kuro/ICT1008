# from bus import *
import os
from flask import Flask, redirect, url_for, render_template, request, jsonify
import osmnx as ox
from collections import defaultdict
from heapq import *
import random
import pandas as pd
from geopy import Nominatim
from geopy.exc import GeocoderTimedOut
import geopandas as gpd
import networkx as nx
import time
from osmnx import settings
from osmnx.utils import log
from osmnx.geo_utils import get_largest_component
from osmnx.downloader import overpass_request
from osmnx.errors import *
from math import sin, cos, sqrt, atan2, radians



# Custom OSM functions to get more OSM data details
def get_node(element):
    """
    Convert an OSM node element into the format for a networkx node.

    Parameters
    ----------
    element : dict
        an OSM node element

    Returns
    -------
    dict
    """
    useful_tags_node = ['ref', 'name', 'railway', 'route_ref']
    node = {}
    node['y'] = element['lat']
    node['x'] = element['lon']
    node['osmid'] = element['id']

    if 'tags' in element:
        for useful_tag in useful_tags_node:
            if useful_tag in element['tags']:
                node[useful_tag] = element['tags'][useful_tag]
    return node


def parse_osm_nodes_paths(osm_data):
    """
    Construct dicts of nodes and paths with key=osmid and value=dict of
    attributes.
    Parameters
    ----------
    osm_data : dict
        JSON response from from the Overpass API
    Returns
    -------
    nodes, paths : tuple
    """

    nodes = {}
    paths = {}
    for element in osm_data['elements']:
        if element['type'] == 'node':
            key = element['id']
            nodes[key] = get_node(element)
        elif element['type'] == 'way':  # osm calls network paths 'ways'
            key = element['id']
            paths[key] = ox.get_path(element)

    return nodes, paths


def create_graph(response_jsons, name='unnamed', retain_all=True, bidirectional=False):
    """
    Create a networkx graph from Overpass API HTTP response objects.

    Parameters
    ----------
    response_jsons : list
        list of dicts of JSON responses from from the Overpass API
    name : string
        the name of the graph
    retain_all : bool
        if True, return the entire graph even if it is not connected
    bidirectional : bool
        if True, create bidirectional edges for one-way streets

    Returns
    -------
    networkx multidigraph
    """

    log('Creating networkx graph from downloaded OSM data...')
    start_time = time.time()

    # make sure we got data back from the server requests
    elements = []
    # for response_json in response_jsons:
    elements.extend(response_jsons['elements'])
    if len(elements) < 1:
        raise EmptyOverpassResponse('There are no data elements in the response JSON objects')

    # create the graph as a MultiDiGraph and set the original CRS to default_crs
    G = nx.MultiDiGraph(name=name, crs=settings.default_crs)

    # extract nodes and paths from the downloaded osm data
    nodes = {}
    paths = {}
    # for osm_data in response_jsons:
    nodes_temp, paths_temp = parse_osm_nodes_paths(response_jsons)
    for key, value in nodes_temp.items():
        nodes[key] = value
    for key, value in paths_temp.items():
        paths[key] = value

    # add each osm node to the graph
    for node, data in nodes.items():
        G.add_node(node, **data)

    # add each osm way (aka, path) to the graph
    G = ox.add_paths(G, paths, bidirectional=bidirectional)

    # retain only the largest connected component, if caller did not
    # set retain_all=True
    if not retain_all:
        G = get_largest_component(G)

    log('Created graph with {:,} nodes and {:,} edges in {:,.2f} seconds'.format(len(list(G.nodes())), len(list(G.edges())), time.time()-start_time))

    # add length (great circle distance between nodes) attribute to each edge to
    # use as weight
    if len(G.edges) > 0:
        G = ox.add_edge_lengths(G)

    return G


# Define map properties
lon, lat = 103.9024, 1.4052
zoom = 13
# Polygon of Punggol
punggol = gpd.read_file('data/polygon-punggol.geojson')
polygon = punggol['geometry'].iloc[0]

app = Flask(__name__)
app.config['TEMPLATES_AUTO_RELOAD'] = True


# Swap order in list
def swapOrder(coords_list, polyline):
    for x in coords_list:
        for j in x:
            coords = list(j)
            coords[0], coords[1] = coords[1], coords[0]
            polyline.append(list(coords))


# Geocode from address to lat lon for plotting
def do_geocode(address):
    locator = Nominatim(user_agent="myGeocoder")
    try:
        return locator.geocode(address)
    except GeocoderTimedOut:
        return do_geocode(address)


# Create walking polyline
def create_polyline(g, start, end):
    new_polyline = []
    path = dijkstra(walk_edges, start, end)[1]
    coords = ox.node_list_to_coordinate_lines(g, path)
    swapOrder(coords, new_polyline)
    return new_polyline


# Get heuristic for findingStation()
def heur(start, end):
    # approximate radius of earth in km
    R = 6373.0

    # Lat and Lon of start and end
    lat1 = radians(start[0])
    lon1 = radians(start[1])
    lat2 = radians(end[0])
    lon2 = radians(end[1])

    dlon = lon2 - lon1
    dlat = lat2 - lat1

    x = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(x), sqrt(1 - x))

    # Distance between current node and end node
    d = R * c * 1000

    return d


# Find nearest station. Returns Heuristic, OSMid, x and y coordinates
def findingStation(startyx):
    heap = []
    for item in mrt_nodes:
        if item[5] == "station" or item[5] == "stop":
            curr = (item[0], item[1])
            h = heur(startyx, curr)
            heappush(heap, (h, item[2], item[0], item[1]))
    return heappop(heap)


# Dijkstra algorithm for walk and MRT
def dijkstra(edges, start, end):
    # Initalize a dictionary to store edges/node
    graph = defaultdict(list)
    # Storing Nodes with similar start/end nodes together in a dictionary
    for startNode, endNode, weight, oneWay in edges:
        # This line sets the connection between the edges to the nodes (e.g. (A->B))
        graph[startNode].append((weight, endNode, random.randrange(2, 6)))

    if start not in graph or end not in graph:
        return "No Path can be found"

    # dist records the min value of each node in heap.
    q, seen, dist = [(0, start, ())], set(), {start: 0}
    while q:

        # Popping the first element in the heap
        (weight, v1, path) = heappop(q)
        if v1 not in seen:
            # continue
            seen.add(v1)
            # Storing the first element popped from the heap into path
            path += (v1,)

            # if v1 reaches destination, returns total weight and path from start to end
            if v1 == end:
                return weight, path, "Total number of stops: " + str(len(path))

            for w, v2, t in graph.get(v1, ()):
                if v2 in seen:
                    continue

                # Not every edge will be calculated. The edge which can improve the value of node in heap will be useful.
                if v2 not in dist or weight + w < dist[v2]:
                    dist[v2] = weight + w
                    # push the element into the piority queue
                    heappush(q, (weight + w, v2, path))
    return None


# =========================================== QUERY DATA =========================================== #
# Walk query data
G_walk = ox.graph_from_polygon(polygon, retain_all=True, truncate_by_edge=True, network_type='walk')

# Train query data from overpass API
train_query_str = '[out:json][timeout:180];(relation["network"="Singapore Rail"]["route"="monorail"]' \
                  '(1.3920,103.8955,1.4191,103.9218); >;);out;'
train_response_json = overpass_request(data={'data': train_query_str}, timeout=180)
train_graph = create_graph(train_response_json, name='unnamed')
G_train = ox.truncate_graph_polygon(train_graph, polygon, truncate_by_edge=True,  retain_all=True)

gdf_nodes, gdf_edges = ox.graph_to_gdfs(G_train)
gdf_nodes.to_csv('data/train_nodes.csv')
gdf_edges.to_csv('data/train_edges.csv')

# ======================================= GET DF DATA TO CSV======================================= #
# Get Walk edge
walk_df = pd.read_csv('data/walk_edges.csv')
col = walk_df[['u', 'v', 'length', 'oneway']]
walk_edges = [tuple(x) for x in col.values]

# Get MRT edges
train_df = pd.read_csv('data/train_edges.csv')
col = train_df[['u', 'v', 'length', 'oneway']]
train_edges = [tuple(x) for x in col.values]

# Get MRT nodes
train_df = pd.read_csv('data/train_nodes.csv')
col = train_df[['y', 'x', 'osmid', 'ref', 'name', 'railway']]
mrt_nodes = [tuple(x) for x in col.values]

# ================================= SPLIT EAST AND WEST LOOP MRT ================================= #
east = []
west = []

for node in mrt_nodes:
    try:
        if "PW" in node[3]:
            west.append(node[2])
        if "PE" in node[3]:
            east.append(node[2])
    except TypeError:
        continue


# =========================================== FLASK =========================================== #
# Redirect users to home page if they try to go to root folder.
@app.route('/')
def index():
    return redirect(url_for('home'))


# Plot base (empty) map when users go into page without query
@app.route('/home')
def home():
    train_path = []
    walk_path = []
    start = []
    end = []
    return render_template('leaflet.html', start=start, end=end, train_path=train_path, walk_path=walk_path)


@app.route('/data', methods=['POST', 'GET'])
def get_path_data():
    # Define polyline lists
    train_polyline = []
    new_polyline = []
    walk_polyline = []
    # Get user input source and destination, mode of transport
    input_src = request.args.get('source', 0, type=str)
    input_dest = request.args.get('dest', 0, type=str)
    transport_mode = request.args.get('transport_mode', type=str)

    # Geocode source and destination to lat lon
    src = do_geocode(input_src)
    dest = do_geocode(input_dest)

    # Set start as list of source lat lon
    start = [src.latitude, src.longitude]
    end = [dest.latitude, dest.longitude]

    # Get nearest nodes for start and end, train and walk
    start_walk = ox.get_nearest_node(G_walk, (src.latitude, src.longitude))
    end_walk = ox.get_nearest_node(G_walk, (dest.latitude, dest.longitude))
    start_train = ox.get_nearest_node(G_train, (src.latitude, src.longitude), return_dist=True)
    end_train = ox.get_nearest_node(G_train, (dest.latitude, dest.longitude), return_dist=True)
    # Find nearest start and end train stations
    start_station_det = findingStation((src.latitude, src.longitude))
    end_station_det = findingStation((dest.latitude, dest.longitude))

    # Check if train in same or different loops
    east_bound = 0
    west_bound = 0
    diff_loop = 0
    for n in mrt_nodes:
        mrt_id = n[2]
        # If start station in east loop
        if mrt_id == start_station_det[1] and start_station_det[1] in east:
            east_bound += 1
        # If start station in west loop
        elif mrt_id == start_station_det[1] and start_station_det[1] in west:
            west_bound += 1
        # If end station in east loop
        elif mrt_id == end_station_det[1] and end_station_det[1] in east:
            east_bound += 1
        # If end station in west loop
        elif mrt_id == end_station_det[1] and end_station_det[1] in west:
            west_bound += 1
        elif west_bound == 2 or east_bound == 2:  # both lrt station in the same lrt loop
            print("same loop")
            break
        elif west_bound == 1 and east_bound == 1:  # both lrt station in different lrt loop
            diff_loop = 1
            break
    # =========================================== ALL =========================================== #
    if transport_mode == "all":
        # Check that the nearest train station for both locations is not the same
        if start_station_det[1] != end_station_det[1]:
            # Check if start and end is Punggol (Still same station) -> only do bus or walk
            if (start_station_det[1] == 6587709456 and end_station_det[1] == 6587709457) or (
                    end_station_det[1] == 6587709456 and start_station_det[1] == 6587709457):
                # ====================================== PURELY WALKING ====================================== #
                walk_polyline.append(create_polyline(G_walk, start_walk, end_walk))

            else:
                # Will return heuristic, OSMid, y, x. E.g. (253.48788074253008, 1840734598, 1.4118877, 103.9003304)
                # Starting node always use start_u, for ending node always use end_v
                start_geom, start_u, start_v = ox.get_nearest_edge(G_train, (start_station_det[2], start_station_det[3]))
                end_geom, end_u, end_v = ox.get_nearest_edge(G_train, (end_station_det[2], end_station_det[3]))
                # =========================================== TRAIN =========================================== #
                if diff_loop == 1:
                    path1 = dijkstra(train_edges, start_u, 6587709457)[1]
                    path2 = dijkstra(train_edges, 6587709457, end_v)[1]
                    train_coords1 = ox.node_list_to_coordinate_lines(G_train, path1)
                    swapOrder(train_coords1, new_polyline)
                    train_coords2 = ox.node_list_to_coordinate_lines(G_train, path2)
                    swapOrder(train_coords2, new_polyline)

                else:
                    path = dijkstra(train_edges, start_u, end_v)[1]
                    train_coords = ox.node_list_to_coordinate_lines(G_train, path)
                    swapOrder(train_coords, new_polyline)

                # =========================================== WALK + MRT =========================================== #
                if start_train[1] > 10:
                    to_mrt = ox.get_nearest_node(G_walk, (start_station_det[2], start_station_det[3]))
                    walk_polyline.append(create_polyline(G_walk, start_walk, to_mrt))

                if end_train[1] > 10:
                    from_mrt = ox.get_nearest_node(G_walk, (end_station_det[2], end_station_det[3]))
                    walk_polyline.append(create_polyline(G_walk, from_mrt, end_walk))

                train_polyline.append(new_polyline)
        else:
            # ====================================== PURELY WALKING ====================================== #
            walk_polyline.append(create_polyline(G_walk, start_walk, end_walk))
    # =========================================== WALK =========================================== #
    elif transport_mode == "walk":
        walk_polyline.append(create_polyline(G_walk, start_walk, end_walk))

    # =========================================== MRT =========================================== #
    elif transport_mode == "mrt":
        # Check that the nearest train station for both locations is not the same
        if start_station_det[1] != end_station_det[1]:
            # Check if start and end is Punggol (Still same station) -> only do bus or walk
            if (start_station_det[1] == 6587709456 and end_station_det[1] == 6587709457) or (
                    end_station_det[1] == 6587709456 and start_station_det[1] == 6587709457):
                # ====================================== PURELY WALKING ====================================== #
                walk_polyline.append(create_polyline(G_walk, start_walk, end_walk))
            else:
                start_geom, start_u, start_v = ox.get_nearest_edge(G_train,
                                                                   (start_station_det[2], start_station_det[3]))
                end_geom, end_u, end_v = ox.get_nearest_edge(G_train, (end_station_det[2], end_station_det[3]))
                # =========================================== TRAIN =========================================== #
                if diff_loop == 1:
                    path1 = dijkstra(train_edges, start_u, 6587709457)[1]
                    path2 = dijkstra(train_edges, 6587709457, end_v)[1]
                    train_coords1 = ox.node_list_to_coordinate_lines(G_train, path1)
                    swapOrder(train_coords1, new_polyline)
                    train_coords2 = ox.node_list_to_coordinate_lines(G_train, path2)
                    swapOrder(train_coords2, new_polyline)

                else:
                    path = dijkstra(train_edges, start_u, end_v)[1]
                    train_coords = ox.node_list_to_coordinate_lines(G_train, path)
                    swapOrder(train_coords, new_polyline)

                # =========================================== WALK + MRT =========================================== #
                if start_train[1] > 10:
                    to_mrt = ox.get_nearest_node(G_walk, (start_station_det[2], start_station_det[3]))
                    walk_polyline.append(create_polyline(G_walk, start_walk, to_mrt))

                if end_train[1] > 10:
                    from_mrt = ox.get_nearest_node(G_walk, (end_station_det[2], end_station_det[3]))
                    walk_polyline.append(create_polyline(G_walk, from_mrt, end_walk))

                train_polyline.append(new_polyline)
        else:
            # ====================================== PURELY WALKING ====================================== #
            walk_polyline.append(create_polyline(G_walk, start_walk, end_walk))

    # Return coordinates, address and polyline for plotting
    return jsonify(start=start, start_road=input_src, end=end, end_road=input_dest,
                   train_path=train_polyline, walk_path=walk_polyline)


@app.context_processor
def override_url_for():
    return dict(url_for=dated_url_for)


# Create variable by date for POST request. Ensures cache is cleared each time
def dated_url_for(endpoint, **values):
    if endpoint == 'static':
        filename = values.get('filename', None)
        if filename:
            file_path = os.path.join(app.root_path, endpoint, filename)
            values['q'] = int(os.stat(file_path).st_mtime)
    return url_for(endpoint, **values)


if __name__ == '__main__':
    app.run(host="127.0.0.1", port=5000, debug=True)