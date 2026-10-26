# Pao Yue-Kong Library / 包玉刚图书馆

独立的2021重开外观模型源。使用源主馆201的身份/尺度约束，不替换东侧信息楼375或其他邻居。层高、窗口数量、曲面及屋顶细部均为有界重建估计；整体顶高27.4m不是实测。

Python3 + numpy + Shapely2.1。Blender4.x仅用于导入同一raw及保存/渲染，不负责重建不同几何。每次运行使用全新输出目录，保留旧输出、失败报告与原生视阅记录。

```sh
python build_model.py --out ../../pao-yue-kong-library-run-geometry-v2/raw
python build_model.py --lod --out ../../pao-yue-kong-library-run-geometry-v2/authored-lod
blender -b -t 2 --python render_previews.py -- --glb ../../pao-yue-kong-library-run-geometry-v2/raw/minhang-baoyugang-library.glb --output ../../pao-yue-kong-library-run-geometry-v2/native --samples 24 --threads 2
```

作者仅准备源码及小规模CPU构件检查；完整raw、native与浏览器验收由协调者执行后另附真实证据，不从这份README推定通过。导出器验证source-freeze.json所有条目与SHA，禁止覆盖已有raw。raw预算45MB、native预算30MB；用户硬限制单个文件严格小于100MB。最终web包需独立验证实际解码，不能直接以源代码估计作为通过。

输出包括：

- `.glb`：封闭分件、ENU→glTF east/up/−north；材料primitive的`extras.semanticParts`带`label/firstIndex/indexCount`。
- `.geometry.json`：实际文件bytes/SHA、三角数、bounds与构造顺序part_summary。
- `.roles.json`：绑定raw的逐件标签/材料/ENU范围、设计开口和接触记录；设计记录不等于独立实际几何审计。
- `native-render-report.json`：实际raw/native/三张图SHA、相机和渲染环境；默认human/browser通过标记false。

`--lod`仅省去重复面砖细缝；所有层轮廓、真实窗洞、门廊、退台、柱、弧形玻璃顶、开放格栅棚、窗框/深侧壁和栏杆保留。不得用统一全模型简化破坏这些构件。

源码中2021六张参考仅存URL/版权/哈希和独立文字观察，不存图片或纹理。两张CC历史原照保留原字节并明确早于2021；见ATTRIBUTION.md。完整私有研究快照和既有概念审阅不属于公开源码白名单。

## geometry-v2 接合修订源码

原21文件冻结源和原始raw/native均保留。此目录修复实际检查发现的常规窗框周边18毫米空气隙，以及格栅棚两端肋与纵梁之间的17.5毫米间隙。常规框外周向洞口外围嵌入20毫米，内孔/玻璃不改；两纵梁端各延长100毫米，所有肋与立柱保留。14斜窗及14棚柱的原几何保留。最终必须以新raw的独立实际检查确认，草稿本身不构成验收。

额外有界修复：v1三视图中六根F5廊柱顶与F6铺面共面，实际Float32高程均20.979999542236328米，造成规则深色圆斑。仅将这六柱顶部降至20.70米，在结构板底20.65米内保留50毫米嵌入；柱底/截面/位置、铺面及14棚柱原样。总允许265件改变，另2988件必须实际逐件一致。新raw仍需柱顶净距和正体积接触审核。
