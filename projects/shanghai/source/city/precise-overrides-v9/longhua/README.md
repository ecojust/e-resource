# 龙华塔：原建筑精确替换准备

本目录仅完成原城市建筑的身份、轮廓、替换分组和观景候选准备，没有安装到主项目，没有生成龙华塔精模，也没有浏览器或建筑外观验收。

唯一模型输入是 `inputs/xuhui-longhua-pagoda/geometry-input.json`，SHA256 `4f9a76d03074049132d50a856bdb892e7f8e76bc3e9172e57dff7d3bacb5e47a`。原8角闭环坐标、绕序、全部边及研究锚点 `[121.4473461596329,31.175617219399008]` 保持不变。锚点是原WGS84坐标多边形的平面质心，属于坐标原点，并非测绘点。OSM为 way47011877@11，源UUID为 `66c3a80d-8e53-4603-8a2e-3579a0caa485`。实时OSM与冻结数据的小差异保留在来源证据，不据此重画源轮廓。

替换只涉及 `14-13719-6697` / local702 / near `14-13719-6697--3_-1-s1`。13个邻居ID为1070、1476、352、1242、1077、1258、1259、511、918、1466、23、354、1221。没有范围删除、邻楼合并、庭院填平或新增源parts；所有相关数据保持原城市基线。

`eleven-targets/precise-buildings-v6.json` 是完整的候选owner registry：11目标、5宏、9near、150个源feature，其中139个邻居保持。新增variant只有78,877B；其14个feature共69,564展开三角，目标组4,336三角。当前MAIN的原8variant完全复用，原10个目标和4宏记录逐值相同。现有24导航与W/Q/H三宏5条accepted目录没有改写，Longhua尚不在任何accepted目录中。

实际vendored Three GLTFLoader/Meshopt解码证明新variant与原near逐面位置Float64、材质、绕序相同，13邻居与目标组各自完整。3,330个三角的法线有浮点位差，最大分量差1.3076074e-8，最大方向差8.0018312e-7度，低于既有1e-7/1e-5度门槛；报告没有将法线称为逐位相同。实际解码法线加0.01的负控被拒绝。随后以真实far及全部9variant运行11目标独立/全/空owner、near退出、恢复和destroy检查，均通过。以上只说明替换几何/生命周期，不代表精模外观已通过。

观景候选见 `navigation-candidates/`。入口门相位没有地理校准，不能称塔门或寺院入口。原CNBH12.2m只是旧城市高度估计，不作为新塔高度。官方40.64m总高和32.3m主体名义值由建模资料单独说明，不冒充测绘。本轮不改寺院、围墙、植被或道路。

## 重建和核验

已有工具仅复制到本隔离目录；原V8和MAIN源码未改。`gltfpack` 使用现有npm1.3.0。以下输出路径必须是新的隔离目录：

```sh
STAGE=/workspace/shanghai_expansion/building-by-building-v9/longhua-integration
PROJECT=/workspace/shanghai_project
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python "$STAGE/tools/build_precise_overrides.py" \
  --project "$PROJECT" --output /tmp/longhua-fresh-NEW \
  --geometry-input-root "$STAGE/inputs" --ids xuhui-longhua-pagoda \
  --asset-prefix assets/city-overrides-v6/14-13719-6697 \
  --gltfpack /workspace/shanghai_tools/node_modules/.bin/gltfpack
node "$STAGE/tools/verify_override_geometry.mjs" /tmp/longhua-fresh-NEW/geometry-comparison-input.json
python "$STAGE/compose_incremental.py" --project "$PROJECT" \
  --prior-root /workspace/shanghai_expansion/building-by-building-v8/integration-hongde/ten-targets \
  --fresh-root /tmp/longhua-fresh-NEW --inputs "$STAGE/inputs" --output "$STAGE/eleven-targets-NEW"
node "$STAGE/tools/verify_override_runtime.mjs" "$PROJECT" "$STAGE/eleven-targets-NEW/precise-buildings-v6.json"
```

完整几何核验生成用的中间逐feature参考位于相邻 `longhua-owner-work/`，不进入小型交付。工具可从冻结城市输入重建这些参考。组合报告准确区分：新near实际本轮解码，旧8near以此前实际解码报告和当前源/资产SHA复用；runtime检查本轮解码了全部far/variant。

`source-delivery/install-manifest.json` 仅提议新variant和显式来源证据白名单，没有安装能力，也不包括精模或新导航。最终模型就绪后用相邻 `integration-longhua-app/` 接入入口构成独立candidate25，保留现有catalog；实际单楼网页通过后再建立新宏目录。不得把owner report的passed当作模型/网页/目录通过。
