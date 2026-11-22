"""Photogrammetric trace of exposed square iron bars at 36 Sinan Road."""
import numpy as np
from photo_plane import position

IRON = "Dark painted gate iron"
PALETTE = {IRON: {"color": [.020, .025, .023], "roughness": .63, "metallic": .43}}

# Coordinates are in the labelled 793 by 941 photograph. Intersections occluded
# by the removable sign were clipped before exporting these independent pieces.
MEASURED_SECTIONS = [
    ('upper crossbar visible 1', 'main rails', [[150.0, 429.0], [252.38, 419.06]], 0.014, 0.04),
    ('upper crossbar visible 2', 'main rails', [[413.67, 403.41], [593.0, 386.0]], 0.014, 0.04),
    ('bottom crossbar', 'main rails', [[150.0, 703.0], [635.0, 772.0]], 0.016, 0.042),
    ('raised middle rail', 'main rails', [[285.0, 339.0], [405.0, 324.0]], 0.012, 0.037),
    ('upright 1', 'main rails', [[186.0, 361.0], [205.0, 740.0]], 0.014, 0.036),
    ('upright 2 visible 1', 'main rails', [[281.0, 275.0], [289.93, 372.4]], 0.014, 0.036),
    ('upright 2 visible 2', 'main rails', [[299.05, 471.88], [323.0, 733.0]], 0.014, 0.036),
    ('upright 3 visible 1', 'main rails', [[408.0, 252.0], [411.31, 401.3]], 0.014, 0.036),
    ('upright 3 visible 2', 'main rails', [[411.74, 420.54], [419.0, 748.0]], 0.014, 0.036),
    ('upright 4', 'main rails', [[566.0, 311.0], [590.0, 804.0]], 0.014, 0.036),
    ('square return 1', 'square turns', [[185.0, 367.0], [159.0, 373.0], [160.0, 398.0], [177.0, 393.0], [176.0, 379.0], [169.0, 380.0]], 0.014, 0.033),
    ('square return 2', 'square turns', [[281.0, 275.0], [255.0, 283.0], [257.0, 308.0], [273.0, 302.0], [272.0, 288.0], [264.0, 291.0]], 0.014, 0.033),
    ('square return 3', 'square turns', [[408.0, 252.0], [431.0, 248.0], [435.0, 276.0], [414.0, 280.0], [413.0, 264.0], [423.0, 263.0]], 0.014, 0.033),
    ('square return 4', 'square turns', [[568.0, 309.0], [531.0, 310.0], [533.0, 347.0], [556.0, 345.0], [555.0, 323.0], [543.0, 325.0]], 0.014, 0.033),
    ('central three peaks', 'triangle crest', [[295.0, 337.0], [310.0, 307.0], [328.0, 334.0], [347.0, 291.0], [365.0, 329.0], [382.0, 298.0], [402.0, 322.0]], 0.0075, 0.0105),
    ('central folded lower edge visible 1', 'triangle crest', [[296.0, 340.0], [313.0, 365.0], [328.0, 339.0], [341.99, 362.32]], 0.0075, 0.0105),
    ('central folded lower edge visible 2', 'triangle crest', [[343.47, 362.4], [351.0, 337.0], [378.0, 368.0], [403.0, 326.0]], 0.0075, 0.0105),
    ('outer diagonal 1', 'side branch', [[151.0, 430.0], [194.0, 494.0]], 0.0068, 0.00952),
    ('outer diagonal 2', 'side branch', [[151.0, 463.0], [197.0, 536.0]], 0.0068, 0.00952),
    ('outer diagonal 3', 'side branch', [[152.0, 503.0], [200.0, 581.0]], 0.0068, 0.00952),
    ('outer diagonal 4', 'side branch', [[152.0, 544.0], [201.0, 620.0]], 0.0068, 0.00952),
    ('outer diagonal 5', 'side branch', [[152.0, 585.0], [201.0, 664.0]], 0.0068, 0.00952),
    ('outer diagonal 6', 'side branch', [[153.0, 622.0], [204.0, 704.0]], 0.0068, 0.00952),
    ('outer diagonal 7', 'side branch', [[153.0, 665.0], [165.0, 638.0]], 0.0068, 0.00952),
    ('outer diagonal 8', 'side branch', [[572.0, 464.0], [599.0, 422.0]], 0.0068, 0.00952),
    ('outer diagonal 9', 'side branch', [[576.0, 526.0], [604.0, 479.0]], 0.0068, 0.00952),
    ('outer diagonal 10', 'side branch', [[581.0, 605.0], [614.0, 549.0]], 0.0068, 0.00952),
    ('outer diagonal 11', 'side branch', [[584.0, 693.0], [625.0, 628.0]], 0.0068, 0.00952),
    ('outer diagonal 12', 'side branch', [[591.0, 761.0], [628.0, 708.0]], 0.0068, 0.00952),
    ('left fan 1', 'left fan', [[254.81, 426.9], [199.62, 614.0]], 0.0066, 0.00924),
    ('left fan 2 visible 1', 'left fan', [[300.92, 339.0], [290.94, 372.05]], 0.0066, 0.00924),
    ('left fan 2 visible 2', 'left fan', [[267.35, 450.18], [201.56, 668.0]], 0.0066, 0.00924),
    ('left fan 3 visible 1', 'left fan', [[319.92, 339.0], [311.99, 365.26]], 0.0066, 0.00924),
    ('left fan 3 visible 2', 'left fan', [[279.52, 472.78], [208.48, 708.0]], 0.0066, 0.00924),
    ('left fan 4 visible 1', 'left fan', [[338.32, 341.0], [332.04, 361.8]], 0.0066, 0.00924),
    ('left fan 4 visible 2', 'left fan', [[298.71, 472.16], [225.67, 714.0]], 0.0066, 0.00924),
    ('left fan 5 visible 1', 'left fan', [[360.1, 340.0], [352.85, 363.37]], 0.0066, 0.00924),
    ('left fan 5 visible 2', 'left fan', [[323.71, 457.39], [242.92, 718.0]], 0.0066, 0.00924),
    ('left fan 6 visible 1', 'left fan', [[383.53, 332.0], [371.67, 369.92]], 0.0066, 0.00924),
    ('left fan 6 visible 2', 'left fan', [[343.78, 459.0], [261.46, 722.0]], 0.0066, 0.00924),
    ('right fan 1', 'right fan', [[407.7, 596.0], [469.65, 746.0]], 0.0066, 0.00924),
    ('right fan 2', 'right fan', [[411.28, 549.0], [496.3, 750.0]], 0.0066, 0.00924),
    ('right fan 3', 'right fan', [[406.96, 484.0], [526.2, 755.0]], 0.0066, 0.00924),
    ('right fan 4', 'right fan', [[406.06, 431.31], [555.36, 758.0]], 0.0066, 0.00924),
    ('right fan 5 visible 1', 'right fan', [[410.04, 398.0], [411.86, 401.79]], 0.0066, 0.00924),
    ('right fan 5 visible 2', 'right fan', [[416.52, 411.49], [585.24, 763.0]], 0.0066, 0.00924),
    ('right fan 6', 'right fan', [[428.66, 384.0], [589.38, 712.0]], 0.0066, 0.00924),
    ('right fan 7', 'right fan', [[433.38, 347.0], [582.94, 642.0]], 0.0066, 0.00924),
    ('left extended diagonal to square', 'left fan', [[257.0, 305.0], [198.0, 525.0]], 0.0068, 0.00952),
    ('left extended diagonal to upper pin', 'left fan', [[277.0, 301.0], [198.0, 598.0]], 0.0068, 0.00952),
    ('central folded branch 1', 'middle branch', [[305.0, 481.0], [359.0, 561.0], [409.0, 460.0]], 0.0072, 0.01008),
    ('central folded branch 2', 'middle branch', [[311.0, 562.0], [362.0, 652.0], [413.0, 535.0]], 0.0072, 0.01008),
    ('central folded branch 3', 'middle branch', [[317.0, 633.0], [364.0, 722.0], [415.0, 624.0]], 0.0072, 0.01008),
    ('central folded branch 4', 'middle branch', [[360.0, 487.0], [365.0, 720.0]], 0.0072, 0.01008),
]

def add_iron(builder, lod):
    """Build each traced bar as a rectangular solid, preserving open gaps."""
    for label, category, points, half_width, thickness in MEASURED_SECTIONS:
        offset = -.007 if category in ("main rails", "square turns") else .009
        centres = [position(u, v, offset) for u, v in points]
        vertices = []
        faces = []
        for a, b in zip(centres, centres[1:]):
            dx, _, dz = b-a
            span = np.hypot(dx, dz)
            if span < .002:
                continue
            width = np.array([-dz, 0., dx]) * (half_width / span)
            front = np.array([0., -thickness/2, 0.])
            base = len(vertices)
            if lod:
                corners = [(1,1),(-1,1),(-1,-1),(1,-1)]
            else:
                # Sub-millimetre corner facets keep the plate's square silhouette.
                chamfer = min(.0008, half_width/8, thickness/12)
                wx = 1-chamfer/half_width
                dy = 1-2*chamfer/thickness
                corners = [(wx,1),(-wx,1),(-1,dy),(-1,-dy),
                           (-wx,-1),(wx,-1),(1,-dy),(1,dy)]
            sides = len(corners)
            vertices.extend([(centre+i*width+j*front).tolist()
                             for centre in (a,b) for i,j in corners])
            for i in range(1, sides-1):
                faces.append([base,base+i+1,base+i])
                faces.append([base+sides,base+sides+i,base+sides+i+1])
            for i in range(sides):
                j = (i+1) % sides
                faces.append([base+i,base+j,base+j+sides])
                faces.append([base+i,base+j+sides,base+i+sides])
        if vertices:
            builder.add(vertices, faces, IRON, label)
