"""Measure exterior silhouettes on the January 2016 courtyard view."""
from pathlib import Path
import hashlib, json, sys
import argparse
here=Path(__file__).resolve().parent
cli=argparse.ArgumentParser(description=__doc__)
cli.add_argument('--calibration',type=Path,default=here/'registered-rear.json')
cli.add_argument('--out',type=Path,default=here/'attachment-observations.json')
cli.add_argument('--photo-directory',type=Path,help='Verify the two retained originals if available.')
args=cli.parse_args()
sys.path.insert(0,str(args.calibration.parent))
from register_court import Camera
c=Camera('25',args.calibration)
def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()
def rect(uv,depth):
    tl,tr,br,bl=[c.wall(p,depth) for p in uv]
    return [round(float(v),4) for v in ((tl[0]+bl[0])/2,(br[2]+bl[2])/2,(tr[0]+br[0])/2,(tl[2]+tr[2])/2)]
# Corners on the exposed face. The left photographs only permit a continuous partial run.
cages=[
 ('west-partial',[(163,359),(275,353),(273,427),(161,423)],-.38,24),
 ('east',[(412,363),(571,355),(579,436),(412,434)],-.42,32)]
hcas=[
 ('west-of-portal',[(292,370),(315,367),(316,383),(292,386)]),
 ('east-of-portal',[(380,361),(405,359),(405,379),(380,381)]),
 ('centre-left-band',[(320,316),(344,314),(344,333),(320,334)]),
 ('centre-right-band',[(350,313),(375,312),(376,330),(350,332)]),
 ('third-storey',[(317,193),(341,188),(342,206),(318,210)]),
 ('fourth-low',[(299,126),(317,121),(317,140),(299,142)]),
 ('fourth-high',[(322,91),(341,87),(342,104),(322,108)]),
 ('fourth-middle',[(353,103),(373,100),(373,115),(353,120)])]
cage_rows=[]
for name,uv,y,count in cages:
    samples=[rect(uv,t)for t in [y-.16,y,y+.16]]
    cage_rows.append(dict(name=name,front_y=y,front_pixels=uv,bounds_x0_z0_x1_z1=samples[1],
                          depth_sensitivity=samples,modelled_bar_intervals=count))
units=[dict(name=name,pixels=uv,assumed_front_y=-.31,bounds_x0_z0_x1_z1=rect(uv,-.31)) for name,uv in hcas]
png='masa-43034625-650.jpg'
photos=[{'by': 'Masa / 4travel', 'file': 'masa-43034625-650.jpg', 'date': '2016-01-20', 'sha256': '4ad01b07ae017279cc1901ce37b6c7c8056611e6ea99c4607aa80d0d882bfb98', 'url': 'https://cdn.4travel.jp/img/thumbnails/imk/travelogue_pict/43/03/46/650x_43034625.jpg?updated_at=1458994605'}, {'by': '高参88', 'file': 'gao-04.jpg', 'date': '2013', 'sha256': '10a935fe8a1953119a49e8850bdb6350359883503952de9532df573de1002002', 'url': 'https://blog.sina.com.cn/s/blog_5d1bdf480101d590.html'}]
if args.photo_directory:
    for record in photos:
        assert sha(args.photo_directory/record['file'])==record['sha256']
data=dict(photographs=photos,
          units='metres, X to photograph right, +Y into building, Z above courtyard walk',
          calibration_sha256=sha(args.calibration),cages=cage_rows,condenser_cases=units,
          scope='1230 entrance and adjacent bays on the rear court. The 2016 image shows a projecting grid left and right of the ground-floor doorway. The east grid continues over the left portion of the balcony bay. The west run is cropped at a photographed vertical divider. Common scale is conditional on the 2.10 ±0.15 m door and datum ±0.18 m.',
          limitations=['The 2013 front view shows a plane grille inside the masonry opening east of the entrance, without the 2016 outer basket. Its thin horizontal crossrails are separately modelled as the earlier state.','Second-storey windows immediately east and west of the door reveal their sash and narrow sill. A projecting second-storey cage cannot be confirmed.','Front depths of 0.38 and 0.42 m are approximate. An uncertainty of 0.16 m each way is propagated above. Rod intervals, basket floor pitch and equipment case depth are illustrative. Condenser casings are read to about 2–3 native pixels.','Occluded western extension and unidentified gear at the far balcony are omitted.'])
data['east_seam']={'boundary_x':4.10,'attachment_near_end_x':4.078,'balcony_owns_right_part':True,'observed_full_east_bound_x':5.4626,'two_short_returns_to_x':4.132,'note':'The photo measures the whole continuous guard. The attachment terminates at the balcony jamb. courtyard_balconies.add_balconies supplies the 2016 grille to its right; its 2013 version supplies the earlier balcony rail.'}
args.out.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
print([(x['name'],x['bounds_x0_z0_x1_z1'])for x in cage_rows+units])
