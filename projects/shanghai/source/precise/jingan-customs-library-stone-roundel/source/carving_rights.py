CREDIT = 'Antigng，2018年1月28日，《静安区图书馆海关楼 1、2》，Wikimedia Commons，CC BY-SA 4.0。石徽起伏据第一张原照裁切、校平光照并转成几何，保留相同许可。'
PHOTO = 'https://commons.wikimedia.org/wiki/File:%E9%9D%99%E5%AE%89%E5%8C%BA%E5%9B%BE%E4%B9%A6%E9%A6%86%E6%B5%B7%E5%85%B3%E6%A5%BC_1.jpg'
LICENSE = 'https://creativecommons.org/licenses/by-sa/4.0'
GEOMETRY = 'Stone medallion adapted from Antigng’s photograph: CC BY-SA 4.0. Original surrounding stonework, procedural model and code: MIT.'
COPYRIGHT = 'Antigng，2018年1月28日，《静安区图书馆海关楼 1、2》，Wikimedia Commons，CC BY-SA 4.0。石徽起伏据第一张原照裁切、校平光照并转成几何，保留相同许可。'

def write_metadata(pack):
    original = pack.write_json
    def write(path, value):
        if path.name == 'manifest.json':
            value = dict(value, geometry_license=GEOMETRY, photo_credit=CREDIT, photo_source=PHOTO,
                         derivative_license_url=LICENSE, copyright=COPYRIGHT)
        return original(path, value)
    pack.write_json = write
