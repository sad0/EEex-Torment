-- EEex-PTEE dev helper: skip the startup movies (LOGO chain + OPENING) on launch.
-- CScreenStart::TimerAsynchronousUpdate plays them on its first tick; jump over that block.
-- Labels come from EEex_scripts/extra_pattern_dbs/ptee.db (tools/port_extra.py).

(function()
	EEex_DisableCodeProtection()
	EEex_JITAt(EEex_Label("Hook-CScreenStart::TimerAsynchronousUpdate()-StartupMovies"), {
		"jmp #$(1) #ENDL", {EEex_Label("Hook-CScreenStart::TimerAsynchronousUpdate()-AfterStartupMovies")}
	})
	EEex_EnableCodeProtection()
end)()
