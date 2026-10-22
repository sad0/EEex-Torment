# Send one key to the Torment window with PostMessage (WM_KEYDOWN / WM_KEYUP): no focus change, no mouse,
# nothing reaches any other window. SDL reads the scancode from lParam.
#   python tools/gamekey.py F8
import ctypes, ctypes.wintypes as W, sys, time
user32 = ctypes.WinDLL('user32', use_last_error=True)
VK = {f'F{i}': 0x6f + i for i in range(1, 13)}
VK.update({'ESCAPE': 0x1b, 'RETURN': 0x0d, 'SPACE': 0x20})
WM_KEYDOWN, WM_KEYUP = 0x100, 0x101


def find_window():
    found = []
    proto = ctypes.WINFUNCTYPE(W.BOOL, W.HWND, W.LPARAM)

    def cb(h, _):
        buf = ctypes.create_unicode_buffer(256)
        user32.GetWindowTextW(h, buf, 256)
        if buf.value.startswith('Planescape Torment - Enhanced Edition'):
            found.append(h)
        return True
    user32.EnumWindows(proto(cb), 0)
    return found


def main():
    name = sys.argv[1].upper()
    vk = VK[name]
    wins = find_window()
    if len(wins) != 1:
        sys.exit(f'expected one Torment window, found {len(wins)}')
    h = wins[0]
    scan = user32.MapVirtualKeyW(vk, 0)
    down = 1 | (scan << 16)
    up = down | (1 << 30) | (1 << 31)
    user32.PostMessageW(h, WM_KEYDOWN, vk, down)
    time.sleep(0.05)
    user32.PostMessageW(h, WM_KEYUP, vk, up)
    print('sent', name, 'to window', hex(h))


if __name__ == '__main__':
    main()
