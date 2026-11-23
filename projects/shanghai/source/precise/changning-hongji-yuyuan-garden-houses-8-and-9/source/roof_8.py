"""No. 8. West lawn gable and tall chimney, clipped side gable and cross-range."""
from shapely.affinity import affine_transform
from shapely.geometry import Polygon
from hongji_roof_geometry import BRICK, STONE, PALETTE, height, roof_envelope, stack_box, strips_and_caps, triangular

DEFAULTS={'wall_width':7.12,'overhang':.59,'front_overhang':.60,'eave_z':5.57,'gable_rise':2.58,'ridge_depth':10.58}

def dimensions(layout):
    return {k:float(layout.get(k,v)) for k,v in DEFAULTS.items()}

def planes(layout):
    d=dimensions(layout);w=d['wall_width'];a=d['overhang'];depth=d['ridge_depth'];e=d['eave_z']
    rise=d['gable_rise'];k=e+rise;N=float(layout.get('north_cafe_outer_eave_x',-5.95))
    out=triangular('west lawn gable','x',(-a,w/2,w+a),(-d['front_overhang'],depth+.75),e,k)
    # The north cross-gable has a short hipped shoulder at its upper end.
    # The rake turns twice above the café doorway, as photographed in 2023.
    axis=depth-.78;half=3.87;run=(N,w+3.13)
    cross=triangular('transverse range','y',(axis-half,axis,axis+half),run,e-.28,k-.20)
    # The crossridge is fractionally oblique to the lawn ridge: its north
    # clipped end is at Y9.80 and its south end at about Y10.94.
    shear=.0743
    for name,poly,plane in cross:
        poly=affine_transform(poly,[1.,0.,shear,1.,0.,-shear*N])
        pa,pb,pc=plane
        plane=(pa-pb*shear,pb,pc+pb*shear*N)
        # A clipped triangle slopes up from the truncated summit in the end
        # gable face to the main ridge, fitted inside the lateral roof planes.
        end_plane=(.75,0.,k-.2-.78-.75*N)
        from hongji_roof_geometry import halfplane
        diff=[end_plane[i]-plane[i] for i in range(3)]
        keep=poly.intersection(halfplane(*diff))
        cap=poly.intersection(halfplane(*[-v for v in diff]))
        if not keep.is_empty:out.append((name,keep,plane))
        if not cap.is_empty:out.append(('clipped café end',cap,end_plane))
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
    x0=-5.24; x1=-4.85; x2=-4.02; inside=.20
    y0,y1,y2,y3=4.88,5.76,7.12,9.18
    low,fold,upper=e-1.61,e+.35,e+1.24
    for label,xa,xb,ya,yb,za,zb in [
            ('low cafe skirt',x0,x1,y0,y1,low,fold),
            ('cafe shoulder',x1,x2,y1,y2,fold,upper)]:
        pitch=(zb-za)/(yb-ya)
        poly=Polygon([(xa,ya),(inside,ya),(inside,yb),(xb,yb)])
        out.append((label,poly,(0.,pitch,za-pitch*ya)))
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
    strips_and_caps(b,roof_sections(layout),8,lod)
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
