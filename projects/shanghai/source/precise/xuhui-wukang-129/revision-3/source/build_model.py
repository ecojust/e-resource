"""Refine the two arched openings of the existing 129 Wukang Road city object."""
from pathlib import Path
import argparse
import importlib.util
import json
import sys

HERE=Path(__file__).absolute().parent
ORIGINAL=HERE.parents[1]
PROJECT=next(p for p in HERE.parents if (p/'tools/package_architectural_model.py').is_file())
sys.path.insert(0,str(HERE))
spec=importlib.util.spec_from_file_location('wukang_original',ORIGINAL/'build_model.py')
original=importlib.util.module_from_spec(spec)
spec.loader.exec_module(original)
sys.path.insert(0,str(PROJECT/'source/precise/hongkou-tanggu-road-apartment-dated-crown/source'))
from crown_builder import CrownBuilder
import finish_surfaces
import wukang_archivolt
import wukang_balcony

ID='xuhui-wukang-129'
SLUG='wukang-129-arched-door-and-balcony'
PALETTE={**wukang_archivolt.PALETTE,**wukang_balcony.PALETTE,**finish_surfaces.PALETTE}
META=dict(id=ID,name='武康路129号德利那齐宅',address='上海市徐汇区武康路129号',
          gers_id='e73638a1-a217-47f7-a17b-151902f0fece',source_local_id=3733,
          heritage_id='sh-historic-b5-xh-j-091-v',city_object=ID,
          geometry_license='CC-BY-SA-4.0',geometry_source_license='ODbL-1.0',
          geometry_source_attribution='© OpenStreetMap contributors, way 582319150. Overture Maps Foundation Buildings.',
          photo_source='https://commons.wikimedia.org/wiki/File:20260209_129_Wukang_Road.jpg',
          earlier_view='https://commons.wikimedia.org/?curid=61788292',
          photo_author='Windmemories (2026) and Antigng (2017), CC BY-SA 4.0',
          original_model_commit='b296b5ac4f68b4e6743f02fb2bb3c01091cab841',
          original_mesh_sha256='c0915a9d76761865b4020d31397b8ef66ddb6efc4112bbee150264119754afa9',
          camera_views=json.loads((HERE/'cameras.json').read_bytes()),viewer_page=SLUG+'.html',
          photos_embedded=False,scope='保留城市原有建筑本体与地块，按两期照片细化街面拱套和二层外开双扇。模型采用2026年可辨的开启角度。')

class Builder(CrownBuilder):
    """Keep the original building coordinate frame and add metric UVs to new finishes."""
    def add(self,vertices,faces,material='limestone',label='detail'):
        before=len(self.parts)
        original.Builder.add(self,vertices,faces,material,label)
        if len(self.parts)>before and material in finish_surfaces.SURFACES:
            finish_surfaces.map_finish(self.parts[-1])

    def save(self,path,metadata=None):
        super().save(path,metadata)
        return finish_surfaces.embed_normals(path)

def add_building(builder,lod=False):
    # The legacy factory supplies all nine building-specific material overrides.
    # Its existing walls, slopes, individually lapped tiles and original openings
    # remain the single source of the house in this revision.
    def use_existing_palette(palette):
        builder.palette.update(palette)
        builder.palette.update(PALETTE)
        return builder
    return original.build(None,builder_factory=use_existing_palette,
                          archivolt=wukang_archivolt.add_archivolt,
                          balcony_doors=wukang_balcony.add_balcony_doors,
                          low_detail=lod)

if __name__=='__main__':
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--output',type=Path,required=True);cli.add_argument('--lod',action='store_true')
    args=cli.parse_args()
    b=Builder(PALETTE);add_building(b,args.lod)
    print(b.save(args.output,META)['sha256'])
