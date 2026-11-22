# 仁记珠宝银楼中华路东立面

4A035位于方浜路口以南，城区原建筑1010对上具名建筑的97.11%。四个街道摄影站的102处对应点用于估算三开间东面、弧形山花、卷草空额和两翼的石栏。底层取2021年封闭铺面；2015年街照中有商铺招牌。[年代、署址与各期照片](../../../source/precise/huangpu-renji-silversmith-east-front/README.md)

中华路和方浜中路转角的局部模型由原始、网页和简化三档的309条射线复查，其中包括石栏的实体和透空位置。42处地面探针覆盖人行道、门前、保留楼后及方浜沿线。原城两档均保留北侧原中国银行南市办事处1149。整片聚合矢量中，仅银楼的一个分件减少51.72平方米；另689个分件全部不相交。[材质和透空](preflight-surface-checks.json) · [地面与原城](placement-geometry.json) · [双矢量六态](final-31262.json)

桌面和手机正看中华路东面时，各取11个表面特征，包括底层闭合店面和顶部檐口。近、远档的44次射线首碰与原城三角形共同核对，交付机位方位为−125度，俯角为64度。[原城视线](actual-camera-city-triangles.json) · [模型两档可见性](both-lod-self-visibility.json)

以存档的模型机位和真实街区瓦片复算视线，可在上海项目目录运行下列命令。命令末尾还可指定包含相同瓦片的站点地址，脚本会逐件复核原始字节。

```sh
node data/audit/renji-silversmith-east-front-v1/trace-registered-city.mjs data/audit/renji-silversmith-east-front-v1/actual-city-ray-inputs.json /tmp/city-rays-297.json
```
