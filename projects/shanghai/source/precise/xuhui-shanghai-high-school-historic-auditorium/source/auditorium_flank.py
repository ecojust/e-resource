"""Eastern auditorium windows and the visible return at the stage, from the 1934 image."""
from pathlib import Path
import json

from shapely.geometry import box
from shapely.ops import unary_union

CAST = 'Shanghai High School hall | cool grey cast trim'
WALL = 'Shanghai High School hall | ochre render'
FRAME = 'Shanghai High School hall | dark east window frames'
GLASS = 'Shanghai High School hall | recessed east window glass'
PALETTE = {
    FRAME: dict(color=[.137,.129,.111], roughness=.72),
    GLASS: dict(color=[.149,.177,.172], roughness=.33,metallic=.16),
}
MEASURED = Path(__file__).absolute().parents[1]/'measurements/registered-east-flank-plane.json'


def add_flank(b, lod=False):
    measured = json.loads(MEASURED.read_bytes())
    x = measured['east_x']
    axes = measured['pier_axes_y']
    bays = measured['bays']
    wall_start, wall_end = measured['wall_limits_y']
    half = .18
    def flank(y,z,d):
        return (x+d,y,z)
    def raised(surface, start, end, mat, title, face=flank):
        b.prism(surface,start,end,face,mat,'east flank/'+title)

    def window(rectangle, name, face, transom):
        left,bottom,right,top = rectangle
        outer = box(left,bottom,right,top)
        # Concealed glass overlaps the jambs so that oblique views never reveal an open slit.
        raised(outer.buffer(.009,join_style=2),-.204,-.184,GLASS,name+' glass',face)
        thickness = min(.052,(right-left)*.10)
        frame = outer.difference(outer.buffer(-thickness,join_style=2))
        if transom:
            z = bottom+(top-bottom)*.73
            frame = frame.union(box(left,z-.027,right,z+.027))
        raised(frame,-.178,-.125,FRAME,name+' frame',face)
        raised(box(left-.045,bottom-.067,right+.045,bottom-.008),-.092,.076,CAST,name+' sill',face)
        return outer

    holes=[]
    for bay in bays:
        for row in ('lower','upper'):
            for index,rect in enumerate(bay[row],start=1):
                name=f"bay {bay['bay']} {row} light {index}"
                holes.append(window(rect,name,flank,bay['bay']>=4 and row=='lower'))
    # The southern three panels terminate at successively lower parapets.
    heights=measured['wall_heights']
    edges=[wall_start,*axes[1:len(heights)],wall_end]
    outline=unary_union([box(y0,0,y1,h) for y0,y1,h in zip(edges[:-1],edges[1:],heights)])
    raised(outline.difference(unary_union(holes)),-.34,0,WALL,'perforated wall')
    plinth=measured['plinth_height']
    raised(box(wall_start,0,wall_end,plinth),.006,.048,CAST,'smooth basement facing')
    raised(box(wall_start,plinth-.043,wall_end,plinth+.035),.038,.079,CAST,'plinth top lip')
    for i,axis in enumerate(axes):
        pier_height=max(heights[max(0,i-1):min(len(heights),i+1)] or [heights[-1]])
        if i==0:
            # Southern corner belongs to the principal facade; its small return continues here.
            axis=wall_start+half
        height=pier_height+(.20 if i<4 else .025)
        raised(box(max(wall_start,axis-half),0,min(wall_end,axis+half),height),
               .001,.155,CAST,f'pilaster {i+1}')
    for i,(a,c,top) in enumerate(zip(edges[:-1],edges[1:],heights)):
        raised(box(a,top-.122,c,top-.005),.002,.132,CAST,f'eave cap {i+1}')
        if i<3:
            for delta in (.29,.74):
                raised(box(a,top-delta-.074,c,top-delta),.002,.057,CAST,f'parapet band {i+1} {delta}')

    # The horizontal joint crosses all three higher bays below the stepped caps.
    # Its two lines, visible above the foliage, continue the principal south moulding.
    raised(box(wall_start,13.53,axes[3],13.71),.003,.118,CAST,'long joint at parapet base')
    if not lod:
        raised(box(wall_start,13.78,axes[3],13.83),.005,.063,CAST,'thin upper bead of high panel course')
        raised(box(wall_start,15.08,axes[2],15.18),.013,.061,CAST,'horizontal fillet in forward upper panels')
