# Minimal Torment.exe window control for in-game tests (ctypes only).
#   python gamectl.py shot <out.png>        capture the game window client area
#   python gamectl.py click <x> <y>         left click at client coordinates (as in the shot)
#   python gamectl.py key <vk>              press a virtual key (e.g. 0x0D Enter, 0x1B Esc)
#   python gamectl.py type <text>           type text
import sys, time, ctypes
from ctypes import wintypes
from PIL import ImageGrab

user32 = ctypes.WinDLL('user32', use_last_error=True)
user32.SetProcessDPIAware()


def find_window():
    found = []
    EnumProc = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)

    def cb(h, _):
        n = user32.GetWindowTextLengthW(h)
        if n and user32.IsWindowVisible(h):
            b = ctypes.create_unicode_buffer(n + 1)
            user32.GetWindowTextW(h, b, n + 1)
            if b.value.startswith('Planescape Torment - Enhanced Edition'):
                found.append(h)
        return True
    user32.EnumWindows(EnumProc(cb), 0)
    if not found:
        sys.exit('game window not found')
    return found[0]


def client_rect(h):
    r = wintypes.RECT(); user32.GetClientRect(h, ctypes.byref(r))
    p = wintypes.POINT(0, 0); user32.ClientToScreen(h, ctypes.byref(p))
    return p.x, p.y, r.right, r.bottom


def focus(h):
    user32.ShowWindow(h, 9)
    user32.SetForegroundWindow(h)
    time.sleep(0.3)


class MOUSEINPUT(ctypes.Structure):
    _fields_ = [('dx', wintypes.LONG), ('dy', wintypes.LONG), ('mouseData', wintypes.DWORD), ('dwFlags', wintypes.DWORD),
                ('time', wintypes.DWORD), ('dwExtraInfo', ctypes.c_size_t)]


class KEYBDINPUT(ctypes.Structure):
    _fields_ = [('wVk', wintypes.WORD), ('wScan', wintypes.WORD), ('dwFlags', wintypes.DWORD), ('time', wintypes.DWORD),
                ('dwExtraInfo', ctypes.c_size_t)]


class INPUT(ctypes.Structure):
    class _U(ctypes.Union):
        _fields_ = [('mi', MOUSEINPUT), ('ki', KEYBDINPUT), ('pad', ctypes.c_byte * 32)]
    _anonymous_ = ('u',)
    _fields_ = [('type', wintypes.DWORD), ('u', _U)]


def send(*inputs):
    arr = (INPUT * len(inputs))(*inputs)
    user32.SendInput(len(inputs), arr, ctypes.sizeof(INPUT))


def mouse(flags):
    i = INPUT(); i.type = 0; i.mi = MOUSEINPUT(0, 0, 0, flags, 0, 0); return i


def key(vk, up=False):
    i = INPUT(); i.type = 1; i.ki = KEYBDINPUT(vk, 0, 2 if up else 0, 0, 0); return i


def unicode_key(ch, up=False):
    i = INPUT(); i.type = 1; i.ki = KEYBDINPUT(0, ord(ch), 4 | (2 if up else 0), 0, 0); return i


if __name__ == '__main__':
    h = find_window()
    x0, y0, w, hgt = client_rect(h)
    cmd = sys.argv[1]
    if cmd == 'shot':
        focus(h)
        ImageGrab.grab(bbox=(x0, y0, x0 + w, y0 + hgt), all_screens=True).save(sys.argv[2])
        print('client', w, hgt)
    elif cmd == 'click':
        focus(h)
        x, y = int(sys.argv[2]), int(sys.argv[3])
        user32.SetCursorPos(x0 + x, y0 + y); time.sleep(0.15)
        send(mouse(0x0002)); time.sleep(0.08); send(mouse(0x0004))
        print('clicked', x, y)
    elif cmd == 'key':
        focus(h)
        vk = int(sys.argv[2], 0)
        send(key(vk)); time.sleep(0.05); send(key(vk, True))
    elif cmd == 'type':
        focus(h)
        for ch in sys.argv[2]:
            send(unicode_key(ch)); send(unicode_key(ch, True)); time.sleep(0.02)
