"""The large dark glazed field recorded at the centre of the 1930s elevation."""
from pathlib import Path
import json
import numpy as np
from shapely.geometry import Polygon
from rosholt_front_plane import on_face

EVIDENCE=json.loads((Path(__file__).resolve().parents[1]/'measurements/ro-s018-central-glazing.json').read_text())
Y=EVIDENCE['frame_plane_y_m']
DARK='1938 centre | dark frame'
BEAD='1938 centre | outer glazing bead'
RECESS='1938 centre | shaded rebate'
LINTEL='1938 centre | grey head lining'
PANEL='1938 centre | opaque lower field'
GLASS=['1938 centre | pane tone '+n for n in ['A','B','C','D','E']]
def finish(v,roughness,metallic=0.):
    col=(float(v)/255+.055)/1.055
    return dict(color=[col**2.4]*3,roughness=roughness,metallic=metallic)
PALETTE={DARK:finish(51,.63,.14),BEAD:finish(66,.61,.15),RECESS:finish(39,.88),LINTEL:finish(125,.9),PANEL:finish(54,.82)}
PALETTE.update({name:finish(val,.29,.18)for name,val in zip(GLASS,[61,75,89,104,117])})
def native(x,y):return (581.3+.052*(y-422)+x,y+.0215*x)
def zone(x0,x1,y0,y1):
    """Map the four measured corners to the common frame plane before extrusion."""
    corners=[native(x0,y0),native(x0,y1),native(x1,y1),native(x1,y0)]
    return Polygon([(p[0],p[2])for p in (on_face(uv,Y)for uv in corners)])
def slab(b,p,depth,thick,material,label):
    # X cross Z points toward the viewer (negative model Y).
    b.prism(p,-(depth+thick),-depth,lambda x,z,d:(x,-d,z),material,label)
def tone(col,row):
    grey=EVIDENCE['pane_column_row_middle_grey_0_to_255'][col][row]
    return GLASS[int(np.digitize(grey,[50,73,91,112]))]
def add_central_glazing(b,lod=False):
    b.palette.update(PALETTE)
    bars=[r['centre']for r in EVIDENCE['tested_x_mullions']]
    courses=[r['centre']for r in EVIDENCE['tested_y_transoms']]
    bottom=EVIDENCE['lower_dark_crosspiece_y']
    edges=[3.6]+bars+[60.8]; rows=courses+[bottom]
    # The camera looks into a broad, shaded rectangular lining. Dark jambs
    # and the distinctly lighter head are separate from the three crossbars.
    slab(b,zone(-.25,68.75,421.98,429.63),.10,.211,LINTEL,'1938 infill | grey head lining')
    slab(b,zone(-.25,3.74,429.50,499.02),.14,.17,RECESS,'1938 infill | western reveal')
    slab(b,zone(60.57,68.75,429.50,499.02),.14,.17,RECESS,'1938 infill | eastern reveal')
    slab(b,zone(2.16,62.63,429.52,499.02),.324,.036,RECESS,'1938 infill | common shadow backing')
    for i,(x,half) in enumerate(zip(edges,[1.15,.83,1.08,.82,1.10])):
        slab(b,zone(x-half,x+half,courses[0]-.55,bottom+.69),Y,.061,DARK,f'1938 infill | vertical framing {i+1}')
    for j,(yy,half) in enumerate(zip(rows,[1.12,.84,1.04,.88])):
        for i,(lo,hi)in enumerate(zip(edges,edges[1:])):
            # Meet the vertical jambs without overlapping independent solids.
            halfs=[1.15,.83,1.08,.82,1.10]
            slab(b,zone(lo+halfs[i],hi-halfs[i+1],yy-half,yy+half),Y,.061,DARK,f'1938 infill | horizontal rail {j+1}.{i+1}')
    xpad=[1.15,.83,1.08,.82,1.10];ypad=[1.12,.84,1.04,.88]
    for i,(lo,hi)in enumerate(zip(edges,edges[1:])):
        for j,(top,base)in enumerate(zip(rows,rows[1:])):
            opening=zone(lo+xpad[i],hi-xpad[i+1],top+ypad[j],base-ypad[j+1])
            pane=opening if lod else opening.buffer(-.016,join_style=2)
            slab(b,pane,Y+.042,.018,tone(i,j),f'1938 infill | glass {i+1}.{j+1}')
            if not lod:
                slab(b,opening.difference(pane),Y+.024,.039,BEAD,f'1938 infill | glazing rebate {i+1}.{j+1}')
    slab(b,zone(2.16,62.63,bottom+.73,499.02),Y+.014,.063,PANEL,'1938 infill | lower dark field to hedge-line')
    # The catalogued photograph does not show the lower termination. The
    # private interiors and colours cannot be reconstructed from this source.
