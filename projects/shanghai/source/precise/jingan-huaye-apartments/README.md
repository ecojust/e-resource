# 华业公寓主楼

华业公寓又名华业大楼，英文史料作 Cosmopolitan Apartments。模型覆盖静安区院内的 H 形主楼、逐层退台、八面红瓦塔及门厅。2019 年航拍可辨西南面的连续弧形阳台、臂楼宽窗与格栅、三联拱窗及檐下装饰；2015 年地面照片与历史东面鸟瞰补足低处入口、朝园侧阳台和两翼顶层。独立的四层南北配楼、连接拱廊和里弄留给相应的独立建筑条目。[独立预览](../../../huaye-apartments.html) · [2019 年航拍](https://commons.wikimedia.org/wiki/File:华业公寓·上海静安·俯拍.jpg) · [2015 年地面照片](https://commons.wikimedia.org/wiki/File:Cosmopolitan_Apartments_Shanghai.JPG)

[原始 GLB](../../../assets/models/candidates/jingan-huaye-apartments/jingan-huaye-apartments-raw.glb) · [网页 GLB](../../../assets/models/candidates/jingan-huaye-apartments/jingan-huaye-apartments-web.glb) · [远景 LOD](../../../assets/models/candidates/jingan-huaye-apartments/jingan-huaye-apartments-lod.glb) · [可编辑 Blender 工程](../../../assets/models/candidates/jingan-huaye-apartments/jingan-huaye-apartments.blend)

## 所在地和年代

上海市房屋管理局首批优秀历史建筑名单的 1B002 记载陕西北路 175 号。静安区政府及上海市政协《联合时报》记作陕西北路 173 号，记载李锦沛设计、1934 年落成，十层中央主楼高四十余米，东西两面都能看到红瓦尖顶。上海市地方志另有较早的建设年份，模型沿用登记和区政府资料的落成年。建筑转角、窗扇、栏杆、遮挡处及屋顶高度均按历史照片和空间尺度近似处理。[市房屋管理局第一批名录](https://fgj.sh.gov.cn/yxlsjz/20200331/fe7b4d6f35774b708a2c5122849065bd.html) · [静安区政府资料](https://web.archive.org/web/20160129170958/http://www.jingan.gov.cn/jagl/006001/006001006/006001006001/006001006001001/20061004/5452bdb9-e826-4c67-82e6-f5bad7803c65.html) · [上海市政协《联合时报》](https://web.archive.org/web/20151002053016/http://www.shszx.gov.cn/node2/node4810/node4851/wswh/u1ai63410.html) · [逐件来源与日期差异](reference-review.json)

照片记录的 DJI 相机位置和云台角度提供了识别无名源建筑的方式。相机位于上海展览中心东侧，距主楼中心约 75 米，向东北约 51° 俯拍，视线穿过屋顶影像中可辨认的八面红瓦塔。红顶两侧各有一片独立登记的无名楼体。地图线索中黄浦区的同名对象距此数公里，面形和地址都不同。[地形、源文件及拍摄参数](footprint-review.json)

## 几何与复建

可编辑工程将西北、东南两条臂楼的各面窗组、主楼中臂、出挑弧形阳台、顶层拱廊、八面塔和瓦垄分组。实墙开洞、后置玻璃、栏杆、窗格和屋顶均为实体几何。原始、网页与 LOD 资产采用同一米制机身坐标，X 指向东南约 146°，Y 指向东北约 56°，Z 朝上。GLB 按标准转换为 Y 朝上。全楼窗墙、户改阳台封闭方式及色泽具有年代差异，模型采用统一的简化表达。

在仓库的 `projects/shanghai` 下运行以下命令，使用 Python、NumPy、Shapely 2.1 以上、Node、Blender 4.3、gltfpack、ImageMagick 和 Open Image Denoise。程序构建两种真实几何，独立解压两个网页变体并对比有向三角面；重新打开 Blender 工程后核对材质和几何，再输出预览。[构建入口](source/build_model.py) · [几何程序](source/huaye_geometry.py)

```sh
python -B source/precise/jingan-huaye-apartments/source/build_model.py \
  --out /tmp/huaye-assets --audit /tmp/huaye-audit \
  --gltfpack gltfpack --oidn oidnDenoise
```

模型、程序和材质使用仓库 MIT 许可。Legolas1024 和 Livelikerw 拍摄的两张照片均为 CC BY-SA 4.0，另参阅两幅历史图片。照片与卫星图像均仅用于研究。地理数据按源记录注明的 OpenStreetMap、Overture 和 East Asian Buildings 来源归属。[MIT](../../../../../LICENSE) · [原始图像出处、拍摄者、许可和散列](reference-review.json) · [源建筑溯源](footprint-review.json)
