# 益民食品一厂旧食堂改建展厅

香烟桥路13号东侧河岸有一座两层灰砖长厅。上海市房屋管理局第五批优秀历史建筑名录以“海宁洋行旧址／上海益民食品一厂历史展示馆”登记这一处，编号5F022。虹口区的展馆介绍说明，今天的厂史展厅由原厂食堂改建。院内另两座建筑分别是1985年拆除后异址缩小复制的原职工小楼，以及1965年拆除后缩小复制的木冷却水塔。[房管局名录](https://fgj.sh.gov.cn/yxlsjz/20200414/b9946bf8508e4b9689671fcd4146bb86.html) · [虹口区展馆介绍](https://www.shhk.gov.cn/qyfwy/030002/030002002/030002002002/20181206/43c1beda-cde3-4a3b-bc6f-858a999280d5.html)

## 四面外墙

西北端临厂门与小楼，东南端临桥与水塔。两面各有四扇上窗和两道中央玻璃门。2013年的西北端与2018年刊出的东南端使用各自的摄影参数。东南端最右的下窗比楼上的窗向左约0.71米，这个偏移直接取自照片。临水和沿街长墙各有14个开间。西南沿街一层第六和第七开间为两处窄木门，每处两扇，每扇有三块凸芯板。街景中可见门槛及双拉手。[两端相机数据](measurements/two-terminal-cameras.json) · [窗洞量测](measurements/terminal-window-reconstruction.json) · [沿街逐开间读图](measurements/street-window-and-roof-survey.json) · [沿街两门实测投影](measurements/two-street-doors.json)

2013年照片存有尼康D70、17毫米焦距和拍摄日期。东南端照片的21条墙面线与17条庭院铺地线估得焦距约912像素。临水长墙近七樘窗按弓顶、起券处与窗槛注册，远处七樘按横向窗位约束。原图能读清的窗由单片弓形上亮、两扇玻璃和细梃构成。第11个临水窗位前有落水管，远端窗框与树后构件的细分采用近窗形制。[庭院消失点](measurements/southeast-courtyard-vanishing-points.json) · [临水立面相机与各窗](measurements/canal-side-camera.json) · [窗框退深读数](measurements/sash-frame-depth.json)

## 尺度与屋顶

模型依城市楼廓与航片取约56.5米长、18.7米宽。两处地面照片中可见灰色封檐和白抹灰三角山花，分别得到约12.0米的脊高。西北山花平面距墙约5.2米，东南山花约5.36米。航片东南转折的判读约为7.7米，航片和立面两种解仍有约2.3米差别。灰砖六个取样区域中三处能读出约5.0至5.3厘米的纵向重复，原创灰砖纹理用每皮5厘米。砖色、瓦色、墙厚及室内退深都存在估计。展件表现改建后的外部，内部展览、历史厂房及院内其他构筑物各有独立范围。[屋顶对照与不确定度](measurements/roof-hip-and-gable.json) · [灰砖周期](measurements/blue-brick-course-readings.json) · [墙带和雨管](measurements/string-courses-and-downpipes.json)

## 模型与复核

原始模型与网页近景各122,956个三角形，远景63,152个。三档分别用同样118个实拍像素检查最先相交的表面，其中107个与原判材质一致。其余11个位置包括相邻玻璃和窄窗梃、灰红砖交界与树影中的颜色误判，逐项保留。沿街两期有方向的街景另有48个可读位置，41个直接击中预期门窗，余下7个先击中灰砖。[逐点材质报告](../../../data/audit/yimin-food-factory-former-canteen-v1/preflight/geometry-rays.json) · [区分实站误差的沿街报告](measurements/streetside-three-mesh-rays.json) · [三个实拍机位的模型对照](../../../data/audit/yimin-food-factory-former-canteen-v1/facade/former-canteen-three-views.jpg)

在仓库根目录可用以下命令重建原始网格和远景网格。两种网格共用窗洞与屋面坐标。

```bash
python projects/shanghai/source/precise/hongkou-yimin-food-factory-former-canteen/source/build_model.py --output yimin-canteen.glb
python projects/shanghai/source/precise/hongkou-yimin-food-factory-former-canteen/source/build_model.py --output yimin-canteen-lod.glb --lod
```
