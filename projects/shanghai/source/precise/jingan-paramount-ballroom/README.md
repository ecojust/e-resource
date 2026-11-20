# 百乐门舞厅（愚园路218号圆角立面与灯塔）

愚园路与万航渡路在这里相交，百乐门面向街口，圆弧入口连接两条沿街伸展的翼楼。第二批上海市优秀历史建筑名录2B010登记了这处舞厅。南京西路1728号的百乐门精品酒店设在另一栋建筑百乐门大都会内，酒店接待处在12楼。[上海市房管局第二批名录](https://fgj.sh.gov.cn/yxlsjz/20210922/8f72fa07617c4828a25ef948cd1c5da7.html) · [精品酒店地址](https://hotels.ctrip.com/hotels/375481.html)

保护牌将建造期记为1931至1934年。上海住房城乡建设管理的建筑介绍记1932年营建、陆根记承建。1933年12月14日舞厅开业，1978年改称红都影剧场，1994年改称百乐门夜总会，2017年修缮后重新开放。档案照片、1994年街景和2009至2015年的街景记录了数次招牌、店面变化。[保护牌与旧照](https://www.sohu.com/a/147633243_687451) · [看看新闻的历史记录](https://www.kankanews.com/detail/DgwMkmBqLyW)

2025年上海住房城乡建设管理刊出的夜景是主立面的依据。模型表现了入口上方的多层竖窗、双排红色PARAMOUNT字牌、分层筒形灯塔、两条街翼以及万航渡路侧的宽厅顶。屋顶脊线和色调参考三期航片。街角半径按具名地块六个控制点拟合，约15.14米。塔顶取35.24米，属于按图估高；屋脊、立面开间、玻璃与灯饰分格也按比例估算。资料尚未提供可核对的舞池、弹簧地板或客房详图，本版本表现建筑外观。[2025年夜景出处](https://m.thepaper.cn/baijiahao_31871641) · [照片、作者与授权](reference-review.json) · [底图与航片](footprint-review.json)

冻结地块857与现行实名轮廓的相交并集比为98.89%。局部原点在东经121.43970609°、北纬31.22545407°；作者X向北、Y向西入楼、Z向上。原粗楼统一估高12.8米，实际屋顶和灯塔有明显高差。西侧两翼之间留出空地，三处门口可以走到门扇前。完整模型和简化模型均可在独立页面下载，Blender工程保留可编辑分组。[独立模型](../../../paramount-ballroom.html) · [在上海地图中打开](../../../index.html#landmark=jingan-paramount-ballroom&mode=overview) · [验收记录](../../../data/audit/paramount-ballroom-v1/README.md)

## 重建模型

从 `projects/shanghai/` 运行。需要 Python 3、NumPy、Shapely 2.1、Node、Blender 4、gltfpack、ImageMagick 7 与 Open Image Denoise 2。可通过 `--gltfpack` 与 `--oidn` 指定命令位置。

```sh
python -B source/precise/jingan-paramount-ballroom/source/build_model.py \
  --out /tmp/paramount/assets --audit /tmp/paramount/audit --decoded /tmp/paramount/decoded
python -B source/precise/jingan-paramount-ballroom/source/check_surfaces.py \
  --manifest /tmp/paramount/assets/manifest.json --out /tmp/paramount/audit/surface-checks.json
python -B data/audit/paramount-ballroom-v1/verify-placement.py \
  --manifest /tmp/paramount/assets/manifest.json --work /tmp/paramount/placement --out /tmp/paramount/audit
```

原创几何、字牌及专属代码采用仓库MIT许可。第三方照片与航片按各来源条款使用，模型仅包含原创材质。地图数据署名 © OpenStreetMap contributors（ODbL）和 Overture Maps Foundation，影像资料来自 Esri World Imagery Wayback 与各影像提供者。
