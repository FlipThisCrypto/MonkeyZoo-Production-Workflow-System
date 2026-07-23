# Clever — Generation Descriptor (approved-reference derived)

Clever is a NON-standard MonkeyZoo design. The shared `gen_char_refs.BASE`
prompt hardcodes the standard cast look ("face colored flat porcelain WHITE,
never brown or skin tone", "black punk pants with silver studs", "grey platform
boots") — which conflicts with Clever. So Clever uses a **dedicated full
text2img prompt** (in `genesis_charart.CLEVER_PROMPT`), not BASE + hair.

Derived only from the approved canon base
(`03_APPROVED_CANON/approved_characters/clever/clever_00_clean_base.png`):

- **Glasses (defining, must never change):** big round thick black-rimmed nerd glasses
- **Hair:** brown, swept to one side, high side ponytail tied with a pink hair-tie
- **Face:** olive-tan / khaki muzzle (distinct from the cast's porcelain-white face)
- **Outfit:** blue short-sleeve t-shirt, white raglan sleeves, small red roundel (π) on chest; red shorts
- **Fur/ears/tail:** brown; round brown ears; long curled brown tail
- **Card colour / backdrop:** turquoise-cyan
- **Style:** thick uniform black outlines, flat solid colours, vector sticker look

Generation: Z-Image Turbo text2img, 8 steps, cfg 1.0, EmptySD3LatentImage
832x1216, denoise 1.0. Identity anchored by the prompt (no img2img — the
LoadImage init path is rejected by this ComfyUI and img2img drifts colours).
