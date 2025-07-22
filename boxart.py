import os
import xbmcgui
import xbmc
import urllib
import urllib2
import struct
import json

def find_default_xbe_files(root_dir):
    xbe_files = []
    for dirpath, _, filenames in os.walk(root_dir):
        for filename in filenames:
            if filename.lower() == "default.xbe":
                xbe_files.append(os.path.join(dirpath, filename))
    return xbe_files

def read_titleid(xbe_path):
    try:
        with open(xbe_path, 'rb') as f:
            f.seek(0)
            if f.read(4) != b'XBEH':
                return None
            f.seek(0x104)
            base_addr = struct.unpack('<I', f.read(4))[0]
            f.seek(0x118)
            cert_addr = struct.unpack('<I', f.read(4))[0]
            cert_offset = cert_addr - base_addr
            f.seek(cert_offset + 0x8)
            titleid = struct.unpack('<I', f.read(4))[0]
            return "%08X" % titleid
    except Exception as e:
        xbmc.log("XBE TitleID Error: %s" % str(e), level=xbmc.LOGERROR)
        return None

def get_xmid_from_api(title_id):
    try:
        url = "https://mobcat.zip/XboxIDs/api.php?id={}".format(title_id)
        response = urllib2.urlopen(url, timeout=10)
        data = json.load(response)
        if isinstance(data, list) and len(data) > 0:
            # Return first XMID
            xmid = data[0].get("XMID")
            return xmid
        else:
            return None
    except Exception as e:
        xbmc.log("API Fetch Error for {}: {}".format(title_id, str(e)), level=xbmc.LOGERROR)
        return None

def download_thumbnail(xmid, save_path):
    try:
        prefix = xmid[:2]
        url = "https://raw.githubusercontent.com/MobCat/MobCats-original-xbox-game-list/main/thumbnail/{}/{}.jpg".format(prefix, xmid)
        urllib.urlretrieve(url, save_path)
        return True
    except Exception as e:
        xbmc.log("Thumbnail Download Error ({}): {}".format(xmid, str(e)), level=xbmc.LOGERROR)
        return False

def main():
    dialog = xbmcgui.Dialog()
    root_dir = dialog.browse(0, "Select Game Root Folder", "files")

    if not root_dir:
        dialog.ok("cortanaCoverDownloader", "No folder selected.")
        return

    xbe_files = find_default_xbe_files(root_dir)

    if not xbe_files:
        dialog.ok("cortanaCoverDownloader", "No default.xbe files found.")
        return

    total = len(xbe_files)
    count = 0

    progress = xbmcgui.DialogProgress()
    progress.create("cortanaCoverDownloader", "Processing...")

    for index, xbe_path in enumerate(xbe_files):
        if progress.iscanceled():
            break

        folder_name = os.path.basename(os.path.dirname(xbe_path))
        title_id = read_titleid(xbe_path)

        if title_id:
            xmid = get_xmid_from_api(title_id)
            if xmid:
                tbn_path = os.path.join(os.path.dirname(xbe_path), "default.tbn")
                if download_thumbnail(xmid, tbn_path):
                    count += 1

        percent = int((float(index + 1) / total) * 100)
        progress.update(percent, "Processing: {}".format(folder_name), "Downloaded: {}".format(count), "Remaining: {}".format(total - (index + 1)))

    progress.close()
    dialog.ok("cortanaCoverDownloader", "Done!", "Thumbnails downloaded: {}".format(count))

if __name__ == "__main__":
    main()
