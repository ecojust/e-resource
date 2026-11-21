"""Intersect visible features from the wide frontal photograph with the courtyard wall."""
from pathlib import Path
import json
import numpy as np
from scipy.spatial.transform import Rotation

ROOT=Path(__file__).resolve().parent
fit=json.loads((ROOT/'courtyard-camera-fit.json').read_bytes())
x,y,z,yaw,pitch,roll,du,dv,scale=fit['fitted_camera_parameters'][0]
f=22/36*4032*1480/3963*scale
rotation=Rotation.from_euler('xyz',[pitch,yaw,roll])


def intersect(u,v,plane):
    front=rotation.inv().apply([(u-740-du)/f,-(v-959/2-dv)/f,1])[[0,2,1]]
    point=np.array([x,y,z])+front*(plane-y)/front[1]
    return [round(float(i),3) for i in point]


samples={
 'central entrance head':(703,431,0),'lower glazing transom':(704,477,0),
 'west inner triple upper left':(469,423,0),'west inner triple upper right':(593,423,0),
 'east inner triple upper left':(813,423,0),'east inner triple upper right':(932,423,0),
 'middle triple west left':(295,430,.48),'middle triple west right':(417,430,.48),
 'middle triple east left':(982,430,.48),'middle triple east right':(1099,430,.48),
 'outer triple west left':(111,431,.48),'outer triple west right':(231,431,.48),
 'outer triple east left':(1159,434,.48),'outer triple east right':(1270,434,.48),
 'side tall window sill at landing':(1037,590,.48),
 'central gable west toe':(420,338,.02),'central gable east toe':(982,343,.02),
 'central gable left plaque shoulder':(588,257,.02),'central gable right plaque shoulder':(821,257,.02),
 'upper sign centre':(704,235,.02),'attic window head':(704,279,.02),
 'inner Chinese left':(622,269,.02),'inner Chinese right':(782,269,.02),
 'outer Chinese left':(563,302,.02),'outer Chinese right':(841,304,.02),
 'cream frieze bottom':(696,419,0),'cream frieze top':(695,374,0),
 'curved gable east toe':(1085,350,.45),'curved gable east crest':(1201,250,.45),
 'curved gable east window sill':(1201,340,.45),'curved gable east window crown':(1201,291,.45),
 'curved gable west toe':(291,346,.45),'curved gable west crest':(165,240,.45),
 'curved gable west window sill':(171,330,.45),'curved gable west window crown':(172,279,.45),
 'small west dormer ridge':(391,228,3.8),'small west dormer glass head':(391,268,3.8),
 'small east dormer ridge':(997,232,3.8),'small east dormer glass head':(997,270,3.8),
}
report={name:{'image_xy':list(row[:2]),'chosen_facade_y':row[2],'model_xyz':intersect(*row)} for name,row in samples.items()}
(ROOT/'courtyard-elevation-picks.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
for name,pick in report.items():print(name,pick['model_xyz'])
