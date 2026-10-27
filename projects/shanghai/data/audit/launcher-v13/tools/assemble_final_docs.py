#!/usr/bin/env python3
"""Assemble final launcher docs/atomic installation plan only from actual proof.

No production writes, Git operations, network calls or browser launches.
Requires the release owner's actual app commit and root's actual image review.
"""
from __future__ import annotations
import argparse,hashlib,json
from pathlib import Path

def sha(path):
 with path.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def read(path):return json.loads(path.read_text())
def meta(path):return {'bytes':path.stat().st_size,'sha256':sha(path)}
def ensure(value,message):
 if not value:raise ValueError(message)

def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--project',type=Path,required=True);p.add_argument('--app-commit',required=True)
 p.add_argument('--archive',type=Path,required=True);p.add_argument('--archive-check',type=Path,required=True)
 p.add_argument('--runtime-check',type=Path,required=True);p.add_argument('--extraction',type=Path,required=True)
 p.add_argument('--smoke',type=Path,required=True);p.add_argument('--visual',type=Path,required=True)
 p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 ensure(not a.output.exists(),'Use a new output directory; preserve prior drafts')
 archive=read(a.archive_check);runtime=read(a.runtime_check);extract=read(a.extraction);smoke=read(a.smoke);visual=read(a.visual)
 ensure(archive.get('passed') and archive.get('publishable') and not archive.get('candidate_only'),'Archive validation incomplete')
 ensure(archive['expected_commit']==archive['manifest_commit']==runtime['expected_commit']==extract['commit']==a.app_commit,'Commit binding differs')
 arcmeta=meta(a.archive)
 ensure(arcmeta['bytes']<100_000_000 and arcmeta=={'bytes':archive['archive_bytes'],'sha256':archive['archive_sha256']},'Archive actual bytes differ')
 ensure(runtime.get('passed') and runtime['archive_sha256']==arcmeta['sha256'] and runtime['runtime_file_count']==31 and runtime['target_id']=='yangpu-library','Actual archive/runtime proof incomplete')
 for entry in runtime['runtime_files']:
  ensure(meta(a.project/entry['file'])=={k:entry[k] for k in ('bytes','sha256')},'Installed runtime changed after archive proof: '+entry['file'])
 ensure(extract['archive_sha256']==arcmeta['sha256'] and extract['main_fallback'] is False and extract['serves_only_archive_members'] is True,'Extraction must use only actual ZIP bytes')
 ensure(smoke.get('passed') and smoke.get('technical_passed') and smoke.get('run_scope')=='catalog-only' and smoke.get('finished_at'),'Actual single-target smoke incomplete')
 ensure(smoke['building_id']=='yangpu-library' and smoke['checks']['full_loaded'] and smoke['checks']['catalog_static_adoption'] and smoke['checks']['source_owner'] and smoke['checks']['runtime_unchanged'],'Smoke target/scope differs')
 ensure(visual.get('passed') and visual.get('reviewer')=='root' and visual.get('building_id')=='yangpu-library' and visual.get('browser_sha256')==sha(a.smoke),'Actual root visual review not bound')
 captures=smoke['captures'];ensure(len(captures)==1 and captures[0]['screenshot_complete'],'Exactly one actual startup capture required')
 image=a.smoke.parent/captures[0]['screenshot']['file'];imagemeta=meta(image)
 ensure(imagemeta=={k:captures[0]['screenshot'][k] for k in ('bytes','sha256')},'Actual screenshot bytes differ')
 viewed=visual.get('actually_viewed',[])
 ensure(any(r.get('file')==image.name and r.get('actually_viewed') is True and all(r.get(k)==v for k,v in imagemeta.items()) for r in viewed),'Root did not record actually viewing this screenshot')
 nav=read(a.project/'data/landmarks.json');registry=read(a.project/'data/precise-buildings-v6.json')
 target=next(r for r in nav if r['id']=='yangpu-library');catalog=read(a.project/registry['ordinary_catalog']['file'])
 counts={'navigation':len(nav),'owners':len(registry['landmarks']),'owner_macros':len(registry['macros']),
  'near_chunks':sum(len(m['near']) for m in registry['macros']),'ordinary_records':catalog['record_count'],'catalog_macros':catalog['macro_count']}
 ensure(counts=={'navigation':31,'owners':17,'owner_macros':11,'near_chunks':15,'ordinary_records':12,'catalog_macros':10},'Installed final counts differ')
 ensure(target['accepted'] is True and not target.get('candidate_only') and target['pending_stages']==[],'Installed target is not accepted')
 ensure(smoke['web_sha256']==target['web_sha256'] and smoke['lod_sha256']==target['lod_sha256'],'Smoke model binding differs')
 ensure(archive['landmarks']==31 and archive['bundled_landmarks']==14 and archive['streamed_landmarks']==17,'Archive navigation counts differ')
 sizes={r:target['assets'][r]['bytes'] for r in ('raw','web','lod','native')}
 for role,entry in target['assets'].items():ensure(meta(a.project/entry['file'])=={'bytes':entry['bytes'],'sha256':entry['sha256']} and entry['bytes']<100_000_000,'Installed asset changed: '+role)
 a.output.mkdir(parents=True);payload=a.output/'payload';payload.mkdir();files=[]
 def add(relative,source):
  before=a.project/relative
  files.append({'file':relative,'source':str(source.resolve()),**meta(source),'old_main':meta(before) if before.is_file() else None})
 def document(relative,text):
  path=payload/relative;path.parent.mkdir(parents=True,exist_ok=True);path.write_text(text,encoding='utf8');add(relative,path)
 source='source/precise/yangpu-library/CURRENT_STATE.md'
 audit='data/audit/launcher-v13/README.md'
 archive_size=f'{arcmeta["bytes"]:,}'
 build_count=archive['zip_crc_streams_verified'];expanded_count=extract['extracted_count']
 image_scope='从实际 ZIP 按请求解压的目录启动，加载固定提交上的杨浦图书馆完整模型，核对 1 张截图；同时检查目录采用、源建筑替换及同块邻居。'
 limitations='未进行现场测绘或摄影测量。西侧、北侧和内院部分窗跨、局部尺寸及饰纹按有限资料推估；屋脊总高不等同于审批图中的 18.49m 檐口高度。'
 document('CURRENT_STATE.md',f'''# 当前状态 · v13

本轮新增杨浦区图书馆整馆模型，覆盖历史旧体、扩建长翼、现代角部和两处内院。已接入上海第三人称漫游，应用提交 `{a.app_commit}`。[模型、预览与来源]({source})。

当前精选导航 31 项、普通精模 12 栋、目录 10 个宏块；源建筑替换登记 17 项，涉及 11 个宏块和 15 个近景分块。保留全市 16 区地图；1,796,419 个建筑及部件要素尚未全部完成逐栋照片复原。

本栋四件模型：原始 GLB {sizes['raw']:,} 字节、网页 GLB {sizes['web']:,} 字节、远景 GLB {sizes['lod']:,} 字节、Blender {sizes['native']:,} 字节，均严格低于 100,000,000 字节。31 件运行时文件保持 V12 字节；近景、LOD、返回和真实 W 行走的[网页验收范围](data/audit/precise-buildings-v13/yangpu-library/README.md)单独记录。

启动包 {archive_size} 字节，SHA256 `{arcmeta['sha256']}`；14 项本地模型、17 项联网模型，固定到上述应用提交。{build_count} 件归档成员通过完整 CRC/SHA 校验；冒烟过程中实际按请求解压 {expanded_count} 件文件并逐件核对 SHA。{image_scope} [下载](downloads/shanghai-web-launcher.zip) · [实际启动包验证范围]({audit})。

{limitations} 软件渲染截图不代表用户设备帧率。本轮只新增这一栋整馆，并非全市逐栋精细建模全部完成。

使用时需要联网。若完整模型读取超时，请刷新页面重新加载；当前没有自动重试。
''')
 document('downloads/README.md',f'''# 上海漫游启动包 · v13

[下载 shanghai-web-launcher.zip](shanghai-web-launcher.zip) · {archive_size} 字节，严格低于 100,000,000 字节。

SHA256：`{arcmeta['sha256']}`

完整解压，进入 `shanghai` 目录运行 `python -m http.server 8000`（macOS/Linux 可用 `python3`），然后访问 <http://localhost:8000/#landmark=yangpu-library&mode=walk>。请通过 HTTP 启动，不能直接双击 `index.html`。

本版导航 31 项，包含 14 项本地模型、17 项联网模型；新增杨浦区图书馆整馆。网页及联网资源固定到提交 `{a.app_commit}`。需要联网获取地图、城市分块和新增建筑；原始 GLB 与 Blender 文件在[项目模型目录](../source/precise/yangpu-library/CURRENT_STATE.md)，未打入启动包。

WASD/方向键行走，Shift 加速，拖动转向，滚轮调镜头；手机使用摇杆。若完整模型读取超时，请刷新页面重新加载，目前没有自动重试。

实际检查：{build_count} 件归档成员完整 CRC/SHA 校验通过；31 件运行时与 MAIN、V13 冻结基线一致。{image_scope}不据此声称包内所有地标、LOD、全城或硬件帧率已经重新验证。详见[归档与启动记录](../{audit})。

{limitations} 全市底图仍含大量基于公开轮廓和高度推定的建筑。本包不是离线地图或测绘成果。
''')
 public='data/audit/launcher-v13/'
 document(public+'README.md',f'''# V13 启动包实际验证

应用提交 `{a.app_commit}`；ZIP {archive_size} 字节，SHA256 `{arcmeta['sha256']}`。

- [archive-check.json](archive-check.json)：实际读取 {build_count} 件成员，检查 CRC、清单 SHA、路径、固定提交链接和 31/14/17 导航数量。未进行联网下载或浏览器验证。
- [runtime-target-check.json](runtime-target-check.json)：实际 ZIP 的 31 件运行时与 MAIN、冻结基线逐字节一致；杨浦图书馆四件本地资产与归档指向一致。
- [extraction.json](extraction.json)：只从该 ZIP 按浏览器请求实际解压 {expanded_count} 件文件、{extract['extracted_bytes']:,} 字节，逐件 SHA 验证；无 MAIN 回退。没有声称全部成员落盘。
- [smoke/browser.json](smoke/browser.json)：固定提交上的新目标完整模型实际加载，单次 full 视图、静态目录采用、源/near/far owner、邻居、实际资产与运行时核验。没有重新执行 LOD/W 或动态目录生命周期。
- [smoke/root-visual-review.json](smoke/root-visual-review.json)：root 实际看过[本次截图](smoke/{image.name})，绑定浏览器报告和图像 SHA。

{image_scope} 此处只记录一个新目标的启动冒烟，软件渲染不代表硬件 FPS。{limitations} 需要联网；读取超时仍需刷新。
''')
 for rel,source_path in [('downloads/shanghai-web-launcher.zip',a.archive),(public+'archive-check.json',a.archive_check),(public+'runtime-target-check.json',a.runtime_check),(public+'extraction.json',a.extraction),(public+'smoke/browser.json',a.smoke),(public+'smoke/root-visual-review.json',a.visual),(public+'smoke/'+image.name,image)]:add(rel,source_path)
 for tool in ('serve_verified_archive.py','check_runtime_target.py','assemble_final_docs.py'):
  add(public+'tools/'+tool,Path(__file__).parent/tool)
 for row in files:ensure(row['bytes']<100_000_000,'File ceiling exceeded')
 plan={'schema':'yangpu-launcher-final-docs-v13','app_commit':a.app_commit,'counts':counts,'files':files,
       'scope':'Actual ZIP, exact runtime/target/archive proofs, request-only extraction and one root-viewed target smoke; atomic root installation only.'}
 (a.output/'installation-plan.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps({'plan':str(a.output/'installation-plan.json'),'file_count':len(files),'bytes':sum(r['bytes'] for r in files),'archive':arcmeta,'counts':counts},indent=2))

if __name__=='__main__':main()
