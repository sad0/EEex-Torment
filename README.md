# EEex-PTEE

Port of EEex (Bubb13) to Planescape: Torment Enhanced Edition.

- ref/ : upstream EEex and InfinityLoader clones (reference, not committed)
- ghidra/ : local Ghidra project (not committed)

- installer/ : WeiDU installer sources (EEex.tp2, same name / labels as upstream; English + French tra; readme)
- tools/package.py : release package -> build/release/ (setup-EEex.exe + EEex/) and build/EEex-PTEE-<ver>.zip
  (run `sh tools/rebuild_all.sh` first). tools/weidu/weidu.exe is WeiDU v251.
