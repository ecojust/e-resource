"""Face and relief return probes on decoded geometry, at documented picture positions."""
from pathlib import Path
import os,runpy
from crown import xz,BRICK,PIER,EDGE,FACE,DISC,LETTER,SCALE_X
root=Path(os.environ.get('SHANGHAI_PROJECT_ROOT',Path(__file__).absolute().parents[4]))
Reader=runpy.run_path(str(root/'data/audit/postal-office-v1/independent-glb-review-helpers.py'))['SerialScene']
def check(reader):
    out=[]
    def beam(label,uv,material):
        x,z=xz(*uv)
        hit=reader.ray([x,-1.,z],[0,1,0],1.7)
        out.append(dict(part=label,picture_2019_rectified_px=uv,origin=[x,-1.,z],direction=[0,1,0],expected=material,hit=hit,passed=(hit['material'] if hit else None)==material))
    for u,top,foot in [(24,190,374),(239,98,293),(496,115,297),(714,219,376)]:
        for k in (.12,.53,.91):beam('projecting pier-cap tongue',(u,top+(foot-top)*k),FACE)
        for delta in (-14,14):beam('separate cap step',(u+delta,top+30),PIER)
        beam('pier shaft',(u,470),PIER)
    for u,t,e in [(147,206,345),(372,113,205),(599,211,354)]:
        beam('small pendant central drop',(u,(t+e)/2),FACE);beam('sky beside pendant',(u+30,t-6),None)
    for u in (145,613):
        for du in (-44,44):beam('stepped arrow wing',(u+du,397),FACE)
        beam('central lower arrow',(u,424),FACE);beam('shoulder',(u,377),FACE);beam('brick below arrow',(u,471),BRICK)
    for u,v in [(378,285),(357,285),(378,311),(405,288),(378,250)]:beam('solid roundel centre',(u,v),DISC)
    for u,v in [(326,285),(431,285),(378,233),(378,336)]:beam('relief annulus',(u,v),EDGE)
    for u,v in [(322,218),(336,229),(341,198),(371,207),(380,223),(401,202),(406,230)]:beam('1933 numeral',(u,v),LETTER)
    beam('lower toe of central crown above the third digit',(371,200),FACE)
    for v,material in [(374,EDGE),(395,PIER),(448,EDGE),(465,BRICK)]:beam('central spandrel',(350,v),material)
    for u,v in [(305,237),(440,355),(186,310),(552,350)]:beam('running bond',(u,v),BRICK)
    return dict(passed=all(r['passed'] for r in out),samples=out)
