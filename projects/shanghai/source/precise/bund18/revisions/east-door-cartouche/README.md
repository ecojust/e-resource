# 外滩18号东门门额石饰

市房管局第二批保护名录2A008将此处登记为麦加利银行，地址为中山东一路18号。原模型在东门顶部采用一个十六瓣圆花。2014年街面照片及2021年正面原照显示，中央是一块近圆形素面石饰，位于矩形衬板上。两侧各有上下横框、收分托座及微微倾斜的石质顶边。按照片重做这些部位，尺寸与突出深度沿用原模型的门轴与照片比例估算。较低门楣两端的小圆饰保留原形。[来源、图幅和原模型定位](reference-review.json) · [2014年立面](https://commons.wikimedia.org/wiki/File:Chartered_Bank_Building_The_Bund.JPG) · [2021年正面](https://commons.wikimedia.org/wiki/File:%E5%A4%96%E6%BB%A9%E9%BA%A6%E5%8A%A0%E5%88%A9%E9%93%B6%E8%A1%8C%E6%97%A7%E5%9D%802021.jpg)

Blender文件保留原楼体，在东门零件集合中可以独立编辑39个石件，包括中央牌板、圆饰、两侧上下横框、冠檐和左右支托。原始及网页模型各移除1,320面旧圆花，新增1,166面；远景移除274面，新增726面。网页近远两档各增加一次绘制调用。原有立面照片沿用ScareCriterion12的2021年影像及其CC BY-SA 4.0许可。[四件模型和签名](manifest.json) · [模型局部对比与验证](../../../../../data/audit/chartered-door-cartouche-v1/README.md)

## 重建

从本目录执行。需要Python、NumPy、Node.js、Blender 4.3.2及项目既有meshopt解码器。下列命令按原Git对象和SHA-256取回并核对四件基线。

```sh
python fetch_baseline.py /tmp/bund18-prior
python build_cartouche.py --prior /tmp/bund18-prior --out /tmp/bund18-final --work /tmp/bund18-work
blender -b --threads 2 --python-exit-code 1 --python native_cartouche.py -- --prior /tmp/bund18-prior/source.blend --out /tmp/bund18-final/bund18.blend --report /tmp/bund18-final/native.json --preview /tmp/bund18-preview
for role in web lod; do
  node ../../../bund17/revisions/street-wing-doors/decode_views.mjs ../../../../../vendor/meshopt_decoder.module.js "/tmp/bund18-final/$role.glb" "/tmp/bund18-work/$role-final.glb"
done
python check_cartouche.py --prior /tmp/bund18-prior --revised /tmp/bund18-final --decoded /tmp/bund18-work --out /tmp/bund18-final/geometry-comparison.json
```
