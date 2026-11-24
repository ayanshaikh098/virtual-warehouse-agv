import pytest
from warehouse.grid import WarehouseGrid

def test_grid_obstacles_and_bounds():
    g=WarehouseGrid(8,6); assert g.is_free((2,2)); g.add_obstacle((2,2)); assert not g.is_free((2,2)); assert g.remove_obstacle((2,2)); assert not g.remove_obstacle((2,2))
    with pytest.raises(ValueError): g.add_obstacle((8,0))
    with pytest.raises(ValueError): g.add_obstacle(g.start)

def test_layout_round_trip(tmp_path):
    g=WarehouseGrid.demo(); p=tmp_path/'map.json'; g.save(p); loaded=WarehouseGrid.load(p); assert loaded.to_dict()==g.to_dict()

def test_invalid_layout_rejected():
    with pytest.raises(ValueError): WarehouseGrid.from_dict({'width':4,'height':4,'bad':'field'})
