# EEex_Profiler_Patch.lua (Torment review)

No label use; no patch. It only calls EEex.WriteProfilerHooks() when EEex_Profiler_ForceTracePatches = true
(EEex_Profiler.lua, default false).

## BG-only data
WriteProfilerHooks reads `EEex_scripts/profiler/profiler.db`: absolute entry points, restore asm and expected
bytes for one game build (ref/EEex/EEex/loader/<ver>/<game>/profiler.db). No Torment profiler.db exists (the dev
install has only profiler/function_names.db). With the option on, EEex.dll logs "Error opening profiler.db" and
returns, which is safe. A BG profiler.db must never be installed for Torment: its entries that start with E9 / FF25
skip the expected-byte check (EEex_HookAttemptProfile) and would patch random Torment code.

## Open question
If tracing is wanted, generate a Torment profiler.db (function starts from .pdata / function_names.db).
