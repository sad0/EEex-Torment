#!/bin/sh
# Generate LuaBindings sources for Torment.exe v3.2.2.0 from bindings/in/Torment-v3.2.2.0.h.
cd "$(dirname "$0")/generated" || exit 1
R="../../ref/InfinityLoader"; C="$R/Core-Shared-Files/generate_bindings/in"
python "$R/scripts/generate_bindings/generate_bindings_main.py" -mode=GenerateHeader \
 -abstractTypesFile="$C/abstract_types.txt" -aliasFiles="$C/alias_v2.6.txt" \
 -alreadyDefinedUsertypesFile="$C/already_defined_usertypes.txt" \
 -bindingsOutFile=./EEexLua_generated.cpp -bindingsPreludeFile="$C/bindings_prelude.txt" \
 -dllName=LuaBindings.dll -fixupFile=../in/fixup_pt.py -ignoreHeaderFile="$C/ignore_header_types.txt" \
 -inFiles="$C/manual_types.txt,$C/manual_reimplementations_export.txt,$C/engine_lua_wrappers.txt,../in/Torment-v3.2.2.0.h" \
 -outFile=./Baldur_generated.h -packingFile=../in/packing_pt.txt -preludeFile="$C/prelude_luabindings.txt" \
 -printFuncWideString=FPrintT -wantedFiles="$C/wanted_types.txt" > gen.log 2>&1
echo "generator exit $?"
