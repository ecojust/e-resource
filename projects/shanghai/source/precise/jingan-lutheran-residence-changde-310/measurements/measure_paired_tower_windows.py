"""Recalculate the four measured arched openings from the original 690 × 441 front photograph."""
from pathlib import Path
import json
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'source'))
from changde_photo_plane import on_wall

# jamb L/R, sill, spring line, intrados crown, adjacent outer moulding, fan base,
# timber transoms, hardwood head under the shadow of the projecting archivolt.
PIXELS=[
    ('upper-left','upper',427.0,467.3,149.8,82.6,61.0,413.3,41.9,87.9,[112.3,130.0],68.9),
    ('upper-right','upper',487.6,527.9,149.8,82.4,61.0,474.1,41.5,87.2,[111.7,130.0],69.1),
    ('middle-left','middle',428.0,469.4,374.7,278.2,258.0,413.5,238.0,281.6,[309.0,328.1,340.7,354.7],266.4),
    ('middle-right','middle',488.8,530.2,374.6,278.4,258.9,474.9,238.2,282.4,[309.0,328.0,340.6,354.8],266.8),
]
def measure():
    rows=[]
    for key,tier,l,r,b,spring,crown,outer_l,outer_top,fanbase,rails,back_crown in PIXELS:
        mid=(l+r)/2
        x=lambda u:on_wall(u,spring)[0]
        z=lambda v:on_wall(mid,v)[2]
        rows.append(dict(key=key,tier=tier,left=x(l),right=x(r),bottom=z(b),spring=z(spring),top=z(crown),
                         outer_radius_x=x(mid)-x(outer_l),outer_crown_z=z(outer_top),fan_base_z=z(fanbase),
                         timber_transoms_z=[z(v) for v in rails],sash_reference_head_z=z(back_crown),
                         front_y_m=0,frame_y_m=.31,glass_y_m=.365,
                         source_px=dict(jamb_edges=[l,r],sill=b,spring=spring,intrados_crown=crown,
                                        left_architrave=outer_l,outer_crown=outer_top,fan_transom=fanbase,
                                        other_transoms=rails,shaded_rear_head=back_crown)))
    return {'model':'No.310 Changde Road, two upper tiers of the projecting tower',
            'coordinate_axes':'Local X to the right in the courtyard view; Y into the house; Z above grade.',
            'primary_image':'gao-09', 'source_size_px':[690,441],
            'other_readings':['gao-04','gao-01','cc-panorama','confirmed-dec15','confirmed-march15','confirmed-n20','far-nw15'],
            'woodwork':'The top rectangular lights have two columns and three rows. At middle height a separately framed pair of rectangular transom lights sits above the two taller leaves. The recess above each fan is shaded. All four openings appear closed in the frontal photograph.',
            'depth_limit':'The masonry overhang and reveal are visible. The absolute sash setback, glass setback, brick moulding profile and hidden rear thickness are estimates.',
            'brick_courses':{'assumed_m':.065,'scale_uncertainty_fraction':.08,
            'independent_native_control_strips':[dict(x_range=[562,600],y_range=[45,145],joint_centres=[46,49,52,55,57,61,63,66,69,72,75,77,81,83,86,89,92,95,97,100,103,106,109,112,115,118,120,123,126,129,132,134,137,140,143]),
            dict(x_range=[557,599],y_range=[247,363],joint_centres=[249,252,255,258,261,263,266,269,272,275,278,281,283,287,289,292,295,298,301,304,307,310,312,316,318,321,324,327,330,333,335,339,341,345,347,350,353,356,359])]},'windows':rows}
if __name__=='__main__':
    Path(__file__).with_name('paired-tower-windows.json').write_text(json.dumps(measure(),ensure_ascii=False,indent=2)+'\n')
