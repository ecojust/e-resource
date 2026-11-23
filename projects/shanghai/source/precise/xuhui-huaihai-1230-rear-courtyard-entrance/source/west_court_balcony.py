"""Western projecting bay measured in the 2016 rear-courtyard photograph.

The two upper storeys have different enclosures. The open second floor and
the shallow ground-floor window screen remain separate from the later guard
that crosses the neighbouring window. X points ENE, positive Y into the house.
"""
from courtyard_balconies import BRICK, CAST, FRAME, GLASS, SILVER, piece, rect
from court_finishes import FOOT

LEFT, RIGHT = -6.72, -3.82
FRONT, BACK = -.79, .72
MOUTH = (LEFT, .84, RIGHT, 12.95)
DEEP = "1230 west balcony | shadowed recess"
LIGHT = "1230 west balcony | pale closed glazing"
PALETTE = {
    DEEP: {"color": [.115,.102,.094], "roughness": .89},
    LIGHT: {"color": [.48,.53,.53], "metallic": .08, "roughness": .43},
}


class RightReturn:
    """Reorient the same closed profile onto the X-constant east return."""
    def __init__(self, builder):
        self.builder = builder

    def add(self, vertices, triangles, material, label):
        vertices = [(RIGHT-depth, along_y, z) for along_y, depth, z in vertices]
        self.builder.add(vertices, triangles, material, label)


def strip(b, x0, x1, z0, z1, y0, y1, material, name):
    piece(b, rect(x0,z0,x1,z1), [], y0,y1,material,"west bay | "+name)


def windows(b, edges, bottom, top, head, front, *, frame, materials, name, lod=False):
    """Build fixed transoms and lower lights, including a missing/open lower light."""
    guard=.046
    bottom_panels=[]
    top_panels=[]
    for i,(left,right) in enumerate(zip(edges,edges[1:])):
        x0=left+(guard if i==0 else .015)
        x1=right-(guard if i==len(edges)-2 else .015)
        bottom_panels.append(rect(x0,bottom+guard,x1,head-.018))
        top_panels.append(rect(x0,head+.018,x1,top-guard))
    piece(b,rect(edges[0],bottom,edges[-1],top),bottom_panels+top_panels,
          front,front+.052,frame,"west bay | "+name+" sash")
    if lod:
        piece(b,rect(edges[0]+guard,head+.018,edges[-1]-guard,top-guard),[],
              front+.027,front+.045,GLASS,"west bay | "+name+" upper backing")
        left=0
        while left<len(materials):
            right=left+1
            while right<len(materials) and materials[right]==materials[left]:
                right+=1
            if materials[left]:
                pane=rect(bottom_panels[left][0][0],bottom+guard,bottom_panels[right-1][1][0],head-.018)
                piece(b,pane,[],front+.027,front+.045,materials[left],"west bay | "+name+" glazing")
            left=right
        return
    for i,(lower,upper) in enumerate(zip(bottom_panels,top_panels)):
        # Opaque rear lining records the dark opening without inventing a leaf angle.
        if materials[i]:
            piece(b,lower,[],front+.027,front+.045,materials[i],"west bay | "+name+" lower light")
        piece(b,upper,[],front+.027,front+.045,GLASS,"west bay | "+name+" transom")


def add_west_balcony(builder, lod=False):
    for material,properties in PALETTE.items():
        builder.palette.setdefault(material,properties)
    side=RightReturn(builder)
    def flat(x0,x1,z0,z1,y0,y1,material,name):
        strip(builder,x0,x1,z0,z1,y0,y1,material,name)
    def slab(low,high,label):
        flat(LEFT,RIGHT,low,high,FRONT,BACK+.10,CAST,label)
    def side_panel(low,high,label):
        strip(side,FRONT,-.015,low,high,0,.07,CAST,label+" east return")

    # The ground enclosure is behind the zinc cage and the storey above projects over it.
    flat(LEFT,RIGHT,.84,1.75,-.015,.13,FOOT,"ground grey window skirt")
    windows(builder,[LEFT,LEFT+.75,LEFT+1.63,LEFT+2.17,RIGHT],1.75,3.57,3.11,-.015,
            lod=lod,frame=SILVER,materials=[GLASS,GLASS,LIGHT,GLASS],name="ground court-facing enclosure")
    flat(LEFT,RIGHT,3.57,3.86,-.025,.14,CAST,"ground head below slab")

    # Only the five regularly spaced openings clear of the foliage are measured.
    slab(3.86,3.99,"lower terrace floor and soffit")
    # The observed dark widths are the part seen through both faces. At this
    # oblique station the rear jamb projects about 0.08 m across the front opening.
    # These bounds use the left 1.2px edge at the back and the right 1.2px edge
    # at the front of the 0.112 m concrete parapet.
    slot_spans=[(-5.1949, -5.02118), (-4.94241, -4.77196), (-4.69294, -4.52571), (-4.44643, -4.28238), (-4.20284, -4.04193)]
    slots=[rect(x0,4.125,x1,4.66) for x0,x1 in slot_spans]
    piece(builder,rect(LEFT,3.99,RIGHT,4.83),slots,FRONT,FRONT+.112,CAST,
          "west bay | open second-floor slotted parapet")
    side_panel(3.99,4.83,"second-floor parapet")
    # The frame at the eastern end of the recessed back is clear below the white casement storey.
    rear_window=(-5.10,-3.95)
    opening=rect(rear_window[0],4.46,rear_window[1],6.64)
    piece(builder,rect(LEFT,3.99,RIGHT,6.83),[opening],BACK,BACK+.10,BRICK,
          "west bay | second-floor recessed brick rear")
    windows(builder,[rear_window[0],-4.54,rear_window[1]],4.46,6.64,6.23,BACK+.045,
            lod=lod,frame=FRAME,materials=[GLASS,GLASS],name="second-floor rear window")

    # Two floors of heavier enclosure. In the lower one, both front and return are pale steel.
    slab(6.83,7.00,"third-floor projecting slab")
    flat(LEFT,RIGHT,7.00,7.88,FRONT,FRONT+.115,CAST,"third-floor solid front skirt")
    side_panel(7.00,7.88,"third-floor solid skirt")
    windows(builder,[LEFT,LEFT+.93,LEFT+1.95,RIGHT],7.88,10.00,9.59,FRONT+.012,
            lod=lod,frame=SILVER,materials=[LIGHT,GLASS,GLASS],name="third-floor white framed enclosure")
    windows(side,[FRONT,-.395,-.012],7.88,10.00,9.59,.010,
            lod=lod,frame=SILVER,materials=[GLASS,GLASS],name="third-floor visible white side sash")
    # The upper bay has a different dark central opening and a deep grey skirt.
    slab(10.00,10.16,"fourth-floor projecting slab")
    flat(LEFT,RIGHT,10.16,11.06,FRONT,FRONT+.11,CAST,"fourth-floor solid grey front skirt")
    side_panel(10.16,11.06,"fourth-floor skirt")
    west_edges=[LEFT,-6.01,-5.36,-4.56,RIGHT]
    windows(builder,west_edges,11.06,12.89,12.55,FRONT+.012,lod=lod,frame=FRAME,
            materials=[GLASS,None,LIGHT,LIGHT],name="fourth-floor dark and pale enclosure")
    windows(side,[FRONT,-.39,-.01],11.06,12.89,12.55,.01,
            lod=lod,frame=FRAME,materials=[GLASS,GLASS],name="fourth-floor east return")
    # A shallow return into the top dark opening is visible. Its interior is not documented.
    flat(LEFT+.065,RIGHT-.065,10.98,12.82,.405,.445,DEEP,"fourth-floor rear of dark opening")
    flat(LEFT,RIGHT,12.89,12.95,FRONT,BACK+.10,CAST,"top enclosure head")
    flat(LEFT,LEFT+.065,3.99,12.89,FRONT+.12,BACK,CAST,"unseen west return")
    if not lod:
        flat(LEFT+.015,RIGHT-.015,11.045,11.079,FRONT-.025,FRONT+.017,FRAME,"upper window sill lip")
        flat(LEFT+.015,RIGHT-.015,7.862,7.895,FRONT-.019,FRONT+.018,SILVER,"third-floor white sill lip")
