# EEex_GameState_Patch.lua: no change needed.
# - SDL_main LuaInit (PT 0x144eb7 call CLUAConsole::LuaInit PT 0x226220, fmap sig): after-call, no register read.
# - CInfGame::DestroyGame LastCall (PT 0x2d861d call __security_check_cookie, function PT 0x2d7600): after-call, no
#   register read, epilogue follows (same as BG).
# - CInfGame::Unmarshal AfterGlobalVariablesUnmarshalled (PT 0x2fa574): before the call to PT 0x2de900 (BG 0x2799e0,
#   fmap sig, same prologue: reads rcx only), right after the global-variable loop (PT 0x2fa55f CVariableHash add).
#   The hook keeps rcx (Torment loads it from rsi instead of r15, irrelevant).
# - dimmInit uiDoFile("includes") (PT 0x48bb8a, string at PT 0x65c488 = "includes", callee PT 0x456d60 = uiDoFile,
#   reads rcx only). After the call Torment only destroys a CString and returns 1 (rax rewritten).
# - CChitin::ShutDown first instruction (PT 0x4a5fd0): push rsi / push r14 / push r15 = 6 bytes as in BG, the four
#   argument registers are saved / restored.
PATCHES = []
