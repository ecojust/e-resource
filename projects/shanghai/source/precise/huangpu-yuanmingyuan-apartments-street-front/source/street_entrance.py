"""Four courtyard entrance columns, recessed timber door, projection awnings and street windows."""
from pathlib import Path
import json
import numpy as np
from shapely import affinity
from shapely.geometry import LineString,Point,Polygon,box
from shapely.ops import unary_union
from east_photo_plane import on_wall
from material_names import MATERIAL
from wing_casements import finish

SURVEY=Path(__file__).resolve().parents[1]/'measurements'
STONE='Drab cream carved entrance stone'
DAMP='Weathered limestone edges'
GRANITE='Grey entrance stair granite'
WOOD='Oxide red varnished timber'
METAL='Dark metal wall letters'
GLASS='Deep brown shop windows'
FANGLASS='Mirrored grey fanlight panes'
AWNING='Black canvas shop awnings'
BRASS='Weathered plaque brass'
INNER='Shaded timber door interior'
PALETTE={STONE:finish([180,169,150],.88),DAMP:finish([130,123,108],.94),
 GRANITE:finish([139,138,131],.88),WOOD:finish([79,43,39],.56),METAL:finish([58,56,53],.61,.23),
 GLASS:finish([77,83,79],.33,.24),FANGLASS:finish([87,85,84],.34,.18),AWNING:finish([44,44,47],.93),
 BRASS:finish([140,118,79],.61,.34),INNER:finish([46,34,31],.93)}
def plate(b,geom,y0,y1,mat,label):
    if geom.is_empty:return
    b.prism(geom,-y1,-y0,lambda x,z,d:(x,-d,z),mat,label)
def rect(a,c,y=0):
    u,v,r,s=map(float,a)
    world=[on_wall(x,z,y,c) for x,z in [(u,v),(r,v),(r,s),(u,s)]]
    pts=np.array(world);return box(np.mean(pts[[0,3],0]),np.mean(pts[[2,3],2]),np.mean(pts[[1,2],0]),np.mean(pts[[0,1],2]))
def tier(b,left,right,z,steps,title):
    for i,(height,front,mat) in enumerate(steps,1):
        plate(b,box(left,z,right,z+height),front,.094,mat,f'{title} {i}')
        z+=height
def dressed_column(b,x,y,lo,hi,r,lod,name,red=False):
    rise=hi-lo
    profile=np.array([[0,1.33],[.018,1.34],[.034,1.27],[.040,1.12],[.050,1.16],[.061,1.10],[.072,1.00],[.46,.987],[.79,.955],[.833,.95],
                      [.840,1.08],[.853,1.10],[.862,.997],[.871,1.02],[.896,1.305],[.912,1.29],[.940,1.08],[.970,1.16]])
    profile[:,0]=lo+profile[:,0]*rise;profile[:,1]*=r
    if red:
        b.lathe([x,y],profile[:7].tolist(),STONE,20 if lod else 36,name+' base')
        b.lathe([x,y],profile[6:11].tolist(),MATERIAL,20 if lod else 40,name+' brick shaft')
        b.lathe([x,y],profile[10:].tolist(),STONE,20 if lod else 36,name+' collar')
    else:b.lathe([x,y],profile.tolist(),STONE,20 if lod else 40,name+' shaft and foot')
    # Two parallel scrolls cast a shallow shadow against each capital at the street face.
    z=lo+.941*rise
    block=box(x-r*1.40,z-r*.43,x+r*1.40,hi-.012)
    plate(b,block,y-r*1.08,y+r,STONE,name+' head')
    for side in [-1,1]:
        centre=np.array([x+side*r*1.05,z-r*.04]);t=np.linspace(.0,2.13*np.pi,26 if lod else 62)
        spiral_r=np.linspace(.47*r,.052*r,len(t))
        nodes=np.c_[centre[0]+side*spiral_r*np.cos(t),np.full(len(t),y-r*1.14),centre[1]+spiral_r*np.sin(t)]
        b.tube(nodes,r*.082,DAMP,5 if lod else 9,name+' volute shadow')
        nodes[:,1]-=r*.065;b.tube(nodes,r*.067,STONE,5 if lod else 8,name+' scroll relief')
        eye=Point(centre).buffer(.07*r,quad_segs=5 if lod else 10)
        plate(b,eye,y-r*1.29,y-r*1.10,STONE,name+' volute eye')
    b.box([x,y,hi-.029],[r*3.06,r*2.50,.063],STONE,label=name+' square abacus')

def add_entrance(b,lod):
    rec=json.loads((SURVEY/'entrance-lower-front-2016.json').read_bytes())
    cam=rec['camera']
    huge=rect(rec['door_opening_px'],cam,.745)
    shops=[rect(row,cam)for row in rec['shop_openings_px']]
    a,_,d,_=huge.bounds
    holes=unary_union([box(a,-.05,d,6.24),*shops])
    facade=box(-11.73,-.03,11.73,6.23).difference(holes)
    plate(b,facade,0.,.74,MATERIAL,'Lower street brick wall with real openings')
    # Brick piers support the paired columns and define the width of the stairs.
    for i,row in enumerate(rec['plinths_px'],1):
        shape=rect(row,cam,.82)
        a,c,d,e=shape.bounds
        plate(b,box(a,-.02,d,e),.82,2.57,MATERIAL,'Doorway brick plinth '+str(i))
        for shift,height,depth,mat in [(0,.048,-.072,DAMP),(.048,.074,-.106,STONE),(.122,.039,-.065,STONE)]:
            plate(b,box(a-.033,e+shift,d+.033,e+shift+height),depth+.82,2.58,mat,f'Portal plinth {i} stone course {shift}')
    for i,(u,ends)in enumerate(zip(rec['column_axes_u'],rec['shaft_outline_at_mid_u']),1):
        axis_plane=1.025
        centre=on_wall(u,500,axis_plane,cam)[0]
        r=(on_wall(ends[1],500,axis_plane,cam)[0]-on_wall(ends[0],500,axis_plane,cam)[0])/2
        lo=on_wall(u,554,axis_plane,cam)[2];hi=on_wall(u,445.5,axis_plane,cam)[2]
        dressed_column(b,centre,axis_plane,lo,hi,r,lod,f'Entrance column {i}')
    a,z0,d,z1=huge.bounds
    lintel=rect(rec['front_lintel_px'],cam,.745)
    # The photographed infill is stone over the opening; neighbouring piers stay brick.
    plate(b,box(a,z1-.032,d,6.10),.745,1.37,STONE,'Chinese inscription stone lintel')
    # Behind the lintel its full-width soffit runs back to the timber fanlight wall.
    plate(b,box(a,z1,d,z1+.068),.747,2.79,STONE,'Entrance shallow soffit')
    b.box([(a+d)/2,.77,.066],[d-a,.95,.132],GRANITE,label='Vestibule outer tread')
    for i in range(1,4):
        b.box([(a+d)/2,.72+i*.29,.058+i*.064],[d-a-.025,.315,.116+i*.128],GRANITE,label=f'Vestibule tread {i}')
    # Dark shopfront boards behind the four sashes. The iron frames, glass,
    # projecting square limestone sills and curved fabric awnings follow the two photos.
    for i,opening in enumerate(shops,1):
        l,bottom,r,top=opening.bounds;mid=(l+r)/2
        plate(b,opening.buffer(.02,join_style=2),.229,.27,GLASS,f'Street shop {i} glass')
        plate(b,opening.difference(opening.buffer(-.038,join_style=2)),.169,.23,WOOD,f'Street shop {i} timber frame')
        side=.11;contour=[(l-side,.085,top+.12),(r+side,.085,top+.12),(r+side,-.71,top-.17),(l-side,-.71,top-.17),
                           (l-side,.085,top+.028),(r+side,.085,top+.028),(r+side,-.71,top-.301),(l-side,-.71,top-.301)]
        b.add(contour,[(3,2,1,0),(4,5,6,7),(1,5,4,0),(2,6,5,1),(3,7,6,2),(0,4,7,3)],AWNING,f'Shop {i} sloping awning')
        b.tube([contour[7],contour[6]],.012,METAL,5 if lod else 8,f'Shop {i} awning rod')
        plate(b,box(l-.076,top+.05,r+.076,top+.27),-.052,.072,STONE,f'Shop {i} dressed head')
    for i,row in enumerate(rec['shared_lower_sills_px'],1):
        l,bot,r,top=rect(row,cam).bounds
        tier(b,l,r,bot,[(.05,-.091,MATERIAL),(.14,-.078,MATERIAL),(.034,-.091,DAMP),(.051,-.152,STONE)],f'Paired shop sill {i}')
    for i,x in enumerate([-3.71,3.47],1):
        plate(b,box(x-.20,2.59,x+.20,3.27),-.048,-.012,BRASS,f'Entrance wall plate {i}')
        plate(b,box(x-.155,2.64,x+.155,3.22),-.060,-.050,DAMP,f'Entrance wall plate {i} field')
    for i,x in enumerate([a-.055,d+.055],1):
        b.tube([[x,-.075,.07],[x,-.075,5.92],[x,-.158,6.10]],.047,METAL,8 if lod else 16,f'Drain pipe along portal {i}')
    for l,r in [(-11.73,a-.02),(d+.02,11.73)]:
        tier(b,l,r,5.90,[(.12,-.085,MATERIAL),(.048,-.135,DAMP),(.079,-.186,STONE),(.083,-.234,DAMP)],'Above ground floor return '+str(round(l)))
    for j,(low,high,fa) in enumerate([(5.37,5.51,.69),(5.51,5.57,.56),(5.57,5.86,.50),(5.86,5.91,.57),(5.91,5.99,.46),(5.99,6.08,.39),(6.08,6.16,.43),(6.16,6.23,.53)]):
        plate(b,box(a-.04,low,d+.04,high),fa,1.38,STONE,'Chinese inscription stepped cornice '+str(j+1))
    for j,(start,end) in enumerate([(-2.84,a+.01),(d-.01,2.77)]):
        if end-start>.003:plate(b,box(start,-.01,end,6.23),.745,1.32,MATERIAL,'Outer reveal and support '+str(j+1))
    return huge

def add_metal_letters(b):
    j=json.loads((SURVEY/'five-entrance-characters.json').read_bytes())
    for item in j['letters']:
        def ring(pts):
            return [(p[0],p[2])for p in (on_wall(u,v,.737)for u,v in pts)]
        shapes=[Polygon(ring(g['shell']),[ring(h)for h in g['holes']]).buffer(0) for g in item['strokes']]
        plate(b,unary_union(shapes),.727,.752,METAL,'Entrance cast lettering '+item['character'])
