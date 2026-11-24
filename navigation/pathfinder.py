"""NetworkX pathfinding with measured diagnostics."""
from __future__ import annotations
import time
import networkx as nx
from warehouse.grid import WarehouseGrid, Cell

ALGORITHMS = ("bfs", "dijkstra", "astar")

def build_graph(grid: WarehouseGrid) -> nx.Graph:
    graph = nx.grid_2d_graph(grid.width, grid.height)
    graph.remove_nodes_from(grid.obstacles)
    return graph

def find_path(grid: WarehouseGrid, start: Cell, goal: Cell, algorithm: str = "astar") -> dict:
    algorithm = algorithm.lower()
    if algorithm not in ALGORITHMS: raise ValueError(f"Unknown algorithm: {algorithm}")
    if not grid.is_free(start) or not grid.is_free(goal): return {"path": [], "length": 0, "explored": 0, "time_ms": 0.0}
    graph = build_graph(grid)
    explored = 0
    t0 = time.perf_counter()
    if algorithm == "bfs":
        try:
            path = nx.bidirectional_shortest_path(graph, start, goal)
            explored = _bfs_explored(graph, start, goal)
        except nx.NetworkXNoPath:
            path, explored = [], len(graph)
    elif algorithm == "dijkstra":
        path, explored = _dijkstra(graph, start, goal)
    else:
        path = nx.astar_path(graph, start, goal, heuristic=lambda a,b: abs(a[0]-b[0])+abs(a[1]-b[1])) if nx.has_path(graph,start,goal) else []
        explored = len(graph) if not path else _astar_explored(graph, start, goal)
    elapsed = (time.perf_counter()-t0)*1000
    return {"path": path, "length": max(0,len(path)-1), "explored": explored, "time_ms": elapsed}

def _bfs_explored(graph, start, goal):
    from collections import deque
    seen={start}; q=deque([start])
    while q:
        node=q.popleft()
        if node==goal: return len(seen)
        for n in graph.neighbors(node):
            if n not in seen: seen.add(n); q.append(n)
    return len(seen)

def _astar_explored(graph, start, goal):
    # Count nodes actually expanded by an equivalent Manhattan A* search.
    import heapq
    h=lambda p: abs(p[0]-goal[0])+abs(p[1]-goal[1])
    q=[(h(start),0,start)]; costs={start:0}; closed=set()
    while q:
        _,cost,node=heapq.heappop(q)
        if node in closed: continue
        closed.add(node)
        if node==goal: return len(closed)
        for nxt in graph.neighbors(node):
            nc=cost+1
            if nc<costs.get(nxt,float('inf')): costs[nxt]=nc; heapq.heappush(q,(nc+h(nxt),nc,nxt))
    return len(closed)

def _dijkstra(graph, start, goal):
    import heapq
    q=[(0,start)]; dist={start:0}; previous={}; settled=set()
    while q:
        cost,node=heapq.heappop(q)
        if node in settled: continue
        settled.add(node)
        if node==goal:
            path=[goal]
            while path[-1]!=start: path.append(previous[path[-1]])
            return list(reversed(path)),len(settled)
        for nxt in graph.neighbors(node):
            nc=cost+1
            if nc<dist.get(nxt,float('inf')): dist[nxt]=nc; previous[nxt]=node; heapq.heappush(q,(nc,nxt))
    return [],len(settled)
