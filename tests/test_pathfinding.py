import pytest
from warehouse.grid import WarehouseGrid
from navigation.pathfinder import find_path

@pytest.mark.parametrize('algo',['bfs','dijkstra','astar'])
def test_algorithms_find_valid_path(algo):
    g=WarehouseGrid(8,6,obstacles={(3,y) for y in range(5) if y!=2}); result=find_path(g,(0,0),(7,5),algo)
    assert result['path'][0]==(0,0) and result['path'][-1]==(7,5)
    assert all(g.is_free(c) for c in result['path']); assert result['length']==len(result['path'])-1

def test_unreachable_and_bad_algorithm():
    g=WarehouseGrid(5,5,obstacles={(2,y) for y in range(5)})
    assert not find_path(g,(0,0),(4,4),'astar')['path']
    with pytest.raises(ValueError): find_path(g,(0,0),(1,1),'greedy')
