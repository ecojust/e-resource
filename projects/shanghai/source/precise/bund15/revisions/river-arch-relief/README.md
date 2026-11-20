# 外滩15号华俄道胜银行东立面拱肩浮雕

市房管局第二批2A005登记“华俄道胜银行”，公布时使用者为中国外汇交易中心，中山东一路15号。2014年1月拍摄的河岸正立面照片能辨认三樘中央拱窗。2月的近照可辨两侧有翅人物、叠合的尖叶和蜷曲叶梢，以及拱顶券石上张口的兽首。[市房管局原表](https://fgj.sh.gov.cn/yxlsjz/20210922/8f72fa07617c4828a25ef948cd1c5da7.html) · [正立面](https://commons.wikimedia.org/wiki/File:Russo-Chinese_Bank_Building,_Shanghai.JPG) · [拱肩特写](https://commons.wikimedia.org/wiki/File:A_Decoration_on_Former_Russo-Chinese_Bank_Building,_Shanghai.JPG)

三樘窗的卷饰重复。限制投影形状、去除重复匹配点后，照片左樘、中樘、右樘各有25、13和8个有效匹配点，覆盖近照33.7%、16.8%与16.8%。左樘对应实际立面南樘，本次按此位置制作一组。特写与正立面均由Livelikerw于2014年拍摄，采用CC BY-SA 3.0许可。五个新增网格按照片轮廓手工建模，人物面容、叶片厚度、兽口深度和石雕的出墙距离均为估算。[两张照片的尺寸、许可与签名](reference-review.json)

原V4.4模型已有96个洞口、后退的玻璃与窗帘，三樘拱肩各有斜向石线、环形装饰与平券石。编辑文件在南樘的拱肩增加两个有翅人物、两组卷叶及中央兽首，沿用原雕刻石灰石材质。原玻璃与窗框背后的空间、东立面其余两樘和另三面建筑均保留。[基准版本](baseline.json) · [资产与校验值](manifest.json) · [同机位前后图](../../../../../data/audit/russo-arch-relief-v1/README.md)

## 重建

在本目录运行下列命令。Python 需要 NumPy 和 Shapely 2，几何检查使用项目内 Node 解码器。Blender 4.3.2 可打开或重新生成带五个独立雕刻物件的原生场景。Blender 保存时会写入应用内部信息，重新保存的文件须通过原有网格、场景物件、材质与贴图复查。

```sh
python -B fetch_baseline.py /tmp/bund15-prior
python -B build_relief.py /tmp/bund15-prior /tmp/bund15-final
blender -b -t 1 --python-exit-code 1 -P native_relief.py -- /tmp/bund15-prior/native.blend /tmp/bund15-final/native.blend /tmp/bund15-final/native-reopen.json
python -B check_revision.py /tmp/bund15-prior /tmp/bund15-final /tmp/bund15-final/geometry-comparison.json
blender -b -t 1 --python-exit-code 1 -P render_relief.py -- /tmp/bund15-prior/native.blend /tmp/bund15-views before
blender -b -t 1 --python-exit-code 1 -P render_relief.py -- /tmp/bund15-final/native.blend /tmp/bund15-views after
```

核对四件哈希后，`register_revision.py <上海项目根目录> --report <输出JSON>` 原位更新地标以及四份外滩元数据。脚本识别旧原生记录的 `russo`、当前地标的 `bund15` 和原包的字节数。四个下载路径均来自本次清单。
