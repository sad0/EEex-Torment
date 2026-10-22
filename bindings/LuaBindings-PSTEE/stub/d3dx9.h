#pragma once
// Minimal stand-in for the DirectX SDK (June 2010) d3dx9.h: only the type names the bindings mention.
#include <d3d9.h>
struct _D3DXMACRO { const char* Name; const char* Definition; };
struct ID3DXBuffer : IUnknown {};
struct ID3DXInclude {};
struct ID3DXEffectPool : IUnknown {};
struct ID3DXBaseEffect : IUnknown {};
struct ID3DXEffect : ID3DXBaseEffect {};
