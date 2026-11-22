"""Four window frames and the two historic fabric shades beneath the date cartouche."""
from math import cos, pi, sin

from shapely.geometry import Polygon, box
from shapely.ops import unary_union

FRAME = 'Tanggu windows | weathered frame'
BAR = 'Tanggu windows | painted glazing bars'
GLASS = 'Tanggu windows | pale glass'
SHADED_GLASS = 'Tanggu windows | shaded glass'
CANVAS = 'Tanggu shades | faded canvas'
EDGE = 'Tanggu shades | pale stitched hem'
SEAM = 'Tanggu shades | bound side seam'
BRICK_RETURN = 'Tanggu panels | warm brick return'
BRICK_FACE = 'Tanggu panels | inset brickwork'


def finish(rgb, rough, metallic=0.):
    def linear(channel):
        value = channel/255
        return value/12.92 if value <= .04045 else ((value+.055)/1.055)**2.4
    return dict(color=[linear(v) for v in rgb],roughness=rough,metallic=metallic)


PALETTE = {
    FRAME:finish((89,88,77),.7,.12), BAR:finish((105,109,104),.64,.18),
    GLASS:finish((153,165,168),.28,.12), SHADED_GLASS:finish((70,77,76),.35,.12),
    CANVAS:finish((92,90,86),.92),EDGE:finish((153,147,135),.94),
    SEAM:finish((111,106,95),.90),
    BRICK_RETURN:finish((152,100,69),.89), BRICK_FACE:finish((164,111,77),.91),
}


def panel(builder, poly, front, depth, y, material, label):
    builder.prism(poly, -front-depth, -front, lambda u,z,d:(u,y-d,z), material,label)


def glazing(builder, panes, y0, y1, material, label):
    verts, faces = [], []
    for pane in panes:
        left,bottom,right,top = pane.bounds
        start=len(verts)
        for y in [y0,y1]:
            verts.extend([(left,y,bottom),(right,y,bottom),(right,y,top),(left,y,top)])
        for loop in [(0,1,2,3),(7,6,5,4),(0,4,5,1),(1,5,6,2),(2,6,7,3),(3,7,4,0)]:
            faces.append(tuple(start+i for i in loop))
    builder.add(verts,faces,material,label)


def add_sash(builder,lod,index,x0,x1,z0,z1,face_y=0.,recess=None):
    """Place a frame within its clear masonry opening. Positive Y runs inward."""
    if index not in (1,2,3,4) or min(x1-x0,z1-z0)<=0:
        raise ValueError('Expected four individually numbered positive clear openings')
    label=f'Crown window {index}'
    width,height=x1-x0,z1-z0
    if recess is None:
        recess=width*.09
    if recess<=0:
        raise ValueError('Choose a positive inward seating depth')
    far = lod is True or lod=='lod'
    frame=min(width*.038,height*.024)
    inside=box(x0+frame,z0+frame,x1-frame,z1-frame)
    panel(builder,box(x0,z0,x1,z1).difference(inside),recess,.050*width,face_y,FRAME,label+' | perimeter')
    left,bottom,right,top=inside.bounds
    # The square-gridded uncovered pair reads as four columns by six rows.
    # Under the canvas only the low horizontal division and paired dark sash
    # are resolved. The covered head remains a plain shaded glazing panel.
    if index in (3,4):
        row_levels=[0.,.151,.311,.474,.644,.824,1.]
        column_levels=[[0.,.246,.535,.748,1.]]*6
    else:
        row_levels=[0.,.24,.54,1.]
        column_levels=[[0.,.50,1.],[0.,.50,1.],[0.,1.]]
    panes=[]
    for row,(lo,hi) in enumerate(zip(row_levels,row_levels[1:])):
        cuts=column_levels[row]
        def hor(t):
            if t in (0.,1.):return frame*.38
            return height*(.012 if t==.644 else .0055)
        for a,b in zip(cuts,cuts[1:]):
            def vert(t):
                if t in (0.,1.):return frame*.38
                return width*(.012 if t in (.535,.50) else .008)
            panes.append(box(left+a*(right-left)+vert(a), bottom+lo*(top-bottom)+hor(lo),
                             left+b*(right-left)-vert(b), bottom+hi*(top-bottom)-hor(hi)))
    grille=inside.buffer(-.001*width,join_style='mitre')
    panel(builder,grille.difference(unary_union(panes)),recess+.009*width,.027*width,face_y,BAR,label+' | glazing bars')
    glass=SHADED_GLASS if index<=2 else GLASS
    depth=face_y+recess+width*(.046 if far else .028)
    glazing(builder,[grille.buffer(-.004*width,join_style='mitre')] if far else panes,
            depth,depth+.006*width,glass,label+' | glazing')


def add_shade(builder,lod,index,x0,x1,z0,z1,face_y=0.,*,projection=None):
    """Build faded canvas, end cheeks and a separate scalloped fabric hem."""
    if index not in (1,2):
        raise ValueError('The published upper-crown photographs show shades on the left pair')
    width,height=x1-x0,z1-z0
    extension=.52*width if projection is None else projection
    if extension<=0:
        raise ValueError('Shade projection must be positive')
    far=lod is True or lod=='lod'
    label=f'Crown canvas {index}'
    # Two individual awnings overlap the masonry jambs. Their hems do not join.
    extra=width*(.17 if index==1 else .16)
    left,right=x0-extra,x1+extra
    anchor_y=face_y-.028*width
    high=z1+.045*height
    drop=(.267 if index==1 else .284)*height
    stations=7 if far else 14
    roof=[(anchor_y-extension*sin(t*pi/(2*stations)),
           high-drop*(1-cos(t*pi/(2*stations)))) for t in range(stations+1)]
    sheet=.014*width
    profile=Polygon(roof+[(y,z-sheet)for y,z in reversed(roof)])
    side=lambda y,z,x:(x,y,z)
    builder.prism(profile,left,right,side,CANVAS,label+' | curved cover')
    forward,lower=roof[-1]
    bottom=lower-sheet
    ends=Polygon([(y,z-sheet)for y,z in roof]+[(anchor_y,bottom-.0008*width)])
    cheek_thickness=width*.010
    # End panels are genuinely closed and meet the underside of the main cloth.
    builder.prism(ends,left,left+cheek_thickness,side,SEAM,label+' | left end panel')
    builder.prism(ends,right-cheek_thickness,right,side,SEAM,label+' | right end panel')
    repeats=8 if index==1 else 9
    pts=[(left,bottom),(right,bottom)]
    count=repeats*(4 if far else 8)
    for i in range(count+1):
        f=i/count
        pts.append((right-(right-left)*f,bottom-height*(.033+.012*(1-cos(2*pi*repeats*f))/2)))
    panel(builder,Polygon(pts),forward-face_y,sheet,face_y,EDGE,label+' | scalloped hem')


def add_crown_windows(builder,lod,openings):
    """Use the four wall apertures, ordered from image left to right."""
    if len(openings)!=4:
        raise ValueError('The crown band contains four openings')
    for i,row in enumerate(openings,1):
        dims=[row[k] for k in ('x0','x1','z0','z1')]
        face=row.get('face_y',0.)
        add_sash(builder,lod,i,*dims,face_y=face,recess=row.get('recess'))
        if i<=2:
            add_shade(builder,lod,i,*dims,face_y=face,projection=row.get('shade_projection'))


def add_crown_brick_panels(builder, lod, panels):
    """Insert four closed, shallow brick recesses in the wall's cut rectangles.

    Input dimensions and depth are in the caller's illustration units. The
    listed depth locates the visible back within the positive-Y wall.
    """
    if len(panels) != 4:
        raise ValueError('The ornamental crown contains four brick panels')
    for index, row in enumerate(panels, 1):
        x0, x1, z0, z1 = [row[k] for k in ('x0', 'x1', 'z0', 'z1')]
        wall = row.get('face_y', 0.)
        depth = row['depth']
        width, height = x1-x0, z1-z0
        if min(width, height, depth) <= 0:
            raise ValueError('Panel width, height and depth must be positive')
        label = f'Crown brick panel {index}'
        edge = min(width*.030, height*.037)
        outer = box(x0, z0, x1, z1)
        inner = outer.buffer(-edge, join_style='mitre')
        # A short front lip is followed by a slightly narrower deep reveal.
        # The overlapping side solids share no faces in their visible surfaces.
        toplip = outer.difference(inner)
        panel(builder, toplip, depth*.02, depth*.22, wall, BRICK_RETURN, label+' | outer lip')
        return_outer = outer.buffer(-edge*.35, join_style='mitre')
        return_inner = outer.buffer(-edge*1.40, join_style='mitre')
        panel(builder, return_outer.difference(return_inner), depth*.24, depth*.76,
              wall, BRICK_RETURN, label+' | brick reveal')
        panel(builder, return_outer, depth, depth*.35, wall, BRICK_FACE, label+' | inset face')
