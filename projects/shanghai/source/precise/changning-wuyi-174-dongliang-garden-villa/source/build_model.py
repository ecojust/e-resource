"""Reconstruct the street and garden elevations of the villa at 174 Wuyi Road."""
import argparse
from pathlib import Path

from wuyi_fabric import PALETTE as FABRIC, PROJECT
from villa_roofs import PALETTE as ROOF, VillaBuilder, add_roofs
from north_balcony import add_north_balcony
from north_garden import PALETTE as GARDEN, add_north_garden
from south_gable_oriel import PALETTE as ORIEL, add_south_oriel
from south_garden_bay import PALETTE as SHOP, add_south_bay
from street_gable import add_street_gable
from villa_envelope import add_envelope

PALETTE={**FABRIC,**ROOF,**GARDEN,**SHOP,**ORIEL}
ID='changning-wuyi-174-dongliang-garden-villa'
SLUG='wuyi-174-dongliang-garden-villa'
META=dict(id=ID,name='武夷路174号花园住宅',address='上海市长宁区武夷路168号翡悦里174号别墅',
          period='2025',viewer_page=SLUG+'.html',heritage_group='5M018',
          scope='朝武夷路的木格山墙、挑檐和铁艺阳台，园内的弧形落地门窗、错层老虎窗和相交的坡屋顶。',
          dimensions='街侧主墙宽约7.2米，两上窗中心约相隔2.60米。屋脊、窗台标高和遮挡处进深按照片及航片估算。',
          photo_author='Antigng（2018）；上海市长宁区人民政府（2024年6月）；棟梁之家开业图组（搜狐，2024年10月）；Alessandro Wang（Financial Times，2025年9月）；SmartShanghai。',
          photo_source='https://www.chinastrategy.org/2025/09/12/maison-dongliang-a-style-sanctuary-in-shanghai/',
          url='https://fgj.sh.gov.cn/yxlsjz/20200414/b9946bf8508e4b9689671fcd4146bb86.html',
          photos_embedded=False,third_party_models_embedded=False,geometry_license='MIT, original reconstruction',
          texture_license='MIT, original procedural roughcast, clay roof tiles and stone balcony facing',license_url='https://opensource.org/license/mit',
          copyright='Original geometry and procedural architectural finishes, MIT. Reference photographs are credited in the source notes.')


def add_building(b,lod=False):
    add_street_gable(b,lod)
    add_north_balcony(b,lod)
    add_envelope(b,lod)
    add_south_bay(b,lod,{'south_eave_z':5.48,'south_bay_soffit_z':5.22})
    add_south_oriel(b,lod)
    add_roofs(b,lod)
    add_north_garden(b,lod)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',required=True,type=Path)
    parser.add_argument('--lod',action='store_true')
    args=parser.parse_args()
    b=VillaBuilder(PALETTE)
    add_building(b,args.lod)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    stats=b.save(args.output,META)
    print(stats['triangles'],stats['parts'],stats['sha256'])


if __name__=='__main__':
    main()
