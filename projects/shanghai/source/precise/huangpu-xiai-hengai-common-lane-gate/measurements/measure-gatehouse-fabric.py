"""Place the surface breaks visible on the front photograph in the shared street coordinate frame."""
from pathlib import Path
import json,sys
import numpy as np
m=Path(__file__).resolve().parent
sys.path.insert(0,str(m.parent/'source'))
from yongjia_photo_plane import on_front
source_points={
 'left_party_edge':[(220,77),(217,157),(215,257),(214,336)],
 'right_party_edge':[(541,66),(540,119),(537,183),(536,279)],
 'medium_parapet_top':[(272,55),(305,53),(338,51),(368,49),(403,47),(428,45)],
 'west_raised_coping':[(228,48),(236,48),(248,48)],
 'east_raised_coping':[(465,38),(479,36),(510,34)],
 'cornice_upper':[(273,83),(304,82),(337,79),(383,78),(416,76),(448,75)],
 'cornice_lower':[(272,90),(299,88),(329,87),(387,85),(418,82),(445,82)],
 'sill_course_top':[(275,221),(305,220),(333,218),(382,216),(410,215),(440,214)],
 'sill_course_bottom':[(274,228),(301,226),(330,225),(381,223),(407,222),(443,221)],
 'panel_band_top':[(286,275),(318,272),(352,271),(387,269),(425,268),(456,266)],
 'panel_band_foot':[(282,281),(309,280),(349,278),(378,277),(413,275),(458,274)]}
facts={}
for name,uv in source_points.items():
    xyz=np.asarray([on_front(u,v)for u,v in uv])
    scalar=xyz[:,0] if name.endswith('edge') else xyz[:,2]
    facts[name]=dict(photo_uv=uv,xz_m=xyz[:,[0,2]].round(4).tolist(),median_m=float(np.median(scalar)),range_m=list(np.round([min(scalar),max(scalar)],5)))
out=dict(source_camera='center15',period='2015 winter',facade_finish='Grey rendered facade. The long ridges beneath the parapet and the windows catch sunlight. Horizontal shadow joints stop at the central upper window surround.',
         observations=facts,panel_band='The surveyed lower edge meets the separate outer portal beam. Mouldings shared by both parts use the front support above the centre opening, with no masonry across the passage.',
         cut='The adjacent white facade on the left and the red-fronted commercial frontage on the right both fall beyond the party edges. The unseen roof deck and unrelated upper roofs are excluded.',
         ac_support='Four grille rails are visible in both contemporary 2015 views. The later large white cooling unit seen in 2020 belongs to a different fit-out.')
(m/'measured-frontage-lines.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
