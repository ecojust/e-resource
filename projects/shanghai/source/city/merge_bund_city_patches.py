"""Create an isolated merged city and optionally connect a non-repository preview.

Immutable untouched GLBs/ID files may use hard links. Metadata files are copied;
patched assets are unlinked before replacement so the original city stays intact.
"""
from pathlib import Path
import argparse,hashlib,json,os,shutil,sys
from build_bund_city_patches import write_json,sha


def write_current_docs(out,m):
    """Refresh copied reports from the actual manifest, retaining source caveats."""
    readme=out/'README.md';report=out/'BUILD_REPORT.md'
    if readme.exists():
        text=readme.read_text()
        if text.startswith('> 外滩细化更新：'):text=text.split('\n\n',1)[1]
        text=text.replace('1,796,435',f"{m['feature_count']:,}")
        text=text.replace('五个精细地标',f"{m['detailed_landmark_record_count']} 个精细地标")
        rows={d['name']:d for d in m['districts']}
        lines=[]
        for line in text.splitlines():
            cells=line.split('|')
            if len(cells)>3 and cells[1].strip() in rows:
                d=rows[cells[1].strip()];cells[2]=f" {d['features']:,} ";line='|'.join(cells)
            lines.append(line)
        readme.write_text('\n'.join(lines)+'\n')
    if report.exists():
        old=report.read_text();tail=old[old.index('高度优先级为'):]
        begin=tail.index('402 个残差父体');end=tail.index('\n\n完整审计',begin)
        tail=tail[:begin]+(
            f"当前 {m['residual_parent_features']} 个通用残差父体保留约{m['residual_parent_area_m2']:,.0f}m²面积。"
            "V2 基线为402个；本轮中国银行主楼残差已由其完整精细模型替代。"
            "原始残差处理剔除42个总残差≤1m²的父体残差，合计22.635866m²。"
            "V2网格审计中1mm点距/0.01m²退化环阈值另略去94个极小polygon片，共0.104702m²，"
            "未丢弃任何一个恢复父体；该数值是原始基线的几何机制审计，非本轮新测量。原始残差GeoJSON仍保留全部组件。"
        )+tail[end:]
        lines=[
            '# 上海 16 区建筑模型构建报告（外滩细化 V3）','',
            f"已完成 {m['model_count']:,} 个通用 GLB，共 {m['feature_count']:,} 个建筑或建筑部件，{m['triangle_count']:,} 个三角形。GLB 总大小 {m['total_model_bytes']:,} 字节；最大单文件 {m['max_file_bytes']:,} 字节，全部低于 100,000,000 字节。",'',
            f"范围是记录的上海16区显示边界内全部可取得的Overture源足迹，并非每栋实体建筑都已被来源测绘的保证。通用几何为真实地图轮廓的LoD1挤出；{m['detailed_landmark_record_count']}个精细地标单独加载，其中10栋为本轮外滩历史建筑。精细模型的屋顶、檐口、柱廊和窗洞另行建模；未有实测依据的尺寸仍注明估计。",'',
            f"计数对账：{m['source_renderable_count']:,} 个源可渲染要素 + {m['residual_parent_features']} 个父楼残差 − {m['landmark_replacement_count']} 个精细模型替代要素 = {m['feature_count']:,} 个通用模型要素。原始地上源共 {m['source_feature_count']:,} 个UUID；原始被部件替代的父楼 {m['nonrenderable_parent_count']} 个保留在源档案中。另有 {m['excluded_underground_count']} 个地下要素独立归档，不抬升为地上楼。",'',
            '| 区 | 模型要素 | 恢复父楼残差 | 地标替代 | 源高度 | 楼层估计 | CMAB估计 | CNBH10m估计 | GHSL估计 | 12m缺省 |',
            '|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
        keys=['features','residual_parent_features','landmark_replacement_count','source_height','floor_estimate','cmab_estimate_matched_rooftop','cnbh_estimate_10m','raster_estimate_2018','fallback_12m']
        for d in m['districts']:lines.append('| '+d['name']+' | '+' | '.join(str(d[k]) for k in keys)+' |')
        report.write_text('\n'.join(lines)+'\n\n'+tail)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for key in ('base-models','patch','output','raw','city-source-dir'):
        p.add_argument('--'+key,type=Path,required=True)
    p.add_argument('--working-project',type=Path)
    p.add_argument('--published-raw-path',default='data/fullcity-raw')
    a=p.parse_args();base=a.base_models.resolve();out=a.output.resolve()
    if out.is_relative_to(base) or base.is_relative_to(out):p.error('Merged directory must be independent of the original city tree')
    if out.exists() and any(out.iterdir()):p.error('Use a new empty merged output directory')
    patch=json.loads((a.patch/'patch-manifest.json').read_text());assert patch['complete']
    assert sha(base/'manifest.json')==patch['base_manifest_sha256']
    out.mkdir(parents=True,exist_ok=True)
    copied=0;linked=0
    for item in base.iterdir():
        if item.name.startswith('.') or item.name in ('COMPLETE','manifest.json'):continue
        target=out/item.name
        if item.is_dir():
            target.mkdir(exist_ok=True)
            for source in item.rglob('*'):
                dest=target/source.relative_to(item)
                if source.is_dir():dest.mkdir(exist_ok=True);continue
                dest.parent.mkdir(parents=True,exist_ok=True)
                if item.name in ('tiles','ids'):
                    try:os.link(source,dest);linked+=1
                    except OSError:shutil.copy2(source,dest);copied+=1
                else:shutil.copy2(source,dest);copied+=1
        else:shutil.copy2(item,target);copied+=1
    patch_ids={r['id'] for r in patch['records']}
    for cell in patch['affected_owner_cells']:
        for old_id in cell['superseded_output_ids']:
            if old_id in patch_ids:continue
            record=json.loads((out/'records'/(old_id+'.json')).read_text())
            for asset in (record['file'],record['feature_ids_file']):(out/asset).unlink(missing_ok=True)
            (out/'records'/(old_id+'.json')).unlink(missing_ok=True)
    replaced=[]
    for sub in ('tiles','ids','records','state'):
        for source in (a.patch/sub).glob('*'):
            if not source.is_file():continue
            dest=out/sub/source.name;dest.unlink(missing_ok=True);shutil.copy2(source,dest)
            replaced.append(str(dest.relative_to(out)))
    for filename in ('build-configuration.json','bund-landmark-exclusions.json','bund-landmark-exclusions.generation-snapshot.json','model-metadata-finalization.json','patch-manifest.json'):
        source=a.patch/filename
        if source.exists():shutil.copy2(source,out/('bund-patch-'+filename))
    sys.path.insert(0,str(a.city_source_dir.resolve()));import build_fullcity_models as builder
    m=builder.build_manifest(out,a.raw,True,[])
    assert m['complete'] and m['coverage_balanced'] and m['feature_count']==1796419
    m['source_raw_directory']=a.published_raw_path
    m['source_raw_directory_base']='project root'
    m['detailed_landmark_record_count']=14
    m['detail_patch']={'owner_cells':[c['tile'] for c in patch['affected_owner_cells']],
                       'runtime_exclusions_sha256':sha(a.patch/'bund-landmark-exclusions.json'),
                       'generation_exclusions_sha256':patch.get('generation_exclusions_sha256',patch['exclusions_sha256']),
                       'unrelated_owner_cell_state_hashes_preserved':True}
    write_json(out/'manifest.json',m)
    for district in m['districts']:
        did=district['id'];tiles=[t for t in m['tiles'] if did in t['district_counts']]
        index={'district_id':did,'district_name':district['name'],'model_features':district['features'],
               'scope':'Available source buildings assigned to this district after exact detailed-landmark replacements; boundary cells can include neighboring districts. Download shared tiles once.',
               'tiles':[{'id':t['id'],'file':'../'+t['file'],'feature_ids_file':'../'+t['feature_ids_file'],
                         'sha256':t['sha256'],'bytes':t['size_bytes'],'district_features':t['district_counts'][did]['features']} for t in tiles]}
        write_json(out/'districts'/(did+'.json'),index)
    # Metadata was copied, so report refresh cannot mutate the original city.
    write_current_docs(out,m)
    if a.working_project:
        working=a.working_project.resolve()
        if (working/'.git').exists():p.error('Working preview must not be a Git repository')
        link=working/'assets/city'
        if link.exists() and not link.is_symlink():p.error('Working assets/city must be an existing symlink, not an owned directory')
        temp=link.with_name('.city-next');temp.unlink(missing_ok=True);temp.symlink_to(out,target_is_directory=True);os.replace(temp,link)
        for name,target in [('bund-landmark-exclusions.json','landmark-exclusions.json'),('bund-landmark-exclusions.generation-snapshot.json','bund-landmark-exclusions.generation-snapshot.json')]:
            write_json(working/'data'/target,json.loads((a.patch/name).read_text()))
        district_path=working/'data/districts.json';data=json.loads(district_path.read_text());stats={d['id']:d for d in m['districts']}
        for d in data['districts']:
            d['modelStats']=stats[str(d['id'])]
            d['modelCollection']='assets/city/manifest.json';d['modelIndex']=f"assets/city/districts/{d['id']}.json"
        write_json(district_path,data)
    # Verify that the source base still has its original manifest and affected
    # asset bytes after hard-link creation and patch replacement.
    assert sha(base/'manifest.json')==patch['base_manifest_sha256']
    for cell in patch['affected_owner_cells']:
        for old_id in cell['superseded_output_ids']:
            record=json.loads((base/'records'/(old_id+'.json')).read_text())
            assert sha(base/record['file'])==record['sha256']
    report={'merged_directory':str(out),'model_count':m['model_count'],'feature_count':m['feature_count'],
            'linked_immutable_files':linked,'copied_metadata_files':copied,'replaced_files':replaced,
            'base_manifest_unchanged':True,'source_raw_directory':m['source_raw_directory'],
            'working_preview_connected':str(a.working_project) if a.working_project else None,
            'full_raw_audit_pending':True}
    write_json(out/'bund-patch-merge-report.json',report);print(json.dumps(report,ensure_ascii=False,indent=2))


if __name__=='__main__':main()
