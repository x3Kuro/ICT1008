import os
from flask import Flask, redirect, url_for, render_template
import osmnx as ox
from collections import defaultdict
from heapq import *
import random
import pandas

# Define map properties
lon, lat = 103.9024, 1.4052
zoom = 8

app = Flask(__name__)


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
df = pandas.read_csv('edges.csv')
col = df[['u', 'v', 'length', 'oneway']]
edges = [tuple(x) for x in col.values]

# Edit 2nd and 3rd variable for the start and end node
temp = dijkstra(edges, 5177288947, 3048521675, 0)  # Shortest Route (Shortest distance taken)

# Use the follow variables for plotting of map
distance = temp[0]
path = temp[1]  # Only this is needed for plotting on map
numOfNodes = temp[2]

'''END OF DIJK.PY'''

G = ox.graph_from_point((lat, lon), distance=5000, network_type='walk')
# # ox.footprints_from_point(point, distance, footprint_type='building', retain_invalid=False)
gdf_nodes, gdf_edges = ox.graph_to_gdfs(G)
# gdf_nodes.to_csv('nodes.csv')
# gdf_edges.to_csv('edges.csv')
# print("Nodes:\n", gdf_nodes.head(), '\n')
# print("Edges:\n", gdf_edges.head(), '\n')
# folium_map = ox.plot_graph_folium(G, zoom=zoom, tiles="OpenStreetMap")
# folium_map = folium.Map(location=[lat, lon], zoom_start=zoom, control_scale=True)
folium_walk_map = ox.plot_route_folium(G, list(path), route_width=3, route_color="skyblue")
folium_walk_map.save('templates/walk.html')


# Redirect users to home page if they try to go to root folder.
@app.route('/')
def index():
    return redirect(url_for('home'))


# Render index.html when users go to /home
@app.route('/home')
def home():
    return render_template('index.html')


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
