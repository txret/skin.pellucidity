"""Pick a random background image for the Home screen.

Called by the skin as
    RunScript(special://skin/scripts/cycle_background.py, <image folder>, <property>)
and stores the chosen image path in Window(home).Property(<property>), which
the Home window uses as its background texture.

Why a script instead of a multiimage control: a window property outlives the
Home window, so returning to Home shows the same photo instead of restarting
a slideshow from a black screen.
"""
import os
import random
import sys

import xbmcgui
import xbmcvfs

IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp', '.gif', '.bmp'}

# Kodi's Home window; properties set on it are readable from every window
HOME_WINDOW_ID = 10000


def list_images(folder):
    """Return the paths of all image files directly inside `folder`."""
    # xbmcvfs instead of os.listdir: the folder is a special:// path and may
    # sit inside an Android APK or on a network share.
    _, files = xbmcvfs.listdir(folder + '/')
    return [f'{folder}/{name}' for name in files
            if os.path.splitext(name)[1].lower() in IMAGE_EXTENSIONS]


def main():
    """Set the window property to an image other than the one it holds now."""
    # RunScript passes its arguments with the spaces that follow the commas
    folder, key = (arg.strip() for arg in sys.argv[1:3])
    home = xbmcgui.Window(HOME_WINDOW_ID)
    current = home.getProperty(key)

    # Never repeat the current image, unless it is the only one there is
    images = list_images(folder.rstrip('/'))
    candidates = [path for path in images if path != current] or images
    if candidates:
        home.setProperty(key, random.choice(candidates))


if __name__ == '__main__':
    main()
