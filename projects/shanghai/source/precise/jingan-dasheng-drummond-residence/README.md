# 大胜胡同德莱蒙德住宅南向花园立面

房屋管理部门的第二批名录将2B017「大胜胡同」记作华山路229–285弄。静安区2022年开馆报道采用229–285号的写法，两者指向华山路东侧的里弄群。本模型只取263弄7号独立花园住宅面向庭院的一侧。2014年2月里弄照片左端的12号是其他住户的门牌，241弄7号普爱堂及其他各排住宅另列。[市房屋管理局原表](https://fgj.sh.gov.cn/yxlsjz/20210922/8f72fa07617c4828a25ef948cd1c5da7.html) · [263弄7号门牌记录](https://www.shzhdj.sh.cn/djWeb/djweb/web/djweb/home!wxinfo.action?showlogo=showlogo&showBack=showBack&articleid=ff8080818b0d1e2b018b130e00570823) · [2014年里弄住宅](https://commons.wikimedia.org/wiki/File:Da-Sheng_Hutong.jpg)

静安区的开馆资料将住宅追溯至1899年，后来曾为光明食品集团办公地，2022年10月起开放为华山·263老字号品牌馆。上海广播电视台在同年刊登的研究根据《字林西报行名录》辨认早期住户为英国律师William Venn Drummond，中文文献也译作担文。普爱堂在1930年购买了这处宅地，神父居住及里弄开发属于后一个时期。「德莱蒙德」沿用当代场所名称。[开馆资料](https://www.jingan.gov.cn/rmtzx/003008/003008006/20220929/aabdb80a-652b-4721-96bd-93c8f6b203c7.html) · [早期住户、旧门牌及1930年交易](https://www.kankanews.com/detail/qMyE3EJgjw8) · [2024年市文旅局场馆介绍](https://whlyj.sh.gov.cn/gqfc/20241025/1c27f347bc9b4d3e9c1023b1dca8658c.html)

2014年5月21日斜向庭照与2022年从院中拍摄的正面，都能辨认三开间红砖门廊、上层长窗与带孔女儿墙。木构三角山花分列门廊两旁，山花下的交叉木格架和两层敞廊在正面照中清楚可见。庭院矮墙两侧可见登上入口平台的石阶、盲拱、曲线墙顶和带浅色石球的方垛。各构件和花园一侧的屋面独立制作，未把照片贴在墙面。上部高度、格条数量、局部纹饰、门廊进深、背面剖口及遭树木遮挡的细节均按照片比例估算。[2014年庭院照片](https://commons.wikimedia.org/wiki/File:德拉蒙德住宅3.jpg) · [2022年正面照片及来源摘要](reference-review.json)

2024年与2026年的航片都显示，主楼位于庭院北侧，当前城市源1355有朝南的两个突出坡顶和位于两者之间的浅色平顶。地图搜索的263弄7号兴趣点落在南侧独立小楼3904内，与此排列和照片不符。庭院外其他房屋沿用原有地块，宅内、宅后及东西侧相连建筑留待有图时复原。[屋顶与兴趣点核对](garden-roof-registration.json) · [源建筑及近远景文件摘要](footprint-review.json)

## 重建

在上海项目根目录运行以下命令。需要 Python、NumPy、Shapely 2.1、Blender 4.3.2、gltfpack 与 Open Image Denoise 的 oidnDenoise。作者参数以米计，正对庭院时右方为当地X，向宅内为当地Y，向上为Z。可编辑源按门廊、山花、廊架、窗、台阶和墙垛分组。

```bash
python source/precise/jingan-dasheng-drummond-residence/source/build_model.py \
  --out assets/models/candidates/jingan-dasheng-drummond-residence \
  --audit data/audit/dasheng-drummond-residence-v1 \
  --decoded /tmp/drummond-decoded
```
