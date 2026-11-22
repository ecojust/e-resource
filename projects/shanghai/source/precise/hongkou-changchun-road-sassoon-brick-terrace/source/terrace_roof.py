"""Front roof pitches and the ridge visible above the Changchun Road street wall."""
import numpy as np
from shapely.geometry import box
from shapely.ops import unary_union
from terrace_wall import limits,finish,CORNICE,block
from sassoon_roof_windows import roof_openings
TILES=['Changchun terrace | weathered roof tile '+n for n in ('clay','umber','rose','brown')]
BED='Changchun terrace | dark joints below roof tiles'
PALETTE={k:finish(rgb,.94) for k,rgb in zip(TILES,[(140,83,61),(130,78,61),(146,94,75),(120,80,66)])}
PALETTE[BED]=finish([105,89,76])
def pitch_z(y):
    return 9.99+.742*(y+.36)
def slab(b,shape,low,high,mat,label):
    if shape.is_empty:return
    if shape.geom_type=='Polygon':
        if shape.area>.00001:b.prism(shape,low,high,lambda x,y,d:(x,y,pitch_z(y)+d),mat,label)
    elif hasattr(shape,'geoms'):
        for item in shape.geoms:slab(b,item,low,high,mat,label)
def add_roof(b,lod=False):
    left,right=limits();left-=.11;right+=.11;eave=-.36;ridge=4.73
    # The rear roof in the collection is separated from these street-facing windows by a ridge.
    # Only the documented front pitch and its short ridge finish are represented.
    holes=[]
    for row in roof_openings().values():
        coords=np.asarray(row['plan_xy']);l,f=coords.min(0);r,k=coords.max(0)
        holes.append(box(l+.025,f+.035,r-.025,k-.035))
    openings=unary_union(holes)
    extent=box(left,eave,right,ridge)
    deck=extent.difference(openings)
    slab(b,deck,-.09,.015,BED,'Terrace roof | front slope around seven dormers')
    block(b,left,right,eave-.06,eave+.16,pitch_z(eave)-.19,pitch_z(eave)-.025,CORNICE,'Terrace roof | board below eave')
    rows=15;step=(ridge-eave)/rows
    # Pan and cover joints remain visible at both distances; farther LOD groups neighbouring pans.
    tile_width=.216 if not lod else .432
    for i in range(rows):
        ya=eave+i*step+.004;yb=eave+(i+1)*step-.004
        xa=left-(tile_width*.5 if i%2 else 0);j=0
        while xa<right:
            lx=max(xa,left)+.004;rx=min(xa+tile_width,right)-.004
            if rx-lx>.018:
                footprint=box(lx,ya,rx,yb).difference(openings)
                mat=TILES[(13*i+7*j+i*j)%4]
                slab(b,footprint,.014,.053,mat,'Terrace roof | field tiles row '+str(i+1))
                if not lod:
                    edge=box(rx-.018,ya,rx,yb).difference(openings)
                    slab(b,edge,.047,.070,mat,'Terrace roof | lapped tile side')
            xa+=tile_width;j+=1
    for j,x in enumerate(np.arange(left,right,.39)):
        x1=min(right,x+.385)
        if x1>x+.05:
            b.tube([(x,ridge,pitch_z(ridge)+.045),(x1,ridge,pitch_z(ridge)+.045)],.095,TILES[j%4],10 if lod else 16,'Terrace roof | rounded ridge tile')
