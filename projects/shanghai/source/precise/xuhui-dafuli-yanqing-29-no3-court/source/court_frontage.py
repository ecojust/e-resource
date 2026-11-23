"""The recorded cut through the No. 3 court and the lower opening behind its gate."""
from court_three import BRICK, CAST, CAP, CREAM, GREEN, GLASS, SILL, SEAM, box
from court_terrace import finish, terrace_bounds

SOFFIT = 'Dafuli 3 | grey cream lower wall'
PAVING = 'Dafuli 3 | shaded court threshold'
TIMBER = 'Dafuli 3 | stained cream jamb'
CLAY = 'Dafuli 3 | small terracotta pier fixture'
PALETTE = {SOFFIT:finish((165,153,143), .93), PAVING:finish((103,100,96),.95),
           TIMBER:finish((154,125,107),.93), CLAY:finish((143,92,67),.89)}

def add_frontage(b, lod, front, wall):
    x0, _, _, _, soffit, _ = terrace_bounds(front,wall)
    x1 = .13
    eye_x, eye_y, eye_z = 4.9063276447, -2.3040789044, 1.56
    ratio = (wall-eye_y)/(.70-eye_y)
    surround_left = eye_x + (-.91-eye_x)*ratio
    surround_right = eye_x + (.91-eye_x)*ratio
    surround_bottom = eye_z + (3.58-eye_z)*ratio
    top = eye_z + (5.68-eye_z)*ratio
    # The brick crop terminates at the visible end of the photographed terrace.
    # No party wall, roof or rooms are extrapolated beyond this section.
    for a,c in ((x0,surround_left),(surround_right,x1)):
        box(b,a,c,wall,wall+.17,surround_bottom,top,BRICK,'upper masonry at the terrace ends')
    box(b,x0,x1,wall,wall+.17,soffit,surround_bottom,BRICK,'brick beneath the upper window crop')
    # The sober court floor closes the section through the obscured ground.
    # Its rear depth follows the same plane as the sash above.
    box(b,x0,1.68,.00,wall+.17,-.068,0,PAVING,'plain court ground section')
    door_l,door_r,head=-1.72,-.58,2.89
    for a,c in ((x0,door_l),(door_r,x1)):
        box(b,a,c,wall,wall+.17,0,soffit,SOFFIT,'lower wall beside the recessed court opening')
    box(b,door_l,door_r,wall,wall+.17,head,soffit,SOFFIT,'lower lintel behind terrace soffit')
    # The real lower green lintel is visible from x=-1.13 to -0.65. The lower
    # door face is concealed in the photograph; give the recess a plain backing.
    box(b,door_l,door_r,wall+.080,wall+.12,.015,head,SILL,'shaded lower door plane')
    box(b,door_l,door_r,wall+.035,wall+.082,2.743,head,GREEN,'visible lower green door head')
    for x in (-1.136,-.935,-.705):
        box(b,x,x+.025,wall+.037,wall+.083,2.62,2.745,GREEN,'lower door upper glazing mullion')
    for a,c in ((-1.11,-.94),(-.907,-.71)):
        box(b,a,c,wall+.076,wall+.081,2.642,2.745,GLASS,'shadowed lower transom')
    # The exposed near jamb has a broad light cap with small tooth-shaped
    # returns and a fluted shadow line; only this photographed side is ornamented.
    box(b,-.58,-.255,wall-.046,wall+.018,.046,3.002,TIMBER,'near jamb of the court doorway')
    for x in (-.546,-.465,-.384):
        box(b,x,x+.020,wall-.056,wall-.043,.14,2.84,CAST,'vertical edge on the lower jamb')
    box(b,-.629,-.221,wall-.071,wall+.026,2.979,3.058,CREAM,'lower jamb capital')
    for n in range(6 if not lod else 3):
        pitch=.060 if not lod else .12
        x=-.605+n*pitch
        box(b,x,x+.033,wall-.069,wall-.040,3.050,3.093,CREAM,'lower jamb tooth')
    box(b,-.663,-.203,wall-.082,wall+.034,3.092,3.154,CREAM,'lower jamb cornice')
    # The small ochre protrusion immediately below the sign belongs to No. 3.
    box(b,.020,.085,-.030,.0,2.109,2.188,CLAY,'terracotta block below the address')
    box(b,.072,.098,-.035,.0,2.108,2.188,CLAY,'exposed return on the block')
    if not lod:
        for z in (2.080,1.835,1.448):
            box(b,-.188,-.161,-.037,-.021,z-.011,z+.011,CAP,'fixing on narrow vertical strap')
