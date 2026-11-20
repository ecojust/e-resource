# 外滩3号东北切角门的葡萄垂饰

市房管局二批2A002记原用名“有利银行”，公布时称“外滩3号餐厅”，地址为中山东一路3号、广东路17号。2013年12月29日，Legolas1024拍下东北切角入口的全门和同一大楼的葡萄垂饰近照。全门照显示半圆券两脚外各有一串石雕。近照可辨上方叶结、左右伸出的卷枝和端珠、果粒间绕过的两条斜带及向下收束的叶尖。另一张带三角山花的正立面大门用作门位排除对照。[市房管局名录](https://fgj.sh.gov.cn/yxlsjz/20210922/8f72fa07617c4828a25ef948cd1c5da7.html) · [东北角入口](https://commons.wikimedia.org/wiki/File:有利大楼东北角入口.jpg) · [葡萄近照](https://commons.wikimedia.org/wiki/File:有利大楼装饰（葡萄）.jpg) · [实取哈希与署名](reference-review.json)

原始V6模型的东北切角约7.31米长，拱边有窗套、腰线和角石。把原始172,401个三角面投影至切角局部，在两侧各取440个采样点，能区分既有平面、分缝和突出的角石。根据照片里的拱幅及起拱线，把两串浮雕布置在距中轴各约2.61米、标高约3.42至4.73米的位置。果粒、斜带、卷叶和石色随影像近似，石雕深度与物种细节没有实测尺寸。[原版工程与作者记录](https://github.com/ecojust/e-resource/tree/ae55637ce1d7cbc4d21fd94934c8309aca1dcd09/projects/shanghai/source/bund/bund_classics/wall-v4.4) · [原门表面采样](../../../../../data/audit/union-grape-pendants-v1/previous-entrance-profiles.json) · [定位参数](geometry-input.json)

三份GLB各保留旧二进制块和旧图元的完整顺序，附加左右两件命名的网格。原生Blender保留其原始门洞、材质、坐标和场景对象，新加的两串石雕可分别编辑。新增几何采用MIT；旧模型作者、照片参考署名和OSM足迹许可随原件保留。新增照片只通过来源链接供核对。[四件资产](manifest.json) · [签名基准](baseline.json) · [表面与保全检验](../../../../../data/audit/union-grape-pendants-v1/geometry-comparison.json)

在本目录运行以下命令。基准下载核对Git对象、SHA256和字节数。用同项目既有的MeshOptimizer解码程序分别解压旧、新两个web和LOD文件，可运行独立三角面比对和表面检验。[构件制作](build_pendants.py) · [原生制作](native_pendants.py) · [独立比对](check_revision.py)

    python -B fetch_baseline.py /tmp/bund03-prior
    python -B build_pendants.py /tmp/bund03-prior /tmp/bund03-revised
    blender -b -t 1 --python-exit-code 1 -P native_pendants.py -- /tmp/bund03-prior/native.blend /tmp/bund03-revised/native.blend /tmp/bund03-revised/native-reopen.json

在上海项目根目录可复核完整的几何保留和54个新旧可见面。令 REVISED 指向前一步产生的三个GLB；下面的两个目录名须分别为 prior 和 output，供对照程序区分。

    PRIOR=/tmp/bund03-prior
    REVISED=/tmp/bund03-revised
    DECODED=/tmp/bund03-decoded
    SOURCE=source/precise/bund03/revisions/northeast-grape-pendants
    DECODER=source/precise/bund17/revisions/street-wing-doors/decode_views.mjs
    mkdir -p "$DECODED/prior" "$DECODED/output"
    for role in web lod; do
      node "$DECODER" vendor/meshopt_decoder.module.js "$PRIOR/$role.glb" "$DECODED/prior/$role.glb"
      node "$DECODER" vendor/meshopt_decoder.module.js "$REVISED/$role.glb" "$DECODED/output/$role.glb"
    done
    python -B "$SOURCE/check_revision.py" "$PRIOR" "$REVISED" "$DECODED" \
      data/audit/postal-office-v1/independent-glb-review-helpers.py /tmp/bund03-checked.json
