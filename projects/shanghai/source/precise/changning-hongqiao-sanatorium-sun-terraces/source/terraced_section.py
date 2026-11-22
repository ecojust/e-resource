"""Four stepped concrete floors and the terrace colonnade shown in the historic section."""
from pathlib import Path
import json
import math

HERE = Path(__file__).resolve().parent
FRAME = json.loads((HERE.parent / 'measurements/terrace-frame.json').read_bytes())
FLOORS = FRAME['floor_to_roof_z_m']
FRONT = FRAME['south_edges_x_m']
PITCH = FRAME['estimated_tile_pitch_m']
FIRST, LAST = FRAME['longitudinal_bounds_grid_j']
LENGTH = (LAST-FIRST)*PITCH
REAR = FRAME['north_limit_x_m']
POSTS = [(v-FIRST)*PITCH for v in FRAME['upper_post_grid_j']]
UPPER = FLOORS[3]
PLASTER = 'Sunlit pale mineral render'
CONCRETE = 'Cut reinforced concrete'
TRIM = 'Pale deck fascia'
JOINT = 'Slate toned cement joint'
METAL = 'Light painted tubular guard'
SASH = 'Shadowed steel window frame'
GLASS = 'Grey glazing'

def block(b, corners, mat, name):
    xa, xb, ya, yb, za, zb = corners
    if min(xb-xa, yb-ya, zb-za) <= 0:
        raise ValueError(f'Empty {name}')
    b.box(((xa+xb)/2,(ya+yb)/2,(za+zb)/2),(xb-xa,yb-ya,zb-za),mat,label=name)

def rail(b, a, end, height, label, lod):
    # All four horizontal tubes continue around the same right-angle corner in the original image.
    outer, corner=FRONT[3],LENGTH-.108
    if a=='long':
        path=[(outer-.104,.035,height),(outer-.104,corner,height)]
    else:
        path=[(outer-.103,corner,height),(end,corner,height)]
    b.tube(path,.020 if height>UPPER+.84 else .014,METAL,8 if lod else 14,label)

def glazed_bays(b,x,ycuts,z,z1,level):
    sill=z+.81;head=z1-.40
    block(b,[x-.15,x+.014,0,LENGTH,z,sill],PLASTER,f'Level {level}/window apron')
    block(b,[x-.15,x+.020,0,LENGTH,head,z1-.070],PLASTER,f'Level {level}/continuous window head')
    for j,(a,c)in enumerate(zip(ycuts,ycuts[1:])):
        if c-a<.5:continue
        left=a+.16;right=c-.16
        for k,pos in enumerate([a,min(c-.15,right)]):
            block(b,[x-.17,x+.027,pos,pos+.155,sill-.006,head+.006],PLASTER,f'Level {level}/reveal bay {j+1}')
        block(b,[x-.055,x-.028,left,right,sill+.017,head-.019],GLASS,f'Level {level}/recessed glazing {j+1}')
        for k in range(5):
            pos=left+(right-left)*k/4
            block(b,[x-.035,x+.009,pos-.017,pos+.017,sill,head],SASH,f'Level {level}/steel uprights bay {j+1}')
        for k,pz in enumerate([sill+.019,head-.36,head-.02]):
            block(b,[x-.034,x+.013,left,right,pz-.018,pz+.018],SASH,f'Level {level}/transom bay {j+1}')
        block(b,[x-.14,x+.064,left-.028,right+.028,sill-.040,sill+.012],'Grey stone sill',f'Level {level}/projecting sill {j+1}')

def building(b,lod=False):
    # The section scale is dimensionless in the scan. One division is taken as roughly one metre.
    # Each structural span contains a pair of smaller window groups in the historic main elevation.
    structural=sorted(set([0.,*POSTS,LENGTH]));ycuts=[structural[0]]
    for a,c in zip(structural,structural[1:]):
        groups=max(1,round((c-a)/2.90));ycuts.extend(a+(c-a)*k/groups for k in range(1,groups+1))
    for level,(z,edge) in enumerate(zip(FLOORS[:4],FRONT),1):
        block(b,[REAR,edge,0,LENGTH,z-.180,z-.022],CONCRETE,f'Level {level}/floor slab')
        block(b,[edge-.115,edge+.010,0,LENGTH,z-.24,z-.011],TRIM,f'Level {level}/slab nose')
        block(b,[REAR,edge-.108,0,LENGTH,z-.024,z-.004],JOINT,f'Level {level}/terrace bedding')
        inside=FRONT[level] if level<4 else FRAME['upper_room_x_m']
        if level<4:
            block(b,[edge-.145,edge-.012,0,LENGTH,z-.022,z+.701],PLASTER,f'Level {level}/solid terrace front')
            block(b,[edge-.172,edge+.011,0,LENGTH,z+.700,z+.748],TRIM,f'Level {level}/upper parapet cap')
            block(b,[inside+.05,edge-.145,0,LENGTH,z-.004,z+.010],'Exposed cement paving',f'Level {level}/balcony pavement')
        glazed_bays(b,inside-.084,ycuts,z,FLOORS[level],level)
        for bay,y in enumerate(POSTS,1):
            block(b,[inside-.24,inside+.045,y-.14,y+.14,z-.026,FLOORS[level]-.07],PLASTER,f'Level {level}/gallery structural pier {bay}')
        # Close each room at the section's rear datum; the end facing the viewer is an open section.
        block(b,[REAR,REAR+.155,0,LENGTH,z-.003,FLOORS[level]-.069],'Rear wall in section',f'Level {level}/back wall')
    low,high=UPPER,FLOORS[4]
    for bay,y in enumerate(POSTS,1):
        block(b,[-.19,.10,y-.17,y+.17,low-.015,high-.086],PLASTER,f'Sundeck/gallery post {bay}')
        block(b,[-.175,.09,y-.162,y+.162,low+.004,low+.051],'Post plinth shadow',f'Sundeck/post foot {bay}')
    # The upper room is set behind the post row, with a cantilevered straight lip at its roof.
    block(b,[REAR,.94,0,LENGTH,high-.166,high],CONCRETE,'Sundeck/main roof')
    block(b,[.81,.96,0,LENGTH,high-.30,high-.02],TRIM,'Sundeck/shading fascia')
    block(b,[REAR,FRAME['upper_room_x_m']+.20,LENGTH-.22,LENGTH,low-.015,high-.11],PLASTER,'Sundeck/far bay return wall')
    # A dark rectangular end wall at the far left is visible beside the turned guard in the terrace photograph.
    block(b,[FRAME['upper_room_x_m']-.02,1.74,LENGTH-.225,LENGTH,low,high-.23],'End wall in shade','Sundeck/recessed squared end')
    outer=FRONT[3];end_wall=1.72;skirt_z=low+.153
    for a,box in [('outer',[outer-.194,outer-.010,.005,LENGTH,low-.022,skirt_z]),('end',[end_wall,outer-.010,LENGTH-.193,LENGTH,low-.022,skirt_z])]:
        block(b,box,'Charcoal parapet plinth','Sundeck/'+a+' parapet plinth')
    for i,rz in enumerate([.28,.47,.66,.91],1):
        for a in ['long','return']:rail(b,a,end_wall,low+rz,'Sundeck/'+a+' guard tube '+str(i),lod)
    positions=[.13,*[LENGTH*k/9 for k in range(1,9)],LENGTH-.107]
    for i,y in enumerate(positions):
        b.tube([(outer-.104,y,skirt_z),(outer-.104,y,low+.91)],.019,METAL,8 if lod else 12,'Sundeck/long guard upright '+str(i+1))
    for i,x in enumerate([2.25,3.37]):
        b.tube([(x,LENGTH-.107,skirt_z),(x,LENGTH-.107,low+.91)],.019,METAL,8 if lod else 12,'Sundeck/end guard upright '+str(i+1))
