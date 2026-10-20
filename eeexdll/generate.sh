#!/bin/sh
# Generate EEex.dll headers/bindings for Torment.exe v3.2.2.0 from bindings/in/Torment-v3.2.2.0.h.
cd "$(dirname "$0")/generated" || exit 1
R="../../ref/InfinityLoader"; C="$R/Core-Shared-Files/generate_bindings/in"; L="$R/Core-Shared-Files/generate_bindings/in_lua"
P="../../bindings/in"
python "$R/scripts/generate_bindings/generate_bindings_main.py" -mode=GenerateHeader \
 -abstractTypesFile="$C/abstract_types.txt" -aliasFiles="$C/alias_v2.6.txt" \
 -alreadyDefinedUsertypesFile="$C/already_defined_usertypes.txt" \
 -bindingsOutFile=./EEexLua_generated.cpp -bindingsPreludeFile="$C/bindings_prelude.txt" \
 -dllName=EEex.dll -fixupFile="$P/fixup_pt.py" -ignoreHeaderFile="$C/ignore_header_types.txt" \
 "-inFiles=NO_BINDINGS;NO_HARDCODED_BINDINGS:$C/manual_types.txt,NO_BINDINGS;NO_HARDCODED_BINDINGS:$C/manual_reimplementations_import.txt,NO_BINDINGS;NO_HARDCODED_BINDINGS:${HDR:-$P}/Torment-v3.2.2.0.h,$C/bindings.txt" \
 -outFile=./Baldur_generated.h -packingFile="$P/packing_pt.txt" -preludeFile="$C/prelude_eeex.txt" \
 -printFuncWideString=FPrintT -suffixFile="$C/suffix_eeex.txt" \
 -wantedFiles="$P/wanted_types_pt.txt,$C/wanted_types_eeex.txt" > gen.log 2>&1
echo "generator exit $?"
python "$R/scripts/generate_bindings/generate_bindings_main.py" -mode=GenerateHeader \
 -ignoreHeaderFile="$L/ignore_header_types.txt" -inFiles="$L/manual_types.txt,${HDR:-$P}/Torment-v3.2.2.0.h" -noCustomTypes \
 -outFile=./Baldur_lua_generated.h -packingFile="$P/packing_pt.txt" -preludeFile="$L/prelude.txt" \
 -wantedFiles="$L/wanted_types.txt" > gen_lua.log 2>&1
echo "lua generator exit $?"
