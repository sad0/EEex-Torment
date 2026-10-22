# uiItem layout in Torment.exe v3.2.2.0

Result: `tools/bindings/manual_fields_uiitem.json`. It uses the manual_fields.json format (`fields`, `sizes`,
`same_as_bg`). Nested offsets are relative to the nested struct. `"pt": "none"` means the BG member is absent in Torment.

- `uiItem`: BG 0x358 -> **PT 0x3b0**, `next` at +0x3a8.
- 134 entries:
  - 127 placements proven (47 uiItem-level entries incl. the 16 nested struct offsets + 80 nested members)
  - 7 BG members proven absent
  - 5 BG members left opaque (unproven, see below)
- 17 sizes (uiItem + 16 nested structs). 8 nested structs are identical to BG (`same_as_bg`).
- The 9 `uiItem` entries already in manual_fields.json (autoprove) are partly **wrong**. Replace them with this file:

  | field | manual_fields.json | correct |
  |---|---|---|
  | scrollbar | 0x180 | **0x198** |
  | slider | 0x1b8 | **0x1d0** |
  | movie | 0x218 | **0x220** |
  | rectangle | 0x2a0 | **0x2e8** (0x2a0 is map) |
  | action | 0x2f0 | **0x2f8** |
  | actionScroll | 0x318 | **0x320** |
  | tooltip | 0x320 | **0x328** |

  button 0x248 and edit 0x1e8 are right. The delta-0 votes were coincidences.

**Tooling note:** tools/bindings/bgtypes.py only knows `uiItem` (856 bytes). It does not parse the nested
`uiItem::*_t` structs. ptlayout.py's `same_as_bg` handling calls `T.structs[name]`, so merging the nested entries
into manual_fields.json as-is would raise a KeyError. The nested types must be added to bgtypes first, or flattened
to uiItem-absolute names (e.g. `text.font` = 0xa8).

## Proof sources

1. **Menu parser** `yy_reduce`, BG 0x3c40c0 / PT 0x4406a0. This is a lemon parser with a switch on the rule number
   (BG 0x9a cases, PT 0xad).
   - Keyword rules write the global item template (BG 0x7176b0 / PT 0x7b7e70).
   - `saveItem` (BG 0x3c2e00 / PT 0x43f3f0) copies that template into each new item.
   - Rule numbers follow the grammar order. BG and PT rules were paired by order and by code shape
     (strdup / variant / `=1` / int). Every pair was cross-checked with the dump.
2. **Typed accesses in fmap-paired functions.**
   - A small register/spill tracker marks item pointers. Sources: registers used with the `next` offset,
     `saveItem` results, `next`/template derefs, and item arguments propagated through call sites.
   - It lists every `[item+X]` access.
   - A BG field is supported when the BG function accesses the BG offset and its PT counterpart accesses the
     predicted PT offset.
   - Function pairs used:
     - drawItem BG 0x3d1210 / PT 0x44ea70
     - list helpers BG 0x3cbb20 / 0x3cc120 -> PT 0x448340 / 0x448990
     - retranslateMenus, uiCreateFromTemplate, startScrollBarCapture, startEditCapture, drawTooltipFromItem, and others
   - Every typed PT access lands either on a field of this layout or on one of the PT-only fields below.
     No unexplained offset is left.
3. **saveItem / uiCreateFromTemplate.**
   - Allocation size: 0x358 (BG) / 0x3b0 (PT).
   - Template copy and memsets. PT memsets: `[0,0xd0) [0xd8,0x15c) [0x160,0x200) [0x204,0x3b0)`.
   - The memsets skip 3 slots that get their own default: text.showhighlight (=0), list.showHighlight (=1),
     edit.cursor (=-1).
   - Writes of instance id, template name, menu and area.
4. **UI.MENU dump.** 1032 items dumped. 1016 matched to the UI.MENU source by order; all 1016 `area` values
   equal the dumped +0x40..+0x4c.
   - Method: for each offset, compare the set of items with a non-zero value against the set of items that use
     each keyword. Example: +0x1b0 is non-zero exactly for the 2 `scrollbar force 1` lists.
   - Lua refs are allocated in parse order. This puts actionEnter at +0x308 and actionExit at +0x30c.
     CHARGEN 8-10 use `actionenter`, `action`, `actionExit`, and their refs are ordered +0x308 < +0x2f8 < +0x30c.
   - `align left|right|center` gives +0x6c = 0|1|2, and `top|center` gives +0x70 = 0|2. So ha comes before va.

Proof rule applied: each recorded offset has aligned code in >= 2 functions, or aligned code + dump consistency.
Each `why` string in the JSON gives the rule pair (with case addresses), the aligned instructions and the dump fact.

## uiItem

| field | BG | PT | evidence (rule pair BG=PT, paired functions, dump) |
|---|---|---|---|
| type | 0x0 | 0x0 | yy_reduce rule 23..32=28..37; funcs: drawItem; dump |
| menu | 0x8 | 0x8 | funcs: initNameMap, sub_3c7b10, sub_3c9f10, uiClearTemplate; dump |
| name | 0x10 | 0x10 | yy_reduce rule 56=62; funcs: initNameMap, sub_3c92c0; dump |
| instanceId | 0x18 | 0x18 | funcs: sub_3c7b10, sub_3c9f10, drawItem, drawTooltipFromItem; dump |
| templateName | 0x20 | 0x20 | funcs: saveMenus, sub_3c7b10, sub_3c9f10, uiClearTemplate |
| areaSrc | 0x28 | 0x28 | yy_reduce rule 35=40; funcs: saveMenus, sub_3c9f10, drawItem, uiCreateFromTemplate; dump |
| area | 0x40 | 0x40 | yy_reduce rule 35=40; funcs: initBounding, saveMenus, sub_3c8f30, sub_3c9f10; dump |
| pad | 0x50 | 0x50 | yy_reduce rule 36=41; funcs: sub_3ce050, drawItem; dump |
| enabled | 0x60 | 0x60 | yy_reduce rule 80=92; funcs: sub_3ce050, sub_3d0a10, drawItem, lastItemUnderPoint; dump |
| ignoreEvents | 0x64 | 0x64 | yy_reduce rule 81=93; funcs: lastItemUnderPoint; dump |
| ha | 0x68 | 0x6c | yy_reduce rule 44=49; funcs: drawItem; dump |
| va | 0x6c | 0x70 | yy_reduce rule 44=49; funcs: drawItem; dump |
| alpha | 0x70 | 0x78 | yy_reduce rule 46=51; funcs: drawItem |
| fill | 0x78 | 0x80 | yy_reduce rule 138=150; funcs: drawItem; dump |
| useOverlayTint | 0x80 | 0x88 | yy_reduce rule 141=154; funcs: drawItem |
| overlayTint | 0x84 | 0x8c | yy_reduce rule 142=155; funcs: drawItem |
| text | 0x90 | 0x98 | yy_reduce rule 38=43; text_t members all +8 vs BG (see uiItem::text_t); dump |
| uiTemplate | 0xd0 | 0xe0 | yy_reduce rule 136=148; uiCreateFromTemplate BG 0x3d7d8d [rax+0xd0] / PT 0x456ba5 [rax+0xe0] (template item to cop; dump |
| bam | 0xd8 | 0xe8 | yy_reduce rule 55=61; bam_t starts with resref; dump |
| bmp | 0x110 | 0x110 | yy_reduce rule 127=139; bmp_t starts with resname; dump |
| list | 0x130 | 0x130 | yy_reduce rule 25=30; list item rule: lea rdx,[rbx+0x130] (table) and [rbx+0x150] = columns in both; dump |
| scrollbar | 0x180 | 0x198 | yy_reduce rule 90=103; scrollbar_t starts with bam (PT +0x198); dump |
| slider | 0x1b8 | 0x1d0 | yy_reduce rule 106=118; slider_t starts with position (PT +0x1d0); dump |
| edit | 0x1e0 | 0x1e8 | yy_reduce rule 95=108; edit_t starts with var (PT +0x1e8); dump |
| mosaic | 0x208 | 0x210 | yy_reduce rule 83=95; mosaic_t starts with resref (PT +0x210); dump |
| movie | 0x218 | 0x220 | movie_t starts with res: BG 0x3cb170 / PT 0x4479e0 (fdiff 1.00) [item+0x218] / [item+0x220 |
| button | 0x248 | 0x248 | yy_reduce rule 120=131; button_t starts with portrait (PT +0x248); dump |
| map | 0x298 | 0x2a0 | yy_reduce rule 130=142; map rules write 1/2 (BG +0x298, PT +0x2a0); dump |
| progressBar | 0x2a0 | 0x2a8 | yy_reduce rule 122=134; progressBar_t starts with percent (PT +0x2a8) |
| slot | 0x2b8 | 0x2c0 | yy_reduce rule 111=122; slot_t starts with icon (PT +0x2c0); dump |
| rectangle | 0x2e0 | 0x2e8 | yy_reduce rule 37=42; rectangle_t starts with number (PT +0x2e8); dump |
| action | 0x2f0 | 0x2f8 | yy_reduce rule 69=81; funcs: startDraggableCapture; dump |
| actionDbl | 0x2f4 | 0x2fc | yy_reduce rule 70=82; dump |
| actionAlt | 0x2f8 | 0x300 | yy_reduce rule 71=83; dump |
| actionDrag | 0x2fc | 0x304 | yy_reduce rule 72=84; funcs: sub_3cef60; dump |
| actionEnter | 0x300 | 0x308 | yy_reduce rule 73=85; dump |
| actionExit | 0x304 | 0x30c | yy_reduce rule 74=86; dump |
| actionUpdate | 0x308 | 0x310 | yy_reduce rule 75=87; list/scrollbar capture handler BG 0x3d0420 [rbx+0x308] / PT 0x44d360 [rdi+0x310] passed to |
| actionSimpleDrag | 0x30c | 0x314 | yy_reduce rule 76=88; dump |
| actionSimpleDrop | 0x310 | 0x318 | yy_reduce rule 77=89; funcs: sub_3d0a10; dump |
| actionHold | 0x314 | 0x31c | yy_reduce rule 78=90; dump |
| actionScroll | 0x318 | 0x320 | yy_reduce rule 79=91; eventMenu BG 0x3d52ee [rbx+0x318] / PT 0x452e5f [rbx+0x320] (Lua ref read on wheel events) |
| framesHeld | 0x31c | 0x324 | BG 0x3ceb50 / PT 0x44bad0 read-increment-write [item+0x31c]/[item+0x324] |
| tooltip | 0x320 | 0x328 | yy_reduce rule 63=72; tooltip_t starts with originalText (PT +0x328); dump |
| glow | 0x340 | 0x380 | yy_reduce rule 67=79; funcs: drawItem; dump |
| pulse | 0x348 | 0x388 | yy_reduce rule 68=80; funcs: drawItem; dump |
| next | 0x350 | 0x3a8 | funcs: initBounding, initNameMap, retranslateMenus, saveMenus; dump |

### uiItem::text_t (BG uiItem+0x90, PT uiItem+0x98)

| member | BG rel | PT rel | PT abs | evidence |
|---|---|---|---|---|
| originalText | 0x0 | 0x0 | 0x98 | yy_reduce rule 38=43; funcs: retranslateMenus; dump |
| text | 0x8 | 0x8 | 0xa0 | yy_reduce rule 38=43; funcs: retranslateMenus, sub_3ce050, drawItem, textHeight(BG 0x3d5870); dump |
| font | 0x10 | 0x10 | 0xa8 | yy_reduce rule 49=54; funcs: drawItem, textHeight(BG 0x3d5870); dump |
| point | 0x18 | 0x18 | 0xb0 | yy_reduce rule 47=52; funcs: drawItem, textHeight(BG 0x3d5870); dump |
| useFontZoom | 0x1c | 0x1c | 0xb4 | yy_reduce rule 48=53; funcs: drawItem, textHeight(BG 0x3d5870); dump |
| color | 0x20 | 0x20 | 0xb8 | yy_reduce rule 50=55; funcs: drawItem; dump |
| upper | 0x28 | 0x28 | 0xc0 | yy_reduce rule 51=56; funcs: drawItem |
| lower | 0x2c | 0x2c | 0xc4 | yy_reduce rule 52=57; funcs: drawItem |
| shadow | 0x30 | 0x30 | 0xc8 | yy_reduce rule 53=58; funcs: drawItem; dump |
| showhighlight | 0x38 | 0x38 | 0xd0 | yy_reduce rule 125=137; funcs: drawItem; dump |

### uiItem::uiTemplate_t (BG uiItem+0xd0, PT uiItem+0xe0)

| member | BG rel | PT rel | PT abs | evidence |
|---|---|---|---|---|
| item | 0x0 | 0x0 | 0xe0 | yy_reduce rule 136=148; uiCreateFromTemplate BG [rax+0xd0] / PT [rax+0xe0]; dump |

### uiItem::bam_t (BG uiItem+0xd8, PT uiItem+0xe8)

| member | BG rel | PT rel | PT abs | evidence |
|---|---|---|---|---|
| resref | 0x0 | 0x0 | 0xe8 | yy_reduce rule 55=61; funcs: sub_3c7ea0, sub_3cc120, drawItem; dump |
| sequence | 0x8 | 0x8 | 0xf0 | yy_reduce rule 58=64; funcs: sub_3c7ea0, sub_3cc120, drawItem; dump |
| frame | 0x18 | 0x10 | 0xf8 | yy_reduce rule 57=63; funcs: drawItem; dump |
| greyscale | 0x20 | 0x18 | 0x100 | yy_reduce rule 61=65; funcs: drawItem; dump |
| usealpha | 0x28 | 0x20 | 0x108 | yy_reduce rule 62=66; funcs: drawItem |
| sequenceonce | 0x10 | **absent** | - | keyword 'sequenceonce' absent from Torment.exe, no PT rule writes the template at BG +0xe8 equivalent |
| scaletoclip | 0x30 | **absent** | - | keyword 'scaleToClip' absent from Torment.exe, no PT rule |

### uiItem::bmp_t (BG uiItem+0x110, PT uiItem+0x110)

| member | BG rel | PT rel | PT abs | evidence |
|---|---|---|---|---|
| resname | 0x0 | 0x0 | 0x110 | yy_reduce rule 127=139; funcs: drawItem; dump |
| resref | 0x8 | 0x8 | 0x118 | yy_reduce rule 126=138; funcs: drawItem |
| area | 0x10 | 0x10 | 0x120 | yy_reduce rule 128=140; funcs: drawItem |

### uiItem::list_t (BG uiItem+0x130, PT uiItem+0x130)

| member | BG rel | PT rel | PT abs | evidence |
|---|---|---|---|---|
| table | 0x0 | 0x0 | 0x130 | yy_reduce rule 89=102; funcs: sub_3cbb20, sub_3cc120, drawItem; dump |
| rowheight | 0x8 | 0x8 | 0x138 | yy_reduce rule 85=98; funcs: sub_3cbb20, sub_3cc120; dump |
| rowwidth | 0xc | 0xc | 0x13c | yy_reduce rule 86=99; funcs: sub_3cbb20, sub_3cc120 |
| rowbackground | 0x10 | 0x10 | 0x140 | yy_reduce rule 88=101; BG 0x3ce050 [rsi+0x140] / PT 0x44a590 [rdi+0x140] (cmp 0 then load the variant) |
| dynamicHeight | 0x18 | 0x18 | 0x148 | yy_reduce rule 87=100; funcs: sub_3cbb20, sub_3cc120; dump |
| columns | 0x20 | 0x20 | 0x150 | yy_reduce rule 25=30; funcs: Infinity_RequestMultiplayerGameDetails, sub_3cbb20, sub_3cc120; dump |
| showHighlight | 0x2c | 0x2c | 0x15c | yy_reduce rule 110=121; saveItem default 1 kept out of the memset: BG [0x71780c] (=template+0x15c) / PT [0x7b7fcc]; dump |
| seperator | 0x30 | 0x30 | 0x160 | yy_reduce rule 140=153; dump |
| selected | 0x34 | 0x38 | 0x168 | funcs: sub_3cbb20, sub_3cc120, drawItem |
| color | 0x40 | 0x40 | 0x170 | yy_reduce rule 54=59; funcs: drawItem; dump |
| currentRow | 0x48 | 0x48 | 0x178 | funcs: sub_3cbb20, sub_3cc120, drawItem |

### uiItem::scrollbar_t (BG uiItem+0x180, PT uiItem+0x198)

| member | BG rel | PT rel | PT abs | evidence |
|---|---|---|---|---|
| bam | 0x0 | 0x0 | 0x198 | yy_reduce rule 90=103; funcs: drawItem; dump |
| function | 0x8 | 0x8 | 0x1a0 | yy_reduce rule 91=104; funcs: drawItem, scrollbarFunction; dump |
| hide | 0x10 | 0x10 | 0x1a8 | yy_reduce rule 94=105; funcs: drawItem; dump |
| top | 0x18 | 0x28 | 0x1c0 | funcs: sub_3cb6f0, Infinity_RequestMultiplayerGameDetails, sub_3cbb20, sub_3cc120 |
| held | 0x1c | 0x2c | 0x1c4 | funcs: drawItem |
| dragging | 0x20 | 0x30 | 0x1c8 | funcs: drawItem |
| contentHeight | 0x24 | 0x34 | 0x1cc | funcs: Infinity_RequestMultiplayerGameDetails, drawItem, scrollbarFunction |
| respectConstraints | 0x28 | **absent** | - | keyword 'respectConstraints' absent from Torment.exe |
| clunkyScroll | 0x2c | **absent** | - | keyword 'clunkyScroll' absent from Torment.exe |
| skipReset | 0x30 | **absent** | - | keyword 'skipReset' absent from Torment.exe |

### uiItem::slider_t (BG uiItem+0x1b8, PT uiItem+0x1d0)

| member | BG rel | PT rel | PT abs | evidence |
|---|---|---|---|---|
| position | 0x0 | 0x0 | 0x1d0 | yy_reduce rule 106=118; funcs: drawItem; dump |
| settings | 0x8 | 0x8 | 0x1d8 | yy_reduce rule 108=119; funcs: drawItem; dump |
| palette | 0x10 | 0x10 | 0x1e0 | yy_reduce rule 133=145; funcs: drawItem |
| background | 0x18 | **absent** | - | keyword 'sliderBackground' absent from Torment.exe |

### uiItem::edit_t (BG uiItem+0x1e0, PT uiItem+0x1e8)

| member | BG rel | PT rel | PT abs | evidence |
|---|---|---|---|---|
| var | 0x0 | 0x0 | 0x1e8 | yy_reduce rule 95=108; funcs: sub_3c7cd0, sub_3cbb20, sub_3cc120, drawItem; dump |
| maxlines | 0x8 | 0x8 | 0x1f0 | yy_reduce rule 96=109; dump |
| maxchars | 0xc | 0xc | 0x1f4 | yy_reduce rule 97=110; dump |
| placeholder | 0x10 | 0x10 | 0x1f8 | yy_reduce rule 139=151; funcs: drawItem; dump |
| cursor | 0x18 | 0x18 | 0x200 | funcs: drawItem; dump |
| selectStart | 0x1c | 0x1c | 0x204 | funcs: drawItem |
| selectEnd | 0x20 | 0x20 | 0x208 | funcs: drawItem |

### uiItem::mosaic_t (BG uiItem+0x208, PT uiItem+0x210)

| member | BG rel | PT rel | PT abs | evidence |
|---|---|---|---|---|
| resref | 0x0 | 0x0 | 0x210 | yy_reduce rule 83=95; funcs: drawItem; dump |

### uiItem::movie_t (BG uiItem+0x218, PT uiItem+0x220)

| member | BG rel | PT rel | PT abs | evidence |
|---|---|---|---|---|
| res | 0x0 | 0x0 | 0x220 | funcs: drawItem |
| subtitle | 0x8 | 0x8 | 0x228 | yy_reduce rule 102=115; funcs: drawItem |
| transparent | 0x18 | 0x18 | 0x238 | yy_reduce rule 103=116; BG 0x3cb170 / PT 0x4479e0 (fdiff 1.00) mov edx,[rbx+0x230] / [rbx+0x238] |
| background | 0x1c | 0x1c | 0x23c | yy_reduce rule 82=94; funcs: drawItem |
| loop | 0x20 | 0x20 | 0x240 | yy_reduce rule 104=117; rule stores 1; dump |
| queuedMovie | 0x28 | **absent** | - | keyword 'queuedMovie' absent from Torment.exe |

### uiItem::button_t (BG uiItem+0x248, PT uiItem+0x248)

| member | BG rel | PT rel | PT abs | evidence |
|---|---|---|---|---|
| portrait | 0x0 | 0x0 | 0x248 | yy_reduce rule 120=131; funcs: sub_3cef60, drawItem; dump |
| paperdoll | 0x8 | 0x10 | 0x258 | yy_reduce rule 121=133; funcs: sub_3cef60, drawItem; dump |
| encumbrance | 0x10 | 0x18 | 0x260 | yy_reduce rule 129=141; funcs: drawItem |
| colorDisplay | 0x14 | 0x1c | 0x264 | yy_reduce rule 134=146; funcs: drawItem |
| frameTimes | 0x18 | 0x20 | 0x268 | yy_reduce rule 135=147; funcs: drawItem; dump |
| toggle | 0x20 | 0x28 | 0x270 | yy_reduce rule 98=111; funcs: drawItem; dump |
| on | 0x28 | 0x30 | 0x278 | yy_reduce rule 100=113; string rule in both; dump |
| highlightGroup | 0x30 | 0x38 | 0x280 | yy_reduce rule 109=120; funcs: drawItem; dump |
| clickable | 0x38 | 0x40 | 0x288 | yy_reduce rule 101=114; funcs: drawItem; dump |
| actionBar | 0x40 | 0x48 | 0x290 | yy_reduce rule 137=149; funcs: drawItem; dump |
| sound | 0x48 | 0x50 | 0x298 | yy_reduce rule 99=112; string rule in both; dump |

### uiItem::map_t (BG uiItem+0x298, PT uiItem+0x2a0)

| member | BG rel | PT rel | PT abs | evidence |
|---|---|---|---|---|
| type | 0x0 | 0x0 | 0x2a0 | yy_reduce rule 130=142; funcs: drawItem; dump |

### uiItem::progressBar_t (BG uiItem+0x2a0, PT uiItem+0x2a8)

| member | BG rel | PT rel | PT abs | evidence |
|---|---|---|---|---|
| percent | 0x0 | 0x0 | 0x2a8 | yy_reduce rule 122=134; funcs: drawItem |
| color | 0x8 | 0x8 | 0x2b0 | yy_reduce rule 123=135; funcs: drawItem |
| fullColor | 0x10 | 0x10 | 0x2b8 | yy_reduce rule 124=136; funcs: drawItem |

### uiItem::slot_t (BG uiItem+0x2b8, PT uiItem+0x2c0)

| member | BG rel | PT rel | PT abs | evidence |
|---|---|---|---|---|
| icon | 0x0 | 0x0 | 0x2c0 | yy_reduce rule 111=122; funcs: sub_3c7ea0, drawItem; dump |
| count | 0x8 | 0x8 | 0x2c8 | yy_reduce rule 112=123; funcs: drawItem; dump |
| usages | 0x10 | 0x10 | 0x2d0 | yy_reduce rule 113=124; funcs: drawItem; dump |
| highlight | 0x18 | 0x18 | 0x2d8 | yy_reduce rule 114=125; funcs: drawItem; dump |
| tint | 0x20 | 0x20 | 0x2e0 | yy_reduce rule 115=126; funcs: drawItem; dump |

### uiItem::rectangle_t (BG uiItem+0x2e0, PT uiItem+0x2e8)

| member | BG rel | PT rel | PT abs | evidence |
|---|---|---|---|---|
| number | 0x0 | 0x0 | 0x2e8 | yy_reduce rule 37=42; funcs: drawItem; dump |
| opacity | 0x8 | 0x8 | 0x2f0 | yy_reduce rule 132=144; funcs: drawItem |

### uiItem::tooltip_t (BG uiItem+0x320, PT uiItem+0x328)

| member | BG rel | PT rel | PT abs | evidence |
|---|---|---|---|---|
| originalText | 0x0 | 0x0 | 0x328 | yy_reduce PT rule 72; funcs: retranslateMenus; dump |
| text | 0x8 | 0x8 | 0x330 | yy_reduce rule 63=73; funcs: retranslateMenus, drawItem, drawTooltipFromItem; dump |
| force | 0x10 | 0x10 | 0x338 | yy_reduce rule 64=74; funcs: drawItem; dump |
| position | 0x18 | 0x28 | 0x350 | yy_reduce rule 66=76; funcs: drawTooltipFromItem |
| forceTop | 0x1c | 0x2c | 0x354 | yy_reduce rule 65=75; funcs: drawItem |


## Nested struct sizes (PT)

| struct | BG | PT | note |
|---|---|---|---|
| text_t | 0x40 | 0x40 | identical; uiItem+0xd8 (PT-only, see below) kept as uiItem padding (binary-identical either way) |
| uiTemplate_t | 0x8 | 0x8 | identical |
| bam_t | 0x38 | 0x28 | sequenceonce, scaletoclip removed; frame/greyscale/usealpha move up |
| bmp_t | 0x20 | 0x20 | identical, same uiItem offset 0x110 |
| list_t | 0x50 | 0x50 | noBorder (PT) takes the BG padding slot +0x34; selected +0x38 |
| scrollbar_t | 0x38 | 0x38 | force/speed (PT) inserted at +0x18/+0x20; 3 BG ints removed |
| slider_t | 0x28 | 0x18 | background removed; right unknown |
| edit_t | 0x28 | 0x28 | identical |
| mosaic_t | 0x10 | 0x10 | |
| movie_t | 0x30 | 0x28 | queuedMovie removed |
| button_t | 0x50 | 0x58 | healthbar (PT) inserted at +0x8 |
| map_t | 0x4 | 0x4 | identical |
| progressBar_t | 0x18 | 0x18 | identical |
| slot_t | 0x28 | 0x28 | identical |
| rectangle_t | 0x10 | 0x10 | identical |
| tooltip_t | 0x20 | 0x30 | constrainTo/target (PT) inserted at +0x18/+0x20 |
| uiItem | 0x358 | 0x3b0 | |

Each size is closed by the next proven member (see `sizes` in the JSON).

## PT-only fields (not in the BG header: opaque padding unless named later)

| PT offset | type | what | evidence |
|---|---|---|---|
| uiItem+0x68 | int | `highlight selected N` | PT rule 97 (`[rax+0x14]` int). Dump: =1 exactly for the 84 items with `highlight selected 1`. drawItem 0x44f30b / 0x450ced |
| uiItem+0x74 | - | padding (alpha aligned to 0x78) | never accessed |
| uiItem+0xd8 | uiVariant* | probably `indent` (text) | PT rule 156. Grammar position: after overlayTint, before noBorder/ignoreFocus, which matches the lexer keyword order (indent, noBorder, ..., ignoreFocus). Read by drawItem 0x45051c / 0x4508c1 and by the text-height routine 0x45432b, next to font/point. Only used inside a list column item (UI.MENU line 4682), so absent from the dump |
| list_t+0x34 (uiItem+0x164) | int | `noBorder` | PT rule 157 stores 1. Dump: =1 exactly for the 5 `noBorder` lists. drawItem 0x450b5c |
| uiItem+0x180 | uiVariant* | `focus` | PT rule 60. Dump: non-null exactly for the 42 `focus` items. These are lists and texts, so it is not a list_t member. drawItem 0x45034a / 0x4503a7 |
| uiItem+0x188, +0x18c, +0x190 | int x3 | focus / controller navigation state (runtime) | No parser rule. +0x188/+0x18c are read next to focus in drawItem (0x450340 / 0x45035d). +0x18c/+0x190 are written by eventMenu PT 0x4525f0, PT 0x44b120, controller navigation PT 0x459ff0 (sets +0x190 = -1) and Infinity_PlaySound PT 0x447be8 (sets +0x18c = -1) |
| uiItem+0x194 | - | padding | never accessed |
| scrollbar_t+0x18 (uiItem+0x1b0) | uiVariant* | `scrollbar force` | PT rule 106. Dump: exactly the 2 `scrollbar force 1` lists. drawItem 0x450db5 |
| scrollbar_t+0x20 (uiItem+0x1b8) | uiVariant* | `scrollbar speed` | PT rule 107. Dump: exactly the 2 `scrollbar speed 3` lists. drawItem 0x451235, PT 0x448299 |
| slider_t+0x14 (uiItem+0x1e4) | 4 bytes | unknown (BG `right` candidate) | never accessed in either exe |
| button_t+0x8 (uiItem+0x250) | uiVariant* | `healthbar` | PT rule 132. Dump: exactly the 12 `healthbar` buttons. drawItem 0x44fa98 / 0x44fab6 |
| tooltip_t+0x18 (uiItem+0x340) | char* / token | probably `tooltip constrainTo` | PT rule 77. Only used by the AREA_MAP note template, which is not dumped. drawItem 0x4514ad, drawTooltipFromItem 0x451e55 / 0x451e8e |
| tooltip_t+0x20 (uiItem+0x348) | char* / token | `tooltip target` | PT rule 78. Dump: exactly the 6 START_MAIN buttons with `tooltip target`. drawItem 0x45145b |
| uiItem+0x358..+0x378 | const char* x5 | nav item names (`navUp`, `navDown`, `navLeft`, `navRight`, `navA`) | PT rules 67-71 (tokenToString). Dump: `navup` at +0x368, `navdown` at +0x370 (ESC_MENU). The other 3 are not placed |
| uiItem+0x390 | uiVariant* | `ignoreFocus` | PT rule 158. Dump: exactly the 52 `ignoreFocus` items |
| uiItem+0x398 | point* | `boundingPoints` polygon | Dump: exactly the 14 `boundingPoints` buttons. PT 0x44bf80 / 0x44dde0 / drawItem pass it with the count to the point-in-polygon test 0x4acef0. PT rule 162 appends points |
| uiItem+0x3a0 | uint16 (+pad) | boundingPoints count | Dump: 7..10, the number of points in the source |

## BG fields absent in Torment (`"pt": "none"`)

These 7 BG members are absent. For each one, the keyword string is missing from Torment.exe, its BG parser rule
has no PT counterpart, and the PT struct has no room for it:
- `bam.sequenceonce`
- `bam.scaletoclip`
- `scrollbar.respectConstraints`
- `scrollbar.clunkyScroll`
- `scrollbar.skipReset`
- `slider.background` (keyword `sliderBackground`)
- `movie.queuedMovie`

**EEex Lua impact:** `EEex_Options.lua` lines 4619 and 4628 set `bam.scaletoclip = 1`. The Torment port must
drop or guard them. All other uiItem fields used by EEex Lua are proven: type, menu, name, instanceId,
templateName, area, pad, ha, va, next, text.text, text.point, bam.resref, list.table/rowheight/columns,
button.portrait, uiTemplate.item.

## Left opaque (unproven)

| BG field | BG off | PT candidate | why not proven |
|---|---|---|---|
| list.printrow | 0x134 | uiItem+0x134 (list+4) | no access in either exe's UI code; closed span table..rowheight (gap 8 = 8) |
| list.category | 0x158 | uiItem+0x158 (list+0x28) | no access in either exe; closed span columns..showHighlight (gap 0xc = 0xc) |
| list.height | 0x168 | uiItem+0x16c (list+0x3c) | no access in either exe; not a closed span (noBorder changes the gap) |
| slider.right | 0x1d8 | uiItem+0x1e4 (slider+0x14) | no access in either exe |
| mosaic.respectClipping | 0x210 | uiItem+0x218 (mosaic+8) | only PT rule 96 (stores 1) + closed span. BG drawItem reads it, Torment never does. It is only used by list-column items, which are not dumped |

The first four look dead in both engines: a raw scan of every function in BG 0x3c0000-0x3e0000 and
PT 0x43c000-0x45c000 finds no access. printrow and category qualify as closed spans for coverage.py if wanted.

## Optional runtime probe

This probe would only add dump confirmation; the proofs above do not need it.
Extend PSTEE_UIProbe.lua to also dump these items, in the same 118-qword format with the tag `PSTEE-UIPROBE-SUB`:
1. **List column items.** For each list item, follow `list.columns` (uiItem+0x150, a uiColumn* array whose
   layout was proven in phase 5b) and dump each column's uiItem chain. Expected:
   - `respectClipping` cells (store menus, UI.MENU lines 6429, 6509, 6597...) -> dword +0x218 = 1
   - `rectangle opacity 150` cells -> qword +0x2f0 != 0
   - the `indent 1` cell of `worldPlayerDialogChoicesList` (line 4682) -> qword +0xd8 != 0
2. **Template inner items**, via uiTemplate.item (qword +0xe0 of the type-0xb items). Expected:
   - TEMPLATE_mageMemorizationSparkle (`usealpha lua`) -> +0x108 != 0
   - TEMPLATE_mapnote (`tooltip constrainTo`) -> +0x340 != 0
3. **One list item after a slider drag / scrollbar use.** Expected: non-zero scrollbar.top (+0x1c0) and
   list.selected (+0x168).

## Working scripts (scratchpad, not in the repo)

All in `scratchpad/uii/`:
- `cases.py`, `tcases.py`, `ruledp.py`: yy_reduce rule extraction and BG/PT pairing
- `typed.py`, `runtyped.py`, `cmp.py`, `evid.py`: typed item-access tracker over paired functions
- `menu.py`, `match.py`, `corr.py`: UI.MENU parser and dump correlation
- `gen.py`: writes the JSON
