"""Build the photographed three-storey garden villa at 1, Lane 336, Jianguo West Road."""
import argparse
import importlib.util
import json
from pathlib import Path
import sys

HERE = Path(__file__).absolute().parent
PROJECT = next(p for p in HERE.parents if (p / 'tools/package_architectural_model.py').is_file())
sys.path.insert(0,str(PROJECT/'source/precise/hongkou-general-post-office/source/common'))
sys.path.insert(0,str(PROJECT/'source/precise/hongkou-tanggu-road-apartment-dated-crown/source'))
sys.path.insert(0,str(HERE))
from photo_architecture import Builder as GeometryBuilder
from crown_builder import CrownBuilder
import entrance_details
import bay_carvings, courtyard_portico, courtyard_roof, finish_surfaces, garden_front, west_side

ID = 'xuhui-jianguo-336-lane-one-villa'
SLUG = 'jianguo-336-lane-one-villa'
META = dict(id=ID, name='福德坊1号花园住宅', address='上海市徐汇区建国西路336弄1号', heritage_group='5D083',
            source='https://fgj.sh.gov.cn/yxlsjz/20200414/b9946bf8508e4b9689671fcd4146bb86.html',
            photo_source='https://blog.sina.cn/dpool/blog/s/blog_5d1bdf480101f66y.html',
            photo_author='高参88文章汇集，部分未署名', photos_embedded=False, geometry_license='MIT',texture_license='MIT',
            viewer_page=SLUG+'.html', scope='1号院内住宅。双层柱廊、弧阶、折角窗湾及西墙依据院内与巷中照片。屋顶、后侧和遮挡处按已知边界估算。',
            camera_views=json.loads((HERE/'cameras.json').read_bytes()))
PALETTE = {**bay_carvings.PALETTE, **garden_front.PALETTE, **courtyard_portico.PALETTE, **courtyard_roof.PALETTE,
           **west_side.PALETTE, **entrance_details.PALETTE, **finish_surfaces.PALETTE}

# The source writer is shared with the hospital doorway. Load it under a private
# module name to keep this villa's photographed lamp binding local to this model.
emission_path = PROJECT/'source/precise/xuhui-shaanxi-202-former-yihe-hospital/source/pendant_emission.py'
emission_spec = importlib.util.spec_from_file_location('fudefang_lamp_writer',emission_path)
emission = importlib.util.module_from_spec(emission_spec)
emission_spec.loader.exec_module(emission)
emission.GLOBE = entrance_details.GLOBE
emission.EMISSION = [1.,.70,.27]

class Builder(CrownBuilder):
    def add(self,vertices,faces,material='limestone',label='detail'):
        count = len(self.parts)
        GeometryBuilder.add(self,vertices,faces,material,label)
        if len(self.parts)>count and material in finish_surfaces.SURFACES:
            finish_surfaces.map_finish(self.parts[-1])

    def save(self,path,metadata=None):
        if any(self.palette[p['material']].get('texture') for p in self.parts):
            super().save(path,metadata)
            report=finish_surfaces.embed_normals(path)
        else:
            report=GeometryBuilder.save(self,path,metadata)
        if any(p['material']==entrance_details.GLOBE for p in self.parts):
            return emission.bind(path,report)
        return report

def add_building(b,lod=False):
    garden_front.add_front(b,lod)
    courtyard_portico.add_courtyard_portico(b,lod)
    west_side.add_west(b,lod)
    courtyard_roof.add_roof(b,lod)
    entrance_details.add_details(b,lod)

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',required=True,type=Path)
    parser.add_argument('--lod',action='store_true')
    args=parser.parse_args()
    b=Builder(PALETTE)
    add_building(b,args.lod)
    print(b.save(args.output,META)['sha256'])
