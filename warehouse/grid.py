"""Validated grid model for a virtual warehouse."""
from __future__ import annotations
import json
from pathlib import Path
from typing import Iterable

Cell = tuple[int, int]

class WarehouseGrid:
    def __init__(self, width: int = 18, height: int = 12, obstacles: Iterable[Cell] = (),
                 start: Cell = (1, 1), pickup: Cell | None = None, delivery: Cell | None = None,
                 charger: Cell | None = None):
        try:
            width, height = int(width), int(height)
        except (TypeError, ValueError) as exc:
            raise ValueError("Warehouse dimensions must be integers") from exc
        if width < 3 or height < 3:
            raise ValueError("Warehouse must be at least 3 by 3 cells")
        self.width, self.height = int(width), int(height)
        pickup = pickup if pickup is not None else (min(3, width - 1), min(9, height - 1))
        delivery = delivery if delivery is not None else (min(16, width - 1), min(2, height - 1))
        charger = charger if charger is not None else (min(16, width - 1), min(9, height - 1))
        self.start, self.pickup, self.delivery, self.charger = start, pickup, delivery, charger
        self.obstacles: set[Cell] = set()
        for cell in obstacles:
            self.add_obstacle(cell)
        for name, cell in (("start", start), ("pickup", pickup), ("delivery", delivery), ("charger", charger)):
            if not self.in_bounds(cell) or cell in self.obstacles:
                raise ValueError(f"Invalid {name} location: {cell}")

    def in_bounds(self, cell: Cell) -> bool:
        return isinstance(cell, (tuple, list)) and len(cell) == 2 and all(isinstance(v, int) for v in cell) and 0 <= cell[0] < self.width and 0 <= cell[1] < self.height

    def is_free(self, cell: Cell) -> bool:
        return self.in_bounds(cell) and tuple(cell) not in self.obstacles

    def add_obstacle(self, cell: Cell) -> None:
        cell = tuple(cell)
        if not self.in_bounds(cell):
            raise ValueError(f"Cell outside warehouse: {cell}")
        if cell in (self.start, self.pickup, self.delivery, self.charger):
            raise ValueError("Cannot place an obstacle on a warehouse station")
        self.obstacles.add(cell)

    def remove_obstacle(self, cell: Cell) -> bool:
        before = len(self.obstacles)
        self.obstacles.discard(tuple(cell))
        return len(self.obstacles) != before

    def to_dict(self) -> dict:
        return {"width": self.width, "height": self.height, "obstacles": [list(c) for c in sorted(self.obstacles)],
                "start": list(self.start), "pickup": list(self.pickup), "delivery": list(self.delivery), "charger": list(self.charger)}

    @classmethod
    def from_dict(cls, data: dict) -> "WarehouseGrid":
        if not isinstance(data, dict): raise ValueError("Layout must be a JSON object")
        allowed = {"width", "height", "obstacles", "start", "pickup", "delivery", "charger"}
        if set(data) - allowed: raise ValueError("Layout contains unknown fields")
        try:
            return cls(width=data["width"], height=data["height"], obstacles=data.get("obstacles", []), start=tuple(data.get("start", (1,1))),
                       pickup=tuple(data["pickup"]) if "pickup" in data else None,
                       delivery=tuple(data["delivery"]) if "delivery" in data else None,
                       charger=tuple(data["charger"]) if "charger" in data else None)
        except (TypeError, KeyError) as exc:
            raise ValueError(f"Invalid warehouse layout: {exc}") from exc

    def save(self, path: str | Path) -> None:
        Path(path).write_text(json.dumps(self.to_dict(), indent=2), encoding="utf-8")

    @classmethod
    def load(cls, path: str | Path) -> "WarehouseGrid":
        try: data = json.loads(Path(path).read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc: raise ValueError(f"Could not load warehouse layout: {exc}") from exc
        return cls.from_dict(data)

    @classmethod
    def demo(cls) -> "WarehouseGrid":
        # Rack rows leave two cross-aisles and clear station approaches.
        obstacles = {(x,y) for x in range(4,14) for y in (2,3,6,7,10)}
        obstacles |= {(3,y) for y in range(2,8)} | {(14,y) for y in range(4,10)}
        return cls(obstacles=obstacles)
