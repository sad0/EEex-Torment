# EEex_GameObject.lua (Torment): label uses

| Label | Verdict | Evidence |
|---|---|---|
| `CGameChunk::VFTable` 0x6494d8, `CGameText::VFTable` 0x62ccd0, `CSparkleCluster::VFTable` 0x62e318, `CVEFVidCell::VFTable` 0x639650, `CVisualEffect::VFTable` 0x639848 | unchanged | equal to tools/bindings/vtmap.json (constructor store, both games) |
| 22 `CProjectile*::VFTable` | unchanged | see EEex_Projectile.md |

## Change
- `EEex_GameObject_CastUserType`: an object with no valid m_objectType and an unknown vtable is checked against the Torment-only projectile classes (EEex_Projectile.lua fallback, AddEffect slot) and cast to its nearest known base projectile class. Guarded by the existence of the fallback function.

## Label fixes needed / open questions
- none.
