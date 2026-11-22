# 武进路225弄9、11号双券宅门

2015年7月19日，高参88从院内两个机位拍下这面砖墙。绿色门牌在左券写9号，在右券写11号。9号的深色铁栅门退在券后，11号的门洞敞开，可以看见门槛后的廊地、灰墙和深色边框。两道券上各有红砖半圆盲券和叶饰小额，二层两扇窗的开扇与遮阳篷也有区别。[双门模型](../../../wujin-225-paired-residential-entrances.html) · [双门模型图板](../../../data/audit/wujin-225-paired-residential-entrances-v1/paired-entrances/courtyard-entrances.jpg)

## 门牌与年代

上海市房屋管理局第五批优秀历史建筑名录第5F010项登记「恩德堂教堂及宿舍」，地址为武进路225弄3–11号，使用状况记为住宅。第5F019项另列乍浦路480、490号「恩德堂」。1942年英文名录在乍浦路480号列有礼拜堂，1947年电话簿也有武进路225弄3号的记录。9号和11号的具体门牌采用高参88原照片所见，宅门的建造年份尚待考证。[名录与旧门牌逐条对照](measurements/wujin-protected-row-and-addresses.json)

## 怎样读这件模型

9号气窗的三根辐条围成四格，11号气窗靠外侧的两格可见横条。2012年12月的9号照片还看得见红色砖券，2015年照片里下层的券与砖面已经刷白，两户之间装有红色软管卷盘柜。本件采用2015年时的外观，保留门额、不同槛高、可见的台阶、11号门后短段廊面和二层窗。墙体截到原照可辨的檐口。同弄还有带卷草浮雕的山墙，两组实照之间的方位与距离待考。[门与气窗的原照标点](measurements/paired-door-photographs.json) · [二层窗的观测](measurements/upper-window-observations.json)

以9号横档净宽取1.43米建立显示比例。两户门中心在模型中相距约3.60米，11号门槛比9号低约0.16米。这些数值由两张照片的砖皮和门框比例估出。旧砖一皮暂取6.3厘米，仍待现场定尺。两原片有112对同名特征点，其中84对参与平面配准，另28对的投影误差中位数为2.91个原图像素。[两机位配准、留出误差及比例依据](measurements/paired-door-camera-fit.json)

## 重建与核对

在本目录执行以下命令。近、远网格和照片核查报告会写入指定目录。

```sh
mkdir -p output
python source/build_model.py --output output/doors-full.glb
python source/build_model.py --lod --output output/doors-lod.glb
python measurements/check_paired_entrances.py output/doors-full.glb output/doors-full-check.json
python measurements/check_paired_entrances.py output/doors-lod.glb output/doors-lod-check.json
python measurements/render_paired_entrances.py output/doors-full.glb output/courtyard-entrances.jpg
```

原照正面和斜面分别标出60和46处门洞、砖券、门扇、门额及内廊观测点。核查程序向整件网格投射每条视线，记录第一处击中的材质和位置。其中10条视线专门检查门后，分别指向11号灰墙、廊地与9号暗处。图板以模型重新绘制。[三档网格逐点核查](../../../data/audit/wujin-225-paired-residential-entrances-v1/paired-entrances/paired-door-photo-review.json) · [来源与许可](SOURCES-LICENSE.md)
