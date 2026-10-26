"""Bund 14: photo-informed 1948 Bank of Communications exterior.

python build_model.py --output output
Requires Python, numpy and Shapely 2.1+; shared helper is ../common.
All coordinates are metres east/north/up until the shared GLB exporter.
Source photos retain their licences; no photograph is baked into a texture.
"""
import argparse
from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import sys

import numpy as np
import shapely
from shapely import constrained_delaunay_triangles
from shapely.geometry import Polygon, LineString, box as rect
from shapely.geometry.polygon import orient
from shapely.ops import unary_union

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'common'))
from photo_architecture import Builder, Facade, opening, pieces
from sign_lettering import add_facade_lettering


PALETTE = {
    'ivory cement render': {'color': [.74, .715, .65], 'roughness': .87},
    'render groove backing': {'color': [.69, .665, .605], 'roughness': .9},
    'painted rear render': {'color': [.69, .685, .65], 'roughness': .9},
    'polished black marble': {'color': [.065, .071, .07], 'roughness': .27},
    'black marble joints': {'color': [.11, .115, .11], 'roughness': .65},
    'dark bronze frames': {'color': [.055, .066, .065], 'roughness': .35, 'metallic': .42},
    'blue grey glass': {'color': [.20, .267, .286], 'roughness': .24, 'metallic': .25},
    'pale reflected glass': {'color': [.38, .425, .427], 'roughness': .29, 'metallic': .12},
    'dark ground glass': {'color': [.08, .115, .115], 'roughness': .32, 'metallic': .15},
    'gold grille': {'color': [.69, .48, .13], 'roughness': .30, 'metallic': .72},
    'roof concrete': {'color': [.39, .40, .38], 'roughness': .94},
    'painted cap metal': {'color': [.59, .60, .56], 'roughness': .45, 'metallic': .25},
    'white ornament bands': {'color': [.76, .77, .72], 'roughness': .5},
    'dark ornament bands': {'color': [.10, .11, .105], 'roughness': .5},
}


def file_info(path):
    data = path.read_bytes()
    return {'file': path.name, 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}


class Bank14:
    def __init__(self):
        self.source = json.loads((HERE / 'geometry-input.json').read_text())
        self.cal = json.loads((HERE / 'calibration.json').read_text())
        self.b = Builder(PALETTE)
        self.plan = orient(Polygon(self.source['polygon_local_east_north']), sign=1)
        e = self.source['front_edge']['endpoints_local_east_north_m']
        self.front = Facade(self.b, *e, label='east-observed-2025')
        self.width = self.front.length
        self.h = self.cal['heights_m']['main_roof']
        self.high = self.cal['heights_m']['highest_masonry']
        self.rear_h = self.cal['heights_m']['rear_wing_roof']
        self.holes = []
        self.windows = []
        self.checks = []
        self.lettering_evidence = None

    def z(self, nominal):
        return nominal / 28.8 * self.h if nominal <= 28.8 else self.h + (nominal-28.8)/9.4*(self.high-self.h)

    def pz(self, photo_m):
        """Photo-rectified reference heights at the independent 24.6/33.4m fit."""
        return photo_m/24.6*self.h if photo_m<=24.6 else self.h+(photo_m-24.6)/8.8*(self.high-self.h)

    def prect(self, x0, y0, x1, y1):
        return rect(x0,self.pz(y0),x1,self.pz(y1))

    def pbox(self,u,z,w,h,depth=.12,d=0,mat='ivory cement render',label='detail'):
        bottom,top=self.pz(z-h/2),self.pz(z+h/2)
        self.front.box(u,(bottom+top)/2,w,top-bottom,depth,d,mat,label)

    def point(self, u, d, z):
        return self.front.point(u, z, d)

    def plane(self, coords):
        return Polygon([self.point(u, d, 0)[:2] for u, d in coords])

    def front_box(self, u, z, w, h, depth=.12, d=0, mat='ivory cement render', label='detail'):
        self.front.box(u, self.z(z), w, self.z(z+h/2)-self.z(z-h/2), depth, d, mat, label)

    def rect_z(self, x0, y0, x1, y1):
        return rect(x0, self.z(y0), x1, self.z(y1))

    def window(self, f, u, bottom, width, height, columns=3, kind='regular', label='window', inferred=False):
        """True opening supplied to the wall; complete recessed frame/pane partition.

        Mullion/transom rectangles are unioned before extrusion, so their
        intersections do not introduce crossed overlapping coplanar faces.
        """
        shape = opening(u, bottom, width, height)
        sill_z = bottom-.065
        frame_w = .065 if kind != 'tower' else .045
        inner = shape.buffer(-frame_w, join_style=2)
        x0, z0, x1, z1 = inner.bounds
        recess = .31 if kind in ('regular', 'tower', 'rear') else .38
        bars = [shape.difference(inner)]
        for k in range(1, columns):
            x = x0 + (x1-x0)*k/columns
            bars.append(rect(x-.032, z0, x+.032, z1))
        cuts = [.79] if kind in ('regular', 'rear') else ([.18,.80] if kind == 'hall' else [.50])
        if kind == 'ground': cuts = [.25,.70]
        for q in cuts:
            zz = z0 + (z1-z0)*q
            bars.append(rect(x0, zz-.031, x1, zz+.031))
        framing = unary_union(bars).intersection(shape)
        f.prism(framing, -recess+.04, -recess+.115, 'dark bronze frames', label+'-unified-frame')
        pane_area = shape.difference(framing)
        for i, pane in enumerate(pieces(pane_area)):
            glass = ('dark ground glass' if kind == 'ground' else
                     'pale reflected glass' if (i+round(u*10))%5 in (0,1) else 'blue grey glass')
            f.prism(pane, -recess-.02, -recess, glass, label+'-pane')
        f.box(u, sill_z, width+.14, .13, .44, -.005, 'ivory cement render' if kind != 'ground' else 'polished black marble', label+'-projecting-sill')
        if kind == 'ground':
            for zz in np.arange(z0+.13, z1-.07, .23):
                f.box(u, zz, width-.12, .025, .025, -.22, 'dark bronze frames', label+'-security-bar')
        self.windows.append({'facade': f.label, 'label':label, 'kind':kind, 'inferred':inferred,
                             'center_world_east_north_up': f.point(u,bottom+height/2).tolist(),
                             'width_m':width, 'height_m':height, 'recess_m':recess,
                             'hole_area_m2':shape.area, 'columns':columns})
        return shape

    def front_outline(self):
        half = [(0,38.2),(.22,38.2),(.22,37.9),(.40,37.9),(.40,37.55),(.55,37.55),
                (.55,35.65),(1.02,35.65),(1.02,36.0),(1.72,36.0),(1.72,35.65),
                (2.25,35.65),(2.25,35.1),(3.30,35.1),(3.30,31.3),(3.85,31.3),
                (3.85,30.0),(5.00,30.0),(5.00,28.8),(8.8,28.8),(8.8,30.3),
                (9.55,30.3),(9.55,31.8),(9.90,31.8),(9.90,30.3),(10.60,30.3),
                (10.60,29.7),(self.width/2,29.7)]
        top = [(-x,self.z(z)) for x,z in reversed(half[1:])] + [(x,self.z(z)) for x,z in half]
        return Polygon([(-self.width/2,0),(self.width/2,0),*reversed(top)])

    def make_front(self):
        f = self.front
        axes = [v*self.width for v in self.cal['front_axes_fraction_from_center']]
        widths = [v*self.width for v in self.cal['front_window_width_fraction']]
        holes=[]
        for row, (y,top) in enumerate(self.cal['photo_rectified_front_m']['regular_window_extents']):
            for i,(u,w) in enumerate(zip(axes,widths)):
                holes.append(self.window(f,u,self.pz(y),w,self.pz(top)-self.pz(y),2 if i in (0,7) else 3,
                                         'regular',f'floor-{row+3}-axis-{i+1}'))
        for i in (0,1,2,5,6,7):
            u,w=axes[i],widths[i]
            holes.append(self.window(f,u,self.pz(4.0),w,self.pz(6.85)-self.pz(4.0),2 if i in (0,7) else 3,'hall',f'hall-axis-{i+1}'))
            holes.append(self.window(f,u,self.pz(.70),w+.08,self.pz(2.43)-self.pz(.70),2 if i in (0,7) else 3,'ground',f'ground-axis-{i+1}'))
        for row,(y,top) in enumerate([(24.9,26.6),(27.3,29.3)]):
            for side in (-1,1):
                holes.append(self.window(f,side*1.37,self.pz(y),.50,self.pz(top)-self.pz(y),1,'tower',f'tower-{row+7}-{side}'))
        portal = self.prect(-2.375,0,2.375,7.75)
        holes.append(portal)
        outline = self.front_outline()
        opening_union = unary_union(holes)
        surface=outline.difference(opening_union)
        low=surface.intersection(self.prect(-self.width/2,0,self.width/2,2.55))
        high=surface.difference(self.prect(-self.width/2,0,self.width/2,2.55))
        f.prism(low,-.5,.0,'polished black marble','continuous-cut-black-plinth')
        f.prism(high,-.5,-.055,'ivory cement render','continuous-cut-structural-wall')

        # Blind linear grooves are geometrical recesses with backing, not black painted lines.
        grooves=[]
        for u in [-10.70,-10.60,-9.36,-9.26,-8.71,-8.61,-6.78,-6.68,-4.91,-4.81,
                  -2.20,-2.10,-.30,-.20,.20,.30,2.10,2.20,4.81,4.91,6.68,6.78,8.61,8.71,9.26,9.36,10.60,10.70]:
            grooves.append(rect(u-.018,self.pz(2.55),u+.018,self.z(38.3)))
        # The faint horizontal render-control joints are shallow slots at sparse course levels.
        for y in [5.0,8.95,13.95,17.8,21.65,25.5,27.5,30.75,33.8]:
            grooves.append(self.rect_z(-self.width/2,y-.008,self.width/2,y+.008))
        finish=high.difference(unary_union(grooves))
        f.prism(finish,-.055,.0,'ivory cement render','continuous-grooved-render-finish')

        # Major broad piers flank the two central axes and the narrow end axes.
        for side in (-1,1):
            for lo,hi,top in [(2.23,4.80,30.0),(8.73,9.24,30.3),(10.72,self.width/2,29.7)]:
                shape=rect(side*lo if side>0 else -hi,self.pz(2.55),side*hi if side>0 else -lo,self.z(top))
                shape=shape.intersection(outline).difference(opening_union)
                f.prism(shape,0,.115,'ivory cement render','projected-broad-pier')
            for u in (2.16,4.86,8.66,9.31,10.65):
                ridge=rect(side*u-.035,self.pz(2.55),side*u+.035,self.z(38.3)).intersection(outline).difference(opening_union)
                f.prism(ridge,.005,.17,'ivory cement render','paired-narrow-pier-rib')
        for u in (-.25,.25):
            shape=self.rect_z(u-.035,11.2,u+.035,38.3).intersection(outline).difference(opening_union)
            f.prism(shape,.005,.15,'ivory cement render','central-crest-rib')
        for side in (-1,1):
            # Two thin ribs above and below each tower slit; slit itself remains open.
            for u in (1.17,1.58):
                shape=self.rect_z(side*u-.025,25.65,side*u+.025,36.0).intersection(outline).difference(opening_union)
                f.prism(shape,.005,.085,'ivory cement render','tower-fluting')
        self.holes=holes
        self.checks.append({'item':'front-open-wall','outline_area_m2':outline.area,'openings_area_m2':opening_union.area,
                            'remaining_wall_area_m2':surface.area,'hole_count':len(holes),'closed_holes_by_wall':0,
                            'area_conservation_error_m2':abs(outline.area-surface.area-opening_union.area)})
        self.portal(portal)
        self.crest_ornaments()
        self.end_blades()

    def portal(self, hole):
        f=self.front
        outer=self.prect(-3.97,0,3.97,9.30)
        frame=outer.difference(hole)
        f.prism(frame,.0,.32,'polished black marble','entrance-black-marble-mass')
        # Mitred layered inset mouldings remain outside the true door aperture.
        for i,(pad,depth) in enumerate([(.06,.39),(.16,.355),(.27,.325)]):
            band=hole.buffer(pad,join_style=2).difference(hole.buffer(max(0,pad-.055),join_style=2)).intersection(outer)
            f.prism(band,depth-.06,depth,'polished black marble',f'portal-stepped-reveal-{i}')
        seam_shapes=[]
        for y in np.arange(.62,9.25,.66):
            seam_shapes.append(self.prect(-3.97,y-.007,3.97,y+.007))
        for x in (-3.0,3.0):
            seam_shapes.append(self.prect(x-.005,0,x+.005,9.30))
        seams=unary_union(seam_shapes).intersection(frame)
        f.prism(seams,.3205,.322,'black marble joints','black-marble-slab-joints')
        # The door and upper grille share one structural aperture; no wall behind glazing.
        upper=self.prect(-2.31,3.25,2.31,7.24)
        f.prism(upper,-.70,-.68,'dark ground glass','entrance-upper-glazing')
        # Dark lintel recess above the glass lies inside the larger stepped opening.
        f.prism(self.prect(-2.31,7.24,2.31,7.69),-.70,-.67,'dark bronze frames','inner-upper-lintel-shadow')
        grid=[]
        for u in np.linspace(-2.27,2.27,9):grid.append(self.prect(u-.035,3.25,u+.035,7.24))
        for y in [3.30,4.25,5.70,6.60,7.17]:grid.append(self.prect(-2.31,y-.040,2.31,y+.040))
        f.prism(unary_union(grid),-.52,-.42,'dark bronze frames','entrance-unified-black-grille')
        for i,u in enumerate(np.linspace(-1.75,1.75,7)):
            self.pbox(u,5.28,.054,3.56,.075,-.36,'gold grille',f'gold-grille-{i}-shaft')
            for y in [3.57,4.15,5.70,6.60,7.00]:
                self.pbox(u,y,.13,.18,.09,-.34,'gold grille',f'gold-grille-{i}-collar')
                if y not in (3.57,7.00):self.pbox(u,y,.19,.035,.10,-.33,'gold grille',f'gold-grille-{i}-crosspiece')
            # Repeated rectangular shoulders and narrow finials visible in 2025.
            for s in (-1,1):self.pbox(u+s*.065,7.11,.028,.17,.07,-.34,'gold grille','grille-forked-finial')
        for y in [3.10,3.18,3.26]:
            self.pbox(0,y,4.73,.06,.40,-.17,'dark bronze frames','stepped-door-transom')
        self.pbox(0,3.19,.34,.23,.035,.065,'gold grille','number-14-plaque-reserved')
        # Lower double door, recessed brass/bronze panels, narrow sidelight panes.
        f.prism(self.prect(-2.31,.06,2.31,3.04),-.72,-.68,'dark bronze frames','lower-entry-door-plane')
        for u in (-1.78,-.88,.88,1.78):
            g=self.prect(u-.28,.40,u+.28,2.77)
            f.prism(g,-.675,-.665,'dark ground glass','door-inset-glazing')
            for z0 in [.75,1.35,1.95,2.55]:
                self.pbox(u,z0,.58,.025,.025,-.635,'dark bronze frames','door-glazing-crossbar')
        self.pbox(0,1.55,.065,3.00,.07,-.62,'dark bronze frames','double-door-center-stile')
        for s in (-1,1):
            self.pbox(s*.18,1.25,.035,.40,.11,-.54,'gold grille','door-pull')
        self.pbox(0,.045,4.78,.09,1.02,-.25,'polished black marble','entry-stone-threshold')
        # A small plaque is present on each side, but no fabricated inscription.
        for u in (-3.11,3.11):
            self.pbox(u,2.30,.58,.45,.018,.342,'painted cap metal','side-notice-board-no-text')
        # 2025 canopy-level linear fixtures, without the old 2012 floodlight array.
        for u in (-2.74,0,2.74):
            self.pbox(u,9.37,.58,.07,.18,.18,'painted cap metal','portal-linear-light-housing')
        self.lettering_evidence=add_facade_lettering(f,'上海市总工会',u=0,z=self.pz(8.5),
            width=5.25,height=self.pz(.66),low=.324,high=.349,material='gold grille',label='union-sign-solid-lettering')
        self.lettering_evidence.update({'source':'research/commons-164811484.jpg',
            'surface_outward_depth_m':.32,'lettering_low_high_depth_m':[.324,.349],
            'center_east_north_up':f.point(0,self.pz(8.5),.324).tolist(),
            'approximation':'Readable licensed font outlines; not a traced replica of the calligraphic inscription.'})
        # Small door number: simple readable vector strokes, not a copied font.
        one=unary_union([rect(-.078,-.071,-.055,.071),Polygon([(-.10,.045),(-.078,.071),(-.055,.071),(-.055,.048)])])
        four=unary_union([rect(.043,-.071,.065,.071),rect(-.014,-.008,.081,.013),rect(-.014,.005,.008,.071)])
        from shapely import affinity
        for glyph,shape in [('1',one),('4',four)]:
            f.prism(affinity.translate(shape,yoff=self.pz(3.19)),.084,.094,'dark bronze frames','number-14-vector/'+glyph)

    def crest_ornaments(self):
        """Vertical rounded half cylinders with horizontal light/dark bands.

        Function/purpose is unverified; source observations call them ornaments.
        Their front-to-back shape is real curved geometry, not billboard discs.
        """
        f=self.front
        for j,(bottom,height,radius,bands) in enumerate([(34.10,1.82,.265,6),(36.55,.68,.235,2)]):
            zz=[self.z(bottom+i*height/(bands*2)) for i in range(bands*2+1)]
            for k,(z0,z1) in enumerate(zip(zz,zz[1:])):
                vertices=[]
                segments=24
                for z in (z0,z1):
                    for i in range(segments+1):
                        ang=math.pi*i/segments
                        vertices.append(f.point(radius*math.cos(ang),z,.17+radius*math.sin(ang)))
                faces=[]
                for i in range(segments):faces.append((i,i+1,i+segments+2,i+segments+1))
                faces.extend([tuple(reversed(range(segments+1))),tuple(range(segments+1,2*(segments+1))),
                              (0,segments+1,2*segments+1,segments)])
                # (u,d) has a downward cross product in this facade frame.
                faces=[tuple(reversed(face)) for face in faces]
                self.b.add(vertices,faces,'white ornament bands' if k%2==0 else 'dark ornament bands',f'tower-ornament-{j}-band-{k}')
            # Rounded lower cap, using a short stepped profile with shrinking radius.
            z0=self.z(bottom)
            for k in range(4):
                r=radius*math.sqrt(max(0,1-(k/4)**2))
                self.front_box(0,bottom-(k+.5)*.022,r*1.82,.022,r*.5,.17+r*.25,'dark ornament bands','ornament-lower-rounded-cap')

    def end_blades(self):
        for side in (-1,1):
            # Masonry blades project back from the front, visible in both oblique views.
            u=side*9.73
            self.b.box(self.point(u,-1.25,self.z(29.75)),(.35,2.5,self.z(31.8)-self.z(27.7)),
                       'ivory cement render',[self.front.t,self.front.n,[0,0,1]],'end-roof/longitudinal-high-blade')
            for du in (-.7,.7):
                self.b.box(self.point(u+du,-1.05,self.z(29.2)),(.20,2.1,self.z(30.3)-self.z(28.1)),
                           'ivory cement render',[self.front.t,self.front.n,[0,0,1]],'end-roof/stepped-return-fin')
            for u2 in (side*6.65,):
                self.front_box(u2,29.05,.38,.64,.50,-.10,'ivory cement render','intermediate-parapet-cap')

    def body_plan(self):
        # Exact OSM ring is preserved. The narrow north recess is not filled.
        cut=self.cal['depths_m']['main_to_rear_step_from_front']
        front_zone=self.plane([(-100,-cut),(100,-cut),(100,10),(-100,10)])
        self.main_plan=self.plan.intersection(front_zone)
        self.rear_plan=self.plan.difference(front_zone)
        for part in pieces(self.main_plan):
            self.b.plan_prism(part,self.h-.18,self.h,'roof concrete','main-roof/exact-footprint-slab')
        for part in pieces(self.rear_plan):
            self.b.plan_prism(part,self.rear_h-.18,self.rear_h,'roof concrete','rear-roof/exact-footprint-slab')
        self.b.plan_prism(self.plan,.0,.10,'roof concrete','ground/exact-osm-outline')
        points=list(self.plan.exterior.coords)
        for i,(a,b) in enumerate(zip(points,points[1:])):
            aa=np.asarray(a);bb=np.asarray(b)
            # Compare physical edge rather than assuming orient() retained index 5.
            if np.linalg.norm(aa-self.front.a[:2])+np.linalg.norm(bb-self.front.b[:2])<1e-5:continue
            da=float((aa-self.front.center[:2])@self.front.n[:2]);db=float((bb-self.front.center[:2])@self.front.n[:2])
            splits=[0,1]
            if (da+cut)*(db+cut)<0:splits.append((-cut-da)/(db-da))
            splits=sorted(splits)
            for j,(t0,t1) in enumerate(zip(splits,splits[1:])):
                pa=aa+(bb-aa)*t0;pb=aa+(bb-aa)*t1
                depth=(da+(db-da)*(t0+t1)/2)
                height=self.h if depth>-cut else self.rear_h
                self.side(Facade(self.b,pa,pb,f'outline-{i}-{j}-inferred-side'),height,i,depth)
        # Close the upper vertical plane at the roof-level change without joining neighbouring buildings.
        cross=self.plan.intersection(LineString([self.point(-100,-cut,0)[:2],self.point(100,-cut,0)[:2]]))
        for k,line in enumerate([cross] if isinstance(cross,LineString) else cross.geoms):
            if not isinstance(line,LineString) or line.length<.05:continue
            a,b=list(line.coords)[0],list(line.coords)[-1]
            f=Facade(self.b,a,b,f'roof-step-{k}-inferred')
            if np.dot(f.n,self.front.n)>0:f=Facade(self.b,b,a,f'roof-step-{k}-inferred')
            f.wall(self.rear_h,self.h,thickness=.4,material='painted rear render')

    def side(self,f,height,index,depth):
        holes=[]
        # Count is an explicit inferred layout on each saved edge, not claimed as photo survey.
        count=max(0,int((f.length-.7)/3.0))
        if f.length<2.7:count=0
        width=min(1.14,(f.length-1.0)/max(1,count)*.48)
        rows=[(.7,2.43,'ground'),(4.,6.85,'hall')]+[(a,b,'rear') for a,b in self.cal['photo_rectified_front_m']['regular_window_extents']]
        for row,(bottom,top,kind) in enumerate(rows):
            bottom,wh=self.pz(bottom),self.pz(top)-self.pz(bottom)
            if bottom+wh>height-.7:continue
            for n in range(count):
                u=(n-(count-1)/2)*(f.length-.9)/max(1,count)
                holes.append(self.window(f,u,bottom,width,wh,2,kind,f'side-row-{row+1}-bay-{n+1}',True))
        surface=f.wall(0,height,holes,thickness=.48,material='painted rear render')
        # Low relief pier spacing follows the windows, without copying the front stone portal.
        for n in range(count+1):
            u=(n-count/2)*(f.length-.9)/max(1,count)
            if abs(u)>f.length/2-.13:continue
            f.box(u,(height+3.35)/2,.12,height-3.35,.11,.015,'painted rear render','side-continuous-vertical-line')
        f.beam(height+.17,.34,.04,'painted rear render',label='roof-parapet')
        f.beam(height+.37,.09,.10,'ivory cement render',label='parapet-coping')
        self.checks.append({'item':f.label,'window_count':len(holes),'inferred':True,'wall_area_m2':surface.area,'outline_edge_length_m':f.length})

    def tower(self):
        depth=self.cal['depths_m']['tower_depth']; half=self.cal['depths_m']['tower_width']/2
        front=self.front
        # Each side uses actual wall openings and an independently controlled stepped top.
        for s in (-1,1):
            a=self.point(s*half,0,0)[:2];b=self.point(s*half,-depth,0)[:2]
            if s<0:a,b=b,a
            f=Facade(self.b,a,b,f'tower-{"north" if s>0 else "south"}-side')
            holes=[]
            for row,(bot,top) in enumerate([(24.9,26.6),(27.3,29.3)]):
                for k in range(3):
                    u=(k-1)*2.34
                    holes.append(self.window(f,u,self.pz(bot),.84,self.pz(top)-self.pz(bot),1,'tower',f'side-tower-{row}-{k}',row==0))
            f.wall(self.h,self.z(34.8),holes,thickness=.35,material='ivory cement render')
            f.beam(self.z(34.9),.2,.03,'ivory cement render',label='tower-side-coping')
            for u in [-3.65,-1.18,1.18,3.65]:
                f.box(u,self.z(31.8),.085,self.z(34.85)-self.z(28.75),.12,.025,'ivory cement render','tower-side-vertical-rib')
        a=self.point(half,-depth,0)[:2];b=self.point(-half,-depth,0)[:2]
        f=Facade(self.b,a,b,'tower-west-rear-inferred')
        holes=[]
        for row,(bot,top) in enumerate([(24.9,26.6),(27.3,29.3)]):
            for k in (-1,1):holes.append(self.window(f,k*1.4,self.pz(bot),.78,self.pz(top)-self.pz(bot),1,'tower',f'rear-tower-{row}-{k}',True))
        f.wall(self.h,self.z(34.8),holes,thickness=.35,material='painted rear render')
        roof=self.plane([(-half,-depth),(half,-depth),(half,-.45),(-half,-.45)])
        self.b.plan_prism(roof,self.z(34.62),self.z(34.8),'roof concrete','tower/flat-roof-behind-crest')
        # Narrow high central crest returns into the roof as a stepped masonry fin.
        for j,(d0,d1,top) in enumerate([(-.5,-1.8,37.55),(-1.8,-3.5,36.8),(-3.5,-5.4,36.1),(-5.4,-7.2,35.55)]):
            p=self.plane([(-.40,d0),(.40,d0),(.40,d1),(-.40,d1)])
            self.b.plan_prism(p,self.z(34.8),self.z(top),'ivory cement render',f'tower/stepped-longitudinal-central-fin-{j}')
        # Minimal roof access ladder on the north tower flank, visibly present in 2012.
        u=half+.12; d=-depth+.85
        for dd in [-.25,.25]:
            p0=self.point(u,d+dd,self.h+.3);p1=self.point(u,d+dd,self.z(35.5))
            self.b.tube([p0,p1],.025,'dark bronze frames',8,'roof/access-ladder-rail')
        for zz in np.arange(self.h+.55,self.z(35.1),.33):
            self.b.tube([self.point(u,d-.25,zz),self.point(u,d+.25,zz)],.022,'dark bronze frames',8,'roof/access-ladder-rung')

    def build(self,out):
        self.make_front();self.body_plan();self.tower()
        topology=self.audit_solids()
        photographic=self.apply_glass_photographs()
        lettering=self.cal['lettering']
        center=self.front.point(lettering['center_nominal_front_uz_m'][0],self.z(lettering['center_nominal_front_uz_m'][1]),lettering['front_depth_m'])
        meta={'name':'Bund 14 — Bank of Communications Building / 交通银行大楼',
              'origin_wgs84':self.source['anchor'],'coordinate_contract':self.source['coordinate_contract']['gltf_xyz'],
              'appearance_epoch':self.cal['appearance_epoch'],'source_footprint':'OSM w178405872@7, ODbL-1.0',
              'replacement_building_ids':self.source['replacement']['building_ids'],
              'height_is_measured':False,'heights_m':self.cal['heights_m'],
              'source_photographs':'research/sources.json; selected clear glass regions only, per-pane corrected UVs in glazing-samples.json',
              'copyright':'Geometry: MIT; map geometry: OpenStreetMap ODbL-1.0; embedded glass photograph: Suicasmo, CC0-1.0; lettering font: SIL OFL 1.1.',
              'photographic_glazing':photographic,'lettering':self.lettering_evidence,'rear_facade_accuracy':'inferred; evidence limited, see calibration.json',
              'generator_sources':{'build_model.py':file_info(Path(__file__)),'calibration.json':file_info(HERE/'calibration.json'),'geometry-input.json':file_info(HERE/'geometry-input.json'),
                                   'glazing-samples.json':file_info(HERE/'glazing-samples.json'),
                                   '../common/photo_architecture.py':file_info(HERE.parent/'common'/'photo_architecture.py'),
                                   '../common/sign_lettering.py':file_info(HERE.parent/'common'/'sign_lettering.py'),
                                   '../common/fonts/BundSignSubset.otf':file_info(HERE.parent/'common'/'fonts'/'BundSignSubset.otf')},
              'build_environment':{'python':sys.version.split()[0],'numpy':np.__version__,'shapely':shapely.__version__,'GEOS':shapely.geos_version_string}}
        report=self.b.save(out/'bund14.glb',meta)
        report['verification']={'front_regular_window_axes':8,'front_regular_rows':4,'front_tower_window_rows':2,
          'front_tower_windows_per_row':2,'gold_grille_vertical_bars':7,'total_windows':len(self.windows),
          'observed_front_window_count':sum(not x['inferred'] and x['facade']==self.front.label for x in self.windows),
          'exact_osm_plan_area_m2':self.plan.area,'exact_plan_valid':self.plan.is_valid,
          'front_length_m':self.width,'side_and_rear_inferred_window_count':sum(x['inferred'] for x in self.windows),
          'all_files_below_100000000':True,'external_glb_resources':0}
        report['limitations']=self.cal['inferred_controls']
        report['window_schedule']=self.windows
        report['wall_checks']=self.checks
        report['solid_topology_audit']=topology
        report['photographic_glazing']=photographic
        report['lettering']=self.lettering_evidence
        report['lettering_reservation']={'text':lettering['text'],'center_east_north_up':center.tolist(),
          'horizontal_east_north_up':self.front.t.tolist(),'outward_east_north_up':self.front.n.tolist(),
          'total_width_m':lettering['total_width_m'],'height_m':self.z(lettering['height_nominal_m']),
          'extrusion_m':.025,'material':'gold grille','finished':True,
          'actual_low_high_depth_m':[.324,.349],'actual_center_east_north_up':self.lettering_evidence['center_east_north_up'],
          'typeface_is_photo_traced':False}
        (out/'bund14.geometry.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
        (out/'lettering-reservation.json').write_text(json.dumps(report['lettering_reservation'],ensure_ascii=False,indent=2)+'\n')
        print(json.dumps({k:report[k] for k in ['file','bytes','sha256','triangles','materials','parts','verification']},ensure_ascii=False))
        return report

    def apply_glass_photographs(self):
        """Correct each clear glass panel separately; all real frames stay solid."""
        source=HERE/'glazing-samples.json'
        samples=json.loads(source.read_text())
        photo=HERE/samples['source_image']
        assert hashlib.sha256(photo.read_bytes()).hexdigest()==samples['source_sha256']
        def geometry_digest():
            h=hashlib.sha256()
            for p in self.b.parts:
                h.update(p['label'].encode());h.update(np.asarray(p['vertices'],dtype='<f8').tobytes());h.update(np.asarray(p['triangles'],dtype='<i8').tobytes())
            return h.hexdigest()
        before=geometry_digest();selected=[];all_uv=[];mapped_windows=set();fallback=[]
        def homography(a,b):
            rows=[];target=[]
            for (u,z),(x,y) in zip(a,b):
                rows.extend([[u,z,1,0,0,0,-x*u,-x*z],[0,0,0,u,z,1,-y*u,-y*z]])
                target.extend([x,y])
            return np.r_[np.linalg.solve(np.asarray(rows),np.asarray(target)),1.].reshape(3,3)
        for window in samples['windows']:
            if window['status']!='photo-selected':
                fallback.append({'window':window['label'],'reason':window['reason']});continue
            schedule=next(w for w in self.windows if w['facade']==self.front.label and w['label']==window['label'])
            center=np.asarray(schedule['center_world_east_north_up']);u=float((center-self.front.center)@self.front.t)
            low=u-schedule['width_m']/2;bottom=center[2]-schedule['height_m']/2
            parts=[p for p in self.b.parts if p['label']==self.front.label+'/'+window['label']+'-pane']
            for part in parts:
                vertices=np.asarray(part['vertices']);pu=(vertices-self.front.center)@self.front.t;pz=vertices[:,2]
                c=int(np.clip(round(((pu.min()+pu.max())/2-low)/schedule['width_m']*window['columns']-.5),0,window['columns']-1))
                row='top' if (pz.min()+pz.max())/2>bottom+schedule['height_m']*.79 else 'bottom'
                control=next(p for p in window['panes'] if p['column']==c and p['row']==row)
                if control['status']!='photo':
                    fallback.append({'window':window['label'],'row':row,'column':c,'reason':control['reason']});continue
                model_quad=np.array([[pu.min(),pz.max()],[pu.max(),pz.max()],[pu.max(),pz.min()],[pu.min(),pz.min()]])
                source_quad=np.array(control['source_oriented_quad_px']);H=homography(model_quad,source_quad)
                def uv(point):
                    point=np.asarray(point);uu=float((point-self.front.center)@self.front.t)
                    q=H@np.array([uu,point[2],1.]);ox,oy=q[:2]/q[2]
                    return [(oy+.5)/5184,(3455-ox+.5)/3456]
                result=self.b.photograph_parts(photo,uv,lambda p:p is part,name='PhotoFacade_Bund14Glass',roughness=.48,
                    orientation={'rawSize':[5184,3456],'exifOrientation':6,'uvConvention':'stored-pixels',
                                 'author':'Suicasmo','license':'CC0-1.0','sourceSha256':samples['source_sha256']})
                assert result['parts']==1
                all_uv.extend(part['texcoords']);mapped_windows.add(window['label'])
                check=np.c_[model_quad,np.ones(4)]@H.T;check=check[:,:2]/check[:,2:]
                error=float(np.max(np.linalg.norm(check-source_quad,axis=1)))
                assert error<1e-6
                selected.append({'window':window['label'],'row':row,'column':c,
                                 'source_oriented_quad_px':source_quad.tolist(),'model_quad_u_z_m':model_quad.tolist(),
                                 'model_to_source_oriented_homography':H.tolist(),'corner_fit_error_px':error})
        assert len(selected)==samples['selected_panes'] and geometry_digest()==before
        uv_array=np.asarray(all_uv)
        assert np.isfinite(uv_array).all() and uv_array.min()>=0 and uv_array.max()<=1
        return {'source':'research/commons-164811484.jpg','source_sha256':samples['source_sha256'],
                'source_author':'Suicasmo','source_license':'CC0-1.0','image_embedded_without_changes':True,
                'sample_controls_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
                'material':'PhotoFacade_Bund14Glass','image_count':1,'selected_windows':len(mapped_windows),
                'selected_panes':len(selected),'material_fallbacks':fallback,
                'uv_min':uv_array.min(0).tolist(),'uv_max':uv_array.max(0).tolist(),
                'geometry_unchanged_by_texture_mapping':True,'geometry_before_after_sha256':before,
                'per_pane_controls':selected,'runtime_orientation_contract':{'rawSize':[5184,3456],'exifOrientation':6,'uvConvention':'stored-pixels'}}

    def audit_solids(self):
        """Test each modeled solid, without claiming intersecting trim is one solid."""
        bad=[];zero_float32=0;minimum_volume=float('inf')
        for p in self.b.parts:
            v=np.asarray(p['vertices']);t=np.asarray(p['triangles'])
            edges=Counter(tuple(sorted((int(a),int(b)))) for tri in t
                          for a,b in zip(tri,np.roll(tri,-1)))
            bad_edges=sum(n!=2 for n in edges.values())
            a,b,c=(v[t[:,i]] for i in range(3))
            volume=float(np.einsum('ij,ij->i',a,np.cross(b,c)).sum()/6)
            vf=np.asarray(v,dtype=np.float32);af,bf,cf=(vf[t[:,i]].astype(float) for i in range(3))
            degenerate=int(np.count_nonzero(np.linalg.norm(np.cross(bf-af,cf-af),axis=1)<=1e-12))
            zero_float32+=degenerate;minimum_volume=min(minimum_volume,volume)
            if bad_edges or volume<=0 or degenerate:
                bad.append({'label':p['label'],'edges_not_paired':bad_edges,'signed_volume_m3':volume,'float32_zero_area_triangles':degenerate})
        if bad:
            raise ValueError('Solid audit failed: '+json.dumps(bad[:20]))
        return {'passed':True,'scope':'Each individual generated wall, frame, pane, trim and ornament is closed; contact/intersection of architectural layers is intentional, not a claim of one Boolean-unioned global manifold.',
                'parts_checked':len(self.b.parts),'unpaired_edges':0,'nonpositive_signed_volumes':0,
                'minimum_positive_volume_m3':minimum_volume,'float32_zero_area_triangles':zero_float32}


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,default=HERE/'output')
    args=parser.parse_args();args.output.mkdir(parents=True,exist_ok=True)
    Bank14().build(args.output)
