"""Regenerate the documented upper gable of the former Yangshupu Road residence."""
import argparse,sys
from pathlib import Path
import numpy as np
from finishes import BRICK,STONE,PALETTE
from pediment import add_pediment
SOURCE=Path(__file__).absolute().parent
PROJECT=next(p for p in [*SOURCE.parents,Path.cwd(),*Path.cwd().parents] if (p/'tools/package_architectural_model.py').is_file())
sys.path.insert(0,str(PROJECT/'tools'))
import package_architectural_model
sys.path.insert(0,str(PROJECT/'source/precise/hongkou-tanggu-road-apartment-dated-crown/source'))
from crown_builder import CrownBuilder
ID='yangpu-yangshupu-road-713-historic-residence'
META=dict(id=ID,name='杨树浦路713号花园住宅的红砖山花',address='杨树浦路713号',heritage_group='5G006',
          viewer_page='yangshupu-road-713-historic-residence.html',
          period='民国时期住宅，山花按2015年4月6日照片呈现。',
          scope='红砖山花上段、双层斜向压顶与折头、带八道扇肋的半圆陶石顶饰、四键饰圆眼和百叶。',
          dimensions='展陈比例由照片上可辨砖皮估算，后缘和遮挡处为截面。',
          photo_author='Fayhoo，2015，CC BY-SA 3.0',
          photo_source='https://commons.wikimedia.org/wiki/File:Pinglianglu_Paichusuo.JPG',
          url='https://fgj.sh.gov.cn/yxlsjz/20200414/b9946bf8508e4b9689671fcd4146bb86.html',
          geometry_license='MIT',texture_license='MIT, project-generated brick and stone',
          license_url='https://opensource.org/license/mit',photos_embedded=False,third_party_models_embedded=False,
          copyright='Original reconstructed geometry and procedural materials, MIT. Reference photograph copyright Fayhoo, CC BY-SA 3.0.')
class GableBuilder(CrownBuilder):
    def add(self,vertices,faces,material=BRICK,label='Gable'):
        super().add(vertices,faces,material,label)
        if material in (BRICK,STONE):
            part=self.parts[-1];coords=np.asarray(part['texcoords'])
            period=(1.92,1.056) if material==BRICK else (.83,.83)
            part['texcoords']=(coords/(.78*np.array(period))).tolist()
def build(lod=False):
    b=GableBuilder(PALETTE);add_pediment(b,lod);return b
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('output',type=Path);p.add_argument('--lod',action='store_true')
    a=p.parse_args();model=build(a.lod);r=model.save(a.output,META);print(len(model.parts),r['triangles'],r['sha256'])
