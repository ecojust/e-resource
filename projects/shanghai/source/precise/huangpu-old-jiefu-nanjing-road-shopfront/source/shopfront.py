"""Measured retail front and upper window rows around the two street faces."""
from functools import lru_cache
import numpy as np
from shapely.geometry import box,LineString
from shapely.ops import unary_union
from photo_architecture import Builder
from street_path import station,xyz,NORTH_LENGTH,CURVE_LENGTH,WEST_LENGTH
from nanjing_steel_windows import add_window,add_brick_pier,window_pair_dimensions,finish,PALETTE as WINDOW,GLASS,TRANSOM
from material_names import MATERIAL

STONE='Warm limestone shop piers'
SHADE='Shadowed shop moulding'
IRON='Patinated black shop metal'
BRONZE='Antique bronze light fittings'
SHOP_GLASS='Grey green shop glazing'
CANOPY='Dark bronze trim'
DISPLAY='Neutral display surface'
PALETTE={STONE:finish([192,174,145],.86),SHADE:finish([129,117,99],.91),
         IRON:finish([49,47,43],.5,.37),BRONZE:finish([161,135,87],.47,.49),
         SHOP_GLASS:finish([111,123,120],.34,.23),CANOPY:finish([75,71,63],.52,.41),
         DISPLAY:finish([89,92,95],.77)}
START=-NORTH_LENGTH;END=CURVE_LENGTH+WEST_LENGTH
LOWER_EDGE=9.1063;UPPER_EDGE=27.496;SCREEN_TOP=23.30
CROWN_START=-3.37794159;CROWN_END=12.94849192
# Every interval is a measured floor or overlapping stone section. The long
# straight profiles meet the rounded section at the two surveyed tangencies.
def spans(a,b,pitch=.34):
    points=[a,*np.arange(max(0.,a),min(b,CURVE_LENGTH),pitch),b]
    points.extend(x for x in [0.,CURVE_LENGTH] if a<x<b)
    return np.unique(np.round(points,6))
def box_strip(b,a,c,bottom,top,back,front,material,label):
    if c<=a or top<=bottom:return
    ss=spans(a,c)
    vertices=[]
    for s in ss:
        vertices.extend([xyz(s,bottom,front),xyz(s,bottom,back),xyz(s,top,back),xyz(s,top,front)])
    faces=[(3,2,1,0)]
    for i in range(0,len(vertices)-4,4):
        for k in range(4):
            j=(k+1)%4;faces.append((i+k,i+j,i+j+4,i+k+4))
    faces.append(tuple(range(len(vertices)-4,len(vertices))))
    b.add(vertices,faces,material,label)
def iron_trace(b,s,z,points,r,projection,label,lod):
    p=[xyz(s+u,z+v,projection) for u,v in points]
    b.tube(p,r,IRON,5 if lod else 8,label)
def shop(b,lod):
    # Central shafts read at the shop architrave. Straight bays continue
    # the measured pier spacing to the visible ends of the two street faces.
    piers=[START+.28,-36.52,-29.43,-22.33,-15.23,-8.13,-1.54,2.42,
           7.52,11.67,18.60,25.57,32.54,39.51,46.48,END-.28]
    for i,(left,right) in enumerate(zip(piers,piers[1:]),1):
        l=left+.46;r=right-.46;mid=(l+r)/2
        box_strip(b,l,r,.12,3.91,-.51,-.477,SHOP_GLASS,f'Shop {i} ground glazing')
        box_strip(b,l,r,5.45,7.89,-.35,-.325,SHOP_GLASS,f'Shop {i} transom glass')
        # Fine stiles, a shallow wainscot and the metal frieze below the upper glass.
        for x in [l,mid,r]:
            box_strip(b,x-.027,x+.027,.10,3.94,-.50,-.42,CANOPY,f'Shop {i} ground frames')
            box_strip(b,x-.027,x+.027,5.44,7.91,-.35,-.282,CANOPY,f'Shop {i} transom frame')
        for z in [.12,3.16,3.89,5.44,7.87]:
            box_strip(b,l,r,z,z+.048,-.49,-.27,IRON,f'Shop {i} transom rails')
        box_strip(b,l-.03,r+.03,4.01,5.42,-.17,.084,IRON,f'Shop {i} metal band')
        for z in [4.04,4.14,5.29,5.37]:
            box_strip(b,l,r,z,z+.025,.08,.105,CANOPY,f'Shop {i} band rim')
        # Alternating diagonal folds are visible on the dark shop frieze.
        repeat=max(2,round((r-l)/.65));width=(r-l)/repeat
        for j in range(repeat):
            x=l+j*width
            points=[(0,.48),(width/2,.88),(width,.48),(width/2,.12),(0,.48)]
            iron_trace(b,x,4.2,points,.018,.12,f'Shop {i} diamond folds',lod)
        if i in (7,8,9):
            # The central street entrance has two full-height doors behind the
            # sightline of the outer columns. Two tubular brass handles remain visible.
            box_strip(b,l,r,.07,.12,-.82,.40,STONE,f'Corner threshold {i}')
            for u in [mid-.145,mid+.145]:
                b.tube([xyz(u,.89,-.372),xyz(u,1.72,-.372)],.018,BRONZE,8,f'Door {i} paired pulls')
    for i,c in enumerate(piers,1):
        r=.50 if i not in (1,len(piers)) else .28
        box_strip(b,c-r,c+r,.03,7.97,-.45,.185,STONE,f'Shop pier {i}')
        box_strip(b,c-r-.03,c+r+.03,.025,.29,-.44,.216,SHADE,f'Shop pier {i} foot')
        # Narrow wall sconces are visible below the iron ribbons in the 2024 view.
        if i in (5,6,7,8,9,10,11,12):
            box_strip(b,c-.14,c+.14,1.87,3.34,.181,.227,BRONZE,f'Sconce {i} stone mount')
            box_strip(b,c-.062,c+.062,1.99,3.22,.228,.297,STONE,f'Sconce {i} tall face')
            for z in [1.95,3.20]:
                box_strip(b,c-.095,c+.095,z,z+.055,.224,.312,BRONZE,f'Sconce {i} brass caps')
    for number,(z,top,depth,mat) in enumerate([(7.87,8.02,.23,SHADE),(8.02,8.12,.31,STONE),
            (8.12,8.66,.26,STONE),(8.66,8.74,.31,SHADE),(8.74,8.84,.51,STONE),
            (8.84,8.98,.58,STONE),(8.98,9.1063,.42,STONE)],1):
        box_strip(b,START,END,z,top,-.44,depth,mat,f'Shop cornice {number}')
    # Narrow flutes alternate across every length of the stone entablature.
    for n,s in enumerate(np.arange(START+.08,END-.06,.19)):
        box_strip(b,s-.015,s+.015,8.18,8.65,.254,.267,SHADE,f'Shop frieze incisions {n//24+1}')
def openings():
    pair=window_pair_dimensions()
    dims=[]
    for i in range(-8,9):
        for base in pair:
            mid=(base['left']+base['right'])/2+i*3.5475
            if START+.52<mid<CROWN_START-.46:dims.append((mid,base['right']-base['left']))
    from corner_crown import layout
    for a,c,_,_ in layout()[2]:
        dims.append(((a+c)/2,c-a))
    dims.extend([(3.30,1.08),(5.49,1.12),(7.56,1.03)])
    for i in range(22):
        mid=12.03+i*1.80
        if CROWN_END+.55<mid<END-.56:dims.append((mid,1.04 if i%2 else 1.10))
    return sorted(dims)
@lru_cache(maxsize=32)
def sash_parts(width,height,lod):
    b=Builder(WINDOW)
    add_window(b,0.,width,0.,height,lod=lod,label='measured sash')
    return b.parts
def transformed_sash(b,mid,width,z,h,lod,label):
    left=mid-width/2
    for part in sash_parts(round(width,4),round(h,4),lod):
        p=np.asarray(part['vertices'],float)
        # Each individual window has a planar reveal even on the curved end;
        # its two jamb axes use the common local tangent and normal.
        xy,t,out=station(mid)
        q=np.empty_like(p);q[:,:2]=xy+(p[:,0,None]-width/2)*t-p[:,1,None]*out;q[:,2]=z+p[:,2]
        kind='glazing' if part['material'] in (GLASS,TRANSOM) else 'sash and spandrel'
        b.add(q,part['triangles'],part['material'],label+' '+kind)
def crown_light(b,section,number):
    from corner_crown import solid_strip
    stations=section[:,0]
    edge=section[:,1]
    bottom=np.full(len(stations),21.22)
    def strip(axis,base,top,front,back,material,part):
        solid_strip(b,axis,base,top,np.full(len(axis),front),np.full(len(axis),back),
                    material,f'Crown return {number} {part}')
    strip(stations,bottom,edge+.004,-.387,-.41,GLASS,'glazing')
    for x in (stations[0]+.021,stations.mean(),stations[-1]-.021):
        axe=np.clip([x-.023,x+.023],stations[0],stations[-1])
        strip(axe,[21.22]*2,np.interp(axe,stations,edge),-.308,-.386,IRON,'steel stiles')
    strip(stations,edge-.32,edge-.276,-.301,-.386,IRON,'sloping transom')
    strip(stations,edge,edge+.026,-.057,-.414,IRON,'top frame reveal')

def upper(b,lod):
    dims=openings()
    floors=[(11.18,3.13),(14.50,3.45),(18.10,3.04),(21.22,3.43)]
    pair=window_pair_dimensions()
    # Explicitly preserve the measured eastern and western sashes and their own
    # lower/upper edges in the lowest complete patterned row.
    pier_centres=[.5*(row['left']+row['right'])for row in pair]
    previous=START
    for i,(mid,width) in enumerate(dims,1):
        l=mid-width/2;r=mid+width/2
        if previous<l:
            for lo,hi in zip([previous,*[s for s in (CROWN_START,2.66,8.86,CROWN_END)if previous<s<l]],
                             [*[s for s in (CROWN_START,2.66,8.86,CROWN_END)if previous<s<l],l]):
                roof=SCREEN_TOP if CROWN_START<.5*(lo+hi)<CROWN_END else UPPER_EDGE
                if abs(mid-pier_centres[1])<.004:
                    z0=min(v['bottom'] for v in pair)-.06
                    z1=max(v['upper'] for v in pair)+.03
                    box_strip(b,lo,hi,LOWER_EDGE,z0,-.48,0.,MATERIAL,f'Brick pier {i} lower')
                    add_brick_pier(b,lo,hi,z0,z1,lod=lod,label='Measured north wide pier')
                    box_strip(b,lo,hi,z1,roof,-.48,0.,MATERIAL,f'Brick pier {i} upper')
                else:
                    box_strip(b,lo,hi,LOWER_EDGE,roof,-.48,0.,MATERIAL,f'Brick pier {i}')
        ceiling=SCREEN_TOP if CROWN_START<mid<CROWN_END else UPPER_EDGE
        box_strip(b,l,r,LOWER_EDGE+.09,10.91,-.41,-.389,GLASS,f'Lowest light {i}')
        box_strip(b,mid-.025,mid+.025,LOWER_EDGE+.06,10.94,-.387,-.312,IRON,f'Lowest light {i} stile')
        box_strip(b,l,r,LOWER_EDGE,LOWER_EDGE+.12,-.41,-.095,IRON,f'Lowest light {i} base')
        from corner_crown import stone_head_sections
        section=next((q for q in stone_head_sections() if abs((q[0,0]+q[-1,0])*.5-mid)<.01),None)
        if section is None and 2.65<mid<8.86:
            # Three exposed sets of sash lights below the changing curved
            # screen. Its steel rim covers the top of these lights.
            box_strip(b,l,r,10.90,11.70,-.405,-.389,TRANSOM,f'Below screen upper light {i}')
            box_strip(b,l,r,10.89,10.945,-.405,-.30,IRON,f'Below screen horizontal rail {i}')
            box_strip(b,l,r,11.70,SCREEN_TOP,-.48,-.10,MATERIAL,f'Screen supporting wall {i}')
            previous=r
            continue
        previous_top=10.91
        for floor,(z,h) in enumerate(floors,1):
            if floor==1:
                for n,c in enumerate(pier_centres):
                    if abs(c-mid)<.004:
                        z=pair[n]['bottom'];h=pair[n]['upper']-z
            if floor==4 and section is not None:break
            if z>=ceiling:break
            box_strip(b,l,r,previous_top,z,-.49,-.09,IRON,f'Bank of sashes {i} rails')
            height=min(ceiling,z+h)-z
            if height>0.05:transformed_sash(b,mid,width,z,height,lod,f'Window {i}.{floor}')
            previous_top=z+height
        if section is not None:
            box_strip(b,l,r,previous_top,21.22,-.49,-.09,IRON,f'Crown return {i} sill')
            crown_light(b,section,i)
        elif previous_top<ceiling:
            box_strip(b,l,r,previous_top,ceiling,-.43,-.105,MATERIAL,f'Parapet panels {i}')
        previous=r
    box_strip(b,previous,END,LOWER_EDGE,UPPER_EDGE,-.48,.01,MATERIAL,'West end jamb')
    for a,c in [(START,CROWN_START),(CROWN_END,END)]:
        box_strip(b,a,c,UPPER_EDGE-.20,UPPER_EDGE-.105,-.43,.054,STONE,'Flank upper string')
        box_strip(b,a,c,UPPER_EDGE-.105,UPPER_EDGE,-.45,.093,STONE,'Flank upper coping')
        for j,x in enumerate(np.arange(a+.18,c-.10,.47)):
            box_strip(b,x-.055,x+.055,UPPER_EDGE-.39,UPPER_EDGE-.18,-.006,.044,STONE,f'Flank corbels {int(a)}.{j//12}')
    # The advertising screen changed between photographs. Only the physical
    # rim and mounting plane shown in 2024 are present.
    for a,c,z,top,depth,mat,label in [
        (2.65,8.86,11.63,SCREEN_TOP,.178,IRON,'Curved screen housing'),
        (2.72,8.79,11.71,SCREEN_TOP-.08,.191,DISPLAY,'Curved display face'),
        (2.68,8.83,11.6,11.715,.234,CANOPY,'Curved screen lower lip'),
        (2.68,8.83,SCREEN_TOP-.092,SCREEN_TOP,.221,CANOPY,'Curved screen upper lip')]:
        box_strip(b,a,c,z,top,-.12,depth,mat,label)
