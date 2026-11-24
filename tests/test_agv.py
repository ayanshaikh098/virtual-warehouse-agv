from warehouse.grid import WarehouseGrid
from agv.vehicle import Vehicle

def test_movement_pause_resume_and_reset():
    v=Vehicle(WarehouseGrid(8,6),speed=2); v.plan((5,1)); v.start(); v.update(.25); assert v.position==(1,1)
    v.pause(); v.update(2); assert v.position==(1,1); v.resume(); v.update(.25); assert v.position==(2,1)
    v.reset(); assert v.position==v.initial_position and v.status=='Idle'

def test_dynamic_obstacle_reroutes():
    v=Vehicle(WarehouseGrid(8,6)); v.plan((6,1)); v.start(); outcome=v.add_obstacle((3,1))
    assert outcome=='rerouted' and v.reroutes==1 and v.status=='Running'
    for _ in range(100): v.update(.1)
    assert v.position==(6,1) and v.status=='Delivered'
