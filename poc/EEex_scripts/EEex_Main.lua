-- EEex-PTEE proof of concept: confirms InfinityLoader can inject into Torment.exe and run Lua.
print("EEex-PTEE POC: EEex_Main.lua is running inside Torment.exe")
local globalsOk = {}
for k, v in pairs(_G) do
	if type(k) == "string" and k:sub(1, 5) == "EEex_" then globalsOk[#globalsOk + 1] = k end
end
table.sort(globalsOk)
print("EEex-PTEE POC: loader globals = " .. table.concat(globalsOk, ", "))
