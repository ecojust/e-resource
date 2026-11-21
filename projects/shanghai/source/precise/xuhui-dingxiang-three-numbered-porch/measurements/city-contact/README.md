# 丁香花园三号楼门廊和原城屋身

两张有数字3的门牌照片分别刊于2015年和2024年。餐厅位置落在原1561内，OpenStreetMap住宅轮廓与其重合97.25%。原城另有一号楼1353，两个地块最近相隔58.33米。依据查阅的两组影像，树冠遮挡了三号楼门廊柱脚与园地的接线。[楼号、照片与航片记录](../building-identity.json) · [OpenStreetMap](https://www.openstreetmap.org/way/1202309544)

测量取主楼四条长度超过8米的边，各取32%和68%两处，分别向内、向外移动1.65米并保留边界位置。每个档位有24种试配。近远模型各与原网格比较117条水平视线，报告另列原壳在门廊侧面与上方的命中。试位覆盖实拍资料容许的不同情形，超出模型范围的原建筑仍可辨认。

在上海项目根目录使用 Python 3、NumPy、Shapely 和支持 module.registerHooks 的 Node.js 运行。程序会验证本地资料的摘要，或从已固定的公共Git版本读取。

```sh
python source/precise/xuhui-dingxiang-three-numbered-porch/measurements/city-contact/measure.py --project . --output porch-and-lot-1561.json
```

底图署名 OpenStreetMap contributors（ODbL）。访谈和第三方照片只列出处。
