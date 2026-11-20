# 永嘉新村15号拱廊与东端山墙

市房管局第二批名录将2D025「永嘉新村」列在永嘉路580号，现用地址为永嘉路580弄。住宅群建于1947年，初为交通银行职工宿舍。采用2014年1月26日的外观，选取西部两层灰瓦排屋东端的15号。2012年有关屋面加建的报道和2014年涉及40号的报道仅用于辨明小区的变迁。[市房管局原表](https://fgj.sh.gov.cn/yxlsjz/20210922/8f72fa07617c4828a25ef948cd1c5da7.html) · [2012年报道](https://web.archive.org/web/20120512000559/https://shanghai.xinmin.cn/xmjd/2012/04/19/14470501.html) · [2014年报道](https://house.people.com.cn/n/2014/0305/c164220-24530373.html)

Livelikerw在2014年1月26日14时52分拍摄的照片中，小门廊东侧挂着绿色“15”号牌。正面带拱小门廊与瓦顶、红棕木窗和墙脚、街边透孔花墙及东侧折返、两层端墙上部的起伏收头依次可辨。同日早两分钟的排屋全景记录灰瓦长屋面与平行弄道。1月24日拍摄的三层四坡顶住宅属于东部另一组建筑。花格、曲线、窗棂的尺寸与数量按照片估算。门牌上的数字做成立体构件，较小的文字和住户临时设施留在照片里。[15号门牌所在的原照](https://commons.wikimedia.org/wiki/File:Yong-Jia_Xincun_3.JPG) · [同日弄道](https://commons.wikimedia.org/wiki/File:One_Longtang_of_Yong-Jia_Xincun.JPG) · [东部三层住宅](https://commons.wikimedia.org/wiki/File:Yong-Jia_Xincun_Shanghai.JPG) · [各次照片时间、哈希及使用范围](reference-review.json)

2024年1月和2026年1月的屋顶影像、保护范围和多个门牌点共同限定对位。15号在城市源4151东端，16、20、21号在同一排，隔着小巷的13、14号属于独立源4677。模型向后只包含正面屋瓦窄带及东端可见山墙。长排的其他住宅、背面、内部房间及东部三层公寓分别留项。建筑群边界能定位整处里弄，户界宽度、东墙进深和院墙的精确位置仍按照片比例估算。[独立门牌与两期航片](number-and-roof.json) · [地块和邻楼](footprint-review.json) · [OpenStreetMap保护范围](https://www.openstreetmap.org/way/490322214)

## 重建

在上海项目目录运行以下命令。需要Python、NumPy、Shapely 2.1、Blender 4.3.2、gltfpack与Open Image Denoise。横向X朝向东端，Y向宅内，Z向上，单位为米。原生场景单独保留门牌、门廊、花墙、窗格、山墙和屋面构件。

```bash
python source/precise/xuhui-yongjia-village-no15/source/build_model.py \
  --out assets/models/candidates/xuhui-yongjia-village-no15 \
  --audit data/audit/yongjia-village-no15-v1 \
  --decoded /tmp/yongjia-no15-decoded
```

[模型与四种下载](../../../yongjia-village-no15.html) · [重开原生场景、解码及地面检查](../../../data/audit/yongjia-village-no15-v1/README.md)
