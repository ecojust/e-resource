"""Transcribe visible outer frame and fixture edges in Fayhoo's and the register's photographs."""
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent

def full(x,y):
    return [round((x+.5)*2041/860-.5,3), round((y+.5)*1363/574-.5,3)]

def quadrilateral(left,top,right,bottom,lean):
    slope=-.029
    return [full(left+lean*.5,top),full(right+lean*.5,top+slope*(right-left)),
            full(right-lean*.5,bottom+slope*(right-left)),full(left-lean*.5,bottom)]

# The close photograph cuts the easternmost opening at the two first levels.
# The other photograph resolves that bay. Preserve the difference in the record.
frames=[
    [None,(57,299,84,346,11),(165,297,222,344,9),(257,293,319,341,6),(355,289,418,338,3),
     (456,286,521,335,0),(558,282,622,331,-4),(707,277,747,327,-10),(781,274,825,324,-12)],
    [None,(89,209,120,248,11),(190,201,241,242,8),(273,198,329,239,6),(363,194,422,235,3),
     (455,190,513,231,0),(543,186,601,228,-4),(679,182,717,224,-8),(749,181,786,220,-12)],
    [(69,137,91,166,9),(119,133,147,163,8),(215,128,258,160,6),(295,124,337,156,5),
     (372,119,422,152,2),(454,116,502,149,0),(535,112,586,145,-3),(659,110,692,141,-8),(725,106,756,138,-9)],
    [(96,78,122,90,5),(148,74,177,86,5),(243,66,275,80,3),(306,62,348,76,3),
     (378,58,420,73,2),(452,54,496,69,0),(525,51,568,65,-1),(636,46,662,60,-5),(694,44,721,57,-5)]]
obs=[]
for level,row in enumerate(frames,1):
    for bay,bounds in enumerate(row,1):
        if bounds is None:
            obs.append(dict(level=level,bay=bay,method='Bay visible in oblique archive view; use upper bay centre and neighbouring frame height.'))
        else:
            obs.append(dict(level=level,bay=bay,view='close',outer_frame=quadrilateral(*bounds)))
# Air-conditioning condensers are documented as building services at the
# photograph date. Eight small street obstructions do not contribute to the facade.
units=[(435,310),(542,306),(776,296),(131,222),(432,206),(528,204),
       (161,144),(518,128),(606,129),(634,121),(709,118),(182,75),(360,62),(510,54)]
# 2017 unmodified 800x1200 frame coordinates. The high side window, opening
# and two cantilevered hoods are registered on the outer return beside the porch.
flank=dict(door=[[522,884],[608,872],[610,1062],[522,1051]],transom=[[533,763],[593,753],[593,792],[533,802]],
 lower_hood=[[475,812],[671,784],[661,817],[484,846]],
 upper_hood=[[493,733],[662,697],[650,723],[504,752]])
front=dict(sash=obs,condensers=[full(x,y) for x,y in units],west_side=flank,
    close_photo_sha256='c488b0074286f2a53096c7a2ef64da30773bf27f5094539a6474d54ed4ace530',
    wide_photo_sha256='4b977f436661e01692a9b14c04b34f657177c2e3ac557c211d785b70755716dd',
    method='Visible sash extents were read in a 860 by 574 copy and converted to the 2041 by 1363 original. The western portal uses the 800 by 1200 archive photograph. The low eastern corner is partly hidden by the bank sign.')
(HERE/'north-wall-openings.json').write_text(json.dumps(front,indent=2,ensure_ascii=False)+'\n')
