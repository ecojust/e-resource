"""Export a front elevation made from the garage model, without archival raster material."""
from pathlib import Path
import sys
from xml.etree.ElementTree import Element,SubElement,ElementTree
import numpy as np
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'source'))
from build_model import Builder
from garage1930s import PALETTE,add_historic_garage,wing_basis
def main(path):
    b=Builder(PALETTE);add_historic_garage(b)
    a,axis,normal=wing_basis()
    svg=Element('svg',{'xmlns':'http://www.w3.org/2000/svg','viewBox':'0 0 904 374','role':'img','aria-label':'白赛仲公寓乌鲁木齐中路侧车库门复原立面，馆方约1932至1937年'})
    SubElement(svg,'rect',{'width':'904','height':'374','fill':'#f7f4ed'})
    records=[]
    for part in b.parts:
        v=np.asarray(part['vertices']);s=(v[:,:2]-a)@axis;d=(v[:,:2]-a)@normal
        # Concave ornamental grilles are projected using their original front triangles.
        for tri in part['triangles']:
            tri=list(tri)
            if np.min(d[tri])>=d.max()-.0001:
                pts=' '.join(f'{34+(s[i]-1.15)*150:.2f},{337-v[i,2]*150:.2f}' for i in tri)
                records.append((d.max(),part['material'],pts))
    shades={'weathered vertical boarding':'#aaa79d','pale stiles and diagonal rails':'#e2dcce','upper geometric grille':'#bdb7a6','dark iron fittings':'#413e38','shadow behind original leaves':'#413f39'}
    for _,material,pts in sorted(records,key=lambda r:r[0]):
        fill=shades[material.split(' | ')[1]]
        SubElement(svg,'polygon',{'points':pts,'fill':fill,'stroke':fill,'stroke-width':'.24'})
    for x,txt in [(34,'第一格 · 遮挡部分留暗'),(500,'第二格 · 合门的 V 形斜压条')]:
        g=SubElement(svg,'text',{'x':str(x),'y':'360','font-size':'14','fill':'#302f2c','font-family':'sans-serif'});g.text=txt
    ElementTree(svg).write(path,encoding='utf-8',xml_declaration=True)
if __name__=='__main__':main(Path(sys.argv[1]))
