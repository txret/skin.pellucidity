"""Quick-jump letter list for the skin's library views.

This is the skin's plugin (the xbmc.python.pluginsource library in
addon.xml): every plugin://skin.pellucidity/ URL runs this file.

The jump column at the right edge of the video and music windows (include
"jump", control 60) uses this plugin as its content:

    plugin://skin.pellucidity/?action=list[&showall=true]
        one item per first letter that occurs in the focused view
    plugin://skin.pellucidity/?action=jump&pos=<letter>
        scroll the view to that letter (what a list item does when clicked)

Listing also stores where each letter sits in the column (window properties
"jump_index_<letter>"), so the views can open the column on the letter of
their first visible item (variable "jump_index" in Includes_variables.xml).

Kodi has no "jump to letter" builtin, so jumping replays the remote control's
SMS-jump actions (jumpsms2 .. jumpsms9), the same thing typing on a phone
keypad does.
"""
import json
import sys
from urllib.parse import parse_qsl

import xbmc
import xbmcaddon
import xbmcgui
import xbmcplugin

ADDON_ID = xbmcaddon.Addon().getAddonInfo('id')

# '#' stands for everything that sorts before the letters (digits)
NUMBER_SIGN = '#'
LETTERS = NUMBER_SIGN + 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'

# phone keypad: the action that cycles through each group of letters
SMS_ACTIONS = {
    'ABC': 'jumpsms2',
    'DEF': 'jumpsms3',
    'GHI': 'jumpsms4',
    'JKL': 'jumpsms5',
    'MNO': 'jumpsms6',
    'PQRS': 'jumpsms7',
    'TUV': 'jumpsms8',
    'WXYZ': 'jumpsms9',
}

# Any id from a media window's <views> list: Kodi redirects focus to whichever view is active
VIEW_CONTROL_ID = 50

# One key press advances one letter within its keypad group; the largest group has four
MAX_KEY_PRESSES = 4


def main():
    """Dispatch on the `action` query parameter of the plugin URL."""
    # Kodi passes the query string as argv[2] ("?a=b&c=d") and the directory
    # handle as argv[1]; a malformed call simply does nothing.
    try:
        params = dict(parse_qsl(sys.argv[2][1:]))
    except IndexError:
        params = {}

    action = params.get('action')
    if action == 'list':
        handle = int(sys.argv[1])
        items = list_letters(params.get('showall', 'false') == 'true')
        publish_letter_positions([item.getLabel() for _, item, _ in items])
        xbmcplugin.addDirectoryItems(handle=handle, items=items)
        # never cache: the letters depend on whatever view is focused right now
        xbmcplugin.endOfDirectory(handle=handle, cacheToDisc=False)
    elif action == 'jump':
        jump_to(params.get('pos', NUMBER_SIGN))


def list_letters(show_all):
    """Return directory items for the first letters present in the focused view.

    show_all: also list the letters without entries (marked with the
    `NotAvailable` property); clicking one jumps to the last letter before it
    that does have entries.
    """
    # Goal: mirror the view's alphabet without touching the database, so it
    # works for any content (library, playlists, plugins). The view is read
    # through info labels: SortLetter of every item gives the set of letters.
    count = xbmc.getInfoLabel('Container.NumItems')
    if not count:
        return []

    present = set()
    for index in range(int(count)):
        letter = xbmc.getInfoLabel(f'ListItem({index}).SortLetter').upper()
        present.add(NUMBER_SIGN if letter.isnumeric() else letter)

    # A view whose items all start with the same letter has nothing to jump to
    if len(present) < 2:
        return []

    items = []
    last_present = NUMBER_SIGN
    for letter in LETTERS:
        item = xbmcgui.ListItem(label=letter, offscreen=True)
        if letter in present:
            last_present = letter
        elif show_all:
            item.setProperty('NotAvailable', 'true')
        else:
            continue
        url = f'plugin://{ADDON_ID}/?action=jump&pos={last_present}'
        items.append((url, item, False))
    return items


def publish_letter_positions(listed):
    """Store the jump column position of every letter as a property of the current window.

    listed: the letters in the order the jump column shows them.
    """
    # Goal: when the column opens it should already be on the letter of the
    # view's first visible item. The skin cannot search a list by label, and
    # running Python at the moment the column opens would make the highlight
    # visibly jump. So the letter -> position table is built here, once per
    # listing, and the view's <onright> only looks it up.
    # Every letter gets a value, so nothing stale is left from an earlier
    # listing. A letter missing from the column takes the position of the
    # nearest letter before it (or the top), matching how show_all jumps.
    window = xbmcgui.Window(xbmcgui.getCurrentWindowId())
    position = 0
    for letter in LETTERS:
        if letter in listed:
            position = listed.index(letter)
        window.setProperty(f'jump_index_{letter}', str(position))


def jump_to(letter):
    """Scroll the focused view to the first item starting with `letter`."""
    # Kodi treats the click as a playback request; answer it as failed so no
    # "playback failed" handling or busy dialog lingers.
    try:
        xbmcplugin.setResolvedUrl(handle=int(sys.argv[1]), succeeded=False, listitem=xbmcgui.ListItem())
    except (IndexError, ValueError):
        pass

    # Digits sort at one end of the list: jump straight to that end. Letters
    # go through the SMS-jump action of their keypad group.
    if letter == NUMBER_SIGN or letter.isdigit():
        descending = xbmc.getInfoLabel('Container.SortOrder') == 'Descending'
        action = 'lastpage' if descending else 'firstpage'
    else:
        action = next((name for group, name in SMS_ACTIONS.items() if letter in group), None)
        if action is None:
            return

    # The action must reach the view, not the jump column that was clicked.
    # Each SMS press moves one letter further within the group, so repeat
    # until the focused item reports the wanted letter.
    xbmc.executebuiltin(f'SetFocus({VIEW_CONTROL_ID})')
    for _ in range(MAX_KEY_PRESSES):
        xbmc.executeJSONRPC(json.dumps({
            'jsonrpc': '2.0',
            'id': 1,
            'method': 'Input.ExecuteAction',
            'params': {'action': action},
        }))
        xbmc.sleep(50)
        if letter in ('0', xbmc.getInfoLabel('ListItem.SortLetter').upper()):
            break


if __name__ == '__main__':
    main()
