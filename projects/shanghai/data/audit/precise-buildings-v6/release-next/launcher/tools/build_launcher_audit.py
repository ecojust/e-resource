#!/usr/bin/env python3
"""Stage byte-exact public launcher audit evidence after actual browser + root visual PASS.
Never launches a browser, alters the application, applies to main, or uploads.
"""
from __future__ import annotations
import argparse,datetime,hashlib,json,os,re,stat,struct,zipfile
from pathlib import Path
from urllib.parse import unquote
LIMIT=100_000_000
TARGET=Path('data/audit/precise-buildings-v6/release-next/launcher')
PHASES=('static_adoption','dynamic_only','dynamic_hash_failure')
IMAGES=('static-catalog-loaded.png','static-catalog-returned.png','dynamic-catalog-loaded.png','dynamic-catalog-returned.png','dynamic-index-hash-rejected-baseline-visible.png')
PROXY_FILES=('browser-catalog.py','catalog-base-probe.js','catalog-extension-probe.js','proxy-only.patch','source-comparison.json','api-preflight.json','proxy-configuration-tests.json','check_proxy_catalog.py','README.md')
class EvidenceError(ValueError):pass
def require(value,message):
 if not value:raise EvidenceError(message)
def digest(data):return hashlib.sha256(data).hexdigest()
def encode(value):return (json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode()
def read(path):
 path=Path(path);before=path.lstat()
 require(stat.S_ISREG(before.st_mode) and not path.is_symlink(),'Expected regular evidence file: '+str(path))
 require(0<before.st_size<LIMIT,'Evidence file is empty or exceeds single-file limit: '+str(path))
 data=path.read_bytes();after=path.stat()
 require((before.st_dev,before.st_ino,before.st_size,before.st_mtime_ns,before.st_ctime_ns)==(after.st_dev,after.st_ino,after.st_size,after.st_mtime_ns,after.st_ctime_ns),'Evidence changed while reading: '+str(path))
 return data
def hash_file(path):
 before=path.lstat();require(stat.S_ISREG(before.st_mode) and 0<before.st_size<LIMIT,'Unsafe/oversize ZIP')
 h=hashlib.sha256()
 with path.open('rb') as f:
  for data in iter(lambda:f.read(1024*1024),b''):h.update(data)
 after=path.stat();require((before.st_ino,before.st_size,before.st_mtime_ns,before.st_ctime_ns)==(after.st_ino,after.st_size,after.st_mtime_ns,after.st_ctime_ns),'ZIP changed while hashing')
 return {'bytes':before.st_size,'sha256':h.hexdigest()}
def parse(data):return json.loads(data)
def check_terminal(browser,visual,archive,browser_sha):
 require(browser.get('schema')=='ordinary-catalog-browser-v1' and browser.get('passed') is True and browser.get('technical_passed') is True and browser.get('finished_utc'),'Actual browser has not completed successfully')
 require(not browser.get('page_errors') and not browser.get('shader_errors'),'Actual browser has page/shader errors')
 phases=browser.get('phases',[])
 require([x.get('name') for x in phases]==list(PHASES) and all(x.get('passed') is True for x in phases),'Actual three-phase evidence incomplete')
 require([x.get('static_navigation_count') for x in phases]==[20,19,19],'Unexpected actual static/dynamic navigation counts')
 require(phases[0].get('single_record_reused') and phases[0].get('warm_reset_same_object_no_new_model_request') and phases[0].get('unload_static_record_retained') and phases[0].get('neighbors')==27,'Static reuse evidence incomplete')
 dynamic=phases[1];resource=dynamic.get('geometry_disposal',{})
 require(dynamic.get('record_removed_on_unload') and dynamic.get('returned_new_object') and dynamic.get('neighbors')==27 and resource.get('detached') and resource.get('geometryCount',0)>0 and resource.get('geometriesDisposed')==resource.get('geometryCount'),'Dynamic unload/return evidence incomplete')
 rejected=phases[2]
 require(rejected.get('precise_model_requests')==0 and rejected.get('no_new_records_or_registry') and len(set(rejected.get('baseline_complete_owner_ids',[])))==28 and rejected.get('neighbor_count')==27,'Hash failure does not preserve the complete baseline')
 require(visual.get('passed') is True and visual.get('final') is True and visual.get('reviewer')=='root','Independent root visual review is absent or failed')
 require(visual.get('browser_report_sha256')==browser_sha,'Root visual review binds a different browser report')
 require(visual.get('archive_sha256')==archive['archive_sha256'] and visual.get('app_commit')==archive['expected_commit'],'Root visual review must bind the actual ZIP SHA and application commit')
 viewed=visual.get('actually_viewed',[])
 require(len(viewed)==5 and {r.get('file') for r in viewed}==set(IMAGES) and all(r.get('actually_viewed') is True for r in viewed),'Root must actually view the five loaded/returned/fallback PNGs')
 return {row['file']:row for row in viewed}
def collect(release,public_verification):
 blobs={};sources={}
 def add(rel,path):
  require(rel not in blobs,'Duplicate audit destination')
  data=read(path);blobs[rel]=data;sources[rel]=Path(path);return parse(data) if rel.endswith('.json') else data
 archive=add('archive-check.json',release/'archive-check.json')
 require(archive.get('passed') is True and archive.get('publishable') is True and not archive.get('candidate_only') and archive.get('landmarks')==20,'Production archive checker did not pass')
 commit=archive.get('expected_commit','');require(re.fullmatch('[a-f0-9]{40}',commit) and commit==archive.get('manifest_commit'),'Invalid application commit binding')
 actual_archive=hash_file(release/'shanghai-web-launcher.zip')
 require(actual_archive=={'bytes':archive.get('archive_bytes'),'sha256':archive.get('archive_sha256')},'Actual ZIP bytes/SHA differ from the independent archive check')
 browser=add('browser/browser.json',release/'browser-catalog-proxy/browser.json')
 visual=add('browser/visual-review.json',release/'browser-catalog-proxy/visual-review.json')
 viewed=check_terminal(browser,visual,archive,digest(blobs['browser/browser.json']))
 public=add('app-next-public-verification.json',public_verification)
 require(public.get('passed') is True and public.get('commit')==commit and public.get('files') and all(x.get('passed') is True and x.get('http_status')==200 for x in public['files']),'Published application verification is incomplete or another commit')
 require(public.get('preview_html',{}).get('passed') is True,'Published preview HTML was not verified')
 root=f'https://rawcdn.githack.com/ecojust/e-resource/{commit}/projects/shanghai/'
 meta=browser.get('metadata',{})
 with zipfile.ZipFile(release/'shanghai-web-launcher.zip') as z:
  for label,path in [('registry','data/precise-buildings-v6.json'),('navigation','data/landmarks.json')]:
   data=z.read('shanghai/'+path);ref=meta.get(label,{})
   require(ref.get('sha256')==digest(data) and ref.get('bytes')==len(data) and ref.get('url')==browser['url']+path,'Browser did not read this extracted ZIP metadata: '+label)
  for label in ('catalog','index','replacement'):
   ref=meta.get(label,{});url=ref.get('url','');require(url.startswith(root),'Remote catalog chain is not pinned to the application commit')
   name=unquote(url[len(root):]);require(name.startswith('data/precise-buildings/') and '..' not in Path(name).parts,'Unexpected remote catalog path')
   data=z.read('shanghai/'+name)
   require(ref.get('sha256')==digest(data) and ref.get('bytes')==len(data),'Actual remote JSON bytes differ from ZIP original audit copy: '+label)
  mask=next((r for r in public['files'] if r['path']=='src/city-feature-mask.js'),None)
  require(mask and digest(z.read('shanghai/src/city-feature-mask.js'))==mask['sha256'],'ZIP mask fix differs from the verified public application')
 for name in IMAGES:
  data=add('browser/'+name,release/'browser-catalog-proxy'/name);row=viewed[name]
  require(data[:8]==b'\x89PNG\r\n\x1a\n' and data[12:16]==b'IHDR','Screenshot is not a PNG: '+name)
  width,height=struct.unpack('>II',data[16:24]);require(width>0 and height>0,'PNG has no image dimensions')
  require(row.get('bytes')==len(data) and row.get('sha256')==digest(data),'Root viewed a different screenshot: '+name)
  require(any(c.get('image')==name and c.get('name')==name[:-4] for c in browser.get('captures',[])),'PNG is not an actual browser capture')
 add('browser/run.txt',release/'browser-catalog-proxy-run.txt')
 for name in PROXY_FILES:add('proxy-qa/'+name,release/'proxy-qa'/name)
 comparison=parse(blobs['proxy-qa/source-comparison.json'])
 for row in comparison['copies']:
  require(row['copy_sha256']==digest(blobs['proxy-qa/'+row['file']]),'Proxy source copy changed after review')
  if row['file'].endswith('.js'):require(row.get('byte_identical') and row['original_sha256']==row['copy_sha256'],'Proxy probe bytes were changed')
 require(comparison['patch_sha256']==digest(blobs['proxy-qa/proxy-only.patch']),'Proxy patch changed')
 for key,name in [('script_sha256','browser-catalog.py'),('probe_sha256','catalog-base-probe.js'),('extension_sha256','catalog-extension-probe.js')]:
  require(browser.get(key)==digest(blobs['proxy-qa/'+name]),'Actual browser used another script/probe: '+key)
 network=browser.get('network',{})
 require(network.get('enabled') and network.get('source_environment') in ('HTTPS_PROXY','HTTP_PROXY') and network.get('bypass')=='localhost,127.0.0.1' and network.get('remote_urls_or_bytes_rewritten') is False,'Actual run did not use the reviewed explicit environment proxy contract')
 require(not any(k in network for k in ('username','password','server','proxy_url')),'Public network report must not expose credential-bearing fields')
 preflight=parse(blobs['proxy-qa/api-preflight.json']);configuration=parse(blobs['proxy-qa/proxy-configuration-tests.json'])
 require(preflight.get('passed') is True and preflight.get('status')==200 and preflight.get('actual_sha256')==meta['catalog']['sha256'] and preflight.get('actual_bytes')==meta['catalog']['bytes'] and not preflight.get('browser_started'),'API-only real proxy preflight does not match actual catalog')
 require(configuration.get('passed') is True and len(configuration.get('tests',[]))==5 and all(t.get('passed') for t in configuration['tests']),'Proxy configuration negative checks missing')
 failed=add('environment-before-page/browser.json',release/'browser-catalog/browser.json')
 add('environment-before-page/run.txt',release/'browser-catalog-run.txt')
 require(failed.get('passed') is False and failed.get('finished_utc') and not failed.get('phases') and not failed.get('captures') and not any(r.get('label')=='PAGE BEGIN' for r in failed.get('events',[])),'Initial environment failure was not scoped before page loading')
 require('ENETUNREACH' in failed.get('error',{}).get('message',''),'Initial environment failure no longer matches the saved network diagnostic')
 # Exact original script is retained too, so the small proxy-only diff is independently reviewable.
 add('proxy-qa/original-browser-catalog.py',release.parent/'ordinary-launcher/browser-catalog.py')
 original=next(r for r in comparison['copies'] if r['file']=='browser-catalog.py')
 require(original['original_sha256']==digest(blobs['proxy-qa/original-browser-catalog.py']),'Original browser script differs from the proxy comparison')
 require(failed.get('script_sha256')==original['original_sha256'] and failed.get('url')==browser.get('url'),'Initial environment diagnostic was not produced by the preserved original script at this extracted launcher URL')
 add('tools/build_launcher_audit.py',Path(__file__).resolve())
 add('tools/test_build_launcher_audit.py',Path(__file__).with_name('test_build_launcher_audit.py'))
 add('tools/gate-tests.txt',Path(__file__).with_name('gate-tests.txt'))
 info={'application_commit':commit,'archive_bytes':actual_archive['bytes'],'archive_sha256':actual_archive['sha256'],
 'browser_report_sha256':digest(blobs['browser/browser.json']),'root_visual_sha256':digest(blobs['browser/visual-review.json']),
 'public_verification_sha256':digest(blobs['app-next-public-verification.json']),'actual_browser_network':network,
 'browser_phases':list(PHASES),'screenshot_count':5,'original_environment_failure_scope':'Metadata prefetch failed before any page was opened; retained as diagnostic, not an application visual failure.',
 'software_renderer':True,'hardware_fps_claim':False,'all_shanghai_individually_refined_claim':False}
 return blobs,sources,info
README='''# 真实启动包目录生命周期验收

此审计绑定应用提交 `{application_commit}`，ZIP `{archive_sha256}`（{archive_bytes}字节），实际浏览器报告 `{browser_report_sha256}` 及 root 逐图视觉报告 `{root_visual_sha256}`。`audit-manifest.json` 列出逐文件原字节SHA与来源；ZIP自身不在此处重复储存。

`archive-check.json` 为独立离线ZIP校验原文件：路径/CRC/包内字节SHA、20条导航、固定提交URL、原目录JSON哈希链均核对。`app-next-public-verification.json` 是同一提交的真实公开资源读取验证，不能把选定文件的核验等同于下载复查全部远程城市资产。

`browser/browser.json`、`browser/run.txt` 和同目录5张PNG来自真实解压网页；`browser/visual-review.json` 的相对图片路径保持有效。root实际查看静态加载/返回、纯目录加载/返回及坏索引回退5图。三阶段依次验证静态20条导航中复用222，临时响应注入移除静态222后由目录真实新增（19条静态导航）、卸载并释放几何、回来重新载入并保留27邻楼，以及等长破坏索引1字节后明确SHA拒绝、零精模请求、保留全部28普通楼owner。这些动态-only与坏索引状态是明确的QA响应注入，并非生产默认配置；原磁盘JSON/模型和固定提交远程字节未被改写。

`proxy-qa/` 保存实际测试脚本、原脚本、两份未修改probe、最小patch、来源比较、真实API预检、配置负控和使用说明。代理只让Playwright使用执行环境的HTTPS_PROXY/HTTP_PROXY，localhost/127.0.0.1直连；报告不含凭据。它不改ZIP、应用URL/模型，不mock远程成功。`environment-before-page/` 保留首次直连ENETUNREACH的原报告与完整日志，失败发生于元数据预取、尚未打开页面，不能当作页面视觉失败或悄悄删除。

软件GPU渲染用于有限场景实际验收，不能据此承诺用户设备FPS或内存性能。本次没有重新做07/09等前一轮15个建筑姿态采集，没有重查全部1708城市格，更不代表全上海179万建筑已经完成逐栋照片级复原。普通背景建筑与青浦道路/铺装/绿化仍含推定或缺失，精模侧后立面/雕饰仍有声明的简化。技术owner断言与root实际画面一起构成本次通过证据。

所有来源文件逐字节复制；本目录只包含证据，不改变模型、运行时或accepted目录。准备工具仅生成隔离payload和new-only安装计划，不写主项目、不上传。最终安装及发布由root单独执行。
'''
def build(release,public,project,output):
 require(not output.exists() and not output.is_symlink(),'Refuse to overwrite prepared output')
 require(not (project/TARGET).exists() and not (project/TARGET).is_symlink(),'Main audit destination already exists; new-only installation required')
 blobs,sources,info=collect(release,public)
 blobs['README.md']=README.format(**info).encode()
 inventory=[{'file':name,'bytes':len(data),'sha256':digest(data),'source':str(sources[name]) if name in sources else 'generated evidence scope README','byte_exact_source_copy':name in sources} for name,data in sorted(blobs.items())]
 manifest={'schema':'launcher-public-audit-inventory-v1','prepared_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'passed':True,'main_modified':False,'uploaded':False,'new_only_target':str(TARGET),'evidence':info,'files':inventory,'max_file_bytes':max(x['bytes'] for x in inventory),'inventory_excludes_self':True}
 blobs['audit-manifest.json']=encode(manifest)
 require(all(0<len(b)<LIMIT for b in blobs.values()),'Public evidence exceeds single-file limit')
 # A final source check prevents packaging a report/log modified after validation.
 for name,path in sources.items():require(read(path)==blobs[name],'Source changed before staging: '+name)
 output.mkdir(mode=0o700,parents=False)
 (output/'INCOMPLETE').write_text('Not installable until installation-plan.json is present.\n')
 payload=output/'payload'/TARGET
 for name,data in blobs.items():
  dest=payload/name;dest.parent.mkdir(parents=True,exist_ok=True)
  with dest.open('xb') as f:f.write(data)
  require(read(dest)==data,'Staged byte mismatch')
 files=[{'file':str(TARGET/name),'path':str(TARGET/name),'source':str(output/'payload'/TARGET/name),'bytes':len(data),'sha256':digest(data),'base_sha256':None,'new':True} for name,data in sorted(blobs.items())]
 plan={'schema':'launcher-public-audit-new-only-install-v1','prepared_utc':manifest['prepared_utc'],'passed':True,'applied':False,'uploaded':False,'project':str(project),'payload_root':str(output/'payload'),'new_only':True,'target_directory':str(TARGET),'evidence':info,'files':files,'file_count':len(files),'total_bytes':sum(x['bytes'] for x in files),'max_file_bytes':max(x['bytes'] for x in files),'audit_manifest_sha256':digest(blobs['audit-manifest.json'])}
 (output/'installation-plan.json').write_bytes(encode(plan));(output/'INCOMPLETE').unlink()
 return plan

def main():
 here=Path(__file__).resolve().parent;release=here.parent
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--release',type=Path,default=release);p.add_argument('--project',type=Path,default=Path('/workspace/shanghai_project'))
 p.add_argument('--public-verification',type=Path,default=release.parent.parent/'publish/app-next-public-verification.json')
 p.add_argument('--output',type=Path,default=here/'prepared')
 p.add_argument('--check-only',action='store_true',help='Validate terminal evidence without creating payload or installation plan')
 a=p.parse_args()
 try:
  if a.check_only:
   blobs,_,info=collect(a.release,a.public_verification);result={'passed':True,'check_only':True,'copied_files':len(blobs),'evidence':info}
  else:result=build(a.release,a.public_verification,a.project,a.output)
 except (OSError,ValueError,KeyError,TypeError,zipfile.BadZipFile) as error:
  print(json.dumps({'passed':False,'error':str(error),'main_modified':False,'uploaded':False},ensure_ascii=False));return 1
 print(json.dumps(result,ensure_ascii=False));return 0
if __name__=='__main__':raise SystemExit(main())
