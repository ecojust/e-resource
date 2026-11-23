"""No. 8. West lawn gable and tall chimney, clipped side gable and cross-range."""
from numpy import array
from numpy.linalg import solve
from shapely.geometry import Polygon
from hongji_roof_geometry import BRICK, STONE, PALETTE, halfplane, height, roof_envelope, stack_box, strips_and_caps, triangular

DEFAULTS={'wall_width':7.12,'overhang':.59,'front_overhang':.60,'eave_z':5.57,'gable_rise':2.58,'ridge_depth':10.58}

def dimensions(layout):
    return {k:float(layout.get(k,v)) for k,v in DEFAULTS.items()}

def planes(layout):
    d=dimensions(layout);w=d['wall_width'];a=d['overhang'];depth=d['ridge_depth'];e=d['eave_z']
    rise=d['gable_rise'];k=e+rise;N=float(layout.get('north_cafe_outer_eave_x',-5.95))
    out=triangular('west lawn gable','x',(-a,w/2,w+a),(-d['front_overhang'],depth+.75),e,k)
    # The north cross-gable has a short hipped shoulder at its upper end.
    # The rake turns twice above the café doorway, as photographed in 2023.
    axis=depth-.78
    shear=.0743
    # Two 2023 images of the café side independently constrain the visible
    # lower eaves and clipped upper rectangle against both door thresholds.
    # The longer range retains its original ridge and far eave.
    outer_axis=axis-.133
    outer_half=3.740
    blend=N+2.65
    inner_axis=axis+shear*(blend-N)
    outer_eave=e-1.229
    clipped_z=k-1.511
    outer_crest=outer_eave+(clipped_z-outer_eave)*outer_half/(outer_half-1.278)
    lip_points=[(N,outer_axis-outer_half,outer_eave),(N,outer_axis,outer_crest),
                (N,outer_axis+outer_half,outer_eave)]
    inner_points=[(blend,inner_axis-3.87,e-.28),(blend,inner_axis,k-.20),
                  (blend,inner_axis+3.87,e-.28)]
    far_points=[(w+3.13,y+shear*(w+3.13-blend),z) for _,y,z in inner_points]
    cap_slope=(k-.2-clipped_z)/1.14
    cap_plane=(cap_slope,0.,clipped_z-cap_slope*N)
    for left,right in ((lip_points,inner_points),(inner_points,far_points)):
        for i in range(2):
            for rows in ((left[i],right[i],right[i+1]),(left[i],right[i+1],left[i+1])):
                poly=Polygon([(x,y) for x,y,_ in rows])
                plane=tuple(solve(array([[x,y,1.]for x,y,_ in rows]),array([z for _,_,z in rows])))
                diff=[cap_plane[q]-plane[q] for q in range(3)]
                keep=poly.intersection(halfplane(*diff))
                cap=poly.intersection(halfplane(*[-v for v in diff]))
                if keep.area>.00001:out.append(('transverse range',keep,plane))
                if cap.area>.00001:out.append(('clipped café end',cap,cap_plane))
    # The east roof beyond the cross-ridge occupies the adjoining *same*
    # range in the birds-eye image. Stop at the visible distinct roof step.
    back=depth+10.67
    rear=triangular('east roof to step','x',(-1.61,w*.52,w+1.21),(depth+.04,back+.45),e-.24,k-.37)
    end=Polygon([(-3,depth),(w+3,depth),(w+3,back+.2),(-3,back-1.16)])
    for name,poly,plane in rear:
        out.append((name,poly.intersection(end),plane))
    # Below the transverse ridge, two independent front photographs show the
    # north-side tiled cover extending left of the main gable. Its outer profile
    # has a very steep lower face and a flatter shoulder above a real break.
    x1=-4.85; x2=-4.02; inside=.20
    y0,y1,y2,y3=4.88,5.76,7.12,9.18
    low,fold,upper=e-1.61,e+.35,e+1.24
    # This outer corner is independently read in 2016 and 2023. A third
    # view exposes the eave edge, while foliage hides the exact outer tip.
    outline=[(-5.472,4.946,e-1.677),(inside,y0,low),(inside,y1,fold),(x1,y1,fold)]
    for indices in ((0,1,2),(0,2,3)):
        tri=[outline[i] for i in indices]
        plane=tuple(solve(array([[x,y,1.] for x,y,z in tri]),array([z for x,y,z in tri])))
        out.append(('low cafe skirt',Polygon([(x,y)for x,y,z in tri]),plane))
    pitch=(upper-fold)/(y2-y1)
    shoulder=Polygon([(x1,y1),(inside,y1),(inside,y2),(x2,y2)])
    out.append(('cafe shoulder',shoulder,(0.,pitch,fold-pitch*y1)))
    pitch=-.31
    poly=Polygon([(x2,y2),(inside,y2),(inside,y3),(x2,y3)])
    out.append(('cafe roof inner slope',poly,(0.,pitch,upper-pitch*y2)))
    return out

def roof_sections(layout):
    """Visible tile faces as (label, XY polygon, (dz/dx,dz/dy,z_intercept)); thick 79 mm."""
    return roof_envelope(planes(layout))

def wall_head_at(x,y,layout):
    z=height(planes(layout),x,y)
    return None if z is None else z-.083

def add_roof(b,lod,layout):
    for name,values in PALETTE.items():b.palette.setdefault(name,values)
    from garden_shells import footprint
    strips_and_caps(b,roof_sections(layout),8,lod,footprint(8,dimensions(layout)))
    d=dimensions(layout);z=d['eave_z']+d['gable_rise']
    x=float(layout.get('chimney_x',d['wall_width']*3.6466/7.12))
    y=float(layout.get('chimney_y',.171));ctr=(x,y)
    # Artwork and wall lettering below the roof belong to the façade unit.
    # The high brick shaft, two pale corbelled belts and square top belong here.
    scale=(d['wall_width']+2*d['overhang'])/8.30
    stem=(1.035*scale,.730*scale);base=z-.63*scale;top=z+2.054*scale
    stack_box(b,ctr,stem,base,top,BRICK,'8 | exposed chimney shaft')
    for i,(h,delta) in enumerate(((.77,.065),(1.72,.055))):
        for j,(step,inc) in enumerate(((-.045,.046),(0.,.092),(.068,.12))):
            low=z+(h+step)*scale
            stack_box(b,ctr,(stem[0]+2*inc*scale,stem[1]+2*inc*scale),low,low+delta*scale,STONE,f'8 | pale stack belt {i+1}.{j+1}')
    stack_box(b,ctr,(stem[0]+.025,stem[1]+.025),top,top+.56*scale,STONE,'8 | pale rectangular chimney cap')
