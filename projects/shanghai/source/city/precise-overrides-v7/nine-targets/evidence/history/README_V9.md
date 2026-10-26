# 九目标替换候选：再加入武康路210号

`nine-targets/` 在已审八目标候选基础上只新增武康路210号源对象。原六个near逐字节复用；本轮只生成和逐三角核验210号所在的24要素near。`complete:true`仅表示源基线的精确拆组及几何证明成立，不能当作210/茶楼精模或浏览器验收。

Registry SHA256：`94bc1152c40287e97578ee0677fe987d50c76648a98fb6b5bdda88348435262d`。

| 项目 | 当前候选 |
|---|---|
| 宏 / near | 3 / 7 |
| 完整源目标 | 9 |
| 保留邻楼 | 116 |
| 展开三角形 | 689,176 |
| gzip合计 | 647,215B |
| 本次新增near | `14-13718-6695/1_0-s1-s1.glb.gz`，121,154B |
| 新增near解压 | 472,348B，117,000三角形 |

武康210源输入SHA为 `d34d51ed9be1f28beefe05e4076d892851bd7dacf13843d5d088148e5f204eca`，UUID `239ee254-3511-4df1-83c3-64d09e707e35`、local563。该near中其他23个要素都保留，包含相邻OSM982对应的local235；其他near的local999没有成为替换目标。210与129属于同宏、不同near，各自保留独立精确owner。

新near SHA256为 `4cdb05627091cdb9dbdc96046cd6718a860fcd32e968bfa1690c84f9f53f4cbc`。实际生产Three/Meshopt解码检查位置Float64、材料、绕序、重数、目标组和23邻楼，缺失/额外三角为0。法线有2,214个三角的逐位差异；最大分量差1.53847e-8、方向差9.49276e-7度，符合原1e-7/1e-5度阈值。对210目标组实际法线分量加0.01的负控被拒绝；不声称法线字节相同。

完整九目标的运行时检查重新实际解码3个far宏共9,309个要素及7个near，逐目标、全部目标、全部隐藏、near卸载和destroy都通过。对应报告为 `nine-targets/runtime-owner-validation.json`，SHA `7a22d928b695b5f5a25ac7c49c9eebd6d00118656a4b711b5f47345cb6c9a910`。

旧六块的几何证据复用与字节核验、新210逐三角核验、完整九目标运行时核验在报告中分别说明。没有重解码全城、没有重建旧六块、没有改主项目/候选应用/原129浏览器输入，也没有运行浏览器或Blender。所有文件严格小于100,000,000B。

## 复现

按 [README.md](README.md) 的原生成器流程，将ID换成 `xuhui-wukang-210`、输出使用全新目录，asset-prefix设为 `assets/city-overrides-v6/14-13718-6695`；比较输入的负控目标显式设为210，先通过 `verify_override_geometry.mjs`。

```bash
python compose_incremental.py --project /workspace/shanghai_project \
  --prior-root eight-targets --fresh-root FRESH_NEW_A \
  --inputs inputs --output FRESH_NINE
node tools/verify_override_runtime.mjs /workspace/shanghai_project FRESH_NINE/precise-buildings-v6.json
```

输出仍不挂 `ordinary_catalog`。最终青浦宏目录须包含222及已验收茶楼，徐汇宏目录须包含129及已验收210；应连同完整宏replacement重新签署。待验模型不能混进accepted index，旧单栋macro也不能覆盖本候选的完整宏。实际目录加载/卸载/返回仍由root另行验收。
