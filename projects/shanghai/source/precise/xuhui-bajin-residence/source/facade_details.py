"""Photo-informed opening joinery. Dimensions/pane details remain estimates."""
import numpy as np
from shapely.geometry import Polygon, box
from shapely.ops import unary_union

def feature(b,f,shape,label,kind='window',wall=(-.28,0),closure=(-.22,-.19)):
    b.features.append({'id':f.label+'/'+label,'kind':kind,'facade_origin_architecture_XYZ':f.center.tolist(),'facade_U_architecture_XYZ':f.t.tolist(),'facade_outward_architecture_XYZ':f.n.tolist(),'plane_axis':'local d','plane_coordinate_m':0,'opening_polygon_UZ_m':list(shape.exterior.coords)[:-1],'opaque_wall_depth_interval_m':list(wall),'expected_closure':{'material':'spatial glass' if kind=='window' else 'recess backing','depth_interval_m':list(closure)},'dimensions_estimated':True})

def window(b,f,shape,label,cols=2,rows=3,sill=True):
    feature(b,f,shape,label,wall=(-.16,0) if f.label=='portal-inner-back' else (-.28,0))
    if f.label=='north-entry-bay' and label=='lower-right-shuttered-window':
        b.features[-1]['expected_closure']['additional_front_shutter']={'material':'green painted frame','depth_interval_m':[.012,.088],'diamond_aperture_separately_recorded':True}
    x0,z0,x1,z1=shape.bounds;w=x1-x0;h=z1-z0
    outer=shape.buffer(-.012,join_style=2);inner=shape.buffer(-.080,join_style=2)
    f.prism(inner,-.22,-.19,'spatial glass',label+'/glazing')
    ground=label.startswith('ground-bay')
    if ground:cols=4
    if label=='middle-attic-window':cols=rows=1
    bars=[]
    for k in range(1,cols):
        x=x0+w*k/cols;bw=.075 if k*2==cols else .034
        bars.append(box(x-bw/2,z0,x+bw/2,z1))
    if ground:
        bars.append(box(x0,z0+2.2-.037,x1,z0+2.2+.037))
        bars.append(box(x0,z0+.67-.035,x1,z0+.67+.035))
        for lo,hi in [(x0,x0+w/4),(x1-w/4,x1)]:bars.append(box(lo,z0+1.38-.018,hi,z0+1.38+.018))
    else:
        for k in range(1,rows):
            z=z0+h*k/rows;bw=.065 if label=='central-upper-window' else .031
            bars.append(box(x0,z-bw/2,x1,z+bw/2))
    panes=inner.difference(unary_union(bars)) if bars else inner
    f.prism(outer.difference(panes),-.16,-.045,'green painted frame',label+'/joinery-grid')
    # Fine stepped perimeter beading is a separate ring with no coincident skin.
    bead=shape.buffer(-.036,join_style=2).difference(shape.buffer(-.052,join_style=2))
    f.prism(bead,-.044,-.022,'green painted frame',label+'/perimeter-bead')
    if ground:
        for k in range(4):
            l=x0+w*k/4+.055;r=x0+w*(k+1)/4-.055
            panel=box(l,z0+.055,r,z0+.635)
            f.prism(panel,-.17,-.13,'green painted frame',label+f'/lower-panel-{k}')
            mould=panel.buffer(-.036).difference(panel.buffer(-.060))
            f.prism(mould,-.129,-.105,'green painted frame',label+f'/panel-bead-{k}')
        for side in [-1,1]:
            u=(x0+x1)/2+side*.075
            f.box(u,z0+1.15,.025,.15,.038,-.010,'dark door hardware',label+'/door-handle')
    if sill:
        f.box((x0+x1)/2,z0-.073,w+.25,.13,.32,.045,'white trim',label+'/stone-sill')
        if f.label.startswith('north'):
            f.box((x0+x1)/2,z1+.075,w+.26,.12,.28,.025,'white trim',label+'/stone-lintel')


def extras(b,W,D,H,roof):
    from photo_architecture import Facade
    half=W/2;y0=-D/2;nf=D/2+H['entry_bay_projection'];bh=H['entry_bay_width']/2
    south=Facade(b,(-half,y0),(half,y0),'south-garden')
    # Five photographed diamonds; central diamond taller, dimensions estimated.
    for i,x in enumerate([-.52,-.26,0,.26,.52]):
        hh=.55 if i==2 else (.39 if i in [1,3] else .32)
        p=Polygon([(x-.12,3.95),(x,3.95-hh/2),(x+.12,3.95),(x,3.95+hh/2)])
        south.prism(p,.005,.025,'white trim',f'observed-diamond-ornament-{i+1}')
    # Tiny apex ventilation slot visible above the arched attic. It is a
    # shallow dark recess in the evidence, not an invented window grid.
    # The large wall already has ten documented through vents below attic.
    north=Facade(b,(bh,nf),(-bh,nf),'north-entry-bay')
    # Observed single shutter on north-right lower window. True diamond cutout.
    u=2.95;z=1.12;w=.94;h=1.39
    panel=box(u-w/2,z+.03,u+w/2,z+h)
    diamond=Polygon([(u-.075,z+1.08),(u,z+.98),(u+.075,z+1.08),(u,z+1.18)])
    louverhole=box(u-.36,z+.13,u+.36,z+.64)
    outer=panel.difference(unary_union([diamond,louverhole]))
    north.prism(outer,.012,.065,'green painted frame','shutter/right-leaf-with-diamond-cutout')
    frame=panel.difference(panel.buffer(-.045,join_style=2))
    north.prism(frame,.066,.088,'green painted frame','shutter/right-raised-stiles')
    for k in range(7):
        zz=z+.17+k*.068
        # Tilted solid louvers, open gaps between them; tangent frame is right-handed.
        slope=.35
        poly=Polygon([(u-.355,zz-.027),(u+.355,zz-.027),(u+.355,zz+.027),(u-.355,zz+.027)])
        def mapping(uu,vv,dd):return north.point(uu,vv,dd+slope*(vv-zz))
        b.prism(poly,.027,.044,mapping,'green painted frame',f'north-entry-bay/shutter/right-louver-{k+1}')
    feature(b,north,diamond,'shutter/right-diamond-aperture','shutter cutout',(.012,.065),(-.22,-.19))
    b.features[-1]['expected_closure']['material']='spatial glass'
    # North arch keystone is kept separate from the stone ring.
    key=Polygon([(-.13,3.67),(.13,3.67),(.18,4.28),(-.18,4.28)])
    north.prism(key,.066,.15,'white trim','tapered-observed-keystone')
    # Visible bargeboards: white fascia underneath a narrow green roof edge.
    bounds=roof['bounds'];xs=[bounds[0],-half,-H['roof_knee_x'],0,H['roof_knee_x'],half,bounds[2]]
    for face_y,label in [(bounds[1],'south-barge'),(bounds[3],'north-eave')]:
        for i,(x0,x1) in enumerate(zip(xs,xs[1:])):
            # Segment at any hip-intersection x as well, so tops never twist.
            if label=='south-barge':zz=lambda x:roof['south_profile'](x)
            else:zz=lambda x:roof['height'](x,face_y)
            cuts=[x0,x1]
            for p in roof['patches']:
                for px,py in list(p['polygon'].exterior.coords):
                    if abs(py-face_y)<1e-8 and x0+1e-8<px<x1-1e-8:cuts.append(px)
            cuts=sorted(set(cuts))
            for j,(a,c) in enumerate(zip(cuts,cuts[1:])):
                z0,z1=zz(a),zz(c)
                f=Facade(b,(a,face_y),(c,face_y),f'{label}/{i}/{j}') if label=='south-barge' else Facade(b,(c,face_y),(a,face_y),f'{label}/{i}/{j}')
                if label!='south-barge':z0,z1=z1,z0
                pp=Polygon([(-f.length/2,z0-.28),(f.length/2,z1-.28),(f.length/2,z1-.081),(-f.length/2,z0-.081)])
                f.prism(pp,-.055,.005,'white trim','white-fascia')
    # Discrete dark-green brackets visible beneath the south gable's verge.
    for side in [-1,1]:
        for i,x in enumerate([2.35,4.55,6.25]):
            xx=side*x;zz=roof['south_profile'](xx)-.25
            b.box((xx,y0-.13,zz-.10),(.13,.40,.20),'green painted frame',label=f'south-garden/eave-bracket-{side}-{i}')
    # Two restrained downpipes following the observed garden end positions.
    for x in [-half+.09,half-.09]:
        b.tube([(x,y0-.07,.40),(x,y0-.07,6.38)],.038,'dark door hardware',8,'south-garden/observed-downpipe')
