# Derive LuaBindings-PSTEE.vcxproj from upstream LuaBindings-v2.6.6.0.vcxproj (paths re-rooted on ref/).
import re, os
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, r'..\..\ref\InfinityLoader\LuaBindings-v2.6.6.0\LuaBindings-v2.6.6.0.vcxproj'), encoding='utf-8-sig').read()
s = src
s = s.replace('{cb4abbed-dc69-4bb4-b62e-e92085d3c529}', '{5e1d2a6b-7c3f-4f0a-9d21-0a7f3b6c8e11}')
s = s.replace('<Import Project="$(VCTargetsPath)\\Microsoft.Cpp.Default.props" />',
              '<PropertyGroup Label="EEexPSTEE"><ILROOT>$(MSBuildProjectDirectory)\\..\\..\\ref\\InfinityLoader\\</ILROOT>'
              '<SolutionDir>$(ILROOT)</SolutionDir></PropertyGroup>\n  <Import Project="$(VCTargetsPath)\\Microsoft.Cpp.Default.props" />', 1)
s = s.replace('..\\User_Macros.props', '$(ILROOT)User_Macros.props')
s = s.replace('..\\LuaBindings-Core-Shared-Files', '$(ILROOT)LuaBindings-Core-Shared-Files')
s = s.replace('$(ProjectDir)headers/LuaBindings-v2.6.6.0_generated', '$(ProjectDir)..\\generated;$(ProjectDir)stub')
s = s.replace('source\\LuaBindings-v2.6.6.0\\generated\\', '..\\generated\\')
s = s.replace('lua_bindings-v2.6.6.0.def', 'lua_bindings-pstee.def')
s = re.sub(r'<OutDir>[^<]*</OutDir>', r'<OutDir>$(MSBuildProjectDirectory)\\..\\..\\build\\LuaBindings-PSTEE\\</OutDir>', s)
s = re.sub(r'<IntDir>[^<]*</IntDir>', r'<IntDir>$(MSBuildProjectDirectory)\\..\\..\\build\\LuaBindings-PSTEE\\obj\\</IntDir>', s)
s = re.sub(r'<PostBuildEvent>.*?</PostBuildEvent>', '', s, flags=re.S)
s = re.sub(r'\s*<ClInclude Include="headers[^"]*" />', '', s)
# BG engine reimplementations: replaced by source/pstee_overrides.cpp (Torment versions)
s = re.sub(r'\s*<ClCompile Include="[^"]*(engine_reimplementations)\.cpp" />', '', s)
# PSTEE copy of main.cpp (DLL name in messages)
s = s.replace(r'$(ILROOT)LuaBindings-Core-Shared-Files\source\main.cpp', r'source\main.cpp')
s = s.replace(r'<ClCompile Include="source\main.cpp" />', r'<ClCompile Include="source\main.cpp" />' + '\n    ' + r'<ClCompile Include="source\pstee_overrides.cpp" />')
open(os.path.join(HERE, 'LuaBindings-PSTEE.vcxproj'), 'w', encoding='utf-8').write(s)
print(re.findall(r'ClCompile Include="([^"]+)"', s))
print(re.findall(r'<AdditionalIncludeDirectories>[^<]*', s)[:1])
print(re.findall(r'<AdditionalDependencies>[^<]*', s)[:1])
