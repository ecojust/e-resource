"""License and attribution for the photograph-derived stone carving."""
CREDIT = "Antigng, Beijing West Road no. 11, lane 1592, 9 August 2017, Wikimedia Commons."
PHOTO = 'https://commons.wikimedia.org/wiki/File:%E5%8C%97%E4%BA%AC%E8%A5%BF%E8%B7%AF1592%E5%BC%8411%E5%8F%B7.jpg'
LICENSE = "https://creativecommons.org/licenses/by-sa/4.0/"
GEOMETRY = "Rectified photograph-derived acanthus and fruit urn relief and its measured tonal surface: CC BY-SA 4.0. Independently constructed masonry and source code: MIT."
COPYRIGHT = GEOMETRY + " " + CREDIT + " The photograph was rectified, sampled and interpreted as an approximate relief; its depth was not surveyed."

def write_metadata(pack):
    original = pack.write_json
    def write(path, value):
        if path.name == 'manifest.json':
            value = dict(value, geometry_license=GEOMETRY, photo_credit=CREDIT, photo_source=PHOTO,
                         derivative_license_url=LICENSE, copyright=COPYRIGHT)
        return original(path, value)
    pack.write_json = write
