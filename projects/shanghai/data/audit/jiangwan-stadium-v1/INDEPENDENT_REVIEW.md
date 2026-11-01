# 江湾体育场主场独立复核

正式结论见 [independent-review.json](independent-review.json)。本轮只核本栋和其原始城市源，未执行历史全资产矩阵。浏览器结果单列；独立审查没有启动浏览器。

实际读图包括六张参考照片、四张主场原设计图和七张最终 Blender PNG。直接解码交付 raw／web／LOD，各151条射线全过；raw与web逐材质、有方向的FLOAT32三角形完全一致。实际只读重开最终Blender后，374,908个模型三角形与raw一致，预览地面排除。

独立实际三角形投影发现旧西台前沿平台连接缺失，作者已补4.35—4.50米闭合连接板；新增20条平台及上梁上下表面探针三档全过。剩余西粗源约49.906平方米差异为北翼外角、场内立面外侧源边细条及小边缘差，明确保留估计边界，未称为已证实天井或100%足迹复刻。独立体育馆、游泳馆及未核细部继续保留。

三档精确裁剪z=0—2米实际三角形后另求地面占用；11个碰撞多边形、956个闭环点完整覆盖，未以显示遮罩填满地面。内场、两短端4.6米中央带以及2322个其他原始源均无冲突，实际相邻原生网格也保留。显示遮罩27／22点生成45个三角形，全局容量192；显示遮罩与碰撞分别验证。

## 重跑本栋几何与原生核对

在仓库根目录运行。需要Node、Python的numpy／shapely，以及Blender4.3.2；这些命令不启动浏览器，不修改资产。最终公开报告留存原实际执行路径，因此重新执行时报告文件自身的SHA可能不同；资产SHA、几何多重集及各断言应一致。

```bash
review_audit=projects/shanghai/data/audit/jiangwan-stadium-v1
review_assets=projects/shanghai/assets/models/candidates/yangpu-jiangwan-stadium
review_work=$(mktemp -d)
node "$review_audit/independent-geometry-check.mjs" "$review_assets" "$review_audit/independent-probes-platform-fix.json" "$review_work/independent-geometry-review.json" "$review_work/triangles"
python "$review_audit/independent-derive-occupancy.py" "$review_work/independent-geometry-review.json" "$review_work/triangles" "$review_work/independent-occupancy"
python "$review_audit/independent-bind-final-package.py" "$review_assets" "$review_work" "$review_work/independent-packaging-binding.json"
blender -b "$review_assets/yangpu-jiangwan-stadium.blend" -t 1 --python-exit-code 1 --python "$review_audit/independent-check-native.py" -- "$review_assets/yangpu-jiangwan-stadium-raw.glb" "$review_work/independent-native-review.json"
```

本次几何解码在原生渲染结束前从冻结三GLB记录启动，`independent-packaging-binding.json`在最终manifest就绪后实际读取四资产，逐一核对同一SHA、字节和面数。未将临时记录称为正式manifest。重新执行时工具可直接读取最终manifest。

## 重跑原城市源及地面合同核对

以下仅从指定基线Git对象提取五件原城市输入，不联网或分发参考照片／PDF。中间三角形与占用缓存均写入临时目录，正式报告记录其散列；无须将它们复制入库。

```bash
python "$review_audit/independent-prepare-city-input.py" "$PWD" "$review_work/city-input"
node "$review_audit/independent-city-source-check.mjs" "$review_work/city-input" "$review_work/city-triangles"
python "$review_audit/independent-check-original-city.py" "$review_work/city-input" "$review_work/city-triangles" "$review_work/independent-original-city-projection.json"
python -c 'import json,sys; from pathlib import Path; d=json.loads(Path(sys.argv[1]).read_text()); Path(sys.argv[2]).write_text(json.dumps(d["proposed_placement_contract"],indent=2)+"\n")' "$review_audit/footprint-review.json" "$review_work/placement-contract.json"
python "$review_audit/independent-check-placement.py" "$review_work" "$review_work/city-input" "$review_work/placement-contract.json" "$review_work/independent-placement-review.json"
```

当前米高、排数、隐藏上梁与未见立面均含估计；通过这些检查不代表室内可达、公开通行许可或1934年原状完整复原。原始照片、PDF以及本独审的初次冻结检查文件与中间缓存只留私有工作区。作者另行标记的原型过程图不作为最终图审证据。最终7张原生PNG逐一实看记录在 [independent-native-image-review.json](independent-native-image-review.json)，散列用于绑定，不替代看图。
