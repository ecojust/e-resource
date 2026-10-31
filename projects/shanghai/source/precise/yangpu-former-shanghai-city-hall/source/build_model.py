"""Photo-guided, original Yangpu former city-hall exterior. MIT geometry.

All elevations and decorative dimensions are author estimates, not a survey.
Geographic source footprint, independent stair/bridge scope and documentary
93/25/20 dimensions are kept distinct. Source photographs are never textures.
"""
from pathlib import Path
import argparse, json, math
import numpy as np
from shapely.geometry import Polygon, box
from shapely.geometry.polygon import orient
from shapely.ops import unary_union
from common.photo_architecture import Builder, Facade as BaseFacade, opening
from components import PALETTE, roof, road_bridge, stairs, rail, bracket

ROOT=Path(__file__).resolve().parent
ID='yangpu-former-shanghai-city-hall'
INPUT=json.loads((ROOT/'model-parameters.json').read_text())
MAIN_POLYGON=INPUT['source_main']['outline']
PALETTE=PALETTE|{'warm stone':{'color':[.76,.73,.65],'roughness':.79},
 'glazed green tile':{'color':[.12,.36,.27],'roughness':.28},
 'green tile roll':{'color':[.17,.44,.33],'roughness':.24},
 'ochre painted line':{'color':[.79,.60,.28],'roughness':.63},
 'door timber':{'color':[.36,.10,.055],'roughness':.64},
 'plinth granite':{'color':[.40,.41,.38],'roughness':.85},
 'painted gable ground':{'color':[.70,.58,.31],'roughness':.62}}


class Facade(BaseFacade):
    """Miter the source outline's inner wall corners; keep true opening reveals.

    Wall caps must meet along a miter, not overlap two rectangular wall ends.
    This also avoids duplicate same-plane edges after material-batch packing.
    """
    def wall(self,bottom,top,holes=(),thickness=.52,material='warm stone',outline=None):
        points=list(orient(Polygon(MAIN_POLYGON),sign=1).exterior.coords)[:-1]
        index=next((i for i,p in enumerate(points) if np.allclose(p,self.a[:2],atol=1e-9,rtol=0)
                    and np.allclose(points[(i+1)%len(points)],self.b[:2],atol=1e-9,rtol=0)),None)
        if index is None:return super().wall(bottom,top,holes,thickness,material,outline)
        prev=BaseFacade(self.builder,points[index-1],points[index])
        nxt=BaseFacade(self.builder,points[(index+1)%len(points)],points[(index+2)%len(points)])
        tangent,normal=self.t[:2],self.n[:2]
        def inside(point,other):
            axes=np.array([normal,other])
            return point-normal*thickness if abs(np.linalg.det(axes))<1e-10 else np.linalg.solve(axes,np.array([normal@point-thickness,other@point-thickness]))
        left=(inside(self.a[:2],prev.n[:2])-self.a[:2])@tangent/thickness
        right=(inside(self.b[:2],nxt.n[:2])-self.b[:2])@tangent/thickness
        def mapper(u,z,d):
            # Only the two outer end caps are mitered. Interior opening loops
            # retain perpendicular reveals and exact recess alignment; shearing
            # the whole back skin would partly obstruct narrow base windows.
            shift=left if abs(u+self.length/2)<1e-8 else right if abs(u-self.length/2)<1e-8 else 0.
            return self.point(u-d*shift,z,d)
        shape=outline if outline is not None else box(-self.length/2,bottom,self.length/2,top)
        if holes:shape=shape.difference(unary_union(holes))
        self.builder.prism(shape,-thickness,0,mapper,material,self.label+' / continuous opened mitered wall')
        return shape


def frame_window(b,f,shape,label,detailed=True,columns=6,rows=4,material='dark red lattice',trim=False):
    x0,z0,x1,z1=shape.bounds
    outer=shape.buffer(-.025,join_style=2);inner=shape.buffer(-.11,join_style=2)
    bars=[]
    for i in range(1,columns if detailed else max(2,columns//2)):
        n=columns if detailed else max(2,columns//2)
        x=x0+(x1-x0)*i/n;bars.append(box(x-.035,z0,x+.035,z1))
    for i in range(1,rows if detailed else 2):
        n=rows if detailed else 2
        z=z0+(z1-z0)*i/n;bars.append(box(x0,z-.035,x1,z+.035))
    panes=inner.difference(unary_union(bars))
    f.prism(outer.difference(panes),-.28,-.13,material,label+' / one-piece lattice')
    f.prism(inner,-.585,-.55,'grey recessed glazing',label+' / recessed glass')
    if trim:
        f.prism(shape.buffer(.13,join_style=2).difference(shape),-.02,.105,'warm stone',label+' / stone trim')
    return {'point':list(f.point(x0+(x1-x0)*.213,z0+(z1-z0)*.317,0)),
            'normal':list(f.n),'depth':.55,'material':'grey recessed glazing','label':label}


def stone_panel_pattern(b,f,u,z,width,height,label,detailed):
    f.box(u,z,width,height,.13,.095,'vermilion timber',label+' / panel')
    # Geometric meander motifs summarize the painted panels without copying art.
    if not detailed:return
    for j in range(max(1,int(width/1.45))):
        count=max(1,int(width/1.45));c=u-width/2+width*(j+.5)/count
        w=min(.96,width/count*.77);h=min(.68,height*.62)
        outer=box(c-w/2,z-h/2,c+w/2,z+h/2)
        ring=outer.difference(outer.buffer(-.045,join_style=2))
        f.prism(ring,.17,.205,'ochre painted line',label+f' / meander border {j}')
        path=[(c-w*.25,z-h*.22),(c+w*.22,z-h*.22),(c+w*.22,z+h*.19),
              (c-w*.09,z+h*.19),(c-w*.09,z)]
        for k,(a,q) in enumerate(zip(path,path[1:])):
            b.tube([f.point(a[0],a[1],.21),f.point(q[0],q[1],.21)],.023,
                   'ochre painted line',sides=6,label=label+f' / meander {j}/{k}')


def painted_fascia(b,f,label,detailed):
    f.box(0,14.72,f.length,.23,.63,.18,'golden glazed crest',label+' / gold lower fillet')
    f.box(0,15.22,f.length,.73,.64,.18,'blue painted bracket',label+' / blue fascia')
    f.box(0,15.68,f.length,.17,.72,.21,'green painted bracket',label+' / upper fascia')
    if detailed:
        for i,u in enumerate(np.linspace(-f.length/2+.75,f.length/2-.75,max(2,int(f.length/1.5)))):
            p=Polygon([(u-.40,15.22),(u,15.45),(u+.40,15.22),(u,14.99)])
            f.prism(p.difference(p.buffer(-.045,join_style=2)),.515,.55,'ochre painted line',label+f' / diamond fascia {i}')


def long_front(b,a,q,bays,label,central,detailed,probes,features):
    f=Facade(b,a,q,label)
    pier=4.65 if central else 1.3
    span=f.length-2*pier;bay=span/bays
    centers=np.linspace(-span/2+bay/2,span/2-bay/2,bays)
    upper_holes=[];base_holes=[]
    for i,u in enumerate(centers):
        width=bay-.85
        for z,h in [(5.05,3.35),(10.10,3.65)]:
            if central and i==bays//2 and z==5.05:
                hshape=opening(float(u),4.3,5.5,4.55)
                upper_holes.append(hshape)
                f.prism(hshape.buffer(-.09,join_style=2),-.96,-.90,'door timber','central entrance / deeply recessed closed timber leaves')
                f.prism(hshape.buffer(.20,join_style=2).difference(hshape),-.25,.21,'vermilion timber','central entrance / deep portal frame')
                for du in [-1.82,0,1.82]:
                    f.box(u+du,6.5,.11,4.15,.16,-.79,'ochre painted line','central entrance / vertical leaf stile')
                probes.append({'point':list(f.point(u+.40,6.2,0)),'normal':list(f.n),'depth':.90,'material':'door timber','label':label+' / main door recess'})
                features['central_door_recesses']+=1
            else:
                shape=opening(float(u),z,width,h,arch=.52 if z>9 else 0)
                upper_holes.append(shape)
                probes.append(frame_window(b,f,shape,label+f' / bay {i} band {z}',detailed,8 if central else 6,5))
                features['window_openings']+=1
        if not (central and i==bays//2):
            stone_panel_pattern(b,f,u,9.15,width,1.13,label+f' / spandrel {i}',detailed)
        # Two base openings per broad bay; main bridge meets the entrance bay.
        for k in [-1,1]:
            if central and i==bays//2:continue
            shape=opening(float(u+k*bay*.23),.95,1.35,2.0)
            base_holes.append(shape)
            probes.append(frame_window(b,f,shape,label+f' / base window {i}/{k}',detailed,3,4,trim=True))
            features['window_openings']+=1
    if central:
        for sign in [-1,1]:
            u=sign*(f.length/2-pier/2)
            for z in [6.0,11.5]:
                shape=opening(u,z,1.05,1.35)
                upper_holes.append(shape)
                probes.append(frame_window(b,f,shape,label+f' / stone pier small window {sign}/{z}',detailed,2,2,trim=True))
                features['window_openings']+=1
    f.wall(0,4.3,base_holes,.52,'warm stone')
    # Stone wall has the full set of openings; red infill only spans each broad bay.
    f.wall(4.3,15.8,upper_holes,.52,'warm stone')
    for i,u in enumerate(centers):
        cell=box(u-bay/2+.22,4.38,u+bay/2-.22,14.62)
        cell=cell.difference(unary_union(upper_holes))
        f.prism(cell,.015,.085,'vermilion timber',label+f' / red bay field {i}')
    for i,u in enumerate(np.linspace(-span/2,span/2,bays+1)):
        p=f.point(float(u),0,.39)
        b.lathe(p[:2],[(4.3,.39),(4.52,.39),(4.70,.28),(14.65,.245),(15.1,.29)],'vermilion timber',
                segments=20 if detailed else 12,label=label+f' / full-height red column {i}')
        b.lathe(p[:2],[(4.3,.45),(4.48,.45),(4.62,.35)],'warm stone',segments=12,
                label=label+f' / column stone foot {i}')
        bracket(b,p[0],p[1],14.8,f.n[:2],label+f' / dougong {i}',detailed)
        features['full_height_red_columns']+=1
    painted_fascia(b,f,label,detailed)
    # A narrow actual stone terrace, with an entrance break, not a solid forecourt.
    if central:
        for sign in [-1,1]:
            u0,u1=((-f.length/2,-5.6) if sign<0 else (5.6,f.length/2))
            c=(u0+u1)/2
            f.box(c,4.22,u1-u0,.22,1.06,.30,'warm stone',label+' / terrace lip')
            rail(b,a=f.point(u0,0,.75),b=f.point(u1,0,.75),z=4.35,
                 label=label+f' / terrace balustrade {sign}',detailed=detailed)
        # Projecting painted entrance canopy and open balustraded upper ledge.
        f.box(0,9.20,6.7,.28,2.2,1.0,'blue painted bracket',label+' / central doorway canopy')
        f.box(0,9.42,6.85,.14,2.3,1.0,'golden glazed crest',label+' / canopy coping')
        rail(b,a=f.point(-3.05,0,2.05),b=f.point(3.05,0,2.05),z=9.50,height=.83,
             spacing=1.25,label=label+' / canopy balustrade',detailed=detailed)
        for u in [-2.8,2.8]:
            p=f.point(u,0,1.75)
            b.lathe(p[:2],[(4.3,.17),(8.9,.15)],'vermilion timber',segments=12,
                    label=label+' / slender entrance canopy post')
    return f


def transform_parts(parts,f):
    for p in parts:
        p['vertices']=[tuple(f.center+f.t*x-f.n*y+np.array([0,0,z])) for x,y,z in p['vertices']]


def side_end(b,a,q,label,detailed,probes,features):
    f=Facade(b,a,q,label);holes=[]
    doorway=opening(0,.65,2.65,3.5,arch=1.32,segments=32 if detailed else 16)
    holes.append(doorway)
    f.prism(doorway.buffer(-.09),-.85,-.77,'door timber',label+' / recessed round-arch timber door')
    f.prism(doorway.buffer(.20).difference(doorway),-.015,.15,'warm stone',label+' / actual arch surround')
    probes.append({'point':list(f.point(.35,1.9,0)),'normal':list(f.n),'depth':.77,
                   'material':'door timber','label':label+' / arched entrance'})
    probes.append({'point':list(f.point(.13,3.84,0)),'normal':list(f.n),'depth':.77,
                   'material':'door timber','label':label+' / upper arch door recess'})
    probes.append({'point':list(f.point(1.85,3.70,0)),'normal':list(f.n),'depth':0,
                   'material':'warm stone','label':label+' / solid arch shoulder control'})
    features['side_arch_doorways']+=1
    for u in [-7.7,-4.25,4.25,7.7]:
        shape=opening(u,1.2,1.35,2.5);holes.append(shape)
        probes.append(frame_window(b,f,shape,label+f' / lower side window {u}',detailed,3,4,trim=True));features['window_openings']+=1
    for z,h in [(5.8,3.0),(10.0,3.65)]:
        shape=opening(0,z,4.0,h,arch=.5 if z>9 else 0);holes.append(shape)
        probes.append(frame_window(b,f,shape,label+f' / upper central glazing {z}',detailed,6,5));features['window_openings']+=1
    f.wall(0,15.8,holes,.52,'warm stone')
    for u in [-2.30,2.30]:f.box(u,9.86,.44,10.80,.26,.14,'vermilion timber',label+' / upper red side pilaster')
    stone_panel_pattern(b,f,0,9.3,4.2,1.15,label+' / central geometric panel',detailed)
    painted_fascia(b,f,label,detailed)
    f.box(0,4.85,5.8,.27,1.75,.65,'warm stone',label+' / projecting doorway balcony')
    rail(b,a=f.point(-2.65,0,1.48),b=f.point(2.65,0,1.48),z=5.0,height=.9,
         spacing=1.35,label=label+' / balcony front',detailed=detailed)
    for sign in [-1,1]:
        rail(b,a=f.point(sign*2.65,0,.05),b=f.point(sign*2.65,0,1.48),z=5.0,height=.9,
             label=label+f' / balcony return {sign}',detailed=detailed,include_end=False)
    temp=Builder(PALETTE)
    stairs(temp,name=label+' / entrance steps',cx=0,width=4.5,y0=-4.4,y1=0,z0=0,z1=.65,
           count=5,detailed=detailed)
    transform_parts(temp.parts,f);b.parts.extend(temp.parts)
    return f


def rear_central(b,a,q,detailed,probes,features):
    """The visible north centre is predominantly pale masonry, not south bays.

    Vegetation hides exact rear fenestration and entry levels. Sparse end glazing
    and the small lower canopy are conservative author estimates; no precise
    mirrored historic reconstruction is asserted.
    """
    f=Facade(b,a,q,'north central masonry');holes=[]
    for u in [-18.2,18.2]:
        for z,h in [(5.1,3.25),(10.1,3.4)]:
            shape=opening(u,z,4.5,h,arch=.35 if z>9 else 0);holes.append(shape)
            probes.append(frame_window(b,f,shape,f'north outer glazing {u}/{z}',detailed,6,4))
            features['window_openings']+=1
        for side in [-1,1]:
            f.box(u+side*2.55,9.85,.34,10.75,.23,.12,'vermilion timber','north / limited outer red pilaster')
        stone_panel_pattern(b,f,u,9.17,4.6,1.05,'north / outer spandrel',detailed)
    for u in [-19.0,-14.0,-9.0,9.0,14.0,19.0]:
        shape=opening(u,1.0,1.4,2.0);holes.append(shape)
        probes.append(frame_window(b,f,shape,f'north base window {u}',detailed,3,4,trim=True))
        features['window_openings']+=1
    door=opening(0,.65,3.8,3.45);holes.append(door)
    f.prism(door.buffer(-.09),-.84,-.78,'door timber','north / recessed estimated lower entrance')
    f.prism(door.buffer(.18).difference(door),-.02,.13,'warm stone','north / entrance surround')
    probes.append({'point':list(f.point(.45,2.15,0)),'normal':list(f.n),'depth':.78,
                   'material':'door timber','label':'north / lower entry recess'})
    f.wall(0,15.8,holes,.52,'warm stone')
    for z in [5.0,9.3,13.9]:
        f.box(0,z,f.length-.2,.20,.22,.065,'stone reveal','north / visible horizontal masonry band')
    f.box(0,4.52,6.1,.28,1.8,.75,'stone reveal','north / small entry canopy')
    for u in [-2.3,2.3]:
        f.box(u,3.82,.22,1.15,1.15,.5,'stone reveal','north / canopy bracket')
    painted_fascia(b,f,'north central masonry',detailed)
    temp=Builder(PALETTE)
    stairs(temp,name='north entry short stair estimate',cx=0,width=4.5,y0=-3.3,y1=0,z0=0,z1=.65,
           count=5,detailed=detailed)
    transform_parts(temp.parts,f);b.parts.extend(temp.parts)


def gable_decoration(b,params,detailed):
    cx,cy=params['cx'],params['cy'];hx=params['inner_width'];hy=params['inner_depth']
    z0=params['skirt_z'];ridge=params['ridge_z'];name=params['name']
    ys=np.linspace(-hy,hy,25)
    profile=[(y,z0+(ridge-z0)*(1-(abs(y)/hy)**.88)+.27*(1-(abs(y)/hy)**2)) for y in ys]
    shape=Polygon([(-hy,z0),(hy,z0),*reversed(profile)]).buffer(-.22,join_style=2)
    for sign in [-1,1]:
        center=cx+sign*hx
        low,high=sorted([center+sign*.025,center+sign*.07])
        mapper=lambda y,z,x:(x,cy+y,z)
        b.prism(shape,low,high,mapper,'painted gable ground',name+f' / decorative gable field {sign}')
        if detailed:
            edge=shape.difference(shape.buffer(-.12,join_style=2))
            low,high=sorted([center+sign*.08,center+sign*.12])
            b.prism(edge,low,high,mapper,'ochre painted line',name+f' / gable frame {sign}')
            for j,y in enumerate(np.arange(-hy+1,hy,.95)):
                for k,z in enumerate(np.arange(z0+.6,ridge,.8)):
                    motif=Polygon([(y-.30,z),(y,z+.25),(y+.30,z),(y,z-.25)])
                    if shape.contains(motif):
                        b.prism(motif.difference(motif.buffer(-.045,join_style=2)),low,high,mapper,
                                'green painted bracket',name+f' / gable diamond {sign}/{j}/{k}')


def ceremonial_stair(b,name,cx,width,y0,y1,z0,z1,detailed):
    ramp_width=2.85
    side_width=(width-ramp_width)/2
    for sign in [-1,1]:
        c=cx+sign*(ramp_width/2+side_width/2)
        stairs(b,name=name+f' / side flight {sign}',cx=c,width=side_width,y0=y0,y1=y1,z0=z0,z1=z1,
               count=14,detailed=detailed,rail_sides=False)
        x=cx+sign*(width/2-.16)
        rail(b,a=[x,y0,z0],b=[x,y1,z1],z=.1,label=name+f' / outer stair rail {sign}',detailed=detailed)
    profile=Polygon([(y0,max(0,z0-.16)),(y1,max(0,z0-.16)),(y1,z1+.05),(y0,z0+.05)])
    b.prism(profile,cx-ramp_width/2,cx+ramp_width/2,lambda y,z,x:(x,y,z),'warm stone',name+' / ceremonial central ramp')
    for sign in [-1,1]:
        b.tube([(cx+sign*(ramp_width/2-.07),y0,z0+.12),(cx+sign*(ramp_width/2-.07),y1,z1+.12)],.09,
               'warm stone',sides=8,label=name+f' / ramp curb {sign}')
    if detailed:
        for i in range(1,8):
            t=i/8;y=y0+(y1-y0)*t;z=z0+(z1-z0)*t+.065
            b.tube([(cx-ramp_width*.38,y,z),(cx+ramp_width*.38,y,z)],.017,'stone reveal',sides=6,
                   label=name+f' / abstract ramp panel joint {i}')


def build(lod=False):
    detailed=not lod;b=Builder(PALETTE);probes=[]
    features={'window_openings':0,'full_height_red_columns':0,'side_arch_doorways':0,'central_door_recesses':0,
              'roof_groups':3,'bridge_road_axis':'local X east-west','south_central_main_bays':5,'south_wing_main_bays_each':3}
    poly=orient(Polygon(MAIN_POLYGON),sign=1)
    # A recessed internal author closure leaves visible openings and doorway
    # recesses; no internal rooms are claimed. It does not extend onto the road.
    b.plan_prism(poly.buffer(-1.25,join_style=2),0,15.4,'stone reveal','main building / recessed interior closure')
    pts=list(poly.exterior.coords)[:-1]
    for i,(a,q) in enumerate(zip(pts,pts[1:]+pts[:1])):
        length=np.linalg.norm(np.asarray(q)-a)
        if length<4:
            f=Facade(b,a,q,f'plan step return {i}');f.wall(0,15.8,(),.52,'warm stone')
        elif abs(q[0]-a[0])<1:
            side_end(b,a,q,'east side' if a[0]>0 else 'west side',detailed,probes,features)
        else:
            central=length>40
            label=('south' if (a[1]+q[1])/2<0 else 'north')+(' central' if central else (' east wing' if (a[0]+q[0])/2>0 else ' west wing'))
            if central and (a[1]+q[1])/2>0:
                rear_central(b,a,q,detailed,probes,features)
            else:
                long_front(b,a,q,5 if central else 3,label,central,detailed,probes,features)
    # Low plinth follows the source boundary; its small projection is original
    # exterior masonry, never expanded into a courtyard floor or road surface.
    ring=poly.buffer(.08,join_style=2).difference(poly.buffer(-.03,join_style=2))
    b.plan_prism(ring,.06,.34,'plinth granite','main building / low continuous plinth')
    for p in INPUT['roofs']:
        roof(b,**p,detailed=detailed);gable_decoration(b,p,detailed)
    bridge=road_bridge(b,**INPUT['bridge_estimate'],detailed=detailed)
    cx=INPUT['bridge_estimate']['cx']
    ceremonial_stair(b,'south lower stair',cx,13.2,-51.3,-33.0,0,2.15,detailed)
    b.box((cx,-31.5,2.04),(13.2,3.0,.22),'warm stone',label='south stair intermediate landing')
    ceremonial_stair(b,'south upper stair',cx,10.4,-30,-21.3,2.15,4.3,detailed)
    allv=np.asarray([v for p in b.parts for v in p['vertices']])
    meta={'id':ID,'name':'原上海特别市政府大楼（绿瓦大楼）外观候选',
      'status':INPUT['status'],'scope':'Three-part historic main building with independent ceremonial south stairs and true road-underpass bridge; author exterior, no interiors or campus neighbors.',
      'scope_kind':'historic-main-building-with-separate-approach',
      'local_origin_wgs84':[121.52123739682835,31.315220250550375],'local_heading_deg':0,
      'source_uuid':'3904106e-f668-46d4-a302-a13ccd00866a','source_local_id':525,'source_macro':'14-13722-6690',
      'documented_long_axis_m':93,'documented_central_depth_m':25,'documented_wing_depth_m':20,
      'documented_depth_interpretation':'plan depth; not frontage segments summing to 65 m',
      'documented_existing_height_m':None,'CNBH_22m_is_raster_estimate_not_measurement':True,
      'model_selected_central_ridge_m':26.7,'model_selected_wing_ridge_m':23.2,
      'model_selected_architectural_top_m':float(allv[:,2].max()),'model_ground_datum_m':0,
      'documented_storeys':4,'visible_facade_glazing_bands_above_base':2,
      'storey_datums_not_surveyed':True,'all_architectural_detail_dimensions_estimated':True,
      'all_elevation_datums_estimated':True,'stair_bridge_width_and_clearance_estimated':True,
      'approach_axis_photo_guided_not_exact_osm_centerline':True,
      'south_bridge_has_true_transverse_road_arch':True,'bridge_ground_and_overhead_scopes_separate':True,
      'east_upper_elevation_partially_occluded_in_reference':True,'north_facade_and_steps_photo_occluded_estimates':True,
      'decorative_patterns_simplified_original_geometry':True,'roof_finials_simplified':True,
      'campus_neighbors_modeled':False,'courtyard_ground_modeled':False,'road_fill_modeled':False,
      'photos_embedded':False,'interiors_modeled':False,'underground_modeled':False,
      'map_replacement':False,'original_historic_state_claimed':False,
      'geometry_license':'MIT','map_reference_license':'ODbL-1.0',
      'copyright':'Original parametric geometry: MIT; source footprint: ODbL-1.0; reference photographs retain their separate rights'}
    features['author_parts']=len(b.parts)
    return b,meta,features,probes


def main():
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);p.add_argument('--lod',action='store_true');a=p.parse_args()
    b,meta,features,probes=build(a.lod)
    a.out.mkdir(parents=True,exist_ok=True)
    out=a.out/(ID+('-lod.glb' if a.lod else '-raw.glb'))
    record=b.save(out,meta)
    (a.out/('features-lod.json' if a.lod else 'features.json')).write_text(json.dumps(features,ensure_ascii=False,indent=2)+'\n')
    if not a.lod:
        (a.out/'surface-probes.json').write_text(json.dumps(probes,ensure_ascii=False,indent=2)+'\n')
        (a.out/'model-input.json').write_text(json.dumps(INPUT,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:record[k] for k in ['file','bytes','sha256','triangles','parts','bounds_glb']},indent=2))


if __name__=='__main__':main()
