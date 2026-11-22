# 新上院南门廊与原城2187

校方修缮测绘南立面的估算全宽为83.72米，原城轮廓的南侧长边实长83.676米。OSM具名新上院与原城2187交并比为0.98144。以南侧长边中点作为配准假设，检查原有实心墙与门廊中央敞口的关系。原图没有门后地坪的绝对标高。[校方修缮记录](https://ahc.sjtu.edu.cn/show.aspx?info_lb=62&flag=3&info_id=324)

在上海项目目录执行下列命令。input-register.json 列出原城表、模型文件的Git版本和SHA。将固定提交中的模型下载到model目录，或用等字节的本地模型。解码脚本读取源码目录下的Meshopt算法。

```sh
node source/precise/hongkou-general-post-office/source/decode_meshopt.mjs model/xuhui-jiaotong-new-upper-hall-inscribed-entrance-web.glb model/full-decoded.glb vendor/meshopt_decoder.module.js
node source/precise/hongkou-general-post-office/source/decode_meshopt.mjs model/xuhui-jiaotong-new-upper-hall-inscribed-entrance-lod.glb model/lod-decoded.glb vendor/meshopt_decoder.module.js
python source/precise/xuhui-jiaotong-new-upper-hall-inscribed-entrance/measurements/entrance-fit/measure.py --city-table assets/city-detail/macros/14-13718-6696/feature-table.json.gz --raw model/xuhui-jiaotong-new-upper-hall-inscribed-entrance-raw.glb --decoded-full model/full-decoded.glb --decoded-lod model/lod-decoded.glb --output portal-and-retained-building.json
```

每档在中央三个横向位置、六个高度发出朝北的18条射线，并在两侧四条轴线、三个高度检查门板或石墩。输出包含每束入射位置与交点深度。原楼的实心外壳仍占据中央开门位置，配准是对照用假设，所有原户和通行地面保持。
