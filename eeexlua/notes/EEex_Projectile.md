# EEex_Projectile.lua (Torment): label uses

| Label(s) | Verdict | Evidence |
|---|---|---|
| 22 `CProjectile*::VFTable` | unchanged | Each equals tools/bindings/vtmap.json's independently derived Torment vtable (ctor store or slot-content match). CProjectileInstant (not in vtmap) checked by hand: DecodeProjectile's fallback allocation stores it (PT 0x282b4a `lea rax, 0x630700` <-> BG 0x22ed71). |
| `Data-...-CProjectile::DecodeProjectile()-RetPtr` (27 ported) | unchanged, **1 label wrong** | Each is the return address of `call 0x27c4a0` inside the fmap-mapped function (UseItem / UseItemPoint / CreateSecondary by manual review). Swing RetPtr / -2 / -3 are in another order in Torment (matched by context). **ForceSpellPoint: PT label 0x1823f1 is 2 bytes too far**: the call at PT 0x1823ea returns to 0x1823ef (`xor edi, edi`), 0x1823f1 is `mov r12, rax` (BG 0x16df88 is the return address `mov r12, rax`; Torment inserted the xor). Effect: decodes from ForceSpellPoint report no source. Not compensated in Lua (would break when the label is fixed). |
| `Data-CGameSprite::UpdateAOE()-...-RetPtr`, `Data-CProjectile::DecodeProjectile()-...-RetPtr` (Multi Magic Missile) | **patched (guard)** | Unsupported in Torment (PATTERNS.md); `EEex_Label` would abort loading. Replaced by `EEex_LabelDefault(..., -1 / -2)` (never a return address). |
| `Data-...-CProjectile::AddEffect()-RetPtr` (25) | unchanged | Return addresses of `call [rax+0xC8]` (AddEffect is virtual in Torment) in the mapped functions; FireSpellPoint RetPtr / -2 share PT 0x17eeeb (tail-merged). Registers: EEex_Projectile_Patch.md. |

## Other Torment changes in this file
- **Torment-only projectile classes**: Torment has 80 projectile vtables (all with one of the three AddEffect bodies at +0xC8) for the 22 EEex names. Their type was `Unknown`, and `isOfType()` then failed (`EEex_BAnd(nil, ...)`, Inheritance has no Unknown entry). `getType()` now falls back to the nearest known base class given by the AddEffect slot (CProjectile 0x279a80 / CProjectileArea 0x279aa0 / CProjectileBAM 0x279b20), and `isOfType()` treats a missing entry as 0.
- **`CProjectile.DecodeProjectile`** has a third argument in Torment (nLevel, bindings manual_types_pt.txt; the binding reads Lua argument 3): `EEex_Projectile_GetStartingPosForID` passes 1, as CGameAIBase::FireSpell (PT 0x17ddfa), Swing (PT 0x433f37) and the sub-decodes (PT 0x2829e2) do.

## Label fixes needed
- `Data-CGameAIBase::ForceSpellPoint()-CProjectile::DecodeProjectile()-RetPtr`: PT 0x1823f1 -> **0x1823ef**.

## Open questions
- The slot-based fallback assumes no class outside the BAM / Area hierarchy shares (by identical-code folding) the 0x279b20 / 0x279aa0 bodies; they use BAM's +0x1f8 field and the 0x16c opcode, so this is very unlikely.
