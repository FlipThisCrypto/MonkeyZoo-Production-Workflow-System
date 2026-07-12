#!/usr/bin/env python3
import json
from pathlib import Path

issue = Path(__file__).resolve().parent
STYLE = (
    "MonkeyZoo house style: chibi cartoon monkey with oversized round head, "
    "huge white oval eyes with tiny black dot pupils, two small dot nostrils, "
    "thick uniform black outlines, flat color fills with soft cel shading, "
    "simplified plush body with visible stitch seams, mitten hands, curled tail, "
    "clean vector cartoon look"
)
NEG = (
    "realistic anatomy, human hands, individual fingers, extra limbs, extra tails, "
    "small eyes, detailed fur texture, photorealism, 3d render, painterly brushwork, "
    "cross-hatching, thin sketchy lines, full-body gradient, watermark text, signature text, "
    "readable text, letters, numbers, logos, redesigned costume, extra characters, "
    "duplicate character, deformed pupils"
)

ID = {
    "Ash": "Ash: pale grey face, ash-grey spiked hair with bright orange tips, black hoodie, black pants, grey boots, brown ears, stitch seams",
    "Moodz": "Moodz: porcelain white face, glossy black emo fringe with blue left streak, grey under-eye rings, black studded vest and pants, platform boots",
    "TwoTone": "TwoTone: white face, two-tone black-and-white glossy hair, grey eye rings, black studded vest pants, grey boots",
    "Static": "Static: white face, jet-black slicked helmet hair, heavy grey under-eye rings, black studded vest pants, grey boots",
    "NeonBlue": "NeonBlue: pale face, white spike hair with cyan tips and cyan root glow, left ear plug, black vest white studs, grey sneakers",
    "Scarline": "Scarline: white face, silver-white helmet hair with bold scarlet red streak on left, black studded biker jacket pants, grey boots",
    "Cheeky": "Cheeky: cream face, solid bright blue eyes, brown hair tuft, dark brown open vest, teal banana-print shorts, bare feet",
    "Clever": "Clever: beige face, brown ponytail with pink hairband, black round glasses, blue shirt with pi logo, red shorts",
    "Emo": "Emo: white face, black hair with blue left streak, grey eye rings, black studded punk vest pants, grey sneakers",
    "LilDevil": "LilDevil: cream face, red slicked hair, purple eyeshadow, long lashes, red ears, red devil bodysuit, fishnet stockings, red heels, arrow tail",
    "Super": "Super: beige face, brown hair tuft, red eye mask, full green superhero suit, white chest oval with black M, green tail",
    "Zombie": "Zombie: mint green skin, exposed purple brain on head, huge white eyes, yellow broken teeth, olive tattered jacket pants, white bone stump arm",
}

REFKEY = {
    "Ash": "ash", "Moodz": "moodz", "TwoTone": "twotone", "Static": "static",
    "NeonBlue": "neonblue", "Scarline": "scarline", "Cheeky": "cheeky",
    "Clever": "clever", "Emo": "emo", "LilDevil": "lildevil", "Super": "super", "Zombie": "zombie",
}

panels_data = [
    dict(page=1, n=1, size="half", chars=["Moodz", "Cheeky", "NeonBlue"],
         loc="Mango Pier boardwalk entrance bright noon sun ocean beyond", cam="wide establishing high angle",
         act="squad arrives on sunny pier; Cheeky racing toward games; NeonBlue waving; Moodz herding group",
         emo="summer joy", dlg='CHEEKY: "Games first. Chaos second."',
         cap="Hottest week of July. One day off.",
         vis="yellow boardwalk bulbs, ocean blue, summer orange; reserve top fifth for balloon"),
    dict(page=1, n=2, size="half", chars=["Static", "LilDevil", "Emo"],
         loc="arcade row Mango Pier", cam="medium three-shot",
         act="Static stares at glowing arcade cabinet; LilDevil holds hot pepper skewer; Emo covers ears from noise",
         emo="suspicion, reckless fun, overwhelm", dlg='STATIC: "That score is not possible."', cap="",
         vis="neon arcade lights; blank glowing cabinet screens no readable text; bubble space top"),
    dict(page=2, n=1, size="third", chars=["Clever", "Ash"],
         loc="frozen banana stand mid-pier", cam="two-shot eye level",
         act="Clever crouches pointing at old wiring under stand; Ash arms crossed unimpressed",
         emo="focused vs bored-hot", dlg='CLEVER: "These cables are not boardwalk stock."', cap="",
         vis="banana stand, summer heat haze"),
    dict(page=2, n=2, size="third", chars=[],
         loc="banana stand counter", cam="medium funny",
         act="faceless tourist chibi monkey fused with beach umbrella like parachute mid-air, cyan glow banana residue",
         emo="slapstick", dlg="", cap="The frozen banana stand had opinions about summer.",
         vis="comic fusion gag; NO named leads"),
    dict(page=2, n=3, size="third", chars=["Clever", "Moodz"],
         loc="banana stand area", cam="close two-shot",
         act="Clever holds glowing blue banana stub with tongs; Moodz eyes widen",
         emo="joke turns worry", dlg='MOODZ: "Everyone stay calm. Calm is the plan."', cap="",
         vis="glowing blue treat, bubble space"),
    dict(page=3, n=1, size="third", chars=["Cheeky", "NeonBlue"],
         loc="boardwalk mid-stretch sunscreen chaos", cam="wide action",
         act="sunscreen foam spray; Cheeky herds crowd with beach ball; NeonBlue ushers kids behind prize stall",
         emo="comedy protect", dlg='NEONBLUE: "Kids first. Always."', cap="",
         vis="white foam, summer chaos, bubble space"),
    dict(page=3, n=2, size="third", chars=["Ash", "TwoTone"],
         loc="stabilizer vent near pier rail", cam="low angle",
         act="Ash reaches glowing overheating vent orange sparks; TwoTone grabs his arm stopping him",
         emo="anger vs firm balance", dlg='TWOTONE: "Balance it. Don\'t blow it."', cap="",
         vis="orange heat vent, ocean rail"),
    dict(page=3, n=3, size="third", chars=["Moodz", "Ash"],
         loc="vent area", cam="close faces",
         act="Moodz steady calm gaze; Ash jaw tight cooling off fists unclenching",
         emo="heat meets anchor", dlg='MOODZ: "The machine eats spikes. Don\'t feed it."', cap="",
         vis="soft close-up bubble space"),
    dict(page=4, n=1, size="half", chars=["Scarline", "Zombie", "Emo"],
         loc="under Mango Pier dark pilings dripping water cyan pipes", cam="wide low establishing",
         act="trio in under-pier shadow; Scarline leads along claw-marked wood; cyan coolant pipes glow",
         emo="quiet dread", dlg="", cap="Below the music, the pier remembered what it was built on.",
         vis="dark teal shadows, cyan coolant glow"),
    dict(page=4, n=2, size="half", chars=["Scarline", "Zombie"],
         loc="sealed maintenance door under pier", cam="medium on door claw marks",
         act="Scarline mitt traces deep claw grooves; Zombie sniffs cyan drip eyes wide recognition",
         emo="discovery", dlg='ZOMBIE: "Old FusionZoo coolant. This was never just a pier."', cap="",
         vis="door, claw marks, coolant drip"),
    dict(page=5, n=1, size="third", chars=["Static", "Clever"],
         loc="arcade interior neon", cam="medium two-shot",
         act="cabinets all glow same blank glyph-ready pulse; Static hands on controls; Clever traces cable map",
         emo="focused tech panic", dlg='STATIC: "It\'s broadcasting through every game."', cap="",
         vis="neon magenta cyan arcade"),
    dict(page=5, n=2, size="third", chars=["Cheeky", "LilDevil"],
         loc="boardwalk outside arcade", cam="action medium",
         act="Cheeky rigs prize claw distraction; LilDevil raises fireworks crate ready to smash",
         emo="comedy disaster edge", dlg='CHEEKY: "Wrong toy, big red."', cap="",
         vis="prize stall fireworks crate"),
    dict(page=5, n=3, size="third", chars=["TwoTone", "LilDevil"],
         loc="outside arcade", cam="tight two-shot",
         act="TwoTone blocks LilDevil swing; fused crowd silhouettes glow soft in background faceless",
         emo="restraint", dlg='TWOTONE: "Smash it and they stay fused."', cap="",
         vis="block pose, bubble space"),
    dict(page=6, n=1, size="half", chars=["Super"],
         loc="boardwalk sky above pier sunset", cam="heroic low angle",
         act="Super Monkey streaks green suit red mask catching two mid-air fused float monkeys faceless",
         emo="flashy confidence", dlg="", cap="Then the sky got a hero.",
         vis="sunset orange sky, green suit pop"),
    dict(page=6, n=2, size="half", chars=["Super", "Scarline", "Zombie"],
         loc="boardwalk after landing", cam="three-shot eye level",
         act="Super poses confident; Scarline and Zombie exchange suspicious look",
         emo="impressed and suspicious", dlg='SCARLINE: "You knew the hatch."', cap="",
         vis="sunset light, bubble space"),
    dict(page=7, n=1, size="third", chars=["Moodz", "Emo", "NeonBlue"],
         loc="central boardwalk dusk", cam="wide group",
         act="Moodz calming gesture; Emo steadies panicking faceless fused monkey; NeonBlue leads kids with glow sticks quiet",
         emo="collective cool-down", dlg='EMO: "Quiet wins. Loud feeds it."', cap="",
         vis="softer palette cooling energy"),
    dict(page=7, n=2, size="third", chars=["Ash", "Static", "Clever"],
         loc="vent and cable junction", cam="medium trio working",
         act="Ash carefully vents controlled orange heat; Static reroutes glowing cables; Clever flips balancer switch",
         emo="teamwork focus", dlg="", cap="",
         vis="technical save, leave space for SFX WHRRRR"),
    dict(page=7, n=3, size="third", chars=["LilDevil", "TwoTone", "Cheeky"],
         loc="fireworks cart near rail", cam="medium",
         act="LilDevil holds fireworks cart still straining; TwoTone adjusts stabilizer box dials; Cheeky waves crowd to beach exit",
         emo="growth comedy", dlg='LILDEVIL: "Fine. Not smashing. Yet."', cap="",
         vis="cart, ocean rail, dusk"),
    dict(page=8, n=1, size="half", chars=["Moodz", "NeonBlue", "Super"],
         loc="beach sand night ocean fireworks sky", cam="wide from behind looking at fireworks",
         act="three leads on sand watching safe red-white-blue fireworks over ocean; quiet beat",
         emo="relief earned peace", dlg="",
         cap="The pier cooled. The sky did not need a sacrifice.",
         vis="fireworks over water night beach"),
    dict(page=8, n=2, size="half", chars=["Scarline", "Zombie", "Super"],
         loc="under-pier piling Super faction mark", cam="close on burn mark faces at edge",
         act="Scarline mitt on fresh burned Super-faction mark; Zombie looks toward Super; Super half-turned away not answering",
         emo="mystery opens", dlg='ZOMBIE: "You knew this place."',
         cap="Summer was the cover. The signal was the test.",
         vis="burn mark blank symbol space, dark under pier"),
]

pages = {}
for p in panels_data:
    pages.setdefault(p["page"], []).append(p)

plan = {"issue_id": "MZ-2026-07-MANGO", "issue_title": "The Meltdown at Mango Pier", "page_count": 8, "pages": []}
for pn in range(1, 9):
    pl = pages[pn]
    recipe = "half+half" if len(pl) == 2 else "third-x3"
    page = {"page_number": pn, "page_purpose": f"Page {pn}", "layout_recipe": recipe, "panels": []}
    for p in pl:
        pid = f"MZ-2026-07-MANGO_P{p['page']:02d}_PANEL{p['n']:02d}"
        refs = [f"references/character_refs/{REFKEY[c]}/" for c in p["chars"]] if p["chars"] else ["references/background_refs/"]
        page["panels"].append({
            "panel_id": pid, "panel_size": p["size"], "characters": p["chars"],
            "location": p["loc"], "camera_angle": p["cam"], "action": p["act"],
            "emotion": p["emo"], "dialogue": p["dlg"], "caption": p["cap"], "sfx": "",
            "visual_notes": p["vis"], "continuity_notes": "Mango Pier July test; temporary fusions only",
            "art_prompt": "SEE art_prompt_pack", "negative_prompt": NEG,
            "references_required": refs, "lora_required": [],
            "controlnet_required": "openpose" if p["chars"] else "depth", "seed_strategy": "per_panel",
        })
    plan["pages"].append(page)

(issue / "page_panel_plan.json").write_text(json.dumps(plan, indent=2), encoding="utf-8")

pack = {"issue_id": "MZ-2026-07-MANGO", "style_lock_phrase": STYLE, "base_negative_prompt": NEG, "panels": []}
for p in panels_data:
    pid = f"MZ-2026-07-MANGO_P{p['page']:02d}_PANEL{p['n']:02d}"
    char_blocks = [ID[c] for c in p["chars"]] if p["chars"] else ["no named lead characters, only faceless tourist chibi monkey if needed"]
    prompt = (
        f"{STYLE}, comic panel, {p['cam']}, {p['loc']}, action: {p['act']}, emotion: {p['emo']}, "
        + "; ".join(char_blocks)
        + f", {p['vis']}, mitten hands only, NO dialogue balloons, NO text, NO letters, NO numbers, NO watermarks, clean lettering space reserved at top"
    )
    pack["panels"].append({
        "panel_id": pid, "page_number": p["page"], "panel_number": p["n"],
        "characters": p["chars"], "prompt": prompt, "negative_prompt": NEG,
        "dialogue": p["dlg"], "caption": p["cap"],
        "resolution": "1216x832" if p["size"] == "half" else "1024x1024",
        "ref_keys": [REFKEY[c] for c in p["chars"]],
    })

(issue / "art_prompt_pack.json").write_text(json.dumps(pack, indent=2), encoding="utf-8")
print("OK", len(pack["panels"]), "panels")
