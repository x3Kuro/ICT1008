from collections import defaultdict
from heapq import *
from pprint import pprint
import random
import pandas

def dijkstra(edges, start, end, choice):
    #Initalise a dictionary to store edges/node
    graph = defaultdict(list)
    #Storing Nodes with similar start/end nodes together in a dictionary
    for startNode, endNode, weight, oneWay in edges:
        # This line sets the connection between the edges to the nodes (e.g. (A->B))
        graph[startNode].append((weight, endNode,random.randrange(2,6)))
        # if oneWay == "False":
        
            
            # {'Punggol': [(10, 'Damai', 4), (9.5, 'Cove', 3), (9, 'Sam Kee', 5), (7.5, 'Soo Teck', 3)], ....} 
            
            # This line allows bidirection search between nodes (e.g. (B->A))
            # graph[endNode].append((weight, startNode, random.randrange(2,6)))

    if start not in graph or end not in graph:
        return "No Path can be found"

    # dist records the min value of each node in heap.  
    q, seen, dist = [(0, start, ())], set(), {start: 0}
    while q:
        
        #Popping the first element in the heap
        (weight, v1, path) = heappop(q)
        if v1 not in seen:
            # continue
            seen.add(v1)
            #Storing the first element popped from the heap into path
            path += (v1,)
                
            #if v1 reaches destination, returns total weight and path from start to end
            if v1 == end:
                return (weight, path, "Total number of stops: " + str(len(path))) 
                
            for w, v2,t in graph.get(v1, ()):
                
                #add in a transfer huristic to each node if least transfer is the option
                if choice == 1:
                    w+=300

                #add in a time huristic to each node if fastest path is the option
                if choice ==2:
                    w+=t

                if v2 in seen:
                    continue

                # Not every edge will be calculated. The edge which can improve the value of node in heap will be useful.
                if v2 not in dist or weight+w < dist[v2]:
                    dist[v2] = weight+w
                    #push the element into the piority queue
                    heappush(q, (weight+w, v2, path))

    return float("inf")


if __name__ == "__main__":
    # edges = [
        # ("A", "B", 7),
        # ("A", "D", 5),
        # ("B", "C", 8),
        # ("B", "D", 9),
        # ("B", "E", 7),
        # ("C", "E", 5),
        # ("D", "E", 15),
        # ("D", "F", 6),
        # ("E", "F", 1),
        # ("E", "G", 9),
        # ("F", "G", 11),
        # ("F", "E", 1),
        # ("Punggol", "Damai", 10),
        # ("Damai", "Oasis", 5.5),
        # ("Oasis", "Kadaloor", 5),
        # ("Kadaloor", "Riviera", 8),
        # ("Riviera", "Coral Edge", 5),
        # ("Coral Edge", "Meridian", 5.5) ,
        # ("Meridian", "Cove", 5),
        # ("Cove", "Punggol", 9.5),
        # ("Punggol", "Sam Kee", 9),
        # ("Sam Kee", "Punggol Point", 10),
        # ("Punggol Point", "Samudera", 5.5),
        # ("Samudera", "Nibong", 5.5),
        # ("Nibong", "Sumang", 4.5),
        # ("Sumang", "Soo Teck", 5),
        # ("Soo Teck", "Punggol", 7.5),
        # ("A","B",1),
        # ("B","C",1),
        # ("A","C",3),
        # ("D", "F", 6),
        # ("E", "F", 1),
        # ("E", "G", 9),
        # ("F", "G", 11),
    # ]

    # print("=== Dijkstra ===")
    # print(edges)
    # print("A -> E: ", end="")
    # print(dijkstra(edges, "Punggol", "Samudera", 0)) #Shortest Route (Shortest distance taken)
    # print(dijkstra(edges, "Punggol", "Samudera", 1)) #Least Transfer
    # print(dijkstra(edges, "Punggol", "Samudera", 2)) #Fastest Route (Shortest amount of time taken)
    # print(dijkstra(edges, "A", "C",0)) #Fastest Route
    # print(dijkstra(edges, "A", "C",1)) #Least Transfer
    # print("F -> G: ", end="")
    # print(dijkstra(edges, "A", "E"))
    # out = dijkstra(edges, "A", "E")
    # data = {}
    # data['cost']=out[0]
    # aux=[]
    # while len(out)>1:
    #     aux.append(out[0])
    #     out = out[1]
    # aux.remove(data['cost'])
    # aux.reverse()
    # data['path']=aux
    # print(data['path'])




    # === Dijkstra === Algorithm
    df = pandas.read_csv('edges.csv')
    col = df[['u','v','length','oneway']]
    edges = [tuple(x)for x in col.values]
    # print(dijkstra(edges, 5177288947, 3048521675, 0)) #Shortest Route (Shortest distance taken)
    # print(dijkstra(edges, 4702863508, 5083408487, 0)) #Shortest Route (Shortest distance taken)
    # print(dijkstra(edges, 5177288947, 3048521675, 1)) #Shortest Route (Shortest distance taken)

    # Edit 2nd and 3rd variable for the start and end node
    temp = dijkstra(edges, 5177288947, 3048521675, 0) #Shortest Route (Shortest distance taken)
    
    
    
    # Use the follow variables for plotting of map
    distance = temp[0]      
    path = temp[1]          # Only this is needed for plotting on map
    numOfNodes = temp[2] 
    print(distance)
    print(path)       # By default is in a tuple
    print(list(path)) # In case if a list is needed
