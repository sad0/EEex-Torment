#!/bin/sh
# Rebuild everything after a layout / proof / patch change: Torment layout -> coverage -> header -> LuaBindings and
# EEex.dll sources -> MSBuild (both DLLs) -> EEex Lua port; --deploy copies DLLs, pattern DBs and Lua to the dev game.
#   sh tools/rebuild_all.sh [--deploy]
set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
MSB="/c/Program Files/Microsoft Visual Studio/18/Community/MSBuild/Current/Bin/amd64/MSBuild.exe"
G="/e/Enhanced Edition/Environnement de test/PSTEE (EEex dev)"
cd "$ROOT/tools/bindings"
python ptlayout.py | head -1
python coverage.py | tail -2
python ptheader.py | tail -2
sh ../../bindings/generate.sh
sh ../../eeexdll/generate.sh
cd "$ROOT/eeexdll" && python patch_sources.py > /dev/null && python make_vcxproj.py > /dev/null
"$MSB" EEex-PSTEE.vcxproj -p:Configuration=Release -p:Platform=x64 -m -nodeReuse:false -v:m > ../build/eeex_build.log 2>&1 || { echo "EEex.dll build FAILED"; python ../tools/buildlog.py ../build/eeex_build.log; exit 1; }
echo "EEex.dll ok"
cd "$ROOT"
MSYS_NO_PATHCONV=1 "$MSB" bindings/LuaBindings-PSTEE/LuaBindings-PSTEE.vcxproj -p:Configuration=Release -p:Platform=x64 -m -nodeReuse:false -v:m > build/lua_build.log 2>&1 || { echo "LuaBindings.dll build FAILED"; python tools/buildlog.py build/lua_build.log; exit 1; }
echo "LuaBindings.dll ok"
cd "$ROOT/eeexlua" && python build.py > /dev/null && echo "Lua port ok"
if [ "$1" = "--deploy" ]; then
	cd "$ROOT/tools" && python deploy.py
	cd "$ROOT"
	cp build/EEex-PSTEE/EEex.dll build/LuaBindings-PSTEE/LuaBindings.dll "$G/"
	cp poc/extra_pattern_dbs/pstee.db "$G/EEex_scripts/extra_pattern_dbs/"
	echo "deployed DLLs + DBs"
fi
