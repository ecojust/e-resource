#!/usr/bin/env python3
"""Compose a reviewed V13 app release without writing MAIN or publishing.

Requires actual accepted model/static browser evidence, active catalog adoption,
native image review and byte-bound decoded/native checks. All output is new.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path, PurePosixPath
import posixpath
import re
from urllib.parse import unquote, urlsplit

HERE = Path(__file__).resolve().parent
V13 = HERE.parent
ID = 'yangpu-library'
PUBLIC = 'data/audit/precise-buildings-v13/yangpu-library'
SOURCE = 'source/precise/yangpu-library'
LIMIT = 100_000_000


def need(value, message):
    if not value:
        raise ValueError(message)


def read(path):
    return json.loads(Path(path).read_text())


def meta(path):
    path = Path(path)
    need(path.is_file(), 'Missing actual file: ' + str(path))
    with path.open('rb') as stream:
        digest = hashlib.file_digest(stream, 'sha256').hexdigest()
    return {'bytes': path.stat().st_size, 'sha256': digest}


def descriptor(path):
    return {'source': str(Path(path).resolve()), **meta(path)}


def bound_file(row, root=None, key='source'):
    value = row.get(key) or row.get('path') or row.get('file')
    need(isinstance(value, str), 'Bound row needs actual path')
    path = Path(value)
    if not path.is_absolute():
        need(root is not None, 'Relative path needs explicit parent')
        path = Path(root) / path
    need(meta(path) == {k: row[k] for k in ('bytes', 'sha256')}, 'Actual bytes changed: ' + str(path))
    return path.resolve()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--main', type=Path, default=Path('/workspace/shanghai_project'))
    parser.add_argument('--qa-support-manifest', type=Path,
                        help='Optional exact support-file whitelist beside the actual successful QA tools')
    parser.add_argument('--data-contract-check', type=Path,
                        help='Defaults to data-contract-check.json beside the accepted plan')
    for key in ('accepted-plan', 'native-report', 'independent-native-review', 'geometry-check',
                'web-check', 'lod-check', 'native-check', 'catalog-browser', 'catalog-visual', 'output'):
        parser.add_argument('--' + key, type=Path, required=True)
    args = parser.parse_args()
    out = args.output.resolve()
    need(out.is_relative_to(HERE) and not out.exists(), 'Use a fresh release subdirectory')
    plan = read(args.accepted_plan)
    need(plan.get('model_accepted') is True and plan.get('browser_accepted') is True,
         'Actual accepted model/static browser plan required')
    need(plan.get('runtime_changed') is False, 'This release does not alter runtime')
    expected_counts = {'navigation_count': 31, 'owner_count': 17, 'owner_macro_count': 11,
                       'near_count': 15, 'catalog_macro_count': 10, 'ordinary_record_count': 12}
    need(all(plan.get(k) == v for k, v in expected_counts.items()), 'Accepted count contract differs')
    contract_path = args.data_contract_check or args.accepted_plan.parent / 'data-contract-check.json'
    contract = read(contract_path)
    need(contract.get('passed') is True and contract['plan']['sha256'] == meta(args.accepted_plan)['sha256'] and
         contract['plan']['bytes'] == meta(args.accepted_plan)['bytes'], 'Final data composition proof differs from accepted plan')
    acceptance_source = bound_file(contract['actual_accept_script'])
    need(acceptance_source.parent == V13 / 'integration' and contract.get('runtime_changed') is False and
         contract.get('catalog_dynamic_lifecycle_claimed') is False,
         'Final acceptance source/scope differs')
    rows = {}
    for row in plan['files']:
        need(row['file'] not in rows, 'Duplicate accepted destination')
        bound_file(row)
        need(0 < row['bytes'] < LIMIT, 'Accepted file reaches size limit')
        current = meta(args.main / row['file']) if (args.main / row['file']).exists() else None
        desired = {k: row[k] for k in ('bytes', 'sha256')}
        need(current == row.get('old_main') or current == desired,
             'MAIN drift before release composition: ' + row['file'])
        rows[row['file']] = dict(row)
    nav = read(rows['data/landmarks.json']['source'])
    record = next(item for item in nav if item['id'] == ID)
    need(record.get('accepted') is True and not record.get('candidate_only'), 'Target remains a candidate')
    need(len(nav) == 31 and record.get('catalog_lifecycle_browser_passed') is False,
         'Static-adoption release must not claim complete dynamic catalog lifecycle')
    assets = record['assets']
    for item in assets.values():
        need(item['file'] in rows and all(rows[item['file']][k] == item[k] for k in ('bytes', 'sha256')),
             'Asset differs from accepted plan')
    native = read(args.native_report)
    independent = read(args.independent_native_review)
    need(native['raw']['sha256'] == assets['raw']['sha256'] and native['native']['sha256'] == assets['native']['sha256'],
         'Native rendering belongs to a different model')
    bound_file(native['raw']); bound_file(native['native'])
    need(native['triangles'] == record['triangles'] and len(native['images']) == 3,
         'Native model count or three-view report differs')
    need(independent.get('passed') is True and independent.get('status') != 'revision_required',
         'Final independent native image review is not passed')
    need(independent['raw_binding']['sha256'] == assets['raw']['sha256'] and
         independent['native_binding']['sha256'] == assets['native']['sha256'],
         'Independent image review belongs to earlier assets')
    reviewed = {Path(item['file']).name: item for item in independent['images']}
    image_paths = []
    for shot in native['images']:
        name = shot['file']
        need(Path(name).name == name and name in reviewed and reviewed[name].get('actually_viewed') is True,
             'Unreviewed native image')
        need(all(shot[k] == reviewed[name][k] for k in ('bytes', 'sha256')), 'Native image review hash differs')
        image_paths.append((name, bound_file(shot, args.native_report.parent, 'file')))
    geometry = read(args.geometry_check)
    need(len(geometry['models']) == 2 and all(item.get('passed') is True for item in geometry['models']),
         'Actual full/LOD source geometry check required')
    by_sha = {item['sha256']: item for item in geometry['models']}
    need(assets['raw']['sha256'] in by_sha, 'Actual geometry check is for an old raw model')
    web = read(args.web_check); lod = read(args.lod_check); reopened = read(args.native_check)
    for report, role in ((web, 'web'), (lod, 'lod')):
        need(report.get('passed') is True and report['web']['sha256'] == assets[role]['sha256'],
             'Actual compressed-role check differs: ' + role)
        need(report.get('normalAngleToleranceDegrees') == .05 and
             report['maximumNormalAngleDegrees'] <= .05,
             'Normal-direction verification tolerance differs')
        need(report['raw']['sha256'] in by_sha, 'Decoded role has no actual source geometry check')
    need(web['raw']['sha256'] == assets['raw']['sha256'], 'Web check raw binding differs')
    need(reopened.get('passed') is True and reopened['sha256'] == assets['native']['sha256'] and
         reopened['triangles'] == record['triangles'], 'Actual reopened native does not equal model triangle count')
    static = read(rows[PUBLIC + '/browser.json']['source'])
    need(static.get('passed') is True and static.get('technical_passed') is True and len(static['captures']) == 6,
         'Six-view actual static browser report required')
    static_visual = read(rows[PUBLIC + '/visual-review.json']['source'])
    need(static_visual.get('passed') is True and static_visual.get('reviewer') == 'root' and
         static_visual.get('browser_sha256') == rows[PUBLIC + '/browser.json']['sha256'] and
         len(static_visual.get('actually_viewed', [])) == 6,
         'Root actual six-image static review required')
    captured_static = {item['screenshot']['file']: item for item in static['captures']}
    need(len(captured_static) == 6, 'Static captures contain duplicate screenshot names')
    for shot in static_visual['actually_viewed']:
        capture = captured_static.get(shot['file'], {})
        need(shot.get('actually_viewed') is True and capture.get('screenshot_complete') is True and
             all(capture.get('screenshot', {}).get(key) == shot[key] for key in ('file', 'bytes', 'sha256')),
             'Root static image is not an actual completed browser capture')
        published_shot = rows.get(PUBLIC + '/' + shot['file'], {})
        need(all(published_shot.get(key) == shot[key] for key in ('bytes', 'sha256')),
             'Actually viewed static screenshot missing from accepted plan')
    catalog = read(args.catalog_browser); visual = read(args.catalog_visual)
    need(catalog.get('passed') is True and catalog.get('technical_passed') is True and catalog.get('finished_at') and
         catalog.get('run_scope') == 'catalog-only' and catalog.get('catalog_stage') == 'active' and catalog.get('building_id') == ID,
         'Actual completed catalog-only browser evidence required')
    need(catalog.get('web_sha256') == assets['web']['sha256'] and catalog.get('lod_sha256') == assets['lod']['sha256'],
         'Catalog browser model binding differs')
    need(all(catalog.get('checks', {}).get(key) is True for key in
             ('runtime_unchanged', 'full_loaded', 'source_owner', 'catalog_static_adoption')),
         'Actual catalog adoption/source/runtime checks incomplete')
    need(catalog.get('runtime_baseline_sha256') == plan['runtime_baseline']['sha256'], 'Catalog runtime binding differs')
    for role, filename in (('landmarks', 'data/landmarks.json'), ('registry', 'data/precise-buildings-v6.json')):
        expected = {key: rows[filename][key] for key in ('bytes', 'sha256')}
        need(all(catalog.get('expected_' + role, {}).get(key) == value for key, value in expected.items()),
             'Catalog expected metadata is not final accepted metadata: ' + role)
        need(all(catalog.get('actual_metadata', {}).get(role, {}).get(key) == value for key, value in expected.items()),
             'Catalog served metadata differs from final accepted metadata: ' + role)
    need(visual.get('passed') is True and visual.get('reviewer') == 'root' and visual.get('building_id') == ID and
         visual.get('browser_sha256') == meta(args.catalog_browser)['sha256'], 'Root catalog image review required')
    need(len(catalog['captures']) == len(visual['actually_viewed']) == 1, 'Catalog-only scope is one actual view')
    catalog_images = []
    for shot in visual['actually_viewed']:
        need(shot.get('actually_viewed') is True and Path(shot['file']).name == shot['file'], 'Unviewed catalog image')
        captured = catalog['captures'][0]
        need(captured.get('screenshot_complete') is True and
             all(captured.get('screenshot', {}).get(key) == shot[key] for key in ('file', 'bytes', 'sha256')),
             'Root catalog image is not the actual completed browser capture')
        catalog_images.append((shot['file'], bound_file(shot, args.catalog_browser.parent, 'file')))
    log = V13 / 'review/runtime-regression.log'
    text_log = log.read_text()
    need('tests 54' in text_log and 'pass 54' in text_log and 'fail 0' in text_log,
         'Actual 54-test runtime regression log missing')
    tool_names = ('browser_acceptance.py', 'audit-asset.js', 'fetch-json.js', 'keyboard-snapshot.js',
                  'streaming-probe.js', 'target-probe.js')
    static_tools = {Path(item['file']).name: item for item in static.get('tools', [])}
    catalog_tools = {Path(item['file']).name: item for item in catalog.get('tools', [])}
    need(set(tool_names).issubset(static_tools) and set(tool_names).issubset(catalog_tools),
         'Actual browser tool descriptors missing')
    tool_directory = Path(static_tools['browser_acceptance.py']['file']).resolve().parent
    need(tool_directory.is_relative_to(V13 / 'qa'), 'Successful tools must be the reviewed local QA package')
    actual_tools = {}
    for name in tool_names:
        source = bound_file(static_tools[name], key='file')
        need(source.parent == tool_directory, 'Static tool package spans unexpected directories')
        need(meta(source) == {key: catalog_tools[name][key] for key in ('bytes', 'sha256')},
             'Static and catalog runs use different final tool bytes: ' + name)
        bound_file(catalog_tools[name], key='file')
        actual_tools[name] = source
    support_files = []
    if args.qa_support_manifest:
        for item in read(args.qa_support_manifest)['files']:
            name = item['file']
            need(Path(name).name == name and name not in tool_names, 'Unsafe or duplicate QA support name')
            source = bound_file(item)
            need(source.parent == tool_directory, 'QA support must belong to the actual successful tool package')
            support_files.append((name, source))

    # Every required proof has been checked before creating the output tree.
    out.mkdir()
    added = []
    def add(name, source=None, content=None):
        rel = PurePosixPath(name)
        need(not rel.is_absolute() and '..' not in rel.parts and name == rel.as_posix() and
             not any(c in name for c in '\\:%?#'), 'Unsafe public destination')
        need(name == 'README.md' or name.startswith(('data/', 'source/', 'assets/')), 'Unexpected publication scope')
        if content is not None:
            source = out / 'payload' / name
            source.parent.mkdir(parents=True, exist_ok=True)
            source.write_text(content)
        source = Path(source).resolve(); info = meta(source)
        need(0 < info['bytes'] < LIMIT, 'Published file reaches 100000000 bytes')
        if name in rows:
            need(all(rows[name][key] == info[key] for key in ('bytes', 'sha256')), 'Conflicting destination: ' + name)
            return
        current = meta(args.main / name) if (args.main / name).exists() else None
        rows[name] = {'file': name, 'source': str(source), **info, 'old_main': current}
        added.append(name)

    for name, path in image_paths:
        add(SOURCE + '/previews/' + name, source=path)
    for name, path in (
        ('native-render-report.json', args.native_report),
        ('independent-native-review.json', args.independent_native_review),
    ):
        add(SOURCE + '/' + name, source=path)
    for name, path in (
        ('geometry-actual.json', args.geometry_check), ('web-compression-actual.json', args.web_check),
        ('lod-compression-actual.json', args.lod_check), ('native-reopen-actual.json', args.native_check),
        ('runtime-regression.log', log), ('catalog/browser.json', args.catalog_browser),
        ('catalog/visual-review.json', args.catalog_visual),
        ('data-contract-check.json', contract_path),
    ):
        add(PUBLIC + '/' + name, source=path)
    for name, path in catalog_images:
        add(PUBLIC + '/catalog/' + name, source=path)
    for name in tool_names:
        add(PUBLIC + '/tools/' + name, source=actual_tools[name])
    for name, source in support_files:
        add(PUBLIC + '/tools/' + name, source=source)
    for name in ('verify_glb.py', 'verify_native.py'):
        add(PUBLIC + '/tools/' + name, source=V13 / 'review' / name)
    assembly_snapshot = out / 'assemble_app_release.snapshot.py'
    assembly_snapshot.write_bytes(Path(__file__).read_bytes())
    add(PUBLIC + '/tools/assemble_app_release.py', source=assembly_snapshot)
    acceptance_snapshot = out / 'prepare_integration.actual-accept.snapshot.py'
    acceptance_snapshot.write_bytes(acceptance_source.read_bytes())
    need(meta(acceptance_snapshot) == {key: contract['actual_accept_script'][key] for key in ('bytes', 'sha256')},
         'Acceptance source changed while snapshotting')
    add(PUBLIC + '/tools/prepare_integration.actual-accept.py', source=acceptance_snapshot)

    sizes = {role: assets[role]['bytes'] for role in assets}
    table = '\n'.join('| ' + label + ' | [' + str(sizes[role]) + ' 字节](../../../' + assets[role]['file'] + ') |' for role, label in
                      [('raw', '原始 GLB'), ('web', '网页 GLB'), ('lod', '远景 LOD'), ('native', 'Blender 可编辑文件')])
    keyboard = static['keyboard']['measurement']
    movement = keyboard['displacement_m']
    uncertainty = '这是依据公开照片、规划资料和地图轮廓制作的外观模型，未经现场测绘或摄影测量。背面与内院窗数、局部尺寸、彩画和脊兽细节为推估；室内孔雀门和室内陈设未建模。'
    model_doc = f'''# 杨浦区图书馆整馆 · v13

已新增完整旧馆与扩建馆体，覆盖两处露天内院、四角现代翼部和南侧入口。主门细化重檐歇山琉璃瓦、瓦垄、斗拱彩画、三跨高窗、八角窗、入口格栅门、石栏杆与灯座；两条旧长翼东端含高窗、拱门和小阳台。

[打开漫游入口](../../../index.html#landmark=yangpu-library&mode=walk) · [建模源码与重建说明](authoring/README.md) · [照片署名与许可](authoring/ATTRIBUTION.md) · [本轮网页实际检查](../../../{PUBLIC}/README.md)

| 文件 | 实际大小与下载 |
|---|---|
{table}

所有文件均严格小于100,000,000字节。完整模型{record['triangles']:,}三角形，作者简化远景模型{record['lod_triangles']:,}三角形；LOD省去细石缝、竖槽并减少瓦垄与曲面采样，不是原模型三角面的严格子集。网页版Meshopt压缩的实际解码几何与原始模型位置、绕序和材质一致；Blender文件已重新打开并核对模型三角数。

![东侧整体](previews/east-full.png)

![东主入口细节](previews/east-entrance-detail.png)

![后侧与两处内院](previews/south-west-courtyards.png)

三图来自同一份最终模型，渲染相机未按照片标定。预览地面和灯光在独立Blender集合内，不属于导出的建筑GLB。模型不含照片贴图，材料、彩画与装饰为程序几何及估计色值。

{uncertainty} 规划图18.49m记为檐口值，本模型将其作为上层檐口约束；最高顶饰约22.48m，22.51m登记值是建模包络，并非官方实测总高。现代部分10.8m与图上H11.05的基准差异仍未解决。名义地面为0，门框收口最低约−0.02m。

四张Commons参考照片保留各自CC BY-SA许可；政府规划图仅用于内部研究，公开包没有其图像像素。代码与原创几何、地图轮廓及参考照片分别遵循[署名说明](authoring/ATTRIBUTION.md)中的许可。

''' 
    add(SOURCE + '/CURRENT_STATE.md', content=model_doc)
    realism = f'''# v13 来源与复原范围

新增杨浦区图书馆整馆，按2018年修缮扩建后的外观建立旧馆、现代翼部、两内院和南侧入口。它替换源owner `14-13722-6690:1196`，保留同一近景块其余9个邻居。全市16区底图保持，1,796,419个建筑及部件尚未逐栋完成照片复原。

依据包括四张已署名的Commons照片、馆方简介和杨浦区政府M101规划公告。主门朝东；地图轮廓用作整馆定位约束，并非实测墙线。18.49m是规划图檐口口径；最高顶饰约22.48m为照片比例推估。扩建10.8m与H11.05差异未强行统一为测量事实。

可见细节包括重檐瓦坡、斗拱和彩画带、石材分缝、真实门窗洞、旧翼东端单高窗/拱门、现代窄竖窗与横向幕墙、屋面绿化。{uncertainty} 模型没有照片纹理；色值、风化程度和彩画不是逐像素复制。

实际交付为原始GLB {sizes['raw']:,}字节、网页GLB {sizes['web']:,}字节、LOD {sizes['lod']:,}字节、Blender {sizes['native']:,}字节，均小于100,000,000字节。原始/压缩模型用真实解码比较；Blender重新打开核对；三个原生视图已人工查看。两处源内院内部采样点上方无高于0.5m模型三角面，这是一项有限几何检查，不等于每个院落像素或全部洞口都经测量。

网页实际检查包含完整模型、LOD、释放/返回、源与近远景替换、9邻居保留、可信W行走与松键停止，以及最终目录对静态模型的采用。共有6张静态/行走截图和1张目录采用截图，经root分别查看。未声明动态专用目录模式、损坏索引恢复、全部31导航、全市16区或用户硬件帧率经过本轮浏览器验证。31件运行时与V12一致；54项相关运行时回归通过。

[模型、预览与来源](../../{SOURCE}/CURRENT_STATE.md) · [实际审计与限制](../../{PUBLIC}/README.md)

''' 
    add('data/bund/REALISM_V13.md', content=realism)
    audit_doc = f'''# 杨浦区图书馆 v13 实际模型与网页检查

本轮新增一栋整馆精细模型。精选导航31项、普通精模12项、目录10个宏块；源建筑替换登记17项，涉及11个宏块和15个近景分块。全市1,796,419个建筑及部件仍未逐栋完成照片复原。

| 实际检查 | 证据与范围 |
|---|---|
| 模型总审查 | [root模型记录](model-review.json)，绑定四件交付资产及九项限定范围 |
| 原始几何 | [真实缓冲区检查](geometry-actual.json)，有限数值、法线、非退化三角面、两个内院内部天空采样点 |
| 网页与LOD压缩 | [完整模型](web-compression-actual.json)、[远景模型](lod-compression-actual.json)，实际Three/Meshopt解码的有向三角位置和材质一致；法线角容差保持0.05° |
| Blender | [实际重新打开](native-reopen-actual.json)，模型{record['triangles']:,}三角形；预览舞台不计入 |
| 原生外观 | [三图及源记录](../../../../{SOURCE}/CURRENT_STATE.md)，[独立图审](../../../../{SOURCE}/independent-native-review.json) |
| 静态场景与行走 | [实际浏览器](browser.json)、[root六图查看](visual-review.json)，完整/LOD/释放/返回、当前源、近远景owner、9邻居、W与停止 |
| 最终目录采用 | [实际浏览器](catalog/browser.json)、[root一图查看](catalog/visual-review.json)，真实session采用同一静态模型，未声称动态全生命周期 |
| 数据组合 | [实际契约检查](data-contract-check.json)，原30导航、16owner和9目录宏块保持；最终生成工具另存[接受时脚本](tools/prepare_integration.actual-accept.py)，候选阶段脚本原样保留 |
| 运行时 | [31文件基线](runtime31.json)、[54项相关回归](runtime-regression.log)，本轮没有生产运行时改动 |

本次可信W输入实际位移{movement:.3f}m，松键后3次记录的坐标和累积距离完全一致。相机与人物分离，未通过直接写坐标模拟行走。实际源模式为 `{static['source_check']['mode']}`；[源组件结果](browser.json)只覆盖当次加载，不是强制回退演练或测绘验证。

6张静态截图包括东入口、东北俯瞰、南入口、LOD、返回、W后；目录单独1图仅证明目录采用与近景状态。软件渲染截图不代表用户设备FPS。模型缺少后侧逐跨照片/实测资料，色彩、不可见细节和部分尺寸为推估；没有室内建模或照片纹理。[完整来源限制](../../../bund/REALISM_V13.md)。

浏览器和验证工具在[tools](tools/)；模型作者脚本在[source](../../../../{SOURCE}/authoring/README.md)。公开应用可以使用普通HTTP服务运行。检查时指定真实data文件和runtime31.json，并把输出写到新的目录；不要覆盖本轮历史证据。重复运行会受网络和地图服务当时状态影响，当前产品完整模型读取超时后需要刷新，尚无自动重试。

本轮首个检查器未拼上近景对象键的宏块前缀，因而没有正确找到已加载的目标分组；该次失败记录不作为验收。最终检查器按实际运行时键匹配，保留源、邻居、模型与释放断言及产品期限，并将31件独立运行时读取并行调度。南侧截图观察位按现有邻居轮廓、高度与模型射线检查调整，避免早期视点处于邻居建筑内；离开测试也改为实际越过产品现有保留距离的位置。相应离线控制、有限净空证明与真实浏览器接受分开记录。这里公开的是实际成功六图与目录单图运行记录所绑定的同一套工具；本轮未量化或宣称检查提速，生产运行时没有因此修改。

```sh
python tools/browser_acceptance.py --url http://127.0.0.1:8000/ --output /tmp/yangpu-new-check --expected-landmarks /path/to/shanghai/data/landmarks.json --expected-registry /path/to/shanghai/data/precise-buildings-v6.json --runtime-baseline runtime31.json --catalog-stage active
```

此命令需Python Playwright、Shapely和可用Chromium；必要时显式加`--use-env-proxy`。它重新检查当前实际服务，不会改变产品网络期限或生产运行时。原始检查绝不由源码语法检查替代。

''' 
    add(PUBLIC + '/README.md', content=audit_doc)
    readme = f'''# 上海漫游 · Shanghai Explorer v13

新增**杨浦区图书馆整馆**：旧馆与扩建翼部、两处内院、重檐琉璃瓦、斗拱彩画、石栏与真实门窗，已接入第三人称漫游。

[杨浦图书馆入口](index.html#landmark=yangpu-library&mode=walk) · [网页模型]({assets['web']['file']}) · [Blender]({assets['native']['file']}) · [模型与预览]({SOURCE}/CURRENT_STATE.md)

![杨浦图书馆模型预览]({SOURCE}/previews/east-full.png)

本版精选导航31项、普通精模12项、目录10个宏块；源替换17项，覆盖11个宏块和15个近景分块。全市16区底图保留，1,796,419个建筑及部件尚未逐栋完成照片复原。

原始GLB {sizes['raw']/1_000_000:.2f}MB、网页GLB {sizes['web']/1_000_000:.2f}MB、LOD {sizes['lod']/1_000_000:.2f}MB、Blender {sizes['native']/1_000_000:.2f}MB，均严格小于100,000,000字节。实际检查包括原始/压缩几何、重新打开Blender、完整/LOD/返回、源与近远景替换、9邻居、W行走及最终目录采用；6张静态图和1张目录图已实际查看。[检查范围]({PUBLIC}/README.md)

本轮31件生产运行时保持V12字节不变。模型没有照片纹理；背面和内院部分细节、尺寸和彩画仍是推估，非测绘或摄影测量。[来源与限制](data/bund/REALISM_V13.md) · [当前启动包状态](CURRENT_STATE.md)

使用时需要联网。完整模型读取超时后请刷新页面，当前没有自动重试。

## v12及更早记录（历史保留）

以下原文完整保留；其数量、链接、启动包及验证范围对应各自历史版本。

''' + (args.main / 'README.md').read_text()
    add('README.md', content=readme)
    # Check only the newly written prose; historical README link scopes remain historical.
    link_checks = []
    for document, content in ((SOURCE + '/CURRENT_STATE.md', model_doc),
                              ('data/bund/REALISM_V13.md', realism), (PUBLIC + '/README.md', audit_doc),
                              ('README.md', readme.split('## v12及更早记录（历史保留）', 1)[0])):
        for reference in re.findall(r'\]\(([^\s)]+)\)', content):
            parsed = urlsplit(reference)
            if parsed.scheme or parsed.netloc or not parsed.path:
                continue
            target = posixpath.normpath(posixpath.join(posixpath.dirname(document), unquote(parsed.path)))
            need(not target.startswith('../') and not target.startswith('/'), 'Public link escapes project')
            found = target in rows or (args.main / target).is_file()
            if parsed.path.endswith('/'):
                found = any(name.startswith(target.rstrip('/') + '/') for name in rows) or (args.main / target).is_dir()
            need(found, f'Broken new documentation link: {document} -> {reference}')
            link_checks.append({'document': document, 'reference': reference, 'target': target})
    (out / 'documentation-links.json').write_text(json.dumps({'passed': True, 'scope': 'New v13 prose only; excludes retained historical README sections.',
        'links': link_checks}, ensure_ascii=False, indent=2) + '\n')
    # Validate every source again after document composition; MAIN is still untouched.
    for item in rows.values():
        bound_file(item)
        need(item['bytes'] < LIMIT, 'Size limit exceeded after composition')
    final = {'schema': 'yangpu-v13-reviewed-app-release', 'utc': datetime.now(timezone.utc).isoformat(),
             'files': list(rows.values()), 'file_count': len(rows), 'total_bytes': sum(item['bytes'] for item in rows.values()),
             'max_file_bytes': max(item['bytes'] for item in rows.values()), 'accepted_plan': descriptor(args.accepted_plan),
             'catalog_browser': descriptor(args.catalog_browser), 'catalog_visual': descriptor(args.catalog_visual),
             'independent_native_review': descriptor(args.independent_native_review), 'main_written': False,
             'data_contract_check': descriptor(contract_path),
             'new_documentation_links': descriptor(out / 'documentation-links.json'),
             'runtime_changed': False, 'catalog_static_adoption_passed': True, 'catalog_dynamic_lifecycle_claimed': False,
             'added_files': added, **expected_counts}
    (out / 'installation-plan.json').write_text(json.dumps(final, ensure_ascii=False, indent=2) + '\n')
    publish = {'files': [{'path': 'projects/shanghai/' + item['file'], 'source': item['source'],
                          'bytes': item['bytes'], 'sha256': item['sha256']} for item in rows.values()]}
    (out / 'publish-manifest.json').write_text(json.dumps(publish, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'plan': descriptor(out / 'installation-plan.json'), 'publish': descriptor(out / 'publish-manifest.json'),
                      'files': final['file_count'], 'bytes': final['total_bytes'], 'largest_file': final['max_file_bytes']}, indent=2))


if __name__ == '__main__':
    main()
