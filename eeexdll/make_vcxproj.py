# Derive EEex-PTEE.vcxproj from upstream EEex-v2.6.6.0.vcxproj (paths re-rooted on ref/).
import re, os
HERE = os.path.dirname(os.path.abspath(__file__))
s = open(os.path.join(HERE, r'..\ref\InfinityLoader\EEex-v2.6.6.0\EEex-v2.6.6.0.vcxproj'), encoding='utf-8-sig').read()
s = s.replace('{5D96A1B5-6B58-49D5-92C1-8164041DD87E}', '{7A41C3D2-5B9E-4C8F-A1D6-3E2B9F0C7D44}')
s = s.replace('<Import Project="$(VCTargetsPath)\\Microsoft.Cpp.Default.props" />',
              '<PropertyGroup Label="EEexPTEE"><ILROOT>$(MSBuildProjectDirectory)\\..\\ref\\InfinityLoader\\</ILROOT>'
              '<SolutionDir>$(ILROOT)</SolutionDir></PropertyGroup>\n  <Import Project="$(VCTargetsPath)\\Microsoft.Cpp.Default.props" />', 1)
s = s.replace('..\\User_Macros.props', '$(ILROOT)User_Macros.props')
s = s.replace('"..\\', '"$(ILROOT)')
s = s.replace('$(ProjectDir)headers/EEex-v2.6.6.0_generated', '$(ProjectDir)generated;$(ProjectDir)..\\bindings\\LuaBindings-PTEE\\stub')
s = s.replace('$(ProjectDir)headers\\EEex-v2.6.6.0_generated', '$(ProjectDir)generated;$(ProjectDir)..\\bindings\\LuaBindings-PTEE\\stub')
s = re.sub(r'source\\EEex-v2\.6\.6\.0\\[Gg]enerated\\', r'generated\\', s)
s = s.replace('EEex-v2.6.6.0.def', 'eeex-ptee.def')
s = re.sub(r'<OutDir>[^<]*</OutDir>', r'<OutDir>$(MSBuildProjectDirectory)\\..\\build\\EEex-PTEE\\</OutDir>', s)
s = re.sub(r'<IntDir>[^<]*</IntDir>', r'<IntDir>$(MSBuildProjectDirectory)\\..\\build\\EEex-PTEE\\obj\\</IntDir>', s)
s = re.sub(r'<PostBuildEvent>.*?</PostBuildEvent>', '', s, flags=re.S)
s = re.sub(r'\s*<ClInclude Include="headers[^"]*" />', '', s)
# Replaced by source/ptee_stubs.cpp: Uncap FPS (not ported yet) and engine_reimplementations / debug (never
# installed by EEex: no Lua patch jumps to them, all $nobinding). visibility_map.cpp is compiled as-is:
# Torment's vismap algorithm is BG's (AUDIT.md); patched copy (patch_sources.py).
s = re.sub(r'\s*<ClCompile Include="[^"]*\\(uncap_fps|engine_reimplementations|debug)\.cpp" />', '', s)
s = s.replace('<ClCompile Include="generated\\Baldur_generated_internal_pointers.cpp" />',
              '<ClCompile Include="generated\\Baldur_generated_internal_pointers.cpp" />\n    <ClCompile Include="source\\ptee_stubs.cpp" />'
              '\n    <ClCompile Include="source\\ptee_engine.cpp" />')
# Torment semantic patches (patch_sources.py): compile the patched copies instead of upstream
for _f in ('EEex.cpp', 'visibility_map.cpp'):
    s = s.replace(rf'<ClCompile Include="$(ILROOT)EEex-Core-Shared-Files\source\{_f}" />', rf'<ClCompile Include="generated\src\{_f}" />')
s = s.replace('<AdditionalIncludeDirectories>$(ProjectDir)generated;', r'<AdditionalIncludeDirectories>$(ProjectDir)generated;$(ProjectDir)source;$(ILROOT)EEex-Core-Shared-Files\source;')
open(os.path.join(HERE, 'EEex-PTEE.vcxproj'), 'w', encoding='utf-8').write(s)
print(re.findall(r'ClCompile Include="([^"]+)"', s)[-5:])
print(re.findall(r'<AdditionalIncludeDirectories>[^<]*', s)[:1])
print(re.findall(r'<AdditionalDependencies>[^<]*', s)[:1])
