# B3EmptyContainer.lua: reviewed, no change needed.
# Hook-CGameContainer::Render()-B3EmptyContainer (PT 0x1aaed5, BG 0x194deb): same outline call (PT 0x305e50) with
# the container in r14 (PT 0x1aaeb8 mov rdx, [r14+0x548]; 0x1aaece lea r9, [r14+0x538]) and the color as the 5th
# argument at [rsp+0x20] (PT 0x1aaeb4 mov [rsp+0x20], eax; same 0xff00 / 0xffff00 values as BG). rcx / rdx / r8 / r9
# are saved and restored by the hook.
PATCHES = []
