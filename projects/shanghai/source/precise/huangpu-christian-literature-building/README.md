# 广学大楼虎丘路西立面

市房管局第二批优秀历史建筑名录以2A020登记广学大楼，列市文体进出口公司、虎丘路128号。邬达克设计的广学、真光两座楼各朝一条街。建筑史资料记载1930年动工、1932年竣工并开幕；黄浦档案资料另记1933年和九层。虎丘路的照片能辨认地面一层和其上七排楼窗，大石尖拱跨过这些楼层。圆明园路209号真光大楼拥有独立门牌和另一组山墙窗。[历史资料和历年照片](reference-review.json) · [两栋城市轮廓和航拍位置](footprint-review.json)

模型制作西楼临虎丘路的街面和约2.85米的素面收口。每侧五间深色砖壁分列在中央玫瑰色石拱两边。折面砖柱延伸到顶部小尖饰，下部石梁带有中英文凸字。建模依据可查年代的外观；石面接缝、横窗分隔、色泽、檐高与细部进深经过估算。字形使用项目内附许可的字体子集。[独立查看](../../../christian-literature.html) · [四种模型文件](../../../assets/models/candidates/huangpu-christian-literature-building/manifest.json) · [网格与地图核验](../../../data/audit/christian-literature-v1/README.md)

在上海项目目录运行以下命令。模型构建依赖Python、NumPy、Shapely、Blender、gltfpack、ImageMagick和Open Image Denoise。

```sh
python source/precise/huangpu-christian-literature-building/source/build_model.py --out /tmp/guangxue-assets --audit /tmp/guangxue-audit --decoded /tmp/guangxue-decoded --blender blender --gltfpack gltfpack --oidn oidnDenoise
python data/audit/christian-literature-v1/check-street.py --project . --manifest /tmp/guangxue-assets/manifest.json --decoded /tmp/guangxue-decoded --out /tmp/guangxue-audit/street-checks.json
```
