"""Construct the four raised cardinal-hour marks measured in the frontal court photograph."""
import json
from pathlib import Path
root=Path(__file__).resolve().parents[1]
# Pixel corners in a fivefold reading crop of the clock. X is right and image rows descend.
numerals={
 '12': [[[(195,69),(201,62),(210,62),(210,119),(199,119),(199,78)]],
        [[(217,66),(225,61),(245,61),(251,66),(251,79),(234,101),(250,101),(250,118),(217,118),(217,105),(238,77),(218,77)]]],
 '3': [[[(341,215),(350,209),(388,209),(398,214),(398,228),(391,236),(398,240),(398,260),(391,265),(348,265),(342,260),(342,246),(356,246),(357,252),(381,252),(381,242),(370,242),(370,232),(378,224),(345,224)]]],
 '6': [[[(197,365),(209,359),(243,359),(254,365),(246,374),(215,374),(211,381),(244,381),(254,388),(254,407),(247,415),(205,415),(196,410)],[(210,397),(210,403),(239,403),(239,396)]]],
 '9': [[[(49,217),(59,210),(96,210),(106,216),(106,259),(99,265),(58,265),(50,259),(56,250),(91,250),(93,243),(58,243),(49,236)],[(63,224),(63,231),(92,231),(92,224)]]]}
out={}
for label,polygons in numerals.items():
 points=[xy for poly in polygons for ring in poly for xy in ring];x=[p[0]for p in points];y=[p[1]for p in points];xc=(min(x)+max(x))/2;yc=(min(y)+max(y))/2
 out[label]=[[[[round((u-xc)*.00638,5),round((yc-v)*.00638,5)]for u,v in ring]for ring in poly]for poly in polygons]
(root/'source/clock-numerals.json').write_text(json.dumps(out,separators=(',',':'))+'\n')
