"""Visible ends of the two garden elevations, including the smaller projecting bay."""
from functools import partial
import json
import math
from pathlib import Path
import numpy as np
from shapely.geometry import box
from shapely.ops import unary_union
import garden_bay as bay
import garden_main_corner as corner

OBS=json.loads((Path(__file__).resolve().parents[1]/'measurements/garden-extensions.json').read_bytes())
SIDE=OBS['side_projection']
X,Y=OBS['main_corner_m']
FRONT_Y=SIDE['front_y_m']
SIDE_X=SIDE['outer_x_m']
END_Y=SIDE['far_y_m']
EDGE_Z=corner.SOFFIT_Z
CAP_Z=6.355
ROOF='Garden roof | weathered charcoal felt and tile edge'
ROOF_SEAM='Garden roof | longitudinal charcoal lines'
DEEP='Garden entrance | dark recessed doorway'
GREEN='Garden entrance | muted green awning metal'
PALETTE={ROOF:dict(color=[.110,.105,.095],roughness=.91),
         ROOF_SEAM:dict(color=[.082,.078,.073],roughness=.90),
         DEEP:dict(color=[.036,.035,.029],roughness=.93),
         GREEN:dict(color=[.187,.244,.197],roughness=.82)}
PLANES={'main_front':('front',Y),'main_return':('side',X),
        'side_projection_front':('front',FRONT_Y),'side_projection_side':('side',SIDE_X)}

def slab(b,plane,d0,d1,shape,material,label):
    face,offset=PLANES[plane]
    if face=='front':
        b.prism(shape,d0,d1,lambda u,z,d:(u,offset-d,z),material,label)
    else:
        b.prism(shape,-d1,-d0,lambda u,z,d:(offset+d,u,z),material,label)
    if material==bay.BRICK:
        corner.brick_uv(b.parts[-1],face=='side')

def rectangle(b,plane,limits,d0,d1,material,label):
    slab(b,plane,d0,d1,box(*limits),material,label)

def sashes(b,row,lod):
    plane=row['plane']
    a,c,bottom,top=row['outer_trim_m']
    narrow=row['columns']==1
    front=partial(rectangle,b,plane)
    prefix=row['kind'].replace('garden-side second bay','Far bay').replace('garden frontage','Front').capitalize()
    label=lambda tag:prefix+' | '+tag
    jamb=.085
    if narrow:
        front((a,bottom,c,top),-.45,-.43,DEEP,label('shadow back'))
        # Only the shaded jamb and head are legible underneath the green canopy.
        for l,r in ((a,a+.084),(c-.084,c)):
            front((l,bottom,r,top),-.445,.0,bay.SOFFIT,label('plaster door return'))
        front((a+.084,top-.090,c-.084,top),-.445,.0,bay.SOFFIT,label('recessed soffit'))
        return
    l,r=a+jamb,c-jamb
    lo,hi=bottom+.110,top-.088
    for start,end in ((a,l),(r,c)):
        front((start,lo,end,hi),-.190,.040,bay.STONE,label('stone jamb'))
    front((a,hi,c,top),-.190,.052,bay.STONE,label('window head'))
    front((a-.016,bottom,c+.016,lo),-.191,.085,bay.LIP,label('projecting stool'))
    if not lod:
        front((a-.020,bottom+.018,c+.020,bottom+.038),.059,.096,bay.STONE,label('drip edge'))
    border=.027
    for start,end in ((l,l+border),(r-border,r)):
        front((start,lo,end,hi),-.200,-.118,bay.STEEL,label('steel jamb'))
    for start,end in ((lo,lo+border),(hi-border,hi)):
        front((l+border,start,r-border,end),-.198,-.120,bay.STEEL,label('steel rail'))
    us=np.linspace(l+border,r-border,row['columns']+1)
    zs=np.linspace(lo+border,hi-border,row['rows']+1)
    for col,(left,right) in enumerate(zip(us,us[1:])):
        for j,(low,high) in enumerate(zip(zs,zs[1:])):
            mat=bay.GLASS[(col+int(j>2)+int('upper' in row['kind']))%3]
            front((left,low,right,high),-.202,-.184,mat,label('glass pane'))
    for u in us[1:-1]:
        front((u-.012,lo+border,u+.012,hi-border),-.187,-.132,bay.MULLION,label('meeting stile'))
    for z in zs[1:-1]:
        front((l+border,z-.009,r-border,z+.009),-.186,-.136,bay.STEEL,label('glazing bar'))

def walls(b):
    ext=OBS['outer_extent_m']
    surfaces={'main_return':box(6.10,0.,ext['side_y_end'],EDGE_Z),
              'main_front':box(corner.FRONT_END,0,ext['front_x_end'],EDGE_Z),
              'side_projection_front':box(SIDE_X,0.,X,CAP_Z-.095),
              'side_projection_side':box(FRONT_Y,0.,END_Y,CAP_Z-.095)}
    # The adjoining corner leaves space for the previous terrace backing.
    # Join this narrow strip into the enlarged wall with the three true apertures.
    surfaces['main_front']=surfaces['main_front'].union(box(-1.77,bay.HEIGHT,corner.FRONT_END,8.67))
    for key,shape in surfaces.items():
        holes=[]
        for row in OBS['aperture_observations']:
            if row['plane']==key:
                l,r,lo,hi=row['outer_trim_m']
                holes.append(box(l,lo,r,hi))
        slab(b,key,-.214,0.,shape.difference(unary_union(holes)),bay.BRICK,
             'Garden extension | '+key.replace('_',' ')+' pierced masonry')
    # Narrow close along the positive-X side of the pre-existing projection.
    # It is an estimate where the garden photograph hides the return.
    b.box((bay.HALF-.085,Y/2,3.20),(.17,Y,6.4),bay.BRICK,label='Bay return | concealed closure')
    corner.brick_uv(b.parts[-1],True)

def far_terrace(b,lod):
    xmax=X+.008
    b.box(((SIDE_X+xmax)/2,(FRONT_Y+END_Y)/2,CAP_Z-.052),
          (xmax-SIDE_X+.085,END_Y-FRONT_Y+.085,.104),bay.COPING,label='Far balcony | stone cap')
    b.box(((SIDE_X+xmax)/2,(FRONT_Y+END_Y)/2,CAP_Z-.138),
          (xmax-SIDE_X+.05,END_Y-FRONT_Y+.05,.068),bay.SOFFIT,label='Far balcony | shadow beneath slab')
    sides=[('side_projection_front',SIDE_X+.018,xmax-.018,3),
           ('side_projection_side',FRONT_Y+.018,END_Y-.018,4)]
    for plane,left,right,count in sides:
        for h,radius in ((.092,.014),(.865,.024)):
            rectangle(b,plane,(left,CAP_Z+h-radius,right,CAP_Z+h+radius),-.029,.022,bay.RAIL,'Far balcony | upper and lower iron rails')
        poles=np.linspace(left,right,count+1)
        for u in poles:
            rectangle(b,plane,(u-.014,CAP_Z,u+.014,CAP_Z+.888),-.027,.016,bay.RAIL,'Far balcony | square iron upright')
        for u,v in zip(poles,poles[1:]):
            for t in ((.42,.58) if not lod else (.5,)):
                s=u+(v-u)*t
                rectangle(b,plane,(s-.008,CAP_Z+.09,s+.008,CAP_Z+.865),-.021,.009,bay.RAIL,'Far balcony | paired slender bars')

def continued_eave(b,plane,start,end,lod):
    side=plane=='main_return'
    edge=corner.EDGE_X if side else corner.EDGE_Y
    # Same three measured boards as the mitered corner, continued to the last
    # part of each roof edge for which the photograph has a sight line.
    for low,high,d0,d1,mat,label in [
            (0,.080,0.,edge,corner.UNDER,'pale soffit'),
            (.075,.146,edge*.90,edge*1.045,corner.BROWN,'stepped fascia'),
            (.138,.478,edge*.835,edge*1.09,corner.DARK,'dark outer lip'),
            (.473,.518,edge*.92,edge*1.08,corner.DARK,'upper rim')]:
        rectangle(b,plane,(start,EDGE_Z+low,end,EDGE_Z+high),d0,d1,mat,'Garden eave extension | '+label)

def roof(b,lod):
    ey=Y-corner.EDGE_Y;ex=X-corner.EDGE_X
    far_y=OBS['outer_extent_m']['side_y_end']
    far_x=OBS['outer_extent_m']['front_x_end']
    depth=OBS['roof']['exposed_depth_m'];h=OBS['roof']['eave_upper_z_m']
    slope=math.tan(math.radians(OBS['roof']['estimated_pitch_degrees']))
    def strip(vertices,name):
        # Top and bottom polygon both use the same mitred inner roof cut.
        lower=[(x,y,z-.065) for x,y,z in vertices]
        ring=lower+vertices
        faces=[(3,2,1,0),(4,5,6,7)]+[(k,(k+1)%4,(k+1)%4+4,k+4) for k in range(4)]
        b.add(ring,faces,ROOF,name)
    strip([(ex,ey,h),(far_x,ey,h),(far_x,ey+depth,h+depth*slope),
           (ex+depth,ey+depth,h+depth*slope)],'Garden roof | front weather slope')
    strip([(ex,ey,h),(ex+depth,ey+depth,h+depth*slope),
           (ex+depth,far_y,h+depth*slope),(ex,far_y,h)],'Garden roof | return weather slope')

def add_extensions(b,lod=False):
    b.palette.update(PALETTE)
    walls(b)
    for row in OBS['aperture_observations']:sashes(b,row,lod)
    far_terrace(b,lod)
    continued_eave(b,'main_front',corner.FRONT_END,OBS['outer_extent_m']['front_x_end'],lod)
    continued_eave(b,'main_return',corner.SIDE_END,OBS['outer_extent_m']['side_y_end'],lod)
    roof(b,lod)
