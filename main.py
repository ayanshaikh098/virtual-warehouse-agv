"""Launch the interactive Virtual Warehouse AGV dashboard."""
from __future__ import annotations
import logging, sys
from pathlib import Path
import pygame
from warehouse.grid import WarehouseGrid
from agv.vehicle import Vehicle
from navigation.pathfinder import ALGORITHMS
from hci.webcam import WebcamController
from hci.gesture_recognition import GestureDebouncer, GESTURE_ACTIONS

ROOT=Path(__file__).resolve().parent
(ROOT/'logs').mkdir(exist_ok=True)
logging.basicConfig(filename=ROOT/'logs'/'agv.log',level=logging.INFO,format='%(asctime)s %(levelname)s %(message)s')

class Dashboard:
    def __init__(self):
        pygame.init(); self.cell=40; self.margin=22; self.top=86; self.map_w=18*self.cell
        self.width=self.margin*2+self.map_w+344; self.height=875
        self.screen=pygame.display.set_mode((self.width,self.height)); pygame.display.set_caption('Virtual Warehouse AGV')
        self.clock=pygame.time.Clock(); self.font=pygame.font.SysFont('segoeui',17); self.small=pygame.font.SysFont('segoeui',14); self.big=pygame.font.SysFont('segoeui',27,bold=True)
        self.grid=WarehouseGrid.demo(); self.vehicle=Vehicle(self.grid); self.algorithm='astar'; self.mode='destination'; self.selected=self.grid.delivery
        self.webcam=WebcamController(); self.debounce=GestureDebouncer(); self.gesture='Camera off'; self.last_message='Select a destination, then start the AGV.'; self.message_time=0
        self.gesture_mode=False
        self.bench={}
        self.running=True; self.buttons=[]

    def note(self,msg): self.last_message=msg; self.message_time=pygame.time.get_ticks(); logging.info(msg)
    def text(self,s,x,y,color=(226,233,241),font=None):
        if hasattr(color, 'render'):
            font, color = color, (226,233,241)
        self.screen.blit((font or self.font).render(str(s),True,color),(x,y))
    def button(self,label,rect,action,active=False):
        r=pygame.Rect(rect); color=(42,95,125) if active else (36,48,61); pygame.draw.rect(self.screen,color,r,border_radius=7); pygame.draw.rect(self.screen,(67,85,103),r,1,border_radius=7)
        surf=self.small.render(label,True,(237,243,249)); self.screen.blit(surf,surf.get_rect(center=r.center)); self.buttons.append((r,action))

    def map_cell(self,cell):
        x=self.margin+cell[0]*self.cell; y=self.top+cell[1]*self.cell
        return pygame.Rect(x,y,self.cell-2,self.cell-2)

    def draw_map(self):
        pygame.draw.rect(self.screen,(16,22,29),(self.margin-7,self.top-7,self.map_w+14,12*self.cell+14),border_radius=12)
        route=set(self.vehicle.path[self.vehicle.path_index+1:])
        for y in range(self.grid.height):
            for x in range(self.grid.width):
                c=(x,y); r=self.map_cell(c)
                color=(31,42,53)
                if c in self.grid.obstacles: color=(102,112,123)
                if c in route: color=(27,84,107)
                if c==self.grid.start: color=(53,105,80)
                if c==self.grid.pickup: color=(160,116,43)
                if c==self.grid.delivery: color=(48,110,143)
                if c==self.grid.charger: color=(116,74,143)
                pygame.draw.rect(self.screen,color,r,border_radius=3)
                if c==self.grid.start: self.text('S',r.x+11,r.y+8,(255,255,255),self.small)
                elif c==self.grid.pickup: self.text('P',r.x+11,r.y+8,(255,255,255),self.small)
                elif c==self.grid.delivery: self.text('D',r.x+11,r.y+8,(255,255,255),self.small)
                elif c==self.grid.charger: self.text('C',r.x+11,r.y+8,(255,255,255),self.small)
        # Draw moving AGV as a rounded body, plus direction indicator.
        x,y=self.vehicle.position; r=self.map_cell((x,y)); car=r.inflate(-10,-10); pygame.draw.rect(self.screen,(63,196,219),car,border_radius=8)
        pygame.draw.circle(self.screen,(12,31,42),(car.centerx,car.centery),4)

    def draw_panel(self):
        px=self.margin+self.map_w+26; pw=self.width-px-self.margin
        pygame.draw.rect(self.screen,(24,32,41),(px,78,pw,self.height-96),border_radius=12)
        self.text('CONTROL DECK',px+16,96,(92,201,217),self.small)
        self.text('AGV status',px+16,124,(148,163,178),self.small); self.text(self.vehicle.status,px+16,147,(239,244,249),self.big)
        self.text(f'Position  {self.vehicle.position}      Target  {self.vehicle.destination or "—"}',px+16,186)
        self.text(f'Algorithm  {self.algorithm.upper()}   |   Speed  {self.vehicle.speed:.1f} cells/s',px+16,213)
        self.text(f'Route  {self.vehicle.stats["length"]} cells  |  Explored  {self.vehicle.stats["explored"]}',px+16,239,self.small)
        self.text(f'Compute  {self.vehicle.stats["time_ms"]:.3f} ms',px+16,260,self.small)
        self.text(f'Deliveries  {self.vehicle.completed_tasks}   |   Reroutes  {self.vehicle.reroutes}',px+16,285,self.small)
        self.text('SIMULATION',px+16,322,(92,201,217),self.small)
        self.button('Start / Resume',(px+16,345,pw-32,36),self.do_start)
        self.button('Pause',(px+16,388,(pw-42)//2,34),self.do_pause)
        self.button('Reset',(px+26+(pw-42)//2,388,(pw-42)//2,34),self.do_reset)
        self.text('TARGET AND MAP',px+16,440,(92,201,217),self.small)
        self.button('Destination',(px+16,463,(pw-42)//2,34),lambda:self.set_mode('destination'),self.mode=='destination')
        self.button('Add obstacle',(px+26+(pw-42)//2,463,(pw-42)//2,34),lambda:self.set_mode('add'),self.mode=='add')
        self.button('Remove obstacle',(px+16,504,(pw-42)//2,34),lambda:self.set_mode('remove'),self.mode=='remove')
        self.button(f'Algorithm: {self.algorithm.upper()}',(px+26+(pw-42)//2,504,(pw-42)//2,34),self.cycle_algorithm)
        self.button('Speed −',(px+16,545,(pw-42)//2,32),lambda:self.speed(-.5))
        self.button('Speed +',(px+26+(pw-42)//2,545,(pw-42)//2,32),lambda:self.speed(.5))
        self.text(f'CAMERA · {"ON" if self.webcam.enabled else "OFF"}  /  GESTURES {"ACTIVE" if self.gesture_mode else "INACTIVE"}',px+16,593,(92,201,217),self.small)
        self.button('Enable webcam' if not self.webcam.enabled else 'Disable webcam',(px+16,616,pw-32,34),self.toggle_camera,self.webcam.enabled)
        self.text(f'Gesture: {self.gesture}',px+16,658,self.small)
        self.button('Calibrate gestures',(px+16,681,pw-32,30),self.calibrate)
        self.text('LAYOUT',px+16,721,(92,201,217),self.small)
        self.button('Save layout',(px+16,744,(pw-42)//2,32),self.save_layout)
        self.button('Load saved',(px+26+(pw-42)//2,744,(pw-42)//2,32),self.load_saved)
        self.text('ALGORITHM COMPARISON',px+16,785,(92,201,217),self.small)
        for i,name in enumerate(('bfs','dijkstra','astar')):
            row=self.bench.get(name)
            label=(f'{name.upper():8} {row["length"]:>2} cells  {row["explored"]:>3} nodes  {row["time_ms"]:.2f} ms' if row else f'{name.upper():8} —')
            self.text(label,px+16,805+i*19,(207,218,228),self.small)

    def draw(self):
        self.screen.fill((13,19,25)); self.text('VIRTUAL WAREHOUSE AGV',self.margin,19,(241,245,250),self.big)
        self.text('AUTOMATED GUIDED VEHICLE  /  DIGITAL SIMULATION',self.margin,53,(146,161,176),self.small)
        self.draw_map(); self.buttons=[]; self.draw_panel()
        msg_color=(113,209,167) if self.vehicle.status=='Delivered' else (238,190,110)
        self.text(self.last_message,self.margin,self.height-28,msg_color,self.small)
        pygame.display.flip()

    def set_mode(self,mode): self.mode=mode; self.note({'destination':'Click a free cell to set the destination.','add':'Click an aisle cell to add a virtual obstacle.','remove':'Click a blocked cell to clear it.'}[mode])
    def do_start(self):
        if self.vehicle.status=='Idle' or self.vehicle.destination is None:
            result=self.vehicle.plan(self.selected)
            self.measure_algorithms(self.selected)
            if not result['path']: self.note('No valid route to that destination.'); return
            self.note(f'{self.algorithm.upper()} route calculated: {result["length"]} cells.')
        self.vehicle.resume(); self.vehicle.start(); self.note('AGV moving.')
    def do_pause(self): self.vehicle.pause(); self.note('Simulation paused.')
    def do_reset(self): self.vehicle.reset(); self.note('AGV returned to the starting point.')
    def speed(self,delta): self.vehicle.speed=max(.5,min(8,self.vehicle.speed+delta)); self.note(f'Speed set to {self.vehicle.speed:.1f} cells per second.')
    def cycle_algorithm(self): self.algorithm=ALGORITHMS[(ALGORITHMS.index(self.algorithm)+1)%len(ALGORITHMS)]; self.vehicle.algorithm=self.algorithm; self.note(f'{self.algorithm.upper()} selected.')
    def measure_algorithms(self,goal):
        from navigation.pathfinder import find_path
        self.bench={name:find_path(self.grid,self.vehicle.position,goal,name) for name in ALGORITHMS}
    def calibrate(self): self.debounce=GestureDebouncer(); self.note('Gesture debounce calibrated. Show one gesture at a time.')
    def toggle_camera(self):
        if self.webcam.enabled: self.webcam.disable(); self.gesture='Camera off'; self.gesture_mode=False; self.note('Webcam disabled and released.')
        elif self.webcam.enable(): self.gesture_mode=False; self.note('Webcam enabled locally. Show two raised fingers to activate gesture controls.')
        else: self.note(f'Webcam unavailable: {self.webcam.error}. Keyboard and mouse remain available.')
    def save_layout(self):
        path=ROOT/'data'/'warehouse_layouts'/'saved_layout.json'; path.parent.mkdir(parents=True,exist_ok=True)
        self.grid.save(path); self.note(f'Layout saved to data/warehouse_layouts/saved_layout.json')
    def load_demo(self):
        self.grid=WarehouseGrid.demo(); self.vehicle=Vehicle(self.grid,algorithm=self.algorithm); self.selected=self.grid.delivery; self.note('Demo warehouse loaded.')
    def load_saved(self):
        path=ROOT/'data'/'warehouse_layouts'/'saved_layout.json'
        try:
            self.grid=WarehouseGrid.load(path); self.vehicle=Vehicle(self.grid,algorithm=self.algorithm); self.selected=self.grid.delivery; self.measure_algorithms(self.selected); self.note('Saved warehouse layout loaded.')
        except ValueError as exc: self.note(str(exc))
    def on_cell(self,c):
        try:
            if self.mode=='destination':
                if not self.grid.is_free(c): self.note('Choose a free cell for the destination.'); return
                self.selected=c; result=self.vehicle.plan(c); self.note(f'Destination set to {c}; {result["length"]} cell route planned.' if result['path'] else 'No route is available to that cell.')
                self.measure_algorithms(c)
            elif self.mode=='add':
                outcome=self.vehicle.add_obstacle(c); self.note({'rerouted':'Route blocked. AGV paused, route recalculated, movement resumed.','unreachable':'Obstacle blocked the route; no alternative path exists.','added':'Virtual obstacle added.'}[outcome])
            else: self.note('Obstacle removed.' if self.grid.remove_obstacle(c) else 'That cell has no removable obstacle.')
        except ValueError as exc: self.note(str(exc))
    def camera_update(self):
        if not self.webcam.enabled: return
        self.gesture=self.webcam.read_gesture().replace('_',' ').title()
        normalized=self.gesture.lower().replace(' ','_')
        if self.debounce.accept(normalized):
            action=GESTURE_ACTIONS.get(normalized)
            if action=='gesture_mode':
                self.gesture_mode=not self.gesture_mode
                self.note(f'Gesture controls {"activated" if self.gesture_mode else "deactivated"}.')
            elif not self.gesture_mode: return
            elif action=='resume': self.vehicle.resume(); self.vehicle.start(); self.note('Open palm: simulation resumed.')
            elif action=='pause': self.do_pause()
            elif action=='confirm_destination': self.note(f'Destination {self.selected} confirmed.')
    def run(self):
        try:
            while self.running:
                dt=min(.1,self.clock.tick(60)/1000)
                for e in pygame.event.get():
                    if e.type==pygame.QUIT: self.running=False
                    elif e.type==pygame.MOUSEBUTTONDOWN and e.button==1:
                        handled=False
                        for rect,action in self.buttons:
                            if rect.collidepoint(e.pos): action(); handled=True; break
                        if not handled:
                            x=(e.pos[0]-self.margin)//self.cell; y=(e.pos[1]-self.top)//self.cell
                            if 0<=x<self.grid.width and 0<=y<self.grid.height: self.on_cell((x,y))
                    elif e.type==pygame.KEYDOWN:
                        if e.key==pygame.K_SPACE: self.do_start()
                        elif e.key==pygame.K_p: self.do_pause()
                        elif e.key==pygame.K_r: self.do_reset()
                        elif e.key==pygame.K_a: self.cycle_algorithm()
                        elif e.key==pygame.K_EQUALS: self.speed(.5)
                        elif e.key==pygame.K_MINUS: self.speed(-.5)
                        elif e.key==pygame.K_ESCAPE: self.running=False
                        elif e.key==pygame.K_c: self.toggle_camera()
                        elif e.key==pygame.K_k: self.calibrate()
                        elif e.key==pygame.K_s: self.save_layout()
                self.camera_update(); self.vehicle.update(dt); self.draw()
        except Exception as exc:
            logging.exception('Unexpected dashboard failure'); print(f'Application error: {exc}',file=sys.stderr)
        finally:
            self.webcam.disable(); pygame.quit()

if __name__=='__main__':
    (ROOT/'logs').mkdir(exist_ok=True)
    Dashboard().run()
