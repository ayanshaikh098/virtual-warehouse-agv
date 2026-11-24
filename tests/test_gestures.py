from hci.gesture_recognition import GestureDebouncer, GESTURE_ACTIONS

def test_mappings_and_debounce():
    assert GESTURE_ACTIONS['open_palm']=='resume' and GESTURE_ACTIONS['fist']=='pause'
    d=GestureDebouncer(1); assert d.accept('fist',0); assert not d.accept('fist',.4); assert d.accept('fist',1.2); assert not d.accept('unknown',3)
