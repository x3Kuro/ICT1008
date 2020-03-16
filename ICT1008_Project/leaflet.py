import os
from flask import Flask, redirect, url_for, render_template, request, jsonify
import osmnx as ox
from collections import defaultdict
from heapq import *
import random
import pandas
from geopy import Nominatim
import geopandas as gpd


# Define map properties
lon, lat = 103.9024, 1.4052
zoom = 13
# Polygon of Punggol
punggol = gpd.read_file('data/polygon-punggol.geojson')
polygon = punggol['geometry'].iloc[0]

app = Flask(__name__)
app.config['TEMPLATES_AUTO_RELOAD'] = True


''' Swap order in list'''
def swapOrder(coords_list, polyline):
    for x in coords_list:
        for j in x:
            coords = list(j)
            coords[0], coords[1] = coords[1], coords[0]
            polyline.append(list(coords))


''' DIJK.PY '''
def dijkstra(edges, start, end, choice):
    # Initalise a dictionary to store edges/node
    graph = defaultdict(list)
    # Storing Nodes with similar start/end nodes together in a dictionary
    for startNode, endNode, weight, oneWay in edges:
        # This line sets the connection between the edges to the nodes (e.g. (A->B))
        graph[startNode].append((weight, endNode, random.randrange(2, 6)))
        # if oneWay == "False":

        # {'Punggol': [(10, 'Damai', 4), (9.5, 'Cove', 3), (9, 'Sam Kee', 5), (7.5, 'Soo Teck', 3)], ....}

        # This line allows bidirection search between nodes (e.g. (B->A))
        # graph[endNode].append((weight, startNode, random.randrange(2,6)))

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
                return (weight, path, "Total number of stops: " + str(len(path)))

            for w, v2, t in graph.get(v1, ()):

                # add in a transfer huristic to each node if least transfer is the option
                if choice == 1:
                    w += 300

                # add in a time huristic to each node if fastest path is the option
                if choice == 2:
                    w += t

                if v2 in seen:
                    continue

                # Not every edge will be calculated. The edge which can improve the value of node in heap will be useful.
                if v2 not in dist or weight + w < dist[v2]:
                    dist[v2] = weight + w
                    # push the element into the piority queue
                    heappush(q, (weight + w, v2, path))

    return float("inf")


# === Dijkstra === Algorithm
train_df = pandas.read_csv('data/train_edges.csv')
col = train_df[['u', 'v', 'length', 'oneway']]
train_edges = [tuple(x) for x in col.values]

walk_df = pandas.read_csv('data/walk_edges.csv')
col = walk_df[['u', 'v', 'length', 'oneway']]
walk_edges = [tuple(x) for x in col.values]

'''END OF DIJK.PY'''

G_walk = ox.graph_from_polygon(polygon, retain_all=True, truncate_by_edge=True, network_type='walk')
G_train = ox.graph_from_polygon(polygon, retain_all=True, truncate_by_edge=True, simplify=False, network_type='none',
                                infrastructure='way["railway"]')
# ox.footprints_from_point(point, distance, footprint_type='building', retain_invalid=False)
# gdf_nodes, gdf_edges = ox.graph_to_gdfs(G_train)
# gdf_nodes.to_csv('data/train_nodes.csv')
# gdf_edges.to_csv('data/train_edges.csv')
# print("Nodes:\n", gdf_nodes.head(), '\n')
# print("Edges:\n", gdf_edges.head(), '\n')
# folium_map = ox.plot_graph_folium(G, zoom=zoom, tiles="OpenStreetMap")


# Redirect users to home page if they try to go to root folder.
@app.route('/')
def index():
    return redirect(url_for('home'))


# Render index.html when users go to /home
@app.route('/home')
def home():
    walk_path = []
    src = []
    return render_template('leaflet.html', start=src, path=walk_path)


@app.route('/data', methods=['POST', 'GET'])
def get_path_data():
    polyline = []
    input_src = request.args.get('source', 0, type=str)
    input_dest = request.args.get('dest', 0, type=str)

    # ============== GEOCODE ============== #
    locator = Nominatim(user_agent="myGeocoder")
    src = locator.geocode(input_src)
    dest = locator.geocode(input_dest)
    # ===================================== #

    start_walk = ox.get_nearest_node(G_walk, (src.latitude, src.longitude))
    end_walk = ox.get_nearest_node(G_walk, (dest.latitude, dest.longitude))
    start_train = ox.get_nearest_node(G_train, (src.latitude, src.longitude), return_dist=True)
    end_train = ox.get_nearest_node(G_train, (dest.latitude, dest.longitude), return_dist=True)

    # =========================================== TRAIN =========================================== #
    # Check that the nearest train station for both locations is not the same
    if start_train[0] != end_train[0]:
        train_polyline = []
        walk1_polyline = []
        walk2_polyline = []
        # Edit 2nd and 3rd variable for the start and end node
        temp = dijkstra(train_edges, start_train[0], end_train[0], 0)
        # Use the follow variables for plotting of map
        train_path = temp[1]
        train_coords = ox.node_list_to_coordinate_lines(G_train, train_path)
        swapOrder(train_coords, train_polyline)

        if start_train[1] > 10:
            to_mrt = ox.get_nearest_node(G_walk, (G_train.nodes[start_train[0]]['y'], G_train.nodes[start_train[0]]['x']))
            temp2 = dijkstra(walk_edges, start_walk, to_mrt, 0)
            walk1_path = temp2[1]
            walk1_coords = ox.node_list_to_coordinate_lines(G_walk, walk1_path)
            swapOrder(walk1_coords, walk1_polyline)
            polyline.append(walk1_polyline)

        if end_train[1] > 10:
            from_mrt = ox.get_nearest_node(G_walk, (G_train.nodes[end_train[0]]['y'], G_train.nodes[end_train[0]]['x']))
            temp3 = dijkstra(walk_edges, from_mrt, end_walk, 0)
            walk2_path = temp3[1]
            walk2_coords = ox.node_list_to_coordinate_lines(G_walk, walk2_path)
            swapOrder(walk2_coords, walk2_polyline)
            polyline.append(walk2_polyline)

        polyline.append(train_polyline)
    # ============================================================================================= #
    # ====================================== PURELY WALKING ====================================== #
    else:
        temp1 = dijkstra(walk_edges, start_walk, end_walk, 0)
        walk_path = temp1[1]
        walk_coords = ox.node_list_to_coordinate_lines(G_walk, walk_path)
        walk_polyline = []
        swapOrder(walk_coords, walk_polyline)
        polyline.append(walk_polyline)
    # ============================================================================================= #

    start = [src.latitude, src.longitude]
    if src == dest:
        polyline = start
    return jsonify(start=start, start_road=input_src, path=polyline)


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