-- EEex-PSTEE dev probe (not shipped): raw memory of the uiItems of a few menus, to place Torment's uiItem
-- members against the UI.MENU source (tools/uiprobe.py reads the dump from EEex_PSTEE.log).
local function dumpMenu(name)
	local menu = EEex_Menu_Find(name)
	if menu == nil then print("PSTEE-UIPROBE: no menu " .. name) return end
	local item = menu.items
	local k = 0
	while item ~= nil do
		local p = EEex_UDToPtr(item)
		local q = {}
		for o = 0, 0x3a8, 8 do
			q[#q + 1] = string.format("%08X%08X", EEex_ReadU32(p + o + 4), EEex_ReadU32(p + o))
		end
		print(string.format("PSTEE-UIPROBE: %s %d %X %s", name, k, p, table.concat(q, " ")))
		item = item.next
		k = k + 1
	end
end

EEex_Menu_AddAfterMainFileLoadedListener(function()
	local menus = EngineGlobals.menus
	for i = 0, EngineGlobals.numMenus - 1 do
		local menu = menus:getReference(i)
		local ok, err = pcall(dumpMenu, menu.name:get())
		if not ok then print("PSTEE-UIPROBE: error " .. tostring(err)) end
	end
end)
