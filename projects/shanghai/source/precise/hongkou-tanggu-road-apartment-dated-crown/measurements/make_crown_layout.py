"""Art-study coordinates. One plaque width sets the exhibit's local scale."""
import json
from pathlib import Path

OUT = Path(__file__).resolve().parent
UNIT = 4.0
def make():
    openings=[]
    for left,right,head in [(-.812,-.572,.355),(-.384,-.147,.353),(.070,.287,.353),(.487,.709,.362)]:
        openings.append(dict(x0=UNIT*left,x1=UNIT*right,z0=0.,z1=UNIT*head,
                             face_y=.035*UNIT,recess=.021*UNIT))
    return {
        'display_units_per_plaque_width':UNIT,
        'scale_note':'归一化建筑展品。年份匾全宽取四个展示单位，文件坐标不代表建筑实测米数。厚度、折面的进退和未见的剖切收口为展示估计。',
        'cartouche':dict(width_m=UNIT,height_m=.181*UNIT,center_x_m=0.,center_z_m=1.16*UNIT,wall_y_m=0.),
        'openings':openings,
        'panels':[dict(x0=UNIT*l,x1=UNIT*r,z0=UNIT*b,z1=UNIT*t,face_y=UNIT*.035,depth=UNIT*.012)
                  for l,r,b,t in [(-.798,-.586,.404,.587),(-.370,-.161,.397,.578),
                                  (.077,.281,.398,.579),(.493,.704,.409,.593)]],
        'towers':{'front_outline_in_plaque_widths':[[.88,.36],[1.10,-.15],[1.41,-.40],[1.77,-.25],[2.02,.15]],
                  'cut_back_y':.47,'cap_top':1.46,'body_top':1.385,'recess_head':.165,
                  'ribs_at_vertices':[2,3],'ribs_head':.695,
                  'evidence':'两侧前沿均有三块可见折面，双道浅色竖肋沿折角收头。斜视可见内侧回折。背侧在统一剖切面收口。'},
        'centre':{'cut_z':-.065,'parapet_top':1.295,'parapet_bottom':.775,
                  'fin_x':[-.443,-.018,.402],'fin_top':.975,'pier_x':[-.966,.920],
                  'cap_white_top':1.012,'cap_white_bottom':.718}
    }
if __name__=='__main__':
    (OUT/'crown-layout.json').write_text(json.dumps(make(),ensure_ascii=False,indent=2)+'\n')
