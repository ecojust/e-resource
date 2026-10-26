"""Beidajie 222: one photograph-informed two-storey street-front house.

Python + numpy + Shapely + fontTools; no Blender, network or production paths.
The exact provider footprint is retained. Visible architecture follows 2022,
with 2016 structural comparison. Textured adaptation: CC BY-SA 4.0.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import sys

import numpy as np
from shapely import affinity
from shapely.geometry import Polygon, LineString, box as rect
from shapely.ops import unary_union

HERE = Path(__file__).resolve().parent
# Published sources use an adjacent common package; staging has next/<house>.
COMMON = next(p for p in (HERE.parent/'common', HERE.parent.parent/'common')
              if (p/'photo_architecture.py').is_file())
sys.path.insert(0, str(COMMON))
from photo_architecture import Builder, Facade, pieces
from sign_lettering import add_facade_lettering

PALETTE = {
    'warm aged plaster': {'color':[.76,.75,.69], 'roughness':.94},
    'quiet rear plaster': {'color':[.63,.64,.60], 'roughness':.94},
    'dark stone plinth': {'color':[.23,.25,.24], 'roughness':.93},
    'aged brown timber': {'color':[.135,.091,.061], 'roughness':.79},
    'weathered timber edge': {'color':[.24,.19,.135], 'roughness':.88},
    'dark carved timber': {'color':[.17,.105,.070], 'roughness':.82},
    'relief highlight timber': {'color':[.23,.16,.105], 'roughness':.82},
    'reddish old door': {'color':[.22,.105,.071], 'roughness':.69},
    'dark inner recess': {'color':[.045,.05,.045], 'roughness':.98},
    'untextured shaded glass': {'color':[.13,.18,.15], 'roughness':.34, 'metallic':.12},
    'upper dark timber': {'color':[.066,.045,.029], 'roughness':.84},
    'upper warm inset timber': {'color':[.17,.125,.077], 'roughness':.88},
    'upper small shaded lights': {'color':[.055,.066,.058], 'roughness':.48, 'metallic':.04},
    'door glass grey': {'color':[.20,.235,.21], 'roughness':.28, 'metallic':.15},
    'slate tile 0': {'color':[.205,.213,.19], 'roughness':.93},
    'slate tile 1': {'color':[.214,.220,.198], 'roughness':.95},
    'slate tile 2': {'color':[.197,.206,.185], 'roughness':.91},
    'slate roof backing': {'color':[.165,.18,.17], 'roughness':.96},
    'warm guardian stone': {'color':[.61,.59,.51], 'roughness':.91},
    'guardian recess': {'color':[.28,.28,.24], 'roughness':.96},
    'gold lettering': {'color':[.68,.48,.16], 'roughness':.48, 'metallic':.42},
    'sign black brown': {'color':[.075,.065,.045], 'roughness':.80},
    'address green': {'color':[.035,.23,.16], 'roughness':.64},
    'address cream': {'color':[.83,.83,.73], 'roughness':.70},
    'lantern vermilion': {'color':[.48,.055,.028], 'roughness':.82},
    'lantern shaded red': {'color':[.29,.03,.017], 'roughness':.88},
    'aircon enamel': {'color':[.70,.72,.67], 'roughness':.65},
    'aircon grille': {'color':[.25,.29,.27], 'roughness':.78},
}


def file_info(path):
    b=Path(path).read_bytes()
    return {'file':Path(path).name,'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}


def homography(src, dst):
    a=[]; b=[]
    for (x,y),(u,v) in zip(src,dst):
        a.extend([[x,y,1,0,0,0,-u*x,-u*y], [0,0,0,x,y,1,-v*x,-v*y]])
        b.extend([u,v])
    return np.r_[np.linalg.solve(np.asarray(a),np.asarray(b)),1.].reshape(3,3)


def project(h, point):
    p=h@np.array([*point,1.]); return p[:2]/p[2]


def round_top_opening(x0,x1,z0,z1,r=.38):
    """Flat lintel with curved shoulder haunches, not a semicircular arch."""
    r=min(r,(x1-x0)/4,(z1-z0)/3)
    points=[(x0,z0),(x1,z0),(x1,z1-r)]
    points.extend((x1-r+r*math.cos(t),z1-r+r*math.sin(t))
                  for t in np.linspace(0,math.pi/2,9)[1:])
    points.append((x0+r,z1))
    points.extend((x0+r+r*math.cos(t),z1-r+r*math.sin(t))
                  for t in np.linspace(math.pi/2,math.pi,9)[1:])
    return Polygon(points)


class Residence222:
    def __init__(self):
        self.g=json.loads((HERE/'geometry-input.json').read_text())
        self.c=json.loads((HERE/'calibration.json').read_text())
        self.b=Builder(PALETTE)
        glass=self.c['glazing']['right_door_material']
        self.b.palette[glass['name']]={k:glass[k] for k in ['color','roughness','metallic']}
        self.original=np.asarray(self.g['polygon_local_east_north'],float)
        self.plan=Polygon(self.original)
        ends=self.g['front_edge']['endpoints_local_east_north_m']
        # Original ring is clockwise; reverse ONLY the facade helper direction.
        self.f=Facade(self.b,ends[1],ends[0],label='observed-SE-front-2022')
        assert np.dot(self.f.n[:2],self.g['front_edge']['outward_normal_east_north'])>.99999
        self.W=self.f.length; self.h=self.c['heights_m']; self.T=self.f.t; self.N=self.f.n
        self.bays=np.asarray(self.c['front_bay_boundaries_normalized'])*self.W
        self.centers=(self.bays[:-1]+self.bays[1:])/2
        self.photo=HERE/self.c['glazing']['photo']
        self.font=HERE/'fonts/Qingpu222SignSubset.otf'
        self.windows=[]; self.photo_maps=[]; self.letters=[]; self.audit=[]
        self.local_plan=np.array([self.local([*p,0])[:2] for p in self.original])
        self.depth=-float(self.local_plan[:,1].min())

    def local(self,p):
        v=np.asarray(p)-self.f.center
        return np.array([v@self.T,v@self.N,v[2]])

    def point(self,u,d,z): return self.f.point(u,z,d)

    def box(self,u,d,z,w,depth,h,material,label):
        self.f.box(u,z,w,h,depth,d,material,label)

    def ellipsoid(self,u,d,z,radii,material,label,segments=20,rings=10):
        """Closed ellipsoid with unique poles, no collapsed polar triangles."""
        rx,ry,rz=radii; verts=[self.point(u,d,z-rz)]
        for j in range(1,rings):
            lat=-math.pi/2+math.pi*j/rings
            for k in range(segments):
                a=math.tau*k/segments
                verts.append(self.point(u+rx*math.cos(lat)*math.cos(a),
                                        d+ry*math.cos(lat)*math.sin(a),z+rz*math.sin(lat)))
        top=len(verts);verts.append(self.point(u,d,z+rz));faces=[]
        for k in range(segments):faces.append((0,1+(k+1)%segments,1+k))
        for j in range(rings-2):
            a=1+j*segments
            for k in range(segments):
                b=a+segments;faces.append((a+k,a+(k+1)%segments,b+(k+1)%segments,b+k))
        for k in range(segments):
            a=1+(rings-2)*segments;faces.append((a+k,a+(k+1)%segments,top))
        # (u,d,z) uses a left-handed local basis; flip to positive ENU volume.
        faces=[tuple(reversed(f)) for f in faces]
        self.b.add(verts,faces,material,label)

    def plan_uv(self,coords):
        return Polygon([self.point(u,d,0)[:2] for u,d in coords])

    def line(self,coords,radius,material,label,sides=8):
        self.b.tube([self.point(*p) for p in coords],radius,material,sides,label)

    def circle_tube(self,u,d,z,radius,thickness,material,label,sectors=32,sides=6):
        # Closed loop has no duplicate end caps; Builder.tube is for open paths.
        verts=[]
        for i in range(sectors):
            a=math.tau*i/sectors;radial=self.T*math.cos(a)+np.array([0.,0.,math.sin(a)])
            center=self.point(u+radius*math.cos(a),d,z+radius*math.sin(a))
            for k in range(sides):
                b=math.tau*k/sides;verts.append(center+thickness*(self.N*math.cos(b)+radial*math.sin(b)))
        faces=[]
        for i in range(sectors):
            for k in range(sides):faces.append((i*sides+k,i*sides+(k+1)%sides,((i+1)%sectors)*sides+(k+1)%sides,((i+1)%sectors)*sides+k))
        volume=sum(np.dot(verts[f[0]],np.cross(verts[f[j]],verts[f[j+1]]))/6
                   for f in faces for j in range(1,len(f)-1))
        if volume<0:faces=[tuple(reversed(f)) for f in faces]
        self.b.add(verts,faces,material,label)

    def opening_frame(self,facade,shape,label,columns=1,rows=1,
                      frame='aged brown timber',glass='untextured shaded glass',
                      depth=-.18,glass_depth=-.24,frame_width=.075,with_glass=True):
        inner=shape.buffer(-frame_width,join_style=2)
        x0,z0,x1,z1=inner.bounds
        bars=[]
        for k in range(1,columns):
            x=x0+(x1-x0)*k/columns;bars.append(rect(x-.025,z0,x+.025,z1))
        for k in range(1,rows):
            z=z0+(z1-z0)*k/rows;bars.append(rect(x0,z-.025,x1,z+.025))
        panes=inner.difference(unary_union(bars)) if bars else inner
        facade.prism(shape.difference(panes),depth-.04,depth+.05,frame,label+'-frame')
        records=[]
        for i,poly in enumerate(pieces(panes)):
            name=label+f'-pane-{i}'
            if with_glass:facade.prism(poly,glass_depth-.020,glass_depth,glass,name)
            records.append({'label':facade.label+'/'+name,'bounds':list(poly.bounds)})
        self.windows.append({'label':label,'opening':list(shape.exterior.coords),
                             'frame_depth':depth,'frame_depth_range':[depth-.04,depth+.05],'glass_depth':glass_depth,'glass_depth_range':[glass_depth-.020,glass_depth] if with_glass else None,'panes':records})
        self.windows[-1].update(facade_origin=facade.center.tolist(),facade_normal=facade.n.tolist())
        return records

    def upper_timber_window(self,facade,shape,index):
        """Small lights and geometric woodwork, not a three-row glass curtain.

        Four decorated upper wood panels are clear in the 2022 left window.
        The middle/right windows show dark dense square/return lattice. Hidden
        lower extents remain restrained repetitions, explicitly not traced.
        """
        x0,z0,x1,z1=shape.bounds;inner=shape.buffer(-.075,join_style=2)
        wood=[shape.difference(inner)];panels=[];columns=[4,4,3][index]
        ix0,iz0,ix1,iz1=inner.bounds;step=(ix1-ix0)/columns
        for k in range(1,columns):
            xx=ix0+k*step;wood.append(rect(xx-.035,iz0,xx+.035,iz1))
        for k in range(columns):
            a=ix0+k*step+.035;b=ix0+(k+1)*step-.035
            top_bottom=iz1-.66
            wood.append(rect(a,top_bottom-.035,b,top_bottom+.035))
            if index==0:
                # Opaque warm wood inset, surrounded by the observed square
                # return motif; no glass/photo is invented in these panels.
                panels.append(rect(a+.065,top_bottom+.10,b-.065,iz1-.10))
                loop=rect(a+.04,top_bottom+.07,b-.04,iz1-.07)
                wood.append(loop.difference(loop.buffer(-.032,join_style=2)))
                for xx in [a+.04,b-.04]:
                    wood.append(rect(xx-.018,top_bottom+.02,xx+.018,top_bottom+.18))
                    wood.append(rect(xx-.018,iz1-.18,xx+.018,iz1-.02))
            else:
                # Upper middle/right portions visibly have small dark lattice.
                for rr in range(3):
                    y=top_bottom+(rr+.5)*.66/3
                    wood.append(rect(a,y-.018,b,y+.018))
                wood.append(rect((a+b)/2-.018,top_bottom,(a+b)/2+.018,iz1))
            available=top_bottom-iz0;rows=max(3,round(available/.46))
            for rr in range(rows):
                lo=iz0+rr*available/rows;hi=iz0+(rr+1)*available/rows
                loop=rect(a+.045,lo+.055,b-.045,hi-.055)
                wood.append(loop.difference(loop.buffer(-.032,join_style=2)))
                # Short alternating connectors join the small square loops.
                middle=(lo+hi)/2
                wood.append(rect(a,middle-.016,a+.08,middle+.016))
                wood.append(rect(b-.08,middle-.016,b,middle+.016))
                xx=(a+b)/2
                wood.append(rect(xx-.016,lo,xx+.016,lo+.09))
                wood.append(rect(xx-.016,hi-.09,xx+.016,hi))
        wood=unary_union(wood).intersection(shape)
        opaque=unary_union(panels).difference(wood) if panels else Polygon()
        lights=shape.difference(wood.union(opaque))
        label=f'upper-window-{index}'
        facade.prism(wood,-.08,.01,'upper dark timber',label+'-frame')
        if not opaque.is_empty:
            facade.prism(opaque,-.035,-.008,'upper warm inset timber',label+'-opaque-top-panels')
        records=[]
        for j,poly in enumerate(pieces(lights)):
            name=label+f'-pane-{j}'
            facade.prism(poly,-.03,-.01,'upper small shaded lights',name)
            records.append({'label':facade.label+'/'+name,'bounds':list(poly.bounds)})
        self.windows.append({'label':label,'opening':list(shape.exterior.coords),
            'frame_depth':-.04,'frame_depth_range':[-.08,.01],
            'glass_depth':-.01,'glass_depth_range':[-.03,-.01],
            'panes':records,'facade_origin':facade.center.tolist(),'facade_normal':facade.n.tolist(),
            'visible_wood_leaf_count':columns,'opaque_top_panels':len(panels),
            'small_light_count':len(records),'front_glass_area_fraction':lights.area/shape.area,
            'hidden_lower_pattern':'restrained continuation; not independently observed behind railing'})

    def shell(self):
        z=self.h;floor=z['floor_step'];deck=z['balcony_floor_top']
        self.b.plan_prism(self.plan,0,floor,'dark stone plinth','exact-source-footprint-plinth')
        self.b.plan_prism(self.plan.buffer(-.12),floor,floor+.05,'weathered timber edge','ground-floor-inferred-empty-interior')
        ground_widths=[self.bays[1]-self.bays[0]-.58,2.62,self.bays[3]-self.bays[2]-.56]
        holes=[round_top_opening(u-w/2,u+w/2,floor,z['ground_clear_door_head'],.33)
               for u,w in zip(self.centers,ground_widths)]
        self.f.wall(floor,deck-.13,holes,thickness=.36,material='warm aged plaster')
        self.audit.append({'check':'ground_continuous_wall','actual_opening_count':3,'shape':'flat heads with curved shoulder haunches'})
        # Only the known small source block. Unobserved rear has no invented windows.
        for i in [0,1,2]:
            a=self.original[(i+1)%4];b=self.original[i]
            side=Facade(self.b,a,b,label=f'unobserved-source-side-{i}')
            if i==1:
                side.wall(floor,z['upper_eave'],material='quiet rear plaster',thickness=.30)
            else:
                roofpts=[]
                for u in np.linspace(-side.length/2,side.length/2,25):
                    q=side.point(u,0,0);d=self.local(q)[1]
                    fraction=(u+side.length/2)/side.length
                    roofpts.append((u,z['upper_eave']+(z['ridge']-z['upper_eave'])*(1-abs(2*fraction-1))+.16))
                outline=Polygon([(-side.length/2,floor),(side.length/2,floor),*reversed(roofpts)])
                side.wall(floor,z['ridge']+.2,material='warm aged plaster',thickness=.28,outline=outline)
        # Open gallery: floor, set-back wall and real clear air between railing and eave.
        gallery=self.plan.intersection(self.plan_uv([[-self.W,.15],[self.W,.15],[self.W,-1.18],[-self.W,-1.18]]))
        self.b.plan_prism(gallery,deck-.17,deck,'aged brown timber','open-gallery-deck')
        inner=Facade(self.b,self.f.point(-self.W/2,0,-1.10)[:2],self.f.point(self.W/2,0,-1.10)[:2],label='recessed-upper-wall')
        upper_widths=[2.66,2.48,2.12]
        upperholes=[rect(u-w/2,deck+.50,u+w/2,z['upper_eave']-.94) for u,w in zip(self.centers,upper_widths)]
        inner.wall(deck,z['upper_eave'],upperholes,thickness=.28,material='warm aged plaster')
        for i,shape in enumerate(upperholes):
            self.upper_timber_window(inner,shape,i)
        # The middle and right lower bays are closed doors; left is a real opening.
        for i in [1,2]:
            u=self.centers[i];w=ground_widths[i]-.15;h=z['ground_clear_door_head']-floor-.11
            shape=rect(u-w/2,floor+.025,u+w/2,floor+h)
            if i==1:
                self.f.prism(shape,-.38,-.30,'reddish old door','central-closed-timber-door')
                self.opening_frame(self.f,shape,'central-door-frame',columns=2,with_glass=False,depth=-.22,frame_width=.085)
                for side in [-1,1]:
                    for zz,hh in [(floor+.66,.98),(floor+1.80,.92)]:
                        self.box(u+side*w*.24,-.265,zz,w*.43,.04,hh,'aged brown timber','central-door-raised-panel')
                for side in [-1,1]:self.ellipsoid(u+side*.07,-.18,floor+1.10,[.025,.03,.025],'gold lettering','door-stud',12,6)
            else:
                panes=self.opening_frame(self.f,shape,'right-closed-glass-door',columns=2,rows=1,depth=-.21,glass_depth=-.18,frame_width=.09,glass='right door estimated glass')
                self.audit.append({'check':'right_door_coherent_glass','whole_leaf_count':2,'photo_texture':False,'paper_labels_added':False,'material_estimate':self.c['glazing']['right_door_material'],'source_image_changed':False})
                for s in [-1,1]:self.box(u+s*.09,-.12,floor+1.1,.035,.04,.38,'dark stone plinth','right-door-handle')
        # Left door: a single narrow leaf rotated inward, leaving a viewable void.
        u=self.centers[0];w=ground_widths[0]-.1;shape=rect(u-w/2,floor,u+w/2,z['ground_clear_door_head']-.08)
        self.opening_frame(self.f,shape,'left-open-portal-surround',with_glass=False,depth=-.20,frame_width=.10)
        hinge=self.f.point(u+w/2-.06,0,-.32);angle=math.radians(72)
        end=hinge-self.T*(w*.45*math.cos(angle))-self.N*(w*.45*math.sin(angle))
        leaf=Facade(self.b,end[:2],hinge[:2],label='left-entry-glass-leaf-open72deg')
        self.opening_frame(leaf,rect(-leaf.length/2,floor+.03,leaf.length/2,z['ground_clear_door_head']-.13),
                           'open-leaf',columns=1,glass='door glass grey',depth=0,glass_depth=.03)
        self.box(self.centers[0],-2.50,1.45,ground_widths[0]-.15,.06,2.35,'dark inner recess','unobserved-interior-shadow-backstop')
        # Street step is local to this block, not a new parcel/adjacent shop.
        for depth,height in [(.64,.10),(.36,.19)]:
            self.box(0,depth/2, height/2,self.W-.1,depth,height,'warm guardian stone','entry-stone-step')

    def gallery(self):
        z=self.h;deck=z['balcony_floor_top'];top=z['upper_eave']-.08
        for u in self.bays[1:-1]:
            self.box(u,0,(deck+top)/2,.235,.235,top-deck,'aged brown timber','independent-upper-timber-column')
            self.box(u,.0,deck+.10,.28,.28,.20,'weathered timber edge','timber-column-foot')
        # Photograph-confirmed open gallery railing with interlocking angular motifs.
        low=z['railing_bottom'];high=z['railing_top']
        for i,(a,b) in enumerate(zip(self.bays[:-1],self.bays[1:])):
            a+=.16;b-=.16
            shapes=[rect(a,low,b,low+.085),rect(a,high-.085,b,high)]
            count=max(3,round((b-a)/.62));cell=(b-a)/count
            for k in range(count):
                x=a+k*cell
                pts=[(x,low+.12),(x,high-.17),(x+cell*.52,high-.17),
                     (x+cell*.52,low+.17),(x+cell,low+.17),(x+cell,high-.12)]
                shapes.append(LineString(pts).buffer(.035,cap_style=2,join_style=2))
                shapes.append(rect(x+cell*.12,low+.37,x+cell*.77,low+.435))
            grille=unary_union(shapes).intersection(rect(a,low,b,high))
            self.f.prism(grille,-.005,.105,'weathered timber edge',f'balcony-key-pattern-{i}')
            self.box((a+b)/2,.047,high+.04,b-a,.16,.08,'aged brown timber','railing-rounded-top-rail')
        # Dark carved beam has real thickness and simplified organic relief;
        # it is not a flat photo of the surrounding white columns.
        lo,hi=z['frieze_bottom'],z['frieze_top']
        self.box(0,.035,(lo+hi)/2,self.W-.13,.22,hi-lo,'dark carved timber','carved-frieze-base')
        for zz in [lo+.025,hi-.025]:
            self.box(0,.17,zz,self.W-.1,.10,.055,'reddish old door','frieze-moulded-border')
        for bay,(a,b) in enumerate(zip(self.bays[:-1],self.bays[1:])):
            a+=.14;b-=.14;mid=(lo+hi)/2;L=b-a
            for strand in [-1,1]:
                pts=[]
                for t in np.linspace(0,1,33):
                    pts.append((a+L*t,.165+.012*math.sin(4*math.pi*t),mid+strand*.075*math.sin(3*math.pi*t)))
                self.line(pts,.018,'relief highlight timber',f'frieze-organic-ribbon-{bay}-{strand}')
            for k in range(12):
                x=a+(k+.5)*L/12;sgn=1 if k%2 else -1
                leaf=Polygon([(x-.09,mid),(x-.045,mid+sgn*.10),(x+.03,mid+sgn*.12),(x+.10,mid+.012)])
                self.f.prism(leaf,.16,.19,'dark carved timber','frieze-simplified-leaf-relief')
        # Exposed timber beam and small geometric trim immediately beneath rafters.
        self.box(0,.02,top-.11,self.W-.1,.24,.22,'aged brown timber','upper-eave-front-beam')
        for a,b in zip(self.bays[:-1],self.bays[1:]):
            count=max(4,int((b-a)/.36))
            grille=rect(a+.12,top-.36,b-.12,top-.30).union(rect(a+.12,top-.19,b-.12,top-.14))
            for x in np.linspace(a+.15,b-.15,count):grille=grille.union(rect(x-.02,top-.35,x+.02,top-.16))
            self.f.prism(grille,-.015,.045,'aged brown timber','upper-open-grid-trim')

    def roof_z(self,d):
        f=min(1.,max(0.,-d/self.depth))
        return self.h['upper_eave']+(self.h['ridge']-self.h['upper_eave'])*(1-abs(2*f-1))

    def tile_shell(self,start,end,U,N,radius,material,label):
        """Thin curved clay cap with actual shell thickness, along roof slope."""
        U=np.asarray(U);N=np.asarray(N);start=np.asarray(start);end=np.asarray(end)
        angles=np.linspace(0,math.pi,9)
        outer=[(radius*math.cos(a),.052*math.sin(a)) for a in angles]
        inner=[(radius*math.cos(a),.052*math.sin(a)-.012) for a in angles[::-1]]
        profile=Polygon(outer+inner)
        E=end-start;L=float(np.linalg.norm(E));E/=L
        if np.dot(np.cross(U,N),E)<0:start,end=end,start;E=-E
        self.b.prism(profile,0,L,lambda u,z,d:start+U*u+N*z+E*d,material,label)

    def roof(self):
        # Bilinear spans preserve the four provider corners, rather than replacing
        # the source trapezoid with an unrelated bounding rectangle.
        left=self.local_plan[0]+[-.04,.42];right=self.local_plan[3]+[.04,.42]
        rearleft=self.local_plan[1]+[-.04,-.18];rearright=self.local_plan[2]+[.04,-.18]
        def uv(t,s):return (1-s)*((1-t)*left+t*right)+s*((1-t)*rearleft+t*rearright)
        corners=[uv(0,0),uv(1,0),uv(1,.5),uv(0,.5),uv(0,1),uv(1,1)]
        for half in [0,1]:
            s0,s1=(0,.5) if half==0 else (.5,1)
            poly=[uv(0,s0),uv(1,s0),uv(1,s1),uv(0,s1)]
            roofheights=[self.h['upper_eave']+(self.h['ridge']-self.h['upper_eave'])*(1-abs(2*s-1)) for s in [s0,s0,s1,s1]]
            vs=[self.point(u,d,h+off) for off in [-.12,0] for (u,d),h in zip(poly,roofheights)]
            fs=[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]
            # Correct cap winding for local clockwise XY if required.
            if Polygon([self.point(u,d,0)[:2] for u,d in poly]).exterior.is_ccw is False:
                fs=[tuple(reversed(x)) for x in fs]
            self.b.add(vs,fs,'slate roof backing',f'pitched-roof-shell-{half}')
        cols=60; courses=15; tile_count=0
        for half in [0,1]:
            for col in range(cols):
                t=(col+.5)/cols
                for row in range(courses):
                    a=row/courses*.5; bb=min(.5,(row+1.15)/courses*.5)
                    s0,s1=(a,bb) if half==0 else (1-a,1-bb)
                    p0=uv(t,s0);p1=uv(t,s1)
                    P0=self.point(*p0,self.h['upper_eave']+(self.h['ridge']-self.h['upper_eave'])*(1-abs(2*s0-1))+.025)
                    P1=self.point(*p1,self.h['upper_eave']+(self.h['ridge']-self.h['upper_eave'])*(1-abs(2*s1-1))+.025)
                    S=(P1-P0);S/=np.linalg.norm(S);normal=np.cross(self.T,S)
                    if normal[2]<0:normal=-normal
                    normal/=np.linalg.norm(normal)
                    # Each uphill tile overlaps the tail of the downhill tile.
                    # Its low end has a real raised lip: adjacent courses are
                    # not the same coplanar infinitely long curved strip.
                    P0+=normal*.020;P1+=normal*.002
                    self.tile_shell(P0,P1,self.T,normal,.101,'slate tile '+str((col//5+row+half)%3),f'roof-overlapping-clay-cap-{half}-{col}-{row}')
                    tile_count+=1
        # Short cap tiles on a continuous ridge, plus actual projecting eave members.
        for k in range(40):
            a=uv(k/40,.5);b=uv((k+1.05)/40,.5)
            P0=self.point(*a,self.h['ridge']+.06);P1=self.point(*b,self.h['ridge']+.06)
            self.tile_shell(P0,P1,self.N,np.array([0,0,1]),.15,'slate tile 1','ridge-overlap-cap')
        for k in range(43):
            u=-self.W/2+(k+.5)*self.W/43
            p0=self.point(u,-.72,self.h['upper_eave']+.20)
            p1=self.point(u,.43,self.h['upper_eave']-.085)
            axis=p1-p0;L=np.linalg.norm(axis);axis/=L;normal=np.cross(self.T,axis)
            self.b.box((p0+p1)/2,(.075,L,.085),'weathered timber edge',[self.T,axis,normal],label='exposed-projecting-eave-rafter')
        self.box(0,.30,self.h['upper_eave']-.04,self.W+.15,.15,.14,'aged brown timber','front-eave-fascia')
        # Curved plaster fire-wall ends project above the front roof edge.
        for u in [-self.W/2+.06,self.W/2-.06]:
            # Each strip is a real solid along the measured side direction.
            pts=[(u,-.90,self.h['upper_eave']+.23),(u,-.45,self.h['upper_eave']+.23),
                 (u,-.05,self.h['upper_eave']+.29),(u,.32,self.h['upper_eave']+.46),
                 (u,.57,self.h['end_wall_front_tip'])]
            self.line(pts,.11,'warm aged plaster','upturned-end-wall-coping',10)
            for dd in [-.08,.07]:self.line([(x,d,z-.10+dd) for x,d,z in pts],.036,'quiet rear plaster','end-wall-coping-layer',8)
            lower=[(-.90,self.h['upper_eave']-.25),(-.10,self.h['upper_eave']-.25),
                   (.15,self.h['upper_eave']+.02),(.40,self.h['upper_eave']+.28),
                   (.57,self.h['end_wall_front_tip']-.15)]
            upper=[(d,z) for _,d,z in reversed(pts)]
            profile=Polygon([(-d,z) for d,z in lower+upper])
            self.b.prism(profile,-.10,.10,lambda x,z,w,u=u:self.point(u+w,-x,z),
                         'warm aged plaster','upturned-end-wall-solid-profile')
        self.audit.append({'check':'roof','individual_overlapping_tile_shells':tile_count,'ridge_cap_tiles':40,'eave_rafters':43,
                           'front_eave_projection_m':.42,'rear_eave_projection_inferred_m':.18,
                           'tile_course_lap_fraction':.15,'tile_normal_lip_offsets_m':[.020,.002],
                           'tile_course_colours':'three restrained slate values, deterministic (col//5+row+half)%3; no random dirt',
                           'rear_pitch':'inferred symmetric form over exact source wall plan; eaves project explicitly'})

    def texture_rect(self,label,bounds,quad,name,facade,mode):
        x0,y0,x1,y1=bounds;h=homography([[x0,y1],[x1,y1],[x1,y0],[x0,y0]],quad)
        def uv(p):
            q=np.asarray(p)-facade.center;coord=[q@facade.t,p[2]]
            return (project(h,coord)+.5)/np.array([4000,3000])
        r=self.b.photograph_parts(self.photo,uv,lambda p:p['label']==label,name=name,roughness=.43,
             orientation={'rawSize':[4000,3000],'exifOrientation':1,'uvConvention':'stored-pixels'})
        self.photo_maps.append(dict(r,label=label,bounds=bounds,source_quad_px=quad,homography=h.tolist(),mode=mode))

    def signage(self):
        z=self.h;u=self.centers[0]
        self.box(u,.09,z['ground_clear_door_head']+.005,3.04,.13,.43,'sign black brown','left-gallery-sign-board')
        self.letters.append(add_facade_lettering(self.f,'上海市鶴龍美術館'[::-1],u=u,z=z['ground_clear_door_head']+.01,
             width=2.65,height=.25,low=.165,high=.185,material='gold lettering',font=self.font,label='right-to-left-gallery-sign'))
        self.letters[-1].update(reading='上海市鶴龍美術館',reading_direction='right-to-left',visual_year=2022)
        # 222 address sign, on the photograph-confirmed left-central white pier.
        u=self.bays[1]+.04;zz=z['ground_clear_door_head']-.12
        self.box(u,.035,zz,.28,.035,.23,'address green','address-222-backplate')
        self.letters.append(add_facade_lettering(self.f,'222',u=u,z=zz+.028,width=.205,height=.12,low=.057,high=.065,
                                  material='address cream',font=self.font,label='address-digits'))
        self.letters.append(add_facade_lettering(self.f,'北大街',u=u,z=zz-.067,width=.18,height=.042,low=.057,high=.062,
                                  material='address cream',font=self.font,label='address-street'))
        # Central cursive board: no guessed transcription. Original image is
        # confined to a separate inner surface, with a solid board and scroll ends.
        c=self.c['center_sign'];u,z,w,h=c['u_m'],c['z_m'],c['width_m'],c['height_m'];d=.10
        before=len(self.b.parts)
        self.box(u,d,z,w,.12,h,'sign black brown','central-cursive-board-solid')
        bounds=[u-w*.45,z-h*.43,u+w*.45,z+h*.43]
        self.f.prism(rect(*bounds),d+.061,d+.069,'sign black brown','central-cursive-board-photo-face')
        label=self.f.label+'/central-cursive-board-photo-face'
        self.texture_rect(label,bounds,c['photo_face_quad_px'],'PhotoFacade_Qingpu222CursiveSign',self.f,'independent safe inner sign face, no invented inscription')
        for side in [-1,1]:
            self.ellipsoid(u+side*w*.47,d-.005,z-h*.43,[.065,.085,.055],'sign black brown','sign-scroll-end',16,8)
        angle=math.radians(-c['tilt_deg'])
        for p in self.b.parts[before:]:
            vv=[]
            for pos in p['vertices']:
                q=self.local(pos);dz=q[2]-z;dd=q[1]-d
                vv.append(self.point(q[0],d+dd*math.cos(angle)+dz*math.sin(angle),z+dz*math.cos(angle)-dd*math.sin(angle)))
            p['vertices']=[tuple(v) for v in vv]
        self.photo_maps[-1]['post_uv_rotation']={'axis':'front tangent','degrees':-c['tilt_deg'],'center_u_d_z':[u,d,z]}

    def guardian(self,u,mirror):
        stone='warm guardian stone';dark='guardian recess';d=.72;ground=.19
        for zz,w,dep,hh in [(ground+.06,.68,.83,.12),(ground+.20,.61,.74,.18),(ground+.35,.64,.77,.12)]:
            self.box(u,d,zz,w,dep,hh,stone,'guardian-plinth-tier')
        base=ground+.41
        self.ellipsoid(u,d-.07,base+.36,[.23,.245,.37],stone,'seated-guardian-haunch')
        self.ellipsoid(u,d+.04,base+.52,[.22,.21,.30],stone,'guardian-upright-chest')
        self.ellipsoid(u,d+.07,base+.80,[.255,.245,.255],stone,'guardian-head')
        self.ellipsoid(u,d+.25,base+.79,[.20,.14,.10],stone,'guardian-upper-muzzle')
        self.ellipsoid(u,d+.27,base+.665,[.185,.125,.055],stone,'guardian-lower-jaw')
        self.ellipsoid(u,d+.255,base+.72,[.14,.09,.038],dark,'guardian-visible-open-mouth',16,8)
        self.ellipsoid(u,d+.365,base+.805,[.075,.032,.045],stone,'guardian-nose',16,8)
        for s in [-1,1]:
            self.ellipsoid(u+s*.16,d+.225,base+.88,[.06,.035,.05],stone,'guardian-brow',16,8)
            self.ellipsoid(u+s*.16,d+.25,base+.87,[.021,.018,.022],dark,'guardian-eye',12,6)
            self.ellipsoid(u+s*.20,d-.02,base+.95,[.08,.09,.105],stone,'guardian-ear',16,8)
            self.line([(u+s*.145,d+.12,base+.40),(u+s*.16,d+.23,base+.11)],.075,stone,'guardian-foreleg',12)
            self.ellipsoid(u+s*.16,d+.29,base+.065,[.11,.155,.067],stone,'guardian-paw',16,8)
            for toe in [-1,0,1]:
                self.ellipsoid(u+s*.16+toe*.053,d+.39,base+.06,[.027,.052,.035],stone,'guardian-toe',12,6)
        # Mane curls follow the visible large-headed guardian silhouette; no
        # invented sex-specific ball/cub or hidden tail iconography.
        for j in range(15):
            a=math.pi*.10+j*math.pi*1.8/14
            cu=u+.24*math.cos(a);cz=base+.80+.24*math.sin(a)
            pts=[]
            for t in np.linspace(0,math.tau*1.4,17):
                r=.035*(1-t/(math.tau*1.7));pts.append((cu+r*math.cos(t),d+.16+.013*math.sin(t),cz+r*math.sin(t)))
            self.line(pts,.013,stone,'guardian-simplified-mane-curl',6)
        # Low pedestal scrolls, described as approximate relief, not a scan.
        for k in [-1,0,1]:
            pts=[]
            for t in np.linspace(0,math.tau*1.2,18):
                r=.055*(1-t/(math.tau*1.5));pts.append((u+k*.17+r*math.cos(t),d+.397,ground+.18+r*math.sin(t)))
            self.line(pts,.014,stone,'guardian-plinth-relief-scroll',6)

    def fixtures(self):
        # Three red lanterns visible under the open gallery eave.
        for i,u in enumerate(self.centers):
            z=self.h['upper_eave']-.65
            self.line([(u,-.25,z+.40),(u,-.25,z+.21)],.012,'aged brown timber','lantern-hanging-cord',6)
            self.ellipsoid(u,-.25,z,[.14,.14,.23],'lantern vermilion',f'lantern-{i}',16,10)
            for k in range(10):
                a=k*math.tau/10;pts=[]
                for t in np.linspace(-math.pi/2+.07,math.pi/2-.07,10):
                    pts.append((u+.142*math.cos(t)*math.cos(a),-.25+.142*math.cos(t)*math.sin(a),z+.23*math.sin(t)))
                self.line(pts,.005,'lantern shaded red','lantern-rib',5)
            self.line([(u,-.25,z-.23),(u,-.25,z-.39)],.018,'lantern shaded red','lantern-short-tassel',6)
        # Clearly visible contemporary air conditioner, not a generic street prop.
        u=self.centers[0]-1.10;z=self.h['upper_eave']-1.05
        self.box(u,-.86,z,.76,.38,.54,'aircon enamel','2022-upper-left-aircon-case')
        for rad in [.20,.16,.12,.08]:
            self.circle_tube(u-.13,-.655,z,rad,.008,'aircon grille','aircon-fan-ring')
        for a in np.linspace(0,math.tau,12,endpoint=False):
            self.line([(u-.13,-.65,z),(u-.13+.20*math.cos(a),-.65,z+.20*math.sin(a))],.006,'aircon grille','aircon-fan-spoke',5)
        for zz in np.linspace(z-.18,z+.18,7):self.box(u+.25,-.655,zz,.15,.014,.018,'aircon grille','aircon-vent-slot')

    def construct(self):
        self.shell();self.gallery();self.roof();self.signage()
        center=self.centers[1]
        self.guardian(center-.94,-1);self.guardian(center+.94,1)
        self.fixtures()

    def build(self,output):
        self.construct()
        metadata={'name':'青浦朱家角北大街222号民宅临街前楼 / Beidajie222',
          'building_id':self.g['id'],'district_id':'310118','district_name':'青浦区','anchor':self.g['anchor'],
          'visual_epoch':'2022-07-23','storeys':2,'front_structural_bays':3,'front_width_m':self.W,
          'height_is_measured':False,'heights_m':self.h,'height_basis':self.c['height_basis'],
          'footprint_source':self.g['source'],'original_footprint_local_enu':self.original.tolist(),
          'geometry_input_sha256':file_info(HERE/'geometry-input.json')['sha256'],
          'calibration_sha256':file_info(HERE/'calibration.json')['sha256'],
          'copyright':'Textured architectural adaptation CC BY-SA 4.0. Original 2022 photograph by 钉钉, CC BY-SA 4.0, embedded unchanged only on the central cursive sign. Right-door glass uses one coherent untextured estimated material; no reflected-scene islands, uncertain paper labels, stone guardian or hardware pixels are mapped onto the door. 2016 reference by Fayhoo, CC BY-SA 3.0 (not embedded). Footprint: Overture ODbL-1.0 aggregate; Qian Shi et al. East Asian Buildings CC BY 4.0, NOT an OSM-surveyed footprint. Font subset SIL OFL1.1; source code MIT.',
          'license':{'model':'CC-BY-SA-4.0','url':'https://creativecommons.org/licenses/by-sa/4.0/','source_code':'MIT','footprint_aggregate':'ODbL-1.0'},
          'photographic_sources':[{'page':'https://commons.wikimedia.org/?curid=121178626','author':'钉钉','license':'CC-BY-SA-4.0',**file_info(self.photo)}],
          'lettering':self.letters,'photographic_mappings':self.photo_maps,
          'architectural_checks':self.audit,'limitations':self.c['limitations']}
        report=self.b.save(output/'qingpu-beidajie-222.glb',metadata)
        (output/'photo-mapping-evidence.json').write_text(json.dumps(self.photo_maps,ensure_ascii=False,indent=2)+'\n')
        (output/'architecture-evidence.json').write_text(json.dumps({'windows':self.windows,'checks':self.audit,'lettering':self.letters,'source_ring_unchanged':True},ensure_ascii=False,indent=2)+'\n')
        return report


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,default=HERE/'output');args=parser.parse_args()
    args.output.mkdir(parents=True,exist_ok=True)
    report=Residence222().build(args.output)
    print(json.dumps({k:report[k] for k in ['file','bytes','sha256','triangles','materials','parts']},ensure_ascii=False,indent=2))


if __name__=='__main__':main()
