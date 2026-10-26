# 北大街222号：来源轮廓与单栋替换契约

`geometry-input.json` 冻结的是既有 Overture 源轮廓，SHA-256 为 `054a6b6fe54b6491c6137ad42612b70550d5955b242d1c562d19f87475e7cbce`。门牌、官方历史建筑条目、2016/2022 原照片及独立屋顶对应支持这一临街前楼的身份；地址 POI 只作身份线索，不用它重新居中或画一个矩形。

| 项目 | 冻结值 |
| --- | --- |
| 来源键 | `building:3fdcd081-70df-4c5d-a08c-2f553289c25b` |
| 城市宏块 | `14-13701-6700` |
| 1-based feature ID | `502` |
| 近景块 | `14-13701-6700--3_2-s1-s0` |
| 来源 | Overture 2026-10-21.0；Zenodo `east_asian_buildings` 2024-11-01 |
| 原始数据 DOI | `10.5281/zenodo.8174931` |
| 既有源轮廓 | 1 个 Polygon，顺时针原环，无内洞；105.213 m² |
| 临街边 | 原环 edge 3，vertex 3 → 0；约 11.980 m |
| 锚点 | `[121.05068296944307, 31.112922937883873]`，原轮廓墨卡托质心反投影 |

这是明确的非 OSM 建筑来源分支。未伪造 OSM way，也未将邻近 OSM 门牌 node 作为建筑轮廓。Overture 集合保留 ODbL-1.0 归属；底层 East Asian Buildings 数据为 Qian Shi 等的 CC BY 4.0。`evidence/zenodo-license-source.json` 记录官方 Zenodo API 返回的标题、作者、许可和响应 SHA；许可证据是冻结后的附加核验，不改变原几何文件。

坐标沿用既有源构建约定：R=6378137，Web Mercator 差乘锚点纬度余弦；本地 `[east,north]`，glTF `[east,height,-north]`。所有原顶点次序和地理坐标保持。原临街边切线为东北→西南，照片左→右为相反方向，故 `photographic_left_to_right_native_u_sign=-1`。建模器可仅反转传给立面构造器的两个端点，以获得朝东南的外法向，不得反写源环。

九个相邻原始宏块共扫描 9,465 个要素，目标唯一；其原属性、原几何与现有效城市 feature 一致。没有关联 building parts、目标残余或 qualified roof override。0.75 m 邻接阈值内未检出别的源轮廓相交/紧邻；这只是现有地图数据检查，不能推断现场没有邻房。

当前近景块共 28 栋，只替换 ID 502。其余 27 栋均保留，完整 ID、键、几何与 owner 见 `geometry-input.json` 和 `mapping-report.json`。不得删除整个近景块或以半径清除邻楼。宏块既有保护数据、401 个全城残余及 126 个有据屋顶的规则保持；此宏块没有目标相关残余/屋顶覆盖。

`existing_height=8.579 m` 来自旧 GHSL 100 m 栅格高度估计，不是此楼实测。模型高度另由明确推定及照片形态决定，不能把该数作为摄影标尺。

## 复算

新公共模块 `../common/freeze_provider_geometry.py` 接受来源分支的 spec。以仍含冻结城市输入的项目为 `PROJECT`，在 `next` 目录执行：

```bash
python common/freeze_provider_geometry.py --project "$PROJECT" --spec qingpu-beidajie-222/geometry-source-spec.json
```

输入哈希、9 个原始宏块、当前完整城市 manifest、feature table 和 ownership 都在 `mapping-report.json`。原始轮廓/目标属性及同块邻楼已嵌入冻结 JSON，建模不依赖运行下载器。复算会覆写几何/映射报告，发布冻结后应在独立目录进行。

`geometry-input-validation.json` 检查源坐标、局部投影、朝向、唯一 owner 以及 1+27 替换分割，结果通过。本次没有改主项目、模型脚本或第一批建筑的冻结输入。
