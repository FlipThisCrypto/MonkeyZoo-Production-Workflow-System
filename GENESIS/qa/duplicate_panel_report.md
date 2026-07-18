# MonkeyZoo: Genesis — Duplicate / Near-Duplicate Panel Report

- Panels analyzed: **96**
- Exact-duplicate pairs: **44**
- Near-duplicate pairs (dhash ≤ 12): **569**
- Same-background clusters (the 5 plates): **8**
- Close background repeats (within 2 reading positions): **65**

## Classification
- Same-background reuse is **acceptable location continuity** (only 5 plates exist).
- The fix applied is **crop variation**: consecutive same-plate panels get distinct
  framings (wide / push-in / reframe) so they read as different camera set-ups rather
  than the same image repeated. New generated art is the owner-gated deeper fix.

## Background clusters
- 23 panels share a plate: P03_PANEL05, P04_PANEL01, P04_PANEL02, P04_PANEL03, P04_PANEL04, P04_PANEL05, P05_PANEL01, P05_PANEL02, P05_PANEL04, P05_PANEL05, P05_PANEL06, P06_PANEL02, P07_PANEL01, P07_PANEL02, P07_PANEL04, P07_PANEL05, P07_PANEL06, P08_PANEL02, P10_PANEL03, P10_PANEL04, P13_PANEL01, P13_PANEL02, P13_PANEL04
- 22 panels share a plate: P01_PANEL01, P01_PANEL02, P01_PANEL03, P02_PANEL03, P02_PANEL04, P02_PANEL06, P08_PANEL03, P08_PANEL04, P08_PANEL06, P11_PANEL05, P11_PANEL06, P12_PANEL02, P12_PANEL03, P12_PANEL04, P12_PANEL06, P15_PANEL01, P15_PANEL02, P15_PANEL04, P16_PANEL03, P16_PANEL04, P16_PANEL05, P16_PANEL06
- 12 panels share a plate: P03_PANEL01, P03_PANEL02, P03_PANEL03, P09_PANEL01, P09_PANEL02, P09_PANEL04, P11_PANEL01, P11_PANEL02, P11_PANEL04, P15_PANEL05, P15_PANEL06, P16_PANEL02
- 9 panels share a plate: P01_PANEL05, P01_PANEL06, P02_PANEL02, P06_PANEL03, P06_PANEL04, P06_PANEL06, P09_PANEL05, P09_PANEL06, P10_PANEL02
- 6 panels share a plate: P13_PANEL05, P13_PANEL06, P14_PANEL02, P14_PANEL03, P14_PANEL04, P14_PANEL06
- 4 panels share a plate: P02_PANEL01, P10_PANEL01, P11_PANEL03, P12_PANEL01
- 2 panels share a plate: P07_PANEL03, P10_PANEL06
- 2 panels share a plate: P13_PANEL03, P14_PANEL01

## Close background repeats (candidates for crop variation)
- p1 P01_PANEL01 ↔ p1 P01_PANEL02 (gap 1, bg dist 0)
- p1 P01_PANEL01 ↔ p1 P01_PANEL03 (gap 2, bg dist 0)
- p1 P01_PANEL02 ↔ p1 P01_PANEL03 (gap 1, bg dist 0)
- p2 P01_PANEL05 ↔ p2 P01_PANEL06 (gap 1, bg dist 0)
- p2 P01_PANEL06 ↔ p2 P02_PANEL02 (gap 2, bg dist 0)
- p3 P02_PANEL03 ↔ p3 P02_PANEL04 (gap 1, bg dist 0)
- p3 P02_PANEL04 ↔ p3 P02_PANEL06 (gap 2, bg dist 0)
- p4 P03_PANEL01 ↔ p4 P03_PANEL02 (gap 1, bg dist 1)
- p4 P03_PANEL01 ↔ p4 P03_PANEL03 (gap 2, bg dist 1)
- p4 P03_PANEL02 ↔ p4 P03_PANEL03 (gap 1, bg dist 0)
- p5 P03_PANEL05 ↔ p5 P04_PANEL01 (gap 2, bg dist 0)
- p5 P04_PANEL01 ↔ p5 P04_PANEL02 (gap 1, bg dist 0)
- p5 P04_PANEL01 ↔ p5 P04_PANEL03 (gap 2, bg dist 0)
- p5 P04_PANEL02 ↔ p5 P04_PANEL03 (gap 1, bg dist 0)
- p5 P04_PANEL02 ↔ p5 P04_PANEL04 (gap 2, bg dist 0)
- p5 P04_PANEL03 ↔ p5 P04_PANEL04 (gap 1, bg dist 0)
- p5 P04_PANEL03 ↔ p6 P04_PANEL05 (gap 2, bg dist 0)
- p5 P04_PANEL04 ↔ p6 P04_PANEL05 (gap 1, bg dist 0)
- p6 P04_PANEL05 ↔ p6 P05_PANEL01 (gap 2, bg dist 0)
- p6 P05_PANEL01 ↔ p6 P05_PANEL02 (gap 1, bg dist 0)
- p6 P05_PANEL02 ↔ p7 P05_PANEL04 (gap 2, bg dist 0)
- p7 P05_PANEL04 ↔ p7 P05_PANEL05 (gap 1, bg dist 0)
- p7 P05_PANEL04 ↔ p7 P05_PANEL06 (gap 2, bg dist 0)
- p7 P05_PANEL05 ↔ p7 P05_PANEL06 (gap 1, bg dist 0)
- p7 P05_PANEL06 ↔ p7 P06_PANEL02 (gap 2, bg dist 0)
- p8 P06_PANEL03 ↔ p8 P06_PANEL04 (gap 1, bg dist 0)
- p8 P06_PANEL04 ↔ p8 P06_PANEL06 (gap 2, bg dist 0)
- p9 P07_PANEL01 ↔ p9 P07_PANEL02 (gap 1, bg dist 0)
- p9 P07_PANEL02 ↔ p9 P07_PANEL04 (gap 2, bg dist 0)
- p9 P07_PANEL04 ↔ p9 P07_PANEL05 (gap 1, bg dist 0)
- p9 P07_PANEL04 ↔ p9 P07_PANEL06 (gap 2, bg dist 0)
- p9 P07_PANEL05 ↔ p9 P07_PANEL06 (gap 1, bg dist 0)
- p9 P07_PANEL06 ↔ p10 P08_PANEL02 (gap 2, bg dist 0)
- p10 P08_PANEL03 ↔ p10 P08_PANEL04 (gap 1, bg dist 0)
- p10 P08_PANEL04 ↔ p10 P08_PANEL06 (gap 2, bg dist 0)
- p11 P09_PANEL01 ↔ p11 P09_PANEL02 (gap 1, bg dist 0)
- p11 P09_PANEL02 ↔ p11 P09_PANEL04 (gap 2, bg dist 0)
- p12 P09_PANEL05 ↔ p12 P09_PANEL06 (gap 1, bg dist 0)
- p12 P09_PANEL06 ↔ p12 P10_PANEL02 (gap 2, bg dist 0)
- p13 P10_PANEL03 ↔ p13 P10_PANEL04 (gap 1, bg dist 0)