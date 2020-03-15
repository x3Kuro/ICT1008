import sys
import json
import pprint

start = sys.argv[1]
end = sys.argv[2]
current_time = int(sys.argv[3])
cost_per_stop = float(sys.argv[4])
cost_per_transfer = float(sys.argv[5])
print("loading JSON")

stops = json.loads(open("stops.json").read())
services = json.loads(open("services.json").read())
routes = json.loads(open("routes.json").read())

print("Initializing  tables")
stop_desc_map = {stop["Description"]: stop for stop in stops}
stop_code_map = {stop["BusStopCode"]: stop for stop in stops}

routes_map = {} 

for route in routes:
    key = (route["ServiceNo"], route["Direction"])
    if key not in routes_map:
        routes_map[key] = []
    # hack around broken data
    if (route["StopSequence"] == 4
            and route["Distance"] == 9.1
            and key == ("34", 1)):
        route["StopSequence"] = 14
    routes_map[key] += [route]

print("Initializing Graph")
graph = {}
for service, path in routes_map.items(): #key,value in dict
    # hack around broken data
    path.sort(key = lambda r: r["StopSequence"])
    for route_index in range(len(path) - 1):
        key = path[route_index]["BusStopCode"]
        if key not in graph:
            graph[key] = {}
        curr_route_stop = path[route_index]
        next_route_stop = path[route_index + 1]
        curr_distance = curr_route_stop["Distance"] or 0
        next_distance = next_route_stop["Distance"] or curr_distance
        distance = next_distance - curr_distance
        assert distance >= 0, (curr_route_stop, next_route_stop)
        curr_code = curr_route_stop["BusStopCode"]
        next_code = next_route_stop["BusStopCode"]
        graph[curr_code][(next_code, service)] = distance

print("Running BFS")

def dijkstras(graph, start, end):
    import heapq
    seen = set()
    # maintain a queue of paths
    queue = []
    # push the first path into the queue
    heapq.heappush(queue, (0, 0, 0, [(start, None)]))
    while queue:
        # get the first path from the queue
        (curr_cost, curr_distance, curr_transfers, path) = heapq.heappop(queue)

        # get the last node from the path
        (node, curr_service) = path[-1]

        # path found
        if node == end:
            return (curr_cost, curr_distance, curr_transfers, path)

        if (node, curr_service) in seen:
            continue

        seen.add((node, curr_service))
        # enumerate all adjacent nodes, construct a new path and push it into the queue
        for (adjacent, service), distance in graph.get(node, {}).items():
            new_path = list(path)
            new_path.append((adjacent, service))
            new_distance = curr_distance + distance
            new_cost = distance + curr_cost
            new_transfers = curr_transfers
            if curr_service != service:
                new_cost += cost_per_transfer
                new_transfers += 1
            new_cost += cost_per_stop

            heapq.heappush(queue, (new_cost, new_distance, new_transfers, new_path))

(cost, distance, transfers, path) = dijkstras(graph, stop_desc_map[start]["BusStopCode"], stop_desc_map[end]["BusStopCode"])

for code, service in path:
    print(service, stop_code_map[code]["BusStopCode"],stop_code_map[code]["RoadName"],stop_code_map[code]["Latitude"], stop_code_map[code]["Longitude"])
print(len(path), "stops")
print("cost", cost)
print("distance", distance, "km")
print("transfers", transfers)