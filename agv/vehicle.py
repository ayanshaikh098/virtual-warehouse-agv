"""Discrete-cell AGV with safe route following and dynamic rerouting."""
from __future__ import annotations
from warehouse.grid import WarehouseGrid, Cell
from navigation.pathfinder import find_path

class Vehicle:
    def __init__(self, grid: WarehouseGrid, speed: float = 3.0, algorithm: str = "astar"):
        self.grid=grid; self.initial_position=grid.start; self.position=grid.start
        self.speed=max(.2,float(speed)); self.algorithm=algorithm; self.destination=None
        self.path=[]; self.path_index=0; self.status="Idle"; self.elapsed=0.0
        self.stats={"length":0,"explored":0,"time_ms":0.0}; self.completed_tasks=0; self.reroutes=0
        self.carrying=False

    def plan(self, destination: Cell) -> dict:
        if not self.grid.is_free(destination):
            self.destination=None; self.path=[]; self.status="Destination unavailable"
            return {"path": [], "length":0,"explored":0,"time_ms":0.0}
        result=find_path(self.grid,self.position,destination,self.algorithm)
        self.destination=destination; self.path=result["path"]; self.path_index=0; self.elapsed=0
        self.stats={k:result[k] for k in ("length","explored","time_ms")}
        self.status="Ready" if self.path else "No route"
        return result

    def start(self):
        if self.path and self.destination is not None: self.status="Running"
        elif not self.path: self.status="No route"

    def pause(self):
        if self.status=="Running": self.status="Paused"

    def resume(self):
        if self.status=="Paused" and self.path: self.status="Running"
        elif self.status=="Ready": self.start()

    def update(self, dt: float):
        if self.status!="Running" or not self.path: return
        self.elapsed += max(0,dt)*self.speed
        while self.elapsed>=1 and self.path_index+1<len(self.path):
            nxt=self.path[self.path_index+1]
            if not self.grid.is_free(nxt): self.reroute(); return
            self.position=nxt; self.path_index+=1; self.elapsed-=1
        if self.position==self.destination:
            self.status="Delivered"; self.completed_tasks+=1; self.elapsed=0

    def add_obstacle(self, cell: Cell):
        self.grid.add_obstacle(cell)
        remaining=self.path[self.path_index+1:] if self.path else []
        if tuple(cell) in remaining and self.status in ("Running","Paused","Ready"):
            was_running=self.status=="Running"; self.status="Paused"
            result=self.plan(self.destination)
            if result["path"]:
                self.reroutes+=1
                self.status="Running" if was_running else "Ready"
                return "rerouted"
            self.status="No route"
            return "unreachable"
        return "added"

    def reroute(self):
        was_running=True; result=self.plan(self.destination)
        if result["path"]: self.reroutes+=1; self.status="Running" if was_running else "Ready"
        else: self.status="No route"

    def reset(self):
        self.position=self.initial_position; self.destination=None; self.path=[]; self.path_index=0
        self.elapsed=0; self.status="Idle"; self.stats={"length":0,"explored":0,"time_ms":0.0}; self.carrying=False
        self.completed_tasks=0; self.reroutes=0
