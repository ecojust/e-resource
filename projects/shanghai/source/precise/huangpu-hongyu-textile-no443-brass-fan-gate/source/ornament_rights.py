"""Preserve attribution and the share-alike grant on the three traced brass ornaments."""
CREDIT = 'Antigng (2015), photograph of the building known as Hongyuan, Wikimedia Commons.'
PHOTO = 'https://commons.wikimedia.org/wiki/File:%E9%B8%BF%E5%85%83%E5%A4%A7%E6%A5%BC.jpg'
LICENSE = 'https://creativecommons.org/licenses/by-sa/4.0/'
GEOMETRY = 'Three photograph-traced pierced brass ornaments: CC BY-SA 4.0. Original architectural geometry and procedural materials: MIT.'
COPYRIGHT = GEOMETRY + ' ' + CREDIT + ' The original photograph was rectified and its visible ornament outlines and holes traced as solid meshes.'

def write_metadata(pack):
    original = pack.write_json
    def write(path, value):
        if path.name == 'manifest.json':
            value = dict(value, geometry_license=GEOMETRY, photo_credit=CREDIT, photo_source=PHOTO,
                         derivative_license_url=LICENSE, copyright=COPYRIGHT)
        return original(path, value)
    pack.write_json = write
