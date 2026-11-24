"""Small task sequence helper for pickup and delivery demonstrations."""
class TaskManager:
    def __init__(self, grid):
        self.grid=grid; self.stage="pickup"
    @property
    def destination(self): return self.grid.pickup if self.stage=="pickup" else self.grid.delivery
    def complete(self): self.stage="delivery" if self.stage=="pickup" else "pickup"
