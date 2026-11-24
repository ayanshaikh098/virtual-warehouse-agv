# Virtual Warehouse AGV

A local, digital-only warehouse and Automated Guided Vehicle simulation with NetworkX routing, a Pygame dashboard, editable obstacles, JSON layouts, and optional local webcam gesture input. The camera is **off by default**; it is opened only after the Enable webcam button (or `C`) is used. Frames are processed in memory and never saved or transmitted.

## Run

Requires Python 3.11 or newer. From this directory:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python main.py
```

If OpenCV or MediaPipe cannot initialize, the dashboard continues and reports the reason. The camera feature requires a working camera and permission from Windows. It is optional; all simulation actions have mouse or keyboard controls.

## Using the dashboard

- Click a free grid cell in **Destination** mode to select and plan a route.
- Start / Resume begins movement; Pause stops it; Reset returns the AGV to its start.
- Add obstacle mode lets you click an aisle tile. If it intersects the remaining route, the AGV computes a replacement route and continues when one exists. Remove obstacle clears a blocked tile.
- Algorithm cycles A*, BFS, and Dijkstra. The panel reports route cell count, explored-node estimate, and measured search time.
- Speed controls adjust the simulation rate. Save layout writes `data/warehouse_layouts/saved_layout.json`; Load saved validates and restores it. The demo map is loaded at startup.
- Webcam: camera enablement does not by itself activate commands. Show two raised fingers to toggle gesture-control mode; then open palm resumes, fist pauses, and thumbs up confirms the selected destination. Two fingers toggles the mode off again. A per-gesture cooldown prevents repeated actions. Use the Calibrate gestures button or `K` to reset the debounce window.
- Keyboard: `Space` start/resume, `P` pause, `R` reset, `A` cycle algorithm, `+`/`-` speed, `S` save layout, `C` camera toggle, `K` calibrate gesture debounce, `Esc` exit.

Legend: `S` start, `P` pickup, `D` delivery, `C` charging station. Rack blocks are gray, the planned route is teal, and the AGV is cyan. Labels supplement color.

## Algorithms and architecture

`warehouse.grid` owns map validation and JSON persistence. `navigation.pathfinder` converts free four-neighbor cells to a NetworkX graph and offers BFS, Dijkstra, and A* with Manhattan heuristic. `agv.vehicle` owns movement, task state, collision prevention, and dynamic rerouting. `hci` imports OpenCV/MediaPipe only when explicitly enabled. `main.py` provides the Pygame presentation layer and activity feedback. The demonstration layout has rack rows with cross-aisles for route-blocking and detour demonstrations.

## Tests

Run `python -m pytest -q` from this directory. Core tests do not need Pygame display, camera hardware, or MediaPipe initialization.
