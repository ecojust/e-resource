"""Digitized coordinates from Shanghai Weifang's second post-restoration photograph."""
from pathlib import Path
from PIL import Image
import argparse,hashlib,json,statistics
p=argparse.ArgumentParser();p.add_argument('photograph',type=Path);p.add_argument('output',type=Path);a=p.parse_args()
im=Image.open(a.photograph).convert('RGB')
assert im.size==(580,380)
openings={
 'upper-west':[[316.0,82.4],[357.4,85.9],[362.0,130.5],[318.7,127.4]],
 'upper-centre':[[370.4,87.9],[411.7,90.7],[416.5,124.3],[373.1,122.1]],
 'upper-east':[[454.0,92.1],[493.6,95.1],[505.1,140.2],[462.0,136.8]],
 'middle-open':[[335.9,182.9],[360.2,183.8],[365.8,237.7],[338.7,236.7]],
 'middle-narrow':[[375.4,197.6],[400.7,198.9],[406.7,255.3],[380.3,252.8]],
 'lower-west':[[296.4,280.5],[326.0,280.9],[327.8,315.0],[298.1,314.8]],
 'lower-centre':[[344.2,300.2],[369.8,300.7],[374.5,337.1],[346.6,336.8]],
 'lower-east':[[393.4,330.0],[415.1,329.7],[419.3,377.5],[398.4,377.5]]}
canopies={
 'centre':{'back_left':[363.6,82.8],'back_right':[415.5,86.4],'tip_left':[368.1,76.8],'tip_right':[424.0,79.4],
           'sheet_inner_ribs':[[[382.4,84.9],[388.0,78.2]],[[399.8,86.5],[403.6,79.1]]],
           'front_edge_outer_hull':[[363.0,79.4],[368.5,76.8],[424.3,79.4],[422.8,82.0]],
           'visible_braces':[[[371.7,98.7],[364.3,82.2]],[[414.0,97.9],[423.0,80.7]]]},
 'east':{'back_left':[445.0,87.8],'back_right':[499.2,92.7],'tip_left':[452.5,82.6],'tip_right':[510.2,88.1],
         'sheet_inner_ribs':[[[468.5,92.0],[471.2,85.4]],[[484.1,93.6],[487.5,87.0]]],
         'front_edge_outer_hull':[[444.7,88.2],[452.3,82.4],[510.2,88.9],[508.6,91.3]],
         'visible_braces':[[[454.9,102.4],[446.1,88.8]],[[496.6,100.7],[508.8,89.8]]]}}
# wall-side rectangular holes are measured separately from the free edge of the hinged leaf
open_leaf={'hinge_top':[360.1,184.0],'hinge_bottom':[365.4,237.0],'free_top':[366.7,177.6],'free_bottom':[372.9,231.7],
           'visible_rails_fraction_top_to_bottom':[.26,.52,.77]}
planter={'wall_left':[370.0,138.8],'wall_right':[424.6,141.6],'outer_left':[375.0,127.4],'outer_right':[433.0,129.3],
'rail_upper_left':[375.2,119.6],'rail_upper_right':[432.8,122.3],'rail_lower_left':[375.1,126.9],'rail_lower_right':[433.0,128.8],
'left_brace_wall':[370.3,145.4],'right_brace_wall':[429.0,146.7],
'note':'The projecting metal shelf under the middle canopy carries a low pale rail and dark items. No individual flower or object is identifiable.'}
samples={'yellow-sunlit-render':[(308,75),(330,72),(432,90),(432,101),(502,77),(422,150)],'lower-render':[(310,202),(320,215),(309,240),(316,276),(305,168)],'bright-sill':[(327,130),(349,132),(344,241),(387,258),(454,139)],'green-glass-bright':[(375,79),(391,80),(404,81),(460,86),(478,87),(497,89)],'green-glass-shadow':[(378,96),(383,95),(407,98),(472,103),(486,105)],'upper-frame':[(336,99),(337,104),(321,99),(347,111),(465,109)],'upper-east-lower-shadow':[(469,121),(469,125),(470,130),(471,133)],'upper-east-lower-reflection':[(487,122),(485,130),(495,132)],'glass-reflection':[(325,105),(331,119),(349,113),(347,123),(477,124)],'dark-recess':[(345,197),(352,213),(347,228),(354,224)],'dark-steel-rainpipe':[(367,178),(370,201),(373,223),(376,247),(378,275),(382,310)]}
sample_row={}
for k,pts in samples.items():
 rgb=[]
 for x,y in pts:
  vals=list(im.crop((x-1,y-1,x+2,y+2)).get_flattened_data());rgb.append([int(statistics.median(a)) for a in zip(*vals)])
 sample_row[k]={'centres_px':pts,'patch_medians_srgb8':rgb,'combined_median_srgb8':[int(statistics.median(a))for a in zip(*rgb)]}
d={'source_url':'http://www.shwfjz.com/showcase/3/','source_image':'http://www.shwfjz.com/newwsm/editor/attached/image/20180109/20180109132998189818.JPG',
   'photo_sha256':hashlib.sha256(a.photograph.read_bytes()).hexdigest(),'size':im.size,'pixel_origin':'top-left, centres, native resolution',
   'features':{'visible_wall_boundary':[[274.6,51.0],[516.8,69.9],[560,251],[273,254]],'openings':openings,'glass_canopies':canopies,'open_right_hand_leaf':open_leaf,'projecting_centre_shelf':planter,'downpipe_centreline':[[367,164],[370,186],[375,234],[378.5,263.5],[383,306],[387,353]],'downpipe_left_arm':[[316,159.0],[343,163],[368,165.8]],'downpipe_right_arm':[[368,165.8],[417.5,166.6],[422.1,164.2]],'edge_observations':{'west':'Closer left body occludes part of the wall. The vertical strip at x≈271–282 is bounded by that occlusion.','lower':'Foliage hides the lower sills, the entrance feet and the eastern wall limit. The three reported lower rectangles end at observed dark regions, not inferred complete sills.'}},'colour_samples':sample_row,
   'colour_scope':'Observed photographic sRGB contains lighting, sky reflection, JPEG compression and tree shading. Canopy alpha, cross-section and hidden fasteners cannot be read directly.'}
a.output.write_text(json.dumps(d,indent=2,ensure_ascii=False)+'\n');print({k:v['combined_median_srgb8']for k,v in sample_row.items()})
