"""The wall-mounted hose reel cabinet between the two numbered doors in 2015."""
from shapely.geometry import Polygon
from courtyard_materials import CABINET,PANEL,PALE,BLACK,STONE
# Hand-drawn centre lines read from the four Chinese characters on the cabinet.
STROKES={
    '软': [[(.09,.23),(.51,.20)],[(.35,.07),(.13,.52),(.49,.47)],[(.34,.28),(.34,.91)],[(.05,.73),(.50,.61)],[(.68,.08),(.52,.42)],[(.64,.27),(.91,.27),(.81,.43)],[(.72,.38),(.67,.66),(.52,.89)],[(.69,.54),(.79,.74),(.96,.90)]],
    '管': [[(.19,.05),(.06,.23)],[(.16,.13),(.43,.13)],[(.27,.13),(.32,.25)],[(.63,.04),(.51,.23)],[(.60,.13),(.94,.13)],[(.75,.14),(.81,.24)],[(.46,.26),(.53,.32)],[(.10,.42),(.11,.34),(.91,.34),(.89,.43)],[(.26,.46),(.74,.46),(.74,.58),(.26,.58),(.26,.46)],[(.26,.58),(.26,.88),(.77,.88),(.77,.69),(.27,.69)]],
    '卷': [[(.28,.08),(.37,.24)],[(.72,.08),(.63,.24)],[(.49,.06),(.46,.32),(.28,.54),(.06,.66)],[(.14,.29),(.87,.29)],[(.07,.43),(.93,.43)],[(.61,.43),(.78,.58),(.96,.65)],[(.32,.61),(.72,.61),(.68,.73),(.53,.75)],[(.33,.62),(.33,.86),(.41,.91),(.78,.91),(.84,.84)]],
    '盘': [[(.43,.05),(.38,.13)],[(.25,.17),(.76,.17),(.76,.47),(.67,.53)],[(.27,.17),(.24,.38),(.14,.53)],[(.12,.34),(.91,.34)],[(.43,.23),(.52,.29)],[(.42,.40),(.52,.46)],[(.22,.60),(.81,.60),(.81,.86)],[(.22,.60),(.22,.87)],[(.42,.62),(.42,.84)],[(.61,.62),(.61,.85)],[(.08,.89),(.94,.89)]]}
def add_hose_cabinet(b,unproject,lod):
    front=-.215
    def face(points,y0,y1,material,title):
        shape=Polygon([unproject(u,v,front)[::2]for u,v in points])
        b.prism(shape,-y1,-y0,lambda x,z,d:(x,-d,z),material,title)
    face([(1086,3405),(1522,3408),(1508,4003),(1073,3994)],front+.018,-.022,CABINET,'Courtyard hose reel | steel enclosure')
    face([(1073,3385),(1554,3388),(1547,3415),(1076,3414)],front-.029,-.011,CABINET,'Courtyard hose reel | top drip edge')
    face([(1096,3431),(1500,3433),(1493,3969),(1085,3964)],front,front+.021,PANEL,'Courtyard hose reel | red cabinet door')
    face([(1114,3663),(1149,3665),(1145,3737),(1110,3734)],front-.011,front+.004,BLACK,'Courtyard hose reel | inset handle')
    for i,ch in enumerate('软管卷盘'):
        for seq in STROKES[ch]:
            points=[unproject(1176+52*i+45*u,3603+65*v,front-.004)for u,v in seq]
            b.tube(points,.0028,PALE,5 if lod else 8,'Courtyard hose reel | '+ch)
    # A small numeral above the latch is also visible. The lower line is below the
    # reliable resolution of the second photograph and is left unlettered.
    face([(1170,3500),(1202,3500),(1201,3542),(1169,3542)],front-.003,front+.004,BLACK,'Courtyard hose reel | equipment label')
