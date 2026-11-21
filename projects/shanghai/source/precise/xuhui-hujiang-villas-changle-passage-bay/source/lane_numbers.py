"""Original outline strokes for the legible lane number on the green lane plate."""
from shapely.geometry import LineString
from shapely.ops import unary_union


def address_digits(face):
    paths = {
        '6': [[(.85,.92),(.62,1),(.35,.96),(.16,.75),(.12,.32),(.24,.12),(.47,.03),(.73,.08),(.86,.26),(.82,.45),(.66,.56),(.38,.55),(.14,.40)]],
        '弄': [[(.16,.96),(.84,.96)],[(.50,.96),(.50,.51)],[(.23,.74),(.77,.74)],[(.09,.51),(.91,.51)],[(.08,.33),(.93,.33)],[(.38,.46),(.37,.26),(.31,.10),(.17,.02)],[(.69,.47),(.69,.03)]],
        '1': [[(.22,.73),(.52,.97),(.52,.05)],[(.23,.05),(.82,.05)]],
        '3': [[(.16,.85),(.38,.98),(.66,.97),(.83,.82),(.78,.62),(.55,.53),(.38,.51),(.60,.51),(.82,.40),(.86,.22),(.75,.07),(.46,.03),(.20,.12)]],
    }
    for index, digit in enumerate('613弄'):
        def xy(x,y):return (-.206+index*.105+x*.079,2.624+.126*y)
        strokes=[LineString([xy(*point)for point in path]).buffer(.006,cap_style=1,join_style=1,resolution=4)for path in paths[digit]]
        face.prism(unary_union(strokes),.046,.049,'Light enamel lettering','Raised address digit '+digit)
