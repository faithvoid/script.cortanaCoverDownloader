import os
import xbmcgui
import xbmc
import urllib
import struct

# Search for default.xbe files in the selected folder
def find_default_xbe_files(root_dir):
    xbe_files = []
    for dirpath, _, filenames in os.walk(root_dir):
        for filename in filenames:
            if filename.lower() == "default.xbe":
                xbe_files.append(os.path.join(dirpath, filename))
    return xbe_files

# Scan titleIDs for searching cover art database
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

# Download cover art from MobCat's API 
def download_cover_art(title_id, save_path):
    folder = title_id[:4]
    url = "https://raw.githubusercontent.com/MobCat/MobCats-original-xbox-game-list/main/icon/{}/{}.png".format(folder, title_id)

    try:
        urllib.urlretrieve(url, save_path)
        return True
    except Exception as e:
        xbmc.log("Download error: %s" % str(e), level=xbmc.LOGERROR)
        return False

def main():
    dialog = xbmcgui.Dialog()
    root_dir = dialog.browse(0, "Select Primary Game Directory", "files")

    if not root_dir:
        dialog.ok("cortanaCoverDownloader", "No folder selected!")
        return

    xbe_files = find_default_xbe_files(root_dir)

    if not xbe_files:
        dialog.ok("cortanaCoverDownloader", "No default.xbe files found!")
        return

    total = len(xbe_files)
    count = 0

    progress = xbmcgui.DialogProgress()
    progress.create("Downloading Covers", "Processing...")

    for index, xbe_path in enumerate(xbe_files):
        if progress.iscanceled():
            break

        title_id = read_titleid(xbe_path)
        label = os.path.basename(os.path.dirname(xbe_path))

        if title_id:
            tbn_path = os.path.join(os.path.dirname(xbe_path), "default.tbn")
            if download_cover_art(title_id, tbn_path):
                count += 1

        percent = int((float(index + 1) / total) * 100)
        progress.update(percent, "Processing: {}".format(label), "Downloaded: {}".format(count), "Remaining: {}".format(total - (index + 1)))

    progress.close()
    dialog.ok("cortanaCoverDownloader", "Done!", "Covers downloaded: {}".format(count))

if __name__ == "__main__":
    main()
