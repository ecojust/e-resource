"""Jinshanwei enclosing walls, gate and pavilion exterior. agent, MIT.

Construct in architectural XYZ metres. Geographic rotation is performed only
after all geometry and metric UVs are complete. Hidden architecture is marked
as estimated in the design and the output feature manifest.
"""
import math
import sys
from pathlib import Path
import numpy as np
from shapely.geometry import Polygon, box as rect
from shapely import constrained_delaunay_triangles
from shapely.geometry.polygon import orient
from shapely.ops import unary_union
from shapely.affinity import scale, translate
from fontTools.ttLib import TTFont
from fontTools.pens.basePen import BasePen
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE/'common'))
from photo_architecture import Builder, Facade, opening
from brick_material import brick_palette


PALETTE = {
    **brick_palette(),
    'worn coping': {'color': [.30,.32,.31], 'roughness': .91},
    'worn paving': {'color': [.29,.305,.29], 'roughness': .95},
    'stone joints': {'color': [.12,.13,.125], 'roughness': .96},
    'arch stone 0': {'color': [.12,.14,.135], 'roughness': .91},
    'arch stone 1': {'color': [.15,.17,.16], 'roughness': .94},
    'arch stone 2': {'color': [.10,.115,.11], 'roughness': .92},
    'pale plaque stone': {'color': [.55,.54,.49], 'roughness': .93},
    'incised plaque dark': {'color': [.17,.19,.17], 'roughness': .91},
    'red timber': {'color': [.145,.045,.027], 'roughness': .80},
    'timber edges': {'color': [.205,.074,.040], 'roughness': .82},
    'dark timber': {'color': [.060,.040,.030], 'roughness': .88},
    'door boards': {'color': [.070,.050,.035], 'roughness': .92},
    'iron fittings': {'color': [.055,.060,.055], 'roughness': .65, 'metallic': .22},
    'recessed glazing': {'color': [.085,.12,.13], 'roughness': .32, 'metallic': .08},
    'light wall infill': {'color': [.60,.59,.54], 'roughness': .95},
    'roof underlay': {'color': [.09,.11,.105], 'roughness': .94},
    'roof tile 0': {'color': [.19,.23,.22], 'roughness': .88},
    'roof tile 1': {'color': [.22,.26,.25], 'roughness': .90},
    'roof tile 2': {'color': [.165,.20,.19], 'roughness': .92},
    'ridge ceramic': {'color': [.25,.29,.275], 'roughness': .88},
}


class GlyphPen(BasePen):
    def __init__(self, gs):
        super().__init__(gs); self.paths=[]; self.current=[]
    def _moveTo(self,p): self.current=[p]
    def _lineTo(self,p): self.current.append(p)
    def _curveToOne(self,a,b,c):
        p,a,b,c = map(np.asarray, [self._getCurrentPoint(),a,b,c])
        self.current.extend(tuple((1-t)**3*p+3*(1-t)**2*t*a+3*(1-t)*t*t*b+t**3*c)
                            for t in np.linspace(0,1,8)[1:])
    def _qCurveToOne(self,a,b):
        p,a,b=map(np.asarray,[self._getCurrentPoint(),a,b])
        self.current.extend(tuple((1-t)**2*p+2*(1-t)*t*a+t*t*b) for t in np.linspace(0,1,8)[1:])
    def _closePath(self):
        if len(self.current)>2:self.paths.append(self.current)
        self.current=[]
    def _endPath(self):self._closePath()


class Gatehouse:
    def __init__(self, design, lod=False):
        self.d=design;self.lod=lod;self.b=Builder(PALETTE);self.features=[]
        self.e=design['enclosure'];self.g=design['entry'];self.p=design['pavilion'];self.s=design['exterior_stair']
        self.hx=self.e['upper_width_m']/2;self.hy=self.e['upper_depth_m']/2
        self.gx=self.e['central_gate_bay_width_m']/2;self.project=self.e['central_gate_projection_m']
        self.walk=self.e['wall_walk_top_m'];self.floor=self.p['body_floor_m']
        self.points=[(-self.hx,-self.hy),(-self.gx,-self.hy),(-self.gx,-self.hy-self.project),
                     (self.gx,-self.hy-self.project),(self.gx,-self.hy),(self.hx,-self.hy),
                     (self.hx,self.hy),(-self.hx,self.hy)]
        self.footprint=Polygon(self.points)
        self.faces=[Facade(self.b,a,b,f'enclosure/edge-{i}') for i,(a,b) in enumerate(zip(self.points,self.points[1:]+self.points[:1]))]
        self.front=self.faces[2]

    def mark(self,kind,**kw):self.features.append({'kind':kind,**kw})

    def battered_mapper(self,f):
        outset=self.e['bottom_wall_outset_m'];top=self.walk-.10
        return lambda u,z,d:f.point(u,z,d+max(0.,1-z/top)*outset)

    def remove_horizontal(self,part,z):
        vertices=np.asarray(part['vertices'])
        part['triangles']=[tri for tri in part['triangles']
                           if not np.all(np.abs(vertices[list(tri),2]-z)<1e-8)]

    def top_surface(self,polygon,z,material,label):
        vertices=[];faces=[]
        for tri in constrained_delaunay_triangles(polygon).geoms:
            points=list(orient(tri,sign=1.).exterior.coords)[:3];start=len(vertices)
            vertices.extend((x,y,z) for x,y in points);faces.append((start,start+1,start+2))
        self.b.add(vertices,faces,material,label)

    def walls(self):
        hole=opening(0,self.g['threshold_m'],self.g['opening_width_m'],self.g['opening_height_m'],
                     self.g['semicircle_rise_m'],48 if not self.lod else 32)
        stair_end_y=self.s['lower_run_start_xy'][1]+(self.s['visible_lower_steps_estimate']+self.s['hidden_upper_steps_estimate'])*self.s['tread_m']+self.s['landing_depth_m']
        notch_y=stair_end_y+self.s['width_m']/2
        notch_width=self.s['width_m']+.10
        core_top=self.walk-.10
        for i,f in enumerate(self.faces):
            face=rect(-f.length/2,0,f.length/2,core_top)
            if i==2:face=face.difference(hole)
            self.b.prism(face,-self.e['upper_wall_walk_width_m'],0,self.battered_mapper(f),'original grey brick',f.label+'/solid-wall-with-real-gate-opening' if i==2 else f.label+'/battered-wall')
            # Remove the internal skin shared with the continuous wall-ring cap.
            self.remove_horizontal(self.b.parts[-1],core_top)
        inner=self.footprint.buffer(-self.e['upper_wall_walk_width_m'],join_style=2)
        pcx,pcy=self.p['center_architecture_xy'];phx=self.p['body_width_m']/2;phy=self.p['body_depth_m']/2
        pavilion_plan=rect(pcx-phx,pcy-phy,pcx+phx,pcy+phy)
        pavilion_support=pavilion_plan.intersection(inner)
        inner_border=inner.buffer(.20,join_style=2).difference(inner).difference(pavilion_plan)
        ring=self.footprint.difference(inner)
        parapet_plan=self.footprint.difference(self.footprint.buffer(-.64,join_style=2))
        notch=rect(-self.hx-1,notch_y-notch_width/2,-self.hx+1,notch_y+notch_width/2)
        parapet_plan=parapet_plan.difference(notch)
        self.mark('estimated_upper_stair_parapet_notch',wall_edge=7,centre_y_m=notch_y,width_m=notch_width,below_walk_wall_unchanged=True)
        # One continuous cap owns the exposed ring surface. Its internal bottom
        # and hidden top beneath parapets are absent, not separated by fake gaps.
        self.b.plan_prism(ring,core_top,self.walk,'original grey brick','enclosure/wall-ring-cap-side-skins')
        self.remove_horizontal(self.b.parts[-1],core_top);self.remove_horizontal(self.b.parts[-1],self.walk)
        self.top_surface(ring.difference(parapet_plan).difference(inner_border),self.walk,'worn paving','enclosure/single-owned-wall-walk-top')
        centre_mask=rect(-self.gx,-self.hy-self.project-1,self.gx,-self.hy+.64)
        centre=parapet_plan.intersection(centre_mask);wings=parapet_plan.difference(centre)
        for name,plan,height in [('wings',wings,self.e['wing_top_m']),('gate-bay',centre,self.e['central_gate_top_m'])]:
            start=len(self.b.parts)
            self.b.plan_prism(plan,self.walk,height-.10,'original grey brick',f'enclosure/{name}/continuous-parapet')
            for part in self.b.parts[start:]:self.remove_horizontal(part,self.walk);self.remove_horizontal(part,height-.10)
            start=len(self.b.parts)
            self.b.plan_prism(plan,height-.10,height,'worn coping',f'enclosure/{name}/single-owned-coping')
            for part in self.b.parts[start:]:self.remove_horizontal(part,height-.10)
        self.b.plan_prism(inner.difference(pavilion_support),self.e['inner_surface_m']-.18,self.e['inner_surface_m'],'worn paving','enclosure/estimated-inward-horizontal-surface')
        self.b.plan_prism(pavilion_support,self.e['inner_surface_m'],self.floor,'original grey brick','pavilion/estimated-support-plinth-over-low-inner-surface')
        self.mark('estimated_pavilion_support',bottom_m=self.e['inner_surface_m'],top_m=self.floor,
                  plan_xy=list(pavilion_support.exterior.coords),scope='Pavilion footprint intersect lower inward surface only; no duplicate plinth over existing wall walk',
                  covered_inner_surface_removed=True,inner_coping_not_run_through_pavilion=True,unobserved_structural_completion=True)
        self.b.plan_prism(inner_border,self.walk,self.walk+.25,'worn coping','enclosure/inner-edge-low-coping')
        self.remove_horizontal(self.b.parts[-1],self.walk)
        self.mark('enclosure',top_outline_xy=self.points,walk_top_m=self.walk,inner_surface_m=self.e['inner_surface_m'],inner_surface_estimated=True,ground_depth_pit=False,whole_enclosure_tiled_roof=False)
        self.mark('walk_surface_ownership_fix',wall_core_top_m=core_top,walk_top_m=self.walk,duplicate_exposed_walk_top_removed=True,shared_internal_horizontal_skins_removed=True,parapet_plan_unioned_before_extrusion=True)
        self.mark('entry_opening',width_m=self.g['opening_width_m'],height_m=self.g['opening_height_m'],bottom_m=self.g['threshold_m'],front_plane_y_m=-self.hy-self.project,opening_polygon_uz=list(hole.exterior.coords),closed_recessed_door=True,walk_through_claim=False)
        self.gate(hole)

    def gate(self,hole):
        f=self.front;mapper=self.battered_mapper(f);radius=self.g['opening_width_m']/2
        spring=self.g['threshold_m']+self.g['opening_height_m']-self.g['semicircle_rise_m']
        thickness=self.g['arch_ring_m'];count=24
        for i in range(count):
            a=i*math.pi/count+.006;b=(i+1)*math.pi/count-.006
            points=[]
            for r,angles in [(radius,np.linspace(a,b,4)),(radius+thickness,np.linspace(b,a,4))]:
                points.extend((r*math.cos(t),spring+r*math.sin(t)) for t in angles)
            self.b.prism(Polygon(points),0,.13,mapper,f'arch stone {i%3}',f'entry/arch-voussoir-{i:02d}')
        levels=12;dy=(spring-self.g['threshold_m'])/levels
        for side in [-1,1]:
            for i in range(levels):
                x0,x1=(radius,radius+thickness) if side>0 else (-radius-thickness,-radius)
                z0=self.g['threshold_m']+i*dy+.012;z1=self.g['threshold_m']+(i+1)*dy-.012
                self.b.prism(rect(x0,z0,x1,z1),0,.13,mapper,f'arch stone {(i+int(side>0))%3}',f'entry/jamb-{side}-{i:02d}')
        door=hole.buffer(-.035,join_style=2);recess=self.g['dark_closed_door_recess_m']
        self.b.prism(door,-recess-.12,-recess,mapper,'door boards','entry/recessed-closed-door')
        for i in range(13):
            x=-radius+(i+1)*self.g['opening_width_m']/14
            line=door.intersection(rect(x-.012,self.g['threshold_m'],x+.012,self.g['threshold_m']+self.g['opening_height_m']))
            if not line.is_empty:self.b.prism(line,-recess-.002,-recess+.012,mapper,'dark timber',f'entry/door-plank-seam-{i}')
        for j,z in enumerate([1.50,2.50,3.35]):
            strip=door.intersection(rect(-radius,z-.065,radius,z+.065))
            self.b.prism(strip,-recess+.013,-recess+.045,mapper,'iron fittings',f'entry/door-strap-{j}')
        if not self.lod:
            for side in [-1,1]:
                c=f.point(side*.28,2.1,-recess+.10)
                ring=[c+np.array([.11*math.cos(a),0,.11*math.sin(a)]) for a in np.linspace(0,2*math.pi,17)]
                self.b.tube(ring,.021,'iron fittings',6,f'entry/door-ring-{side}')
        self.plaque(mapper)
        self.mark('masonry_gate_detail',stone_back_depth_m=0,stone_front_relief_m=.13,wall_reveal_meets_stone_without_overlap=True,voussoirs=count,jamb_blocks=2*levels,plaque_text=self.g['plaque_text'],door_recess_m=recess,visible_arch_is_geometry=True)

    def plaque(self,mapper):
        w,h,z=self.g['plaque_width_m'],self.g['plaque_height_m'],self.g['plaque_center_height_m']
        outer=rect(-w/2,z-h/2,w/2,z+h/2)
        self.b.prism(outer,-.02,.105,mapper,'pale plaque stone','entry/plaque-stone')
        border=outer.buffer(-.055,join_style=2).difference(outer.buffer(-.085,join_style=2))
        self.b.prism(border,.106,.12,mapper,'incised plaque dark','entry/plaque-border')
        font=TTFont(HERE/'plaque-glyphs.otf');gs=font.getGlyphSet();cmap=font.getBestCmap()
        for i,ch in enumerate(self.g['plaque_text']):
            pen=GlyphPen(gs);gs[cmap[ord(ch)]].draw(pen);poly=Polygon()
            for points in pen.paths:poly=poly.symmetric_difference(Polygon(points).buffer(0))
            x0,y0,x1,y1=poly.bounds;k=.72/max(x1-x0,y1-y0)
            poly=scale(poly,xfact=k,yfact=k,origin=(0,0));x0,y0,x1,y1=poly.bounds
            poly=translate(poly,xoff=(i-.5)*1.12-(x0+x1)/2,yoff=z-(y0+y1)/2)
            self.b.prism(poly,.107,.119,mapper,'incised plaque dark',f'entry/plaque-glyph-{ch}')
        self.mark('licensed_vector_plaque',text=self.g['plaque_text'],font_subset='Agent Gate Plaque Subset derived from Noto Serif CJK SC / SIL OFL1.1',exact_photographic_calligraphy=False)

    def low_steps(self):
        n=self.g['front_low_steps'];rise=self.g['step_total_rise_m']/n;tread=self.g['step_depth_m'];width=self.g['step_width_m']
        wall_y=-self.hy-self.project-self.e['bottom_wall_outset_m'];outer_y=wall_y-n*tread
        for i in range(n):
            a=outer_y+i*tread;b=outer_y+(i+1)*tread
            self.b.plan_prism(rect(-width/2,a,width/2,b),0,(i+1)*rise,'worn paving',f'front-steps/riser-{i+1}')
        threshold_skin_y=float(self.battered_mapper(self.front)(0,self.g['threshold_m'],0)[1])
        self.b.plan_prism(rect(-width/2,wall_y,width/2,threshold_skin_y),0,self.g['threshold_m'],'worn paving','front-steps/threshold-landing')
        self.mark('front_steps',count=n,rise_each_m=rise,tread_m=tread,top_m=self.g['threshold_m'],stair_walkability_verified=False)

    def leaf(self,f,left,width,label,coarse=False):
        bottom=self.floor+.22;top=self.p['body_eave_m']-.32
        panel=rect(left,bottom,left+width,top)
        lattice_bottom=bottom+.72
        nx,ny=(3,4) if coarse else (4,12)
        x0,x1=left+.10,left+width-.10;z0,z1=lattice_bottom,top-.11
        holes=[]
        for i in range(nx):
            for j in range(ny):
                xa=x0+(x1-x0)*i/nx+.018;xb=x0+(x1-x0)*(i+1)/nx-.018
                za=z0+(z1-z0)*j/ny+.017;zb=z0+(z1-z0)*(j+1)/ny-.017
                holes.append(rect(xa,za,xb,zb))
        grid=panel.difference(unary_union(holes))
        f.prism(grid,-.15,.02,'red timber',label+'/pierced-frame-and-lattice')
        f.prism(rect(left+.08,bottom+.08,left+width-.08,top-.08),-.205,-.19,'recessed glazing',label+'/recessed-glazing')
        low=rect(left+.10,bottom+.10,left+width-.10,lattice_bottom-.12)
        f.prism(low,-.005,.035,'dark timber',label+'/lower-solid-panel')
        if not self.lod:
            bead=low.difference(low.buffer(-.026,join_style=2))
            f.prism(bead,.036,.056,'timber edges',label+'/lower-panel-bead')
        self.mark('front_window_leaf',label=label,clear_grid_apertures=nx*ny,leaf_bounds_uz=list(panel.bounds),same_apertures_in_lod=True)

    def pavilion(self):
        cx,cy=self.p['center_architecture_xy'];hx=self.p['body_width_m']/2;hy=self.p['body_depth_m']/2
        points=[(cx-hx,cy-hy),(cx+hx,cy-hy),(cx+hx,cy+hy),(cx-hx,cy+hy)]
        faces=[Facade(self.b,a,b,f'pavilion/side-{i}') for i,(a,b) in enumerate(zip(points,points[1:]+points[:1]))]
        front=faces[0];z0=self.floor;z1=self.p['body_eave_m']
        post_top=z1-.32  # Posts meet the upper beam underside without duplicate side skins.
        # Union the four beams before extrusion: each corner has one top and
        # underside, while the occupied volume matches the four original beams.
        beam_plans=[Polygon([f.point(u,0,d)[:2] for u,d in
                    [(-f.length/2-.10,-.17),(f.length/2+.10,-.17),
                     (f.length/2+.10,.17),(-f.length/2-.10,.17)]]) for f in faces]
        self.b.plan_prism(unary_union(beam_plans),post_top,z1,'red timber','pavilion/continuous-unioned-upper-beam')
        for i,f in enumerate(faces):
            f.box(0,z0+.10,f.length,.2,.28,0,'dark timber','sill-beam')
            if i:
                f.prism(rect(-f.length/2,z0+.2,f.length/2,z1-.32),-.20,-.02,'light wall infill','estimated-or-observed-light-infill')
                for u in [-f.length/2,0,f.length/2]:
                    f.box(u,(z0+post_top)/2,.20,post_top-z0,.30,.015,'red timber','side-timber-post')
        for x in [-hx,-3.10,3.10,hx]:
            front.box(x,(z0+post_top)/2,.25,post_top-z0,.35,.055,'red timber','front-post')
            front.box(x,z0+.14,.36,.28,.46,.045,'worn coping','front-post-base')
        # Six fine centre leaves; two coarse leaves on each side. Counts are
        # explicit approximations, not a claim to recovered historic joinery.
        for i in range(6):self.leaf(front,-2.98+i*(5.96/6)+.015,5.96/6-.03,f'pavilion/front/centre-leaf-{i}')
        for side in [-1,1]:
            a,b=(-hx+.16,-3.24) if side<0 else (3.24,hx-.16)
            for i in range(2):self.leaf(front,a+i*(b-a)/2+.015,(b-a)/2-.03,f'pavilion/front/side-{side}-leaf-{i}',True)
        # Visible eaves have timber support rhythm. Concealed connections are
        # generalized bracket arms, not a reconstruction of a specific dougong.
        for i,f in enumerate(faces):
            count=7 if i in [0,2] else 4
            for j,u in enumerate(np.linspace(-f.length/2+.35,f.length/2-.35,count)):
                pts=[f.point(u,z1-.75,0),f.point(u,z1-.55,.38),f.point(u,z1-.26,.95)]
                self.b.tube(pts,.085,'dark timber',6,f'pavilion/bracket-{i}-{j}/curved-arm')
                f.box(float(u),z1-.20,.22,.18,1.15,.49,'red timber',f'bracket-{j}/bearing')
                if not self.lod:f.box(float(u),z1-.57,.39,.15,.28,.29,'timber edges',f'bracket-{j}/cross-block')
        self.mark('pavilion_post_beam_join',upper_beam_footprints_unioned_before_extrusion=True,post_top_m=post_top,upper_beam_bottom_m=post_top,estimated_joinery=True,same_facing_overlap_removed=True)
        self.mark('pavilion',body_bounds_xy=[cx-hx,cy-hy,cx+hx,cy+hy],floor_m=z0,eave_m=z1,front_leaf_count=10,front_grid_apertures=336,side_rear_not_cloned=True,hidden_rear_simplified=True)

    def exterior_stair(self):
        s=self.s;n1=s['visible_lower_steps_estimate'];n2=s['hidden_upper_steps_estimate'];n=n1+n2
        riser=s['total_rise_m']/n;tread=s['tread_m'];w=s['width_m'];x,y=s['lower_run_start_xy'];land=s['landing_depth_m']
        z=0.;pieces=[]
        for i in range(n):
            if i==n1:
                self.b.plan_prism(rect(x-w/2,y,x+w/2,y+land),0,z-.08,'original grey brick','east-stair/estimated-mid-landing-support')
                self.remove_horizontal(self.b.parts[-1],z-.08)
                self.b.plan_prism(rect(x-w/2,y,x+w/2,y+land),z-.08,z,'worn paving','east-stair/estimated-mid-landing-tread')
                self.remove_horizontal(self.b.parts[-1],z-.08)
                pieces.append((y,z,y+land,z));y+=land
            z=(i+1)*riser
            self.b.plan_prism(rect(x-w/2,y,x+w/2,y+tread),0,z-.075,'original grey brick',f'east-stair/support-step-{i+1:02d}')
            self.remove_horizontal(self.b.parts[-1],z-.075)
            self.b.plan_prism(rect(x-w/2-.025,y-.015,x+w/2+.025,y+tread),z-.075,z,'worn coping',f'east-stair/tread-{i+1:02d}')
            # Keep the tread underside only in the small genuine nosing
            # overhang; under the support it is an internal shared interface.
            tread_part=self.b.parts[-1];self.remove_horizontal(tread_part,z-.075)
            overhang=rect(x-w/2-.025,y-.015,x+w/2+.025,y+tread).difference(rect(x-w/2,y,x+w/2,y+tread))
            before=len(self.b.parts);self.top_surface(overhang,z-.075,'worn coping',f'east-stair/nosing-underside-{i+1:02d}')
            self.b.parts[-1]['triangles']=[tuple(reversed(t)) for t in self.b.parts[-1]['triangles']]
            pieces.append((y,z,y+tread,z));y+=tread
        # The upper platform reaches the wall only at full height, avoiding an
        # invented stair tunnel through the solid lower enclosure wall.
        xx=-self.hx+self.e['upper_wall_walk_width_m']-.15
        platform=rect(x-w/2,y,xx,y+w).difference(self.footprint)
        self.b.plan_prism(platform,0,z-.09,'original grey brick','east-stair/estimated-full-height-link-support')
        self.remove_horizontal(self.b.parts[-1],z-.09)
        self.b.plan_prism(platform,z-.09,z,'worn paving','east-stair/estimated-top-link-platform')
        self.remove_horizontal(self.b.parts[-1],z-.09)
        # Rails follow each tread rise without dipping through the landing.
        for side in [-1,1]:
            railx=x+side*(w/2-.12)
            rail=[(railx,s['lower_run_start_xy'][1],riser+.90)]
            for a,za,b,zb in pieces:rail.append((railx,b,zb+.90))
            self.b.tube(rail,.043,'iron fittings',6,f'east-stair/handrail-{side}')
            for i,(a,za,b,zb) in enumerate(pieces):
                if i%3==0 or i==len(pieces)-1:
                    self.b.tube([(railx,(a+b)/2,za),(railx,(a+b)/2,za+.90)],.032,'iron fittings',6,f'east-stair/rail-post-{side}-{i}')
        for side in [-1,1]:
            yy=y+.10 if side<0 else y+w-.10
            start_x=x+w/2-.10 if side<0 else x-w/2+.10
            if side<0:
                self.b.tube([(start_x,yy,z+.9),(xx,yy,z+.9)],.043,'iron fittings',6,f'east-stair/top-link-handrail-{side}')
            else:
                # One swept elbow owns both rails and their shared corner.
                self.b.tube([(start_x,y,z+.9),(start_x,yy,z+.9),(xx,yy,z+.9)],.043,'iron fittings',6,'east-stair/top-link-continuous-outer-elbow-rail')
            for j,px in enumerate(np.linspace(start_x,xx,5)):
                self.b.tube([(px,yy,z),(px,yy,z+.9)],.032,'iron fittings',6,f'east-stair/top-link-post-{side}-{j}')
        # The last return endpoint is already owned by top-link-post-1-0.
        for j,py in enumerate(np.linspace(y,y+w-.10,3)[:-1]):
            self.b.tube([(x-w/2+.10,py,z),(x-w/2+.10,py,z+.9)],.032,'iron fittings',6,f'east-stair/top-link-outer-post-{j}')
        self.mark('east_exterior_stair',lower_steps=n1,upper_steps=n2,riser_m=riser,tread_m=tread,landing_depth_m=land,top_m=z,top_link_bounds_xy=[x-w/2,y,xx,y+w],hidden_upper_connection_estimated=True,upper_flight_continues_outside_wall=True,lower_wall_cut=False,walkability_verified=False,top_platform_does_not_cover_last_treads=True,platform_surface_clipped_outside_enclosure=True)

    def construct(self):
        from roof_geometry import build_roof
        self.walls();self.low_steps();self.pavilion();self.exterior_stair()
        self.mark('roof',**build_roof(self.b,self.d,self.lod))
        return self.b,self.features


def construct(design,lod=False):return Gatehouse(design,lod).construct()
