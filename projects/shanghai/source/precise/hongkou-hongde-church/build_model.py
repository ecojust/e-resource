#!/usr/bin/env python3
"""Hongde Tang: closed walls with genuine openings, curved tiled roofs and brackets.
Geometry in metres; no network, production writes, Blender or registration.
"""
import argparse
from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import sys

import numpy as np
from shapely.geometry import Polygon, Point, LineString, box as rect
from shapely.ops import unary_union
from shapely import affinity

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / 'common'))
from photo_architecture import Builder, Facade, opening, pieces
from sign_lettering import add_facade_lettering

P = {
    'grey brick mortar': {'color': [.405, .402, .378], 'roughness': .93},
    'grey brick 0': {'color': [.377, .374, .350], 'roughness': .92},
    'grey brick 1': {'color': [.391, .387, .363], 'roughness': .94},
    'grey brick 2': {'color': [.365, .362, .340], 'roughness': .94},
    'pale door stone': {'color': [.59, .57, .51], 'roughness': .84},
    'foundation stone': {'color': [.35, .35, .33], 'roughness': .92},
    'painted red column': {'color': [.37, .095, .067], 'roughness': .76},
    'red timber frame': {'color': [.25, .075, .055], 'roughness': .68},
    'bracket blue green': {'color': [.19, .37, .36], 'roughness': .83},
    'bracket muted blue': {'color': [.23, .40, .43], 'roughness': .81},
    'beam ochre': {'color': [.49, .36, .13], 'roughness': .80},
    'roof backing': {'color': [.20, .21, .19], 'roughness': .95},
    'tile 0': {'color': [.29, .285, .255], 'roughness': .89},
    'tile 1': {'color': [.25, .255, .235], 'roughness': .91},
    'tile 2': {'color': [.33, .315, .28], 'roughness': .9},
    'ridge red': {'color': [.34, .15, .11], 'roughness': .9},
    'quiet glass': {'color': [.13, .17, .17], 'roughness': .37, 'metallic': .10},
    'stained blue': {'color': [.045, .085, .35], 'roughness': .32, 'metallic': .10},
    'stained amber': {'color': [.44, .32, .075], 'roughness': .35, 'metallic': .05},
    'stained ruby': {'color': [.32, .07, .075], 'roughness': .34, 'metallic': .10},
    'stained pale': {'color': [.42, .43, .37], 'roughness': .38, 'metallic': .08},
    'interior dark': {'color': [.065, .055, .045], 'roughness': .95},
    'plaque blue': {'color': [.035, .09, .27], 'roughness': .55},
    'sign gold': {'color': [.61, .43, .12], 'roughness': .57, 'metallic': .25},
    'iron': {'color': [.18, .19, .17], 'roughness': .67, 'metallic': .22},
}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


class Church:
    def __init__(self):
        self.g = json.loads((HERE / 'geometry-input.json').read_text())
        self.c = json.loads((HERE / 'calibration.json').read_text())
        assert sha(HERE / 'geometry-input.json') == self.c['source_geometry_sha256']
        self.v = self.c['nominal_estimates_m']
        self.b = Builder(P)
        a, b = self.g['front_edge']['endpoints_local_east_north_m']
        self.f = Facade(self.b, b, a, 'north-front')
        self.W = self.g['front_edge']['length_m']
        self.plan = Polygon(self.g['polygon_local_east_north'])
        self.openings = []
        self.roof_laps = []
        self.signs = []

    def point(self, u, depth, z):
        return self.f.point(u, z, -depth)

    def box(self, u, depth, z, w, length, h, mat, label):
        self.f.box(u, z, w, h, length, -depth, mat, label)

    def local_facade(self, a, b, label):
        return Facade(self.b, self.point(*a, 0)[:2], self.point(*b, 0)[:2], label)

    def shell(self, top_vertices, top_faces, thickness, material, label):
        """Solid vertical-thickness surface; shared boundary nodes, no open rims."""
        top = np.asarray(top_vertices, float)
        faces = []
        for f in top_faces:
            for k in range(1, len(f)-1):
                tri = [f[0], f[k], f[k+1]]
                cross = np.cross(top[tri[1]]-top[tri[0]], top[tri[2]]-top[tri[0]])
                if cross[2] < 0: tri.reverse()
                if abs(cross[2]) < 1e-11: raise ValueError('Collapsed roof parameter cell')
                faces.append(tuple(tri))
        n = len(top)
        vertices = np.concatenate([top, top - [0, 0, thickness]])
        edges = Counter(tuple(sorted((a, b))) for f in faces for a, b in zip(f, f[1:]+f[:1]))
        original = list(faces)
        faces.extend(tuple(i+n for i in reversed(f)) for f in original)
        for f in original:
            for a, b in zip(f, f[1:]+f[:1]):
                if edges[tuple(sorted((a, b)))] == 1:
                    faces.append((b, a, a+n, b+n))
        self.b.add(vertices, faces, material, label)

    def wall(self, facade, outline, holes, label, brick=True, thickness=.48):
        holes = unary_union(holes) if holes else Polygon()
        surface = outline.difference(holes)
        facade.prism(surface, -thickness, 0, 'grey brick mortar', label+'-continuous-wall')
        if brick:
            x0, z0, x1, z1 = outline.bounds
            course = .16
            for row in range(math.ceil((z1-z0)/course)):
                z = z0+row*course
                u = x0-.39 if row % 2 else x0
                index = 0
                while u < x1:
                    tile = rect(u+.008, z+.008, u+.38, min(z+.151, z1-.003)).intersection(surface)
                    if tile.area > .002:
                        facade.prism(tile, -.006, .018, 'grey brick '+str(((row*73856093) ^ (index*19349663) ^ (sum(map(ord,label))*83492791)) % 3), label+'-brick')
                    u += .39; index += 1
        return surface

    def glazing(self, facade, shape, label, diagonal=True, stained=False, cols=2, rows=4, split_lattice_z=None):
        inner = shape.buffer(-.075, join_style=2)
        outer = shape.buffer(-.018, join_style=2)
        x0, z0, x1, z1 = shape.bounds
        bars = []
        if diagonal:
            spacing = .42
            for slope in (-1., 1.):
                for offset in np.arange(z0-(x1-x0)-spacing, z1+(x1-x0)+spacing, spacing):
                    bars.append(LineString([(x0-.3, offset-slope*.3), (x1+.3, offset+slope*(x1-x0+.3))]).buffer(.023, cap_style=2))
        else:
            bars += [rect(x0+(x1-x0)*i/cols-.027,z0-.1,x0+(x1-x0)*i/cols+.027,z1+.1) for i in range(1,cols)]
            bars += [rect(x0-.1,z0+(z1-z0)*i/rows-.027,x1+.1,z0+(z1-z0)*i/rows+.027) for i in range(1,rows)]
        if split_lattice_z is not None:
            upper_half = rect(x0-1,split_lattice_z,x1+1,z1+1)
            bars = [b.intersection(upper_half) for b in bars]
            bars += [rect(x0+(x1-x0)*i/cols-.026,z0-.1,x0+(x1-x0)*i/cols+.026,split_lattice_z) for i in range(1,cols)]
            bars += [rect(x0-.1,z0+(split_lattice_z-z0)*i/rows-.026,x1+.1,z0+(split_lattice_z-z0)*i/rows+.026) for i in range(1,rows)]
            bars.append(rect(x0-.1,split_lattice_z-.045,x1+.1,split_lattice_z+.045))
        panes = inner.difference(unary_union(bars))
        frame = outer.difference(panes)
        facade.prism(frame, -.20, -.14, 'red timber frame', label+'-union-frame-lattice')
        for i, pane in enumerate(pieces(panes)):
            mat = 'stained blue' if stained=='blue' else (['stained blue', 'stained amber', 'stained pale', 'stained ruby'][i % 4] if stained else 'quiet glass')
            facade.prism(pane, -.18, -.16, mat, label+'-separate-glass-pane')
        # Glass front is20mm behind frame front; pane boundaries avoid bars.
        self.openings.append({'label':label, 'facade':facade.label, 'bounds_u_z':list(shape.bounds),
                              'void_area_m2':shape.area, 'glass_setback_m':.020,
                              'glass_depth':[-.18,-.16], 'frame_depth':[-.20,-.14], 'panes':len(pieces(panes))})

    def structure(self):
        v = self.v; tw = v['tower_width']; td = v['tower_depth']
        self.b.plan_prism(self.plan, 0, .24, 'foundation stone', 'exact-source-footprint-base')
        # Original four-point slanted source walls are retained; not an invented rectangle.
        from shapely.geometry.polygon import orient
        ring = list(orient(self.plan, sign=1.).exterior.coords)
        for i,(a,b) in enumerate(zip(ring,ring[1:])):
            fa = Facade(self.b,a,b,'source-outer-'+str(i))
            if np.dot(fa.n,self.f.n) > .9: continue
            fa.wall(.24,v['wing_wall_top'],thickness=.45,material='grey brick mortar')
            fa.beam(.48,.32,.04,'foundation stone',label='unobserved-side-rear-base')
            fa.beam(v['wing_wall_top']-.10,.20,.08,'pale door stone',label='unobserved-side-rear-cap')
        door = opening(0,.72,2.15,3.50,arch=1.05,segments=40)
        mid = [opening(u,6.05,w,3.25 if u==0 else 2.88,arch=.72 if u==0 else 0,segments=36)
               for u,w in [(-2.0,1.15),(0,1.55),(2.0,1.15)]]
        upper = [opening(u,10.65,.70,1.65) for u in [-1.22,0,1.22]]
        self.wall(self.f,rect(-tw/2,.24,tw/2,v['tower_masonry_top']),[door,*mid,*upper],'tower-north')
        for i,shape in enumerate(mid):self.glazing(self.f,shape,'tower-middle-'+str(i),True,False)
        for i,shape in enumerate(upper):self.glazing(self.f,shape,'tower-upper-'+str(i),False,False,1,3)
        # True masonry opening remains open under the stained arched transom.
        trim = door.buffer(.27,join_style=2).difference(door)
        self.f.prism(trim,-.04,.19,'pale door stone','arched-entry-stone-ring')
        transom = door.intersection(rect(-2,3.12,2,4.5))
        self.glazing(self.f,transom,'entry-stained-transom',True,True)
        self.f.box(0,3.13,2.14,.105,.14,-.07,'red timber frame','entry-transom-beam')
        # Open timber door leaves are local solid slabs, not a photographed doorway plane.
        for side in [-1,1]:
            hinge = self.point(side*1.0,.20,1.90)
            along = self.f.t*side*.30 - self.f.n*.95
            normal = np.cross(along,[0,0,1]);normal/=np.linalg.norm(normal)
            self.b.box(hinge+along*.44,(.88,.065,2.32),'red timber frame',[along,normal,[0,0,1]],'open-door-leaf')
        self.box(0,3.8,1.95,3.1,.15,2.8,'interior dark','entry-inner-dark-return-not-front-blocker')
        self.box(0,2.0,.68,3.1,4.0,.15,'foundation stone','entry-inner-floor')
        # Tower east return is visible; only its observed upper arch row is asserted.
        tower = [(-tw/2,0),(tw/2,0),(tw/2,td),(-tw/2,td)]
        for i,(a,b) in enumerate(zip(tower,tower[1:]+tower[:1])):
            if i==0:continue
            fa=self.local_facade(a,b,'tower-return-'+str(i))
            hs=[opening(u,10.55,.95,1.78,arch=.45) for u in [-2.,0,2.]] if i==3 else []
            self.wall(fa,rect(-fa.length/2,.24,fa.length/2,v['tower_masonry_top']),hs,'tower-return-'+str(i),brick=i==3)
            for j,h in enumerate(hs):self.glazing(fa,h,'visible-east-arched-'+str(j),False,False,2,3)
        for side in [-1,1]:
            x0,x1=sorted([side*(tw/2),side*(self.W/2)])
            center=side*(tw/2+(self.W/2-tw/2)*.54)
            facade=self.local_facade((self.W/2,v['wing_front_recess']),(-self.W/2,v['wing_front_recess']),'recessed-wing-'+str(side))
            # Reverse to ensure outward north; explicit local shape coordinates use actual facade u.
            if np.dot(facade.n,self.f.n)<0:facade=self.local_facade((-self.W/2,v['wing_front_recess']),(self.W/2,v['wing_front_recess']),'recessed-wing-'+str(side))
            low=opening(center,.72,1.65,3.05,arch=.82,segments=36)
            circle=Point(center,5.12).buffer(.70,quad_segs=20)
            self.wall(facade,rect(x0,.24,x1,v['wing_wall_top']),[low,circle],'wing-'+str(side))
            for shape,label in [(low,'high-arch'),(circle,'round-window')]:
                self.glazing(facade,shape,'wing-'+str(side)+'-'+label,True,'blue' if label=='round-window' else True,3,4,split_lattice_z=2.65 if label=='high-arch' else None)
                facade.prism(shape.buffer(.12,join_style=2).difference(shape),-.02,.045,'grey brick 1','brick-opening-ring')
            # Two visible freestanding red columns per wing, with stone footing.
            for u in [side*(tw/2+.58),side*(self.W/2-.58)]:
                center_xy=self.point(u,.17,0)[:2]
                self.b.lathe(center_xy,[(.25,.46),(.42,.46),(.50,.37),(.60,.34),(5.90,.32),(6.02,.37),(6.15,.37)],'painted red column',28,'wing-free-red-column')
                self.b.lathe(center_xy,[(.12,.49),(.23,.49),(.25,.46)],'foundation stone',28,'column-stone-foot')
            self.box((x0+x1)/2,.18,6.17,x1-x0,.40,.48,'red timber frame','wing-front-painted-beam')
            self.box((x0+x1)/2,-.035,6.18,x1-x0-.1,.035,.28,'bracket blue green','wing-teal-beam-panel')
            for u in np.arange(x0+.28,x1-.15,.86):
                diamond=Polygon([(u,6.03),(u+.22,6.18),(u,6.33),(u-.22,6.18)])
                self.f.prism(diamond,.005,.022,'beam ochre','beam-geometric-ornament')
            # The upper setback strip is a separate plane, not stretched onto the low wing wall.
            fa=self.local_facade((-self.W/2,3.0),(self.W/2,3.0),'nave-upper-front-'+str(side))
            hs=[opening(side*u,7.70,1.05,1.05) for u in [5.25,7.20]]
            outline=rect(max(x0,-self.W/2+1.25),6.3,min(x1,self.W/2-1.25),8.9)
            self.wall(fa,outline,hs,'clerestory-'+str(side),True,.40)
            for j,h in enumerate(hs):self.glazing(fa,h,'clerestory-'+str(side)+'-'+str(j),True,False)
        # Interior nave upper enclosure is a conservative unfenestrated shell.
        inner=self.plan.buffer(-1.25,join_style=2).intersection(Polygon([self.point(u,d,0)[:2] for u,d in [(-40,3),(40,3),(40,50),(-40,50)]]))
        ring=list(orient(inner,sign=1.).exterior.coords)
        for i,(a,b) in enumerate(zip(ring,ring[1:])):
            fa=Facade(self.b,a,b,'upper-nave-conservative-'+str(i))
            if np.dot(fa.n,self.f.n)>.9:continue
            fa.wall(6.2,8.9,thickness=.3,material='grey brick mortar')
        # Central steps are visible projections, not an altered source footprint.
        for i in range(4):
            h=.18*(i+1);depth=.35*(4-i)
            self.box(0,-depth/2,h/2,3.15,depth,h,'foundation stone','entrance-step-'+str(i))

    def roof_point(self, spec, side, q, t):
        # t0=inner high ring, t1=outer eave. Corners sweep upward separately.
        hx=spec['inner'][0]*(1-t)+spec['outer'][0]*t
        hy=spec['inner'][1]*(1-t)+spec['outer'][1]*t
        if side==0:u,d=q*hx,-hy
        elif side==1:u,d=hx,q*hy
        elif side==2:u,d=-q*hx,hy
        else:u,d=-hx,-q*hy
        z=spec['high']-(spec['high']-spec['low'])*t**.78+.20*t**8+spec['corner']*t**6*abs(q)**6
        return u+spec.get('u',0),d+spec['d'],z

    def roof(self,spec,label,cols=18,rows=10,tiles=True):
        samples=cols*2
        rings=14
        top=[]
        for j in range(rings+1):
            for side in range(4):
                for i in range(samples):
                    top.append(self.point(*self.roof_point(spec,side,-1+2*i/samples,j/rings)))
        perimeter=4*samples;faces=[]
        for r in range(rings):
            for k in range(perimeter):
                a=r*perimeter+k;b=r*perimeter+(k+1)%perimeter
                faces.append((a,b,b+perimeter,a+perimeter))
        self.shell(top,faces,.15,'roof backing',label+'-continuous-curved-solid')
        # Segmented, cambered tiles have22mm shingle steps at overlaps and12mm skin.
        if tiles:
            for side in range(4):
                for row in range(rows):
                    a=row/rows;b=min(1,(row+1)/rows+.012)
                    for col in range(cols):
                        q0=-1+2*col/cols+.007;q1=-1+2*(col+1)/cols-.007
                        pts=[];quads=[]
                        for j in range(3):
                            t=a+(b-a)*j/2
                            for k in range(5):
                                q=q0+(q1-q0)*k/4
                                u,d,z=self.roof_point(spec,side,q,t)
                                # Same q profile in adjacent rows: overlap clearance is independent of tile camber.
                                z+=.045+.022*(t-a)/(b-a)+.026*math.sin(math.pi*k/4)
                                pts.append(self.point(u,d,z))
                        for j in range(2):
                            for k in range(4):
                                a0=j*5+k;quads.append((a0,a0+1,a0+6,a0+5))
                        self.shell(pts,quads,.012,'tile '+str((col+row+side)%3),label+f'-tile-{side}-{row}-{col}')
                self.roof_laps.append({'roof':label,'side':side,'rows':rows,'columns':cols,'step_nominal_m':.022,'skin_m':.012,'t_overlap':.012,'coplanar_stacked_skin':False})
                # Exposed radial rafter ends below eaves, including real curved path.
                for col in range(cols+1):
                    q=-1+2*col/cols
                    points=[]
                    for t in np.linspace(.70,1,5):
                        u,d,z=self.roof_point(spec,side,q,t);points.append(self.point(u,d,z-.25))
                    self.b.tube(points,.078,'bracket muted blue',8,label+'-curved-rafter')
                # Ridges along four hip corners and the eave border follow the curved roof.
                points=[self.point(*self.roof_point(spec,side,-1,t))+[0,0,.07] for t in np.linspace(0,1,15)]
                self.b.tube(points,.115,'ridge red',10,label+'-raised-hip-ridge')
                pts=[self.point(*self.roof_point(spec,side,q,1))+[0,0,.02] for q in np.linspace(-1,1,25)]
                self.b.tube(pts,.085,'ridge red',8,label+'-eave-border')

    def shed_point(self,spec,q,t):
        u=spec['u']+q*spec['half_width']
        d=spec['back_depth']*(1-t)+spec['front_depth']*t
        outer=max(0,spec['outer_side']*q)
        z=spec['high']-(spec['high']-spec['low'])*t**.78+.20*t**8+spec['corner']*t**6*outer**6
        return u,d,z

    def shed_roof(self,spec,label,cols,rows):
        top=[];faces=[];nx=cols*2;ny=14
        for j in range(ny+1):
            for i in range(nx+1):top.append(self.point(*self.shed_point(spec,-1+2*i/nx,j/ny)))
        for j in range(ny):
            for i in range(nx):
                a=j*(nx+1)+i;faces.append((a,a+1,a+nx+2,a+nx+1))
        self.shell(top,faces,.15,'roof backing',label+'-one-continuous-curved-slope')
        for row in range(rows):
            a=row/rows;b=min(1,(row+1)/rows+.012)
            for col in range(cols):
                q0=-1+2*col/cols+.004;q1=-1+2*(col+1)/cols-.004
                pts=[];quads=[]
                for j in range(3):
                    t=a+(b-a)*j/2
                    for k in range(5):
                        q=q0+(q1-q0)*k/4;u,d,z=self.shed_point(spec,q,t)
                        z+=.045+.022*(t-a)/(b-a)+.026*math.sin(math.pi*k/4)
                        pts.append(self.point(u,d,z))
                for j in range(2):
                    for k in range(4):
                        v=j*5+k;quads.append((v,v+1,v+6,v+5))
                self.shell(pts,quads,.012,'tile '+str((col+row)%3),label+f'-tile-0-{row}-{col}')
        for col in range(cols+1):
            q=-1+2*col/cols
            points=[self.point(*self.shed_point(spec,q,t))-[0,0,.25] for t in np.linspace(.70,1,5)]
            self.b.tube(points,.078,'bracket muted blue',8,label+'-curved-rafter')
        eave=[self.point(*self.shed_point(spec,q,1))+[0,0,.02] for q in np.linspace(-1,1,35)]
        self.b.tube(eave,.085,'ridge red',8,label+'-continuous-front-eave-border')
        # Only the exposed outer end receives a raised curved edge, no central ridge/apex.
        edge=[self.point(*self.shed_point(spec,spec['outer_side'],t))+[0,0,.03] for t in np.linspace(0,1,15)]
        self.b.tube(edge,.085,'ridge red',8,label+'-outer-curved-edge')
        self.roof_laps.append({'roof':label,'side':0,'rows':rows,'columns':cols,'step_nominal_m':.022,'skin_m':.012,'t_overlap':.012,'shape':'continuous short-depth curved shed, no pavilion peak'})

    def bracket(self,u,d,z,label,rotate=False):
        # Curved upward arms are real solid outlines, with stepped bearing blocks.
        if not rotate:fa=self.f;centeru=u;offset=-d
        else:
            fa=self.local_facade((u,d-.8),(u,d+.8),label+'-perpendicular');centeru=0;offset=0
        for level,length in enumerate([.34,.50,.67]):
            h=z+level*.17
            xs=np.linspace(-length,length,13)
            lower=[(centeru+x,h+.12*(abs(x)/length)**2) for x in xs]
            upper=[(centeru+x,h+.12*(abs(x)/length)**2+.13) for x in xs[::-1]]
            fa.prism(Polygon(lower+upper),offset-.10,offset+.10,'bracket blue green',label+'-curved-arm-'+str(level))
            for side in [-1,1]:fa.box(centeru+side*length*.78,h+.24,.16,.15,.24,offset,'bracket muted blue',label+'-bearing-block')
        fa.box(centeru,z-.10,.24,.28,.25,offset,'painted red column',label+'-seat')

    def roof_system(self):
        v=self.v
        # Low wing roof is a wide shallow hip ring; central tower hides its inner middle.
        for side in [-1,1]:
            center=side*(v['tower_width']/2+(self.W/2-v['tower_width']/2)/2)
            width=(self.W-v['tower_width'])/4+.25
            low={'u':center,'half_width':width,'back_depth':3.08,'front_depth':-.65,'low':6.65,'high':7.55,'corner':.46,'outer_side':side}
            self.shed_roof(low,'wing-continuous-low-eave-'+str(side),22,9)
            for u in np.linspace(center-width+.35,center+width-.35,6):self.bracket(u,.15,6.22,'wing-dougong')
        # Nave roof stays within the raw source corridor; hidden rear form is explicitly estimated.
        nave={'d':16.8,'outer':[self.W/2-.65,13.55],'inner':[.16,8.0],'low':9.05,'high':v['nave_roof_ridge'],'corner':.30}
        self.roof(nave,'conservative-nave-hip',20,12)
        self.box(0,16.8,11.80,.42,16.35,.26,'roof backing','nave-inner-ring-solid-ridge-closure')
        self.b.tube([self.point(0,8.8,11.90),self.point(0,24.8,11.90)],.14,'ridge red',10,'nave-estimated-ridge')
        # Tower double eaves: lower ring around a setback upper drum, upper pyramidal roof.
        low={'d':v['tower_depth']/2,'outer':[4.50,4.55],'inner':[2.3,2.3],'low':v['tower_lower_eave_center'],'high':v['tower_lower_roof_inner'],'corner':.82}
        self.roof(low,'tower-lower-eave',22,10)
        for side in [-1,1]:
            for u in np.linspace(-3.25,3.25,8):self.bracket(u,v['tower_depth']/2+side*3.55,12.95,'tower-lower-bracket')
            for d in np.linspace(.55,6.95,8):self.bracket(side*3.55,d,12.95,'tower-side-bracket',True)
        self.box(0,v['tower_depth']/2,16.40,4.70,4.70,.85,'red timber frame','upper-roof-setback-drum-estimate')
        high={'d':v['tower_depth']/2,'outer':[3.95,3.95],'inner':[.10,.10],'low':v['tower_upper_eave_center'],'high':v['tower_upper_apex'],'corner':.90}
        self.roof(high,'tower-upper-pyramidal-eave',22,13)
        for side in [-1,1]:
            for u in np.linspace(-2.5,2.5,7):self.bracket(u,v['tower_depth']/2+side*2.6,16.05,'tower-upper-bracket')
            for d in np.linspace(1.15,6.35,7):self.bracket(side*2.6,d,16.05,'tower-upper-side-bracket',True)
        self.b.lathe(self.point(0,v['tower_depth']/2,0)[:2],[(21.15,.18),(21.35,.22),(21.48,.12),(21.55,.035)],'tile 1',16,'small-roof-cap-estimate')

    def signs_details(self):
        font=HERE/'fonts/HongdeSubset.otf'
        self.f.box(0,5.18,2.18,.88,.08,.045,'sign gold','2024-blue-plaque-gold-rim')
        self.f.box(0,5.18,2.03,.73,.035,.105,'plaque blue','2024-blue-plaque-face')
        self.signs.append(add_facade_lettering(self.f,'鴻德堂',0,5.18,1.65,.46,.127,.147,'sign gold',label='2024-plaque-readable-font-approximation',font=font))
        self.signs.append(add_facade_lettering(self.f,'上帝愛世人',0,9.82,3.05,.38,.025,.050,'sign gold',label='2024-upper-lettering-not-2014-cross',font=font))
        # Visible stone doorway ornament and ventilators, restrained geometric approximation.
        for side in [-1,1]:
            self.f.prism(Point(side*1.70,3.45).buffer(.16,quad_segs=12),.02,.07,'iron','visible-round-wall-vent')
        # No invented sculpted guardian/statue; small plinths represent only observed bases.
        for side in [-1,1]:self.box(side*1.95,-.48,.43,.66,.65,.86,'pale door stone','guardian-base-only-statue-unmodeled')
        # Stone rings articulate circular/arched aperture boundaries; no street tree or people baked in.

    def audit(self):
        failures=[];records=[];allv=[]
        for part in self.b.parts:
            v=np.asarray(part['vertices'],dtype=np.float32).astype(float);t=np.asarray(part['triangles']);allv.append(v)
            cross=np.cross(v[t[:,1]]-v[t[:,0]],v[t[:,2]]-v[t[:,0]])
            edges=Counter(tuple(sorted((int(a),int(b)))) for tri in t for a,b in zip(tri,np.roll(tri,-1)))
            volume=float(np.einsum('ij,ij->',v[t[:,0]],np.cross(v[t[:,1]],v[t[:,2]]))/6)
            wrong=sum(n!=2 for n in edges.values());zero=int(np.sum(np.linalg.norm(cross,axis=1)<1e-9))
            if wrong or zero or volume<=0:failures.append({'label':part['label'],'nonmanifold_edges':wrong,'zero_triangles':zero,'volume':volume})
            records.append({'label':part['label'],'material':part['material'],'triangles':len(t),'volume_m3':volume})
        points=np.concatenate(allv)
        return {'schema':'hongde-parts-geometry-audit-v8','passed':not failures,'parts':len(records),'triangles':sum(p['triangles'] for p in records),
                'all_parts_closed_positive_float32':not failures,'failures':failures,'bbox_enu_m':[points.min(0).tolist(),points.max(0).tolist()],
                'part_records':records,'opening_records':self.openings,'roof_lap_design':self.roof_laps,'sign_records':self.signs,
                'source_geometry_sha256':sha(HERE/'geometry-input.json'),'source_polygon_not_orthogonalized':True,
                'native_visual_passed':False,'browser_passed':False,'height_measured':False}

    def build(self,output):
        self.structure();self.roof_system();self.signs_details()
        qa=self.audit();output.mkdir(parents=True,exist_ok=True)
        (output/'geometry-report.json').write_text(json.dumps(qa,ensure_ascii=False,indent=2)+'\n')
        if not qa['passed']:raise ValueError('Actual parts failed: '+str(qa['failures'][:10]))
        metadata={'id':self.g['id'],'name':self.g['name_zh'],'source_geometry_sha256':sha(HERE/'geometry-input.json'),'calibration_sha256':sha(HERE/'calibration.json'),
            'copyright':'Photo-informed geometry CC BY-SA4.0; Livelikerw (2014) and Windmemories (2024), Wikimedia Commons; source footprint © OpenStreetMap contributors / Overture Maps Foundation ODbL1.0; font Noto CJK SIL OFL1.1',
            'license':'CC-BY-SA-4.0','appearance_epoch':'2024-01-07 visible facade,2014 daylight material classes','height_measured':False,'ground_base_m':0,
            'embedded_photos':False,'rear_roof_and_dimensions_estimated':True,'source_photo_sha256':{str(i):sha(HERE/f'photos/commons-{i}.jpg') for i in [37225841,143735176]}}
        raw=output/'hongkou-hongde-church-raw.glb';self.b.save(raw,metadata)
        assert raw.stat().st_size<40_000_000,'Raw exceeded its agreed safe margin'
        result={'id':self.g['id'],'raw':{'file':raw.name,'bytes':raw.stat().st_size,'sha256':sha(raw)},'triangles':qa['triangles'],'parts':qa['parts'],
                'geometry_qa_passed':True,'native_visual_passed':False,'browser_passed':False,'embedded_images':0,'ground_base_m':0,
                'source_geometry_sha256':sha(HERE/'geometry-input.json'),'front_azimuth_deg':self.g['front_edge']['outward_azimuth_deg'],
                'recommended_preview_azimuth_deg':25.574730186207086,'recommended_preview_elevation_deg':12,'height_estimate_m':qa['bbox_enu_m'][1][2],
                'limitations':self.c['limitations']}
        (output/'asset-metadata.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps(result,ensure_ascii=False,indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,default=HERE/'output');args=parser.parse_args();Church().build(args.output)
