"""Transcribe apartment facade openings from the native published pictures."""
import json
from pathlib import Path
import numpy as np
from register_court import Camera,DATA
root=Path(__file__).resolve().parent
def write(q):return [float(v)for v in q]
# Corners are inside the visible masonry opening, not the face of a guard or its shade.
windows={
 '25':{
 'west-plain.top4':[(271,98),(321,87),(321,123),(271,133)],
 'west-plain.middle3':[(266,178),(318,169),(318,212),(264,219)],
 'west-plain.lower2':[(260,271),(316,264),(317,310),(259,315)],
 'east-of-entry.top4':[(383,72),(439,62),(442,96),(383,104)],
 'east-of-entry.middle3':[(385,162),(449,151),(453,196),(387,204)],
 'east-of-entry.lower2':[(388,257),(454,251),(457,304),(390,307)],
 },
 '04':{
 'east-of-entry.lower2':[(165,176),(378,182),(370,334),(160,330)],
 'east-of-entry.ground':[(241,523),(400,525),(395,684),(233,685)],
 'east-of-rail.lower2':[(911,202),(1092,206),(1095,350),(910,346)],
 'east-of-rail.ground':[(909,529),(1092,531),(1103,679),(910,680)],
 }}
data=[]
for key,rows in windows.items():
 c=Camera(key)
 for name,pts in rows.items():
  if name=='east-of-rail.ground':note='East edge partially screened by foliage. Ground-floor security grille projects outside the fixed original jamb.'
  elif name=='east-of-entry.ground':note='Gao04 original masonry jamb/sill. The forward metal-bar cage visible in Masa25 has different depth.'
  elif name=='west-plain.top4':note='Air conditioner brackets shade part of right jamb.'
  else:note='Estimate at structural opening in the orange brick plane.'
  m=np.array([c.wall(p) for p in pts]);data.append({'station':key,'opening':name,'pixels_tl_tr_br_bl':pts,'xyz':m.tolist(),'bounds_x0_z0_x1_z1':write([np.mean(m[[0,3],0]),np.mean(m[[2,3],2]),np.mean(m[[1,2],0]),np.mean(m[[0,1],2])]),'note':note})
cornices=[{'label':'25 crown underside above west/plain','key':'25','pixel':[246,75],'y':-.37},{'label':'25 crown underside above east balcony','key':'25','pixel':[470,28],'y':-.37},{'label':'Gao04 second-floor balcony front top','key':'04','pixel':[650,328],'y':-.192},{'label':'Gao04 second-floor front lip below turquoise apron','key':'04','pixel':[645,450],'y':-.192},{'label':'Gao04 first-floor solid balcony paraped rim, added thin garden rail above','key':'04','pixel':[634,675],'y':-.192},{'label':'Gao04 floor3 underside at its front edge','key':'04','pixel':[651,109],'y':-.192},{'label':'25 floor4 balcony front lower edge','key':'25','pixel':[531,103.5],'y':-.192},{'label':'25 floor3 balcony front lower edge','key':'25','pixel':[544,215],'y':-.192}]
for q in cornices:q['xyz']=write(Camera(q['key']).wall(q['pixel'],q['y']))
report={'scale':'Calibrated conditional on 2.10 ±0.15m door leaf, common factor ±7%, plus ±0.18m ground datum. Façade opening positions are independently measured in the stated shot.','windows':data,'heights':cornices,'unsupported':['Masa26 is an adjacent composition: do not register its balcony onto Gao04.','Both photographers leave trees, grilles and newer enclosures across the first-floor frontage.','The full street building and rear of the court building are separate scopes.']}
(root/'window-controls.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
for row in data:print(row['opening'],row['station'],[round(i,2) for i in row['bounds_x0_z0_x1_z1']])
print([(q['label'],round(q['xyz'][2],2))for q in cornices])
