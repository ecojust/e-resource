"""Package the documented three-span bridge and verify its reopened editable model."""
import argparse
import os
import sys
from pathlib import Path

source = Path(__file__).resolve().parent
sys.path.insert(0, str(source.parents[3] / 'tools'))
from package_architectural_model import build
from zhapu_bridge import PALETTE, build_bridge

ident = 'huangpu-zhapu-road-bridge'
scope = '乍浦路桥三跨钢筋混凝土梁、两处水面以上桥墩、实心栏墙、两侧人行道和上游桥名牌。'
meta = dict(id=ident, name='乍浦路桥', viewer_page='zhapu-road-bridge.html', scope=scope,
            model_scope_zh=scope, source_register=f'source/precise/{ident}/reference-review.json',
            status='River and street elevations reconstructed from attributed public photographs.',
            documented_dimensions=dict(length_m=71.94, spans_m=[17.68,36.58,17.68], total_width_m=17.3,
                                       carriageway_width_m=12.9, walkway_width_each_m=2.2),
            estimated='梁下缘线形、墩头断面、栏墙高度、路面标线和桥名牌的尺寸、字形和色泽按公开照片估计。',
            coordinate_convention='X across the bridge, positive east. Y along the bridge, positive north. Z relative to photographic waterline.',
            copyright='Original geometry and code under MIT. Reference photographs retain their own licences.')

if __name__ == '__main__':
    options = argparse.ArgumentParser(add_help=False)
    options.add_argument('--blender', default='blender')
    args, rest = options.parse_known_args()
    os.environ['ZHAPU_BLENDER'] = args.blender
    sys.argv[1:] = [*rest, '--blender', str(source/'blender_preview.py')]
    build(source, meta, PALETTE, build_bridge)
    import json
    manifest_file = Path(rest[rest.index('--out') + 1])/'manifest.json'
    manifest = json.loads(manifest_file.read_bytes())
    manifest['all_dimensions_estimated'] = False
    manifest['dimension_source'] = 'Shanghai municipal gazetteer, table of bridges over Suzhou Creek, row 3.'
    manifest_file.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + chr(10))
    audit = Path(rest[rest.index('--audit') + 1])/'geometry-native.json'
    record = json.loads(audit.read_bytes())
    record['render'] = 'Cycles, 12 samples, from reopened blend. OIDN RT sRGB postfilter.'
    audit.write_text(json.dumps(record, ensure_ascii=False, indent=2) + chr(10))
