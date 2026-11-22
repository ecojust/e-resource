"""The first three public column stations behind Guang Er Warehouse's river gate, measured in plan 29 and photographs 23/30/31."""
import json
from pathlib import Path
import numpy as np
from shapely.geometry import Polygon
from south_entrance import finish

DATA=Path(__file__).resolve().parents[1]/'measurements/public-entrance-passage.json'
CONCRETE='River passage | exposed concrete'
SOFFIT='River passage | concrete ceiling'
WALK='River passage | warm grey paving'
JOINT='River passage | floor joints'
SIDE='River passage | charcoal edge tile'
STEEL='River passage | charcoal metal'
GLASS='River passage | shaded shop glazing'
GLASS2='River passage | warm shop glazing'
LIGHT='River passage | warm lamp diffuser'
REFLECTOR='River passage | satin pale reflector'
PALETTE={
    CONCRETE:finish([121,119,111],.94),SOFFIT:finish([134,129,118],.92),
    WALK:finish([166,160,148],.87),JOINT:finish([124,122,114],.96),
    SIDE:finish([62,64,62],.74),STEEL:finish([57,55,50],.53,.3),
    GLASS:finish([61,71,70],.27,.38),GLASS2:finish([87,80,64],.32,.32),
    LIGHT:finish([248,229,191],.51),REFLECTOR:finish([207,201,178],.45,.21),
}


def add_passage(b, lod=False, layout=None):
    """Build the measured straight portion. The open north end accepts the next floor segment.
    
    Optional passage_end_y chooses a shorter photographed segment. The three structural stations are
    retained at their measured coordinates. A longer undocumented passage is not generated.
    """
    low=lod is True or lod=='lod'
    layout={} if layout is None else layout
    data=json.loads(DATA.read_bytes())
    end=min(float(layout.get('passage_end_y',data['first_lateral_change_y_m'])),data['first_lateral_change_y_m'])
    start=0.0
    piers=np.array(data['pier_centres_x_y_m'],dtype=float)
    centre=float(piers.mean(axis=(0,1))[0])
    half=float(np.mean(data['column_grid_widths_m']))/2
    cap=float(data['relative_camera_30']['beam_underside_m'])
    def box(x0,x1,y0,y1,z0,z1,mat,name):
        if x1<=x0 or y1<=y0 or z1<=z0:return
        b.box([(x0+x1)/2,(y0+y1)/2,(z0+z1)/2],[x1-x0,y1-y0,z1-z0],mat,label=name)
    # Broad aisle widens immediately behind the mouth. The narrow neck terminates at the existing street threshold.
    plan=Polygon([(-2.485,start),(2.48,start),(2.48,.34),(centre+half,.43),
                  (centre+half,end),(centre-half,end),(centre-half,.43),(-2.485,.34)])
    b.prism(plan,-.095,-.001,lambda x,y,z:(x,y,z),WALK,'Passage | continuous level paving with entrance neck')
    tile_width=.74;tile_length=1.48
    if not low:
        # The photograph resolves larger rectangular centre stones and darker narrow perimeter paving.
        # Unit size is an estimate; all joints appear only in the accessible floor strip.
        for col in range(-4,5):
            x=centre+tile_width*(col+.5)
            box(x-.004,x+.004,.6,end,-.0015,.0012,JOINT,f'Floor | longitudinal joint {col+5}')
        for i in range(1,int(end/tile_length)+1):
            y=i*tile_length; box(centre-half+.39,centre+half-.39,y-.004,y+.004,-.0015,.0013,JOINT,f'Floor | transverse joint {i}')
    lateral=.55
    for side,sign in [('West',-1),('East',1)]:
        x=centre+sign*half
        box(x-.44,x+.44,.38,end,-.07,.003,SIDE,f'{side} | dark perimeter paving')
        glass_x=x+sign*(lateral+.09)
        for bay,(y1,y2) in enumerate(zip([.39,*piers[:,0,1]],[*piers[:,0,1],end]),1):
            y2=min(y2,end)
            if y1>=y2-.10:continue
            # A side opening to the next public branch occurs near the recorded stopping station.
            if bay==4 and side=='East': y2=min(y2,end-.80)
            shop_top=3.14;bottom=.13
            glazing=GLASS if (bay+(sign>0))%2 else GLASS2
            box(glass_x-.042,glass_x+.042,y1,y2,bottom,shop_top,glazing,f'{side} shopfront {bay} | glazing')
            for k,z in enumerate((.18,2.53,3.12),1):
                box(glass_x-.07,glass_x+.07,y1,y2,z-.035,z+.035,STEEL,f'{side} shopfront {bay} | rail {k}')
            lengths=y2-y1;count=max(1,int(round(lengths/(1.35 if low else 1.15))))
            for k,y in enumerate(np.linspace(y1+.024,y2-.024,count+1),1):
                box(glass_x-.072,glass_x+.072,y-.023,y+.023,bottom,shop_top,STEEL,f'{side} shopfront {bay} | frame {k}')
            box(glass_x-.16,glass_x+.16,y1,y2,shop_top+.03,cap-.06,CONCRETE,f'{side} shopfront {bay} | concrete head')
    for row,pair in enumerate(piers,1):
        for side,(x,y) in zip(('West','East'),pair):
            box(x-.225,x+.225,y-.27,y+.27,0.,cap+.015,CONCRETE,f'{side} concrete column | station {row}')
        y=float(pair[:,1].mean())
        if y<end:
            box(centre-half-.61,centre+half+.61,y-.27,y+.27,cap,cap+.40,CONCRETE,f'Passage | exposed crossbeam {row}')
    box(centre-half-.63,centre+half+.63,.39,end,cap+.40,cap+.54,SOFFIT,'Passage | exposed concrete soffit')
    # Folded linear reflectors. Two pale faces meet either side of a narrow continuous central metal fin.
    # The relative widths come from the intervals (315–333,346–391) and (692–738,751–768) at v250 in photo 30.
    for side,sign in [('West',-1),('East',1)]:
        axis=centre+sign*2.46
        def reflector_section(x0,x1,z0,z1,depth,mat,title,y1,y2):
            profile=Polygon([(x0,z0),(x1,z1),(x1,z1+depth),(x0,z0+depth)])
            b.prism(profile,-y2,-y1,lambda x,z,d:(x,-d,z),mat,title)
        first=.66;pitch=1.29
        units=max(1,int(np.ceil((end-first)/pitch)))
        for k in range(units):
            y1=first+k*pitch;y2=min(end,first+(k+1)*pitch)
            seam=.008 if not low and k else 0.
            if y2<=y1+seam:continue
            for direction in (-1,1):
                left,right=sorted((axis+direction*.045,axis+direction*.47))
                rightward=direction>0
                z0=4.13 if rightward else 4.30;z1=4.30 if rightward else 4.13
                reflector_section(left,right,z0,z1,.027,LIGHT,f'{side} light | folded panel {k+1} {direction:+}',y1+seam,y2)
                if not low:
                    out=axis+direction*.478
                    box(out-.011,out+.011,y1+seam,y2,4.295,4.36,REFLECTOR,f'{side} light | return {k+1} {direction:+}')
        box(axis-.048,axis+.048,first,end,4.107,4.172,STEEL,f'{side} light | continuous dark spine')
        for k,y in enumerate(np.arange(first+.48,end,2*pitch),1):
            box(axis-.022,axis+.022,y-.027,y+.027,4.17,cap+.405,STEEL,f'{side} light | ceiling hanger {k}')
