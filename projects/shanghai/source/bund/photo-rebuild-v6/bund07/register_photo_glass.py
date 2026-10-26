#!/usr/bin/env python3
"""Explicit manual safe glazing samples from the unchanged 2025 CC0 original.

Coordinates are stored/upright pixels (EXIF1); no image is modified or created.
The sampled rectangles are inset within real visible panes, excluding frames,
exterior cast shadows, rails, lamps, people and vegetation. These are approximate
registered pane interiors, not a metric photogrammetric facade texture.
"""
from pathlib import Path
import hashlib,json
HERE=Path(__file__).resolve().parent
IMAGE=HERE/'research/bund07-2025-suicasmo-original.jpg'
# Each entry: target exact opening label, top full pane, lower left, lower right.
SAMPLES=[
 ('front-L4-center-0',[
  [[2417,895],[2484,909],[2485,946],[2417,934]],
  [[2419,967],[2443,972],[2444,1082],[2419,1078]],
  [[2458,978],[2489,985],[2490,1093],[2459,1087]]]),
 ('front-L4-center-1',[
  [[2716,956],[2792,973],[2793,1025],[2717,1008]],
  [[2718,1041],[2740,1047],[2741,1138],[2719,1134]],
  [[2759,1053],[2793,1061],[2794,1150],[2760,1143]]]),
 ('front-L4-center-3',[
  [[3240,1091],[3297,1104],[3298,1137],[3241,1126]],
  [[3238,1159],[3255,1164],[3256,1257],[3239,1253]],
  [[3277,1170],[3299,1176],[3300,1264],[3278,1259]]]),
 ('front-L3-center-0',[
  [[2417,1521],[2490,1537],[2491,1580],[2418,1566]],
  [[2419,1605],[2441,1610],[2442,1703],[2420,1699]],
  [[2458,1616],[2492,1624],[2493,1711],[2459,1706]]]),
 ('front-L3-center-1',[
  [[2727,1574],[2803,1591],[2804,1630],[2728,1614]],
  [[2729,1647],[2751,1652],[2752,1747],[2730,1743]],
  [[2770,1658],[2806,1667],[2807,1757],[2771,1749]]]),
 ('front-L3-center-3',[
  [[3255,1657],[3317,1670],[3318,1718],[3256,1705]],
  [[3261,1745],[3281,1751],[3282,1824],[3262,1820]],
  [[3299,1757],[3320,1764],[3321,1835],[3300,1829]]])]

def main():
 windows=[]
 for label,quads in SAMPLES:
  windows.append({'label':label,'top_pane_fraction_of_inner_height':.40,'lower_middle_mullion_fraction':.50,'pane_layout':'one full-width top transom; two separate lower lights','panes':[{'id':name,'source_quad_px':quad,'selection':'Manually inspected glass interior, deliberately inset from black frame and exterior reveal.'} for name,quad in zip(['top','bottom-left','bottom-right'],quads)]})
 out={'schema':'bund07-individual-glass-controls-v1','image':'research/bund07-2025-suicasmo-original.jpg','image_sha256':hashlib.sha256(IMAGE.read_bytes()).hexdigest(),'image_bytes':IMAGE.stat().st_size,'source_url':'https://commons.wikimedia.org/wiki/File:Great_Northern_Telegraph_Building_20250501.jpg','author':'Suicasmo','license':'CC0-1.0','date':'2025-05-01','stored_size':[5184,3456],'exif_orientation':1,'coordinate_contract':'Stored and oriented source pixels coincide; UV=(x/5184,y/3456), top-left origin. Original JPEG unchanged.','scope':'Six unobstructed front central third/fourth-floor assemblies, eighteen glass panes. Stone, black frames, external shadows, iron rails, lamps and people are excluded.','limitations':['Samples are manually inset into visible real glazing and fitted independently to the corresponding geometric pane. They are not full-facade photogrammetry.','Glazing/frame dimensions are separate photo estimates. Safe inset samples slightly crop curtain/reflection content; do not infer complete interior layout.','End triplets, central paired third-floor lights, central fourth-floor middle/far-right lights, lower floors and side/rear glass remain geometric materials.','No external photo editing, resampling or generated replacement imagery.'],'windows':windows}
 (HERE/'photo-glass-controls.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps({'windows':len(windows),'panes':sum(len(w['panes']) for w in windows),'source_sha256':out['image_sha256']},indent=2))
if __name__=='__main__':main()
