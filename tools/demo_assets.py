"""Ressources libres pour la version démo en ligne (GitHub Pages) : icônes SVG et pack de sons synthétisé.

Tout est généré par ce script : aucune ressource Sphero n'est utilisée.
"""
import array, base64, io, json, math, random, struct, wave

SR = 22050          # fréquence d'échantillonnage du pack démo (mono 16 bits)
BPM = 120
BEAT = 60 / BPM
BAR = 4 * BEAT       # 2 s
LOOP = 4 * BAR       # 8 s : boucles parfaitement rebouclables

# ----------------------------------------------------------------------------------------------
# Icônes (blanches, traits arrondis) — mêmes noms que les ressources de l'app d'origine
# ----------------------------------------------------------------------------------------------
def _svg(body, vb="0 0 64 64", w=None, h=None):
    size = f' width="{w}" height="{h}"' if w else ""
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{vb}"{size} fill="none" stroke="#fff" stroke-width="4" stroke-linecap="round" stroke-linejoin="round">{body}</svg>'

def _battery(fill, level):
    bars = "".join(f'<rect x="22" y="{46 - i * 11}" width="20" height="8" rx="1" fill="{fill}" stroke="none"/>' for i in range(level))
    return _svg(f'<rect x="16" y="12" width="32" height="44" rx="4"/><path d="M26 6h12"/>{bars}')

def _facets(top):
    rnd = random.Random(7 if top else 11)
    cols = ["#ff4f9a", "#8b5cf6", "#22d3ee", "#f97316", "#34d399", "#6366f1"]
    polys = []
    for _ in range(46):
        x, y = rnd.uniform(-100, 1500), rnd.uniform(0, 260)
        pts = " ".join(f"{x + rnd.uniform(-260, 260):.0f},{y + rnd.uniform(-160, 160):.0f}" for _ in range(3))
        polys.append(f'<polygon points="{pts}" fill="{rnd.choice(cols)}" opacity="{rnd.uniform(.05, .22):.2f}"/>')
    fade = "0" if top else "1"
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1400 260"><defs><linearGradient id="f" x1="0" y1="0" x2="0" y2="1">'
            f'<stop offset="0" stop-color="#fff" stop-opacity="{1 if top else 0}"/><stop offset="1" stop-color="#fff" stop-opacity="{fade}"/></linearGradient>'
            f'<mask id="m"><rect width="1400" height="260" fill="url(#f)"/></mask></defs><g mask="url(#m)">{"".join(polys)}</g></svg>')

MAT = ["#e8334a", "#f29e4c", "#f2d24a", "#8cbf4c", "#147a68", "#145c96", "#603a6e", "#a3336b"]

def _howto(step):
    mat = "".join(f'<rect x="{30 + i * 38}" y="120" width="34" height="52" rx="3" fill="{c}" stroke="none"/>' for i, c in enumerate(MAT))
    ring = {1: '<circle cx="250" cy="60" r="22" stroke="#9ff" stroke-width="7"/><path d="M250 82v24" stroke="#fff" stroke-width="5"/>',
            2: '<circle cx="125" cy="98" r="16" stroke="#9ff" stroke-width="6"/><path d="M100 108l50 0" stroke="#fff" stroke-width="3" stroke-dasharray="4 6"/>',
            3: '<path d="M70 70q30-40 60 0t60 0t60 0" stroke="#fff" stroke-width="5"/><circle cx="240" cy="40" r="6" fill="#fff"/>'}[step]
    label = {1: "1 · METS L'ANNEAU", 2: "2 · TAPE UNE COULEUR", 3: "3 · JOUE !"}[step]
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 340 200"><rect width="340" height="200" fill="#1d1236"/>'
            f'<rect x="20" y="112" width="310" height="68" rx="6" fill="#0d0d0f"/>{mat}<g fill="none" stroke-linecap="round">{ring}</g>'
            f'<text x="20" y="34" fill="#fff" font-family="Arial Narrow,Arial,sans-serif" font-size="20" font-weight="bold">{label}</text></svg>')

ICONS = {
    "icon_connect.png": _svg('<rect x="8" y="10" width="26" height="44" rx="4"/><circle cx="46" cy="38" r="10"/><path d="M46 28v-6"/>'),
    "icon_settings.png": _svg('<circle cx="32" cy="32" r="9"/><path d="M32 6v8M32 50v8M6 32h8M50 32h8M13.6 13.6l5.7 5.7M44.7 44.7l5.7 5.7M13.6 50.4l5.7-5.7M44.7 19.3l5.7-5.7"/>'),
    "ic_unmuted.png": _svg('<path d="M10 24h10l14-12v40L20 40H10z"/><path d="M42 22q8 10 0 20M48 16q14 16 0 32"/>'),
    "ic_muted.png": _svg('<path d="M10 24h10l14-12v40L20 40H10z"/><path d="M42 24l14 16M56 24L42 40"/>'),
    "ic_tab_library.png": _svg('<rect x="8" y="10" width="20" height="20" rx="3"/><rect x="36" y="10" width="20" height="20" rx="3"/><rect x="8" y="36" width="20" height="20" rx="3"/><rect x="36" y="36" width="20" height="20" rx="3"/>'),
    "ic_tab_editor.png": _svg('<path d="M32 8a24 24 0 1 0 0 48c4 0 6-3 4-6s0-7 4-7h6a10 10 0 0 0 10-10C56 19 45 8 32 8z"/><circle cx="20" cy="30" r="3"/><circle cx="28" cy="19" r="3"/><circle cx="41" cy="20" r="3"/>'),
    "ic_tab_my_music.png": _svg('<path d="M8 18h18l5 6h25v28H8z"/><path d="M30 46V32l14-3v14"/><circle cx="27" cy="46" r="3"/><circle cx="41" cy="43" r="3"/>'),
    "ic_tab_record.png": _svg('<circle cx="32" cy="32" r="22"/><circle cx="32" cy="32" r="10" fill="#fff"/>'),
    "ic_tab_record_stop.png": _svg('<circle cx="32" cy="32" r="22"/><rect x="23" y="23" width="18" height="18" rx="2" fill="#fff"/>'),
    "icon_battery_green.png": _battery("#5fd38d", 3),
    "icon_battery_yellow.png": _battery("#f2d24a", 2),
    "icon_battery_red.png": _battery("#ff5a5a", 1),
    "icon_battery_unknown.png": _svg('<rect x="16" y="12" width="32" height="44" rx="4"/><path d="M26 6h12M27 28q0-6 5-6t5 5q0 4-5 6v3"/><circle cx="32" cy="45" r="1.5" fill="#fff"/>'),
    "icon_reset_colors.png": _svg('<path d="M14 32a18 18 0 1 0 6-13"/><path d="M14 10v10h10"/>'),
    "ic_sample_recording_play.png": _svg('<circle cx="32" cy="32" r="24"/><path d="M27 21l16 11-16 11z" fill="#fff"/>'),
    "ic_sample_recording_stop.png": _svg('<circle cx="32" cy="32" r="24"/><rect x="24" y="24" width="16" height="16" fill="#fff"/>'),
    "ic_sample_recording_save.png": _svg('<circle cx="32" cy="32" r="24"/><path d="M32 18v20M24 31l8 8 8-8M22 45h20"/>'),
    "ic_sample_recording_delete.png": _svg('<circle cx="32" cy="32" r="24"/><path d="M23 24h18M28 24v-3h8v3M25 24l2 18h10l2-18"/>'),
    "ic_close.png": _svg('<path d="M14 14l36 36M50 14L14 50" stroke-width="7"/>'),
    "ic_pad_edited.png": _svg('<path d="M12 52l4-14L42 12l10 10-26 26z"/><path d="M36 18l10 10"/>'),
    "tap_finger.png": _svg('<circle cx="32" cy="18" r="9" stroke="#9ff"/><path d="M32 27v16M20 50h24"/><path d="M14 44l6 6M50 44l-6 6"/>', vb="0 0 64 64"),
    "logo_specdrums.png": ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 720 150"><text x="360" y="100" text-anchor="middle" fill="#fff" '
                           'font-family="Arial Narrow,Arial,sans-serif" font-size="84" font-weight="300" textLength="600" lengthAdjust="spacingAndGlyphs">bagues musicales</text>'
                           '<circle cx="684" cy="62" r="14" fill="none" stroke="#9ff" stroke-width="7"/></svg>'),
    "intro.jpg": ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 212 212"><defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1">'
                  '<stop offset="0" stop-color="#7c3aed"/><stop offset="1" stop-color="#0ea5e9"/></linearGradient></defs><rect width="212" height="212" fill="url(#g)"/>'
                  '<path d="M16 120q15-50 30 0t30 0t30 0t30 0t30 0t30 0" fill="none" stroke="#fff" stroke-width="6" stroke-linecap="round"/>'
                  '<text x="106" y="186" text-anchor="middle" fill="#fff" font-family="Arial Narrow,Arial,sans-serif" font-size="30" font-weight="bold">DÉMO</text></svg>'),
    "background_facets_top.webp": _facets(True),
    "background_facets_bottom.webp": _facets(False),
    "how_to_play_1.jpg": _howto(1),
    "how_to_play_2.jpg": _howto(2),
    "how_to_play_3.jpg": _howto(3),
}

def icon_uri(name):
    svg = ICONS[name]
    return "data:image/svg+xml;base64," + base64.b64encode(svg.encode()).decode()

# ----------------------------------------------------------------------------------------------
# Synthèse du pack « Démo synthé » (la mineur, 120 BPM)
# ----------------------------------------------------------------------------------------------
def _buf(sec):
    return [0.0] * int(round(sec * SR))

def _add(dst, src, at):
    i0 = int(round(at * SR))
    for i, v in enumerate(src):
        j = (i0 + i) % len(dst)   # rebouclage : les queues de notes reviennent au début de la boucle
        dst[j] += v

def _env(n, a, d):
    na = max(1, int(a * SR))
    return [(i / na if i < na else math.exp(-(i - na) / (d * SR))) for i in range(n)]

def kick(dur=.45):
    n = int(dur * SR); out = []; ph = 0
    for i in range(n):
        t = i / SR; f = 45 + 95 * math.exp(-t * 28); ph += 2 * math.pi * f / SR
        out.append(math.sin(ph) * math.exp(-t * 7) * .95)
    return out

def snare(dur=.28, seed=1):
    rnd = random.Random(seed); n = int(dur * SR)
    return [((rnd.uniform(-1, 1) * .7) + .35 * math.sin(2 * math.pi * 185 * i / SR)) * math.exp(-i / SR * 16) * .6 for i in range(n)]

def hat(dur=.07, seed=2):
    rnd = random.Random(seed); n = int(dur * SR); prev = 0; out = []
    for i in range(n):
        x = rnd.uniform(-1, 1); y = x - prev; prev = x
        out.append(y * math.exp(-i / SR * 60) * .25)
    return out

def clap(seed=3):
    out = [0.0] * int(.3 * SR)
    for k, off in enumerate((0, .012, .024)):
        s = snare(.2, seed + k)
        _add_lin(out, [v * .8 for v in s], off)
    return out

def _add_lin(dst, src, at):
    i0 = int(at * SR)
    for i, v in enumerate(src):
        if i0 + i < len(dst): dst[i0 + i] += v

def tone(freq, dur, harm=(1, .5, .25), a=.005, d=.3, vib=0.0):
    n = int(dur * SR); env = _env(n, a, d); out = []
    for i in range(n):
        t = i / SR; f = freq * (1 + vib * math.sin(2 * math.pi * 5 * t))
        out.append(env[i] * sum(h * math.sin(2 * math.pi * f * (k + 1) * t) for k, h in enumerate(harm)) / sum(harm))
    return out

NOTE = lambda m: 440 * 2 ** ((m - 69) / 12)
PROG = [(57, 60, 64), (53, 57, 60), (48, 52, 55), (55, 59, 62)]   # Am  F  C  G

def loop_drums():
    out = _buf(LOOP)
    for b in range(16):
        t = b * BEAT
        if b % 2 == 0: _add(out, kick(), t)
        else: _add(out, snare(), t)
        if b % 4 == 3: _add(out, kick(), t + BEAT * .75)
        for h in range(2): _add(out, hat(), t + h * BEAT / 2)
    return out

def loop_bass():
    out = _buf(LOOP)
    for bar, chord in enumerate(PROG):
        root = chord[0] - 12
        for e in range(8):
            m = root + (12 if e in (3, 7) else 0)
            _add(out, tone(NOTE(m), BEAT * .48, (1, .6, .4, .2), .004, .12), bar * BAR + e * BEAT / 2)
    return [v * .7 for v in out]

def loop_chords():
    out = _buf(LOOP)
    for bar, chord in enumerate(PROG):
        for m in chord:
            _add(out, tone(NOTE(m + 12), BAR, (1, .3, .12), .25, 1.4, .004), bar * BAR)
    return [v * .28 for v in out]

def loop_arp():
    out = _buf(LOOP)
    for bar, chord in enumerate(PROG):
        seq = [chord[0], chord[1], chord[2], chord[1] + 12, chord[2] + 12, chord[1] + 12, chord[2], chord[1]]
        for s in range(16):
            _add(out, tone(NOTE(seq[s % 8] + 12), .22, (1, .2), .002, .09), bar * BAR + s * BEAT / 4)
    return [v * .3 for v in out]

def sustained(freq):
    """Note tenue rebouclable : nombre entier de périodes, sans attaque (l'appli gère le fondu)."""
    periods = max(1, round(freq * .5)); dur = periods / freq; n = int(round(dur * SR)); f = periods / (n / SR)
    return [(.55 * math.sin(2 * math.pi * f * i / SR) + .25 * math.sin(4 * math.pi * f * i / SR) + .1 * math.sin(6 * math.pi * f * i / SR)) * .55
            for i in range(n)]

def wav_b64(samples):
    peak = max(1e-9, max(abs(v) for v in samples)); g = min(1.0, .92 / peak)
    pcm = array.array("h", (int(max(-1, min(1, v * g)) * 32767) for v in samples))
    out = io.BytesIO()
    with wave.open(out, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())
    return base64.b64encode(out.getvalue()).decode()

def demo_pack():
    sounds = [  # (id, nom, catégorie, type, maintien, quantification, générateur)
        ("d01", "Grosse caisse", 0, 0, False, 9, kick),
        ("d02", "Caisse claire", 0, 0, False, 9, snare),
        ("d03", "Clap", 3, 0, False, 9, clap),
        ("d04", "Charleston", 0, 0, False, 9, lambda: hat(.12)),
        ("d05", "Note tenue La", 2, 0, True, 9, lambda: sustained(NOTE(69))),
        ("d06", "Note tenue Do", 2, 0, True, 9, lambda: sustained(NOTE(72))),
        ("d07", "Note tenue Mi", 2, 0, True, 9, lambda: sustained(NOTE(76))),
        ("d08", "Note tenue Sol", 2, 0, True, 9, lambda: sustained(NOTE(79))),
        ("d09", "Batterie", 0, 1, False, 0, loop_drums),
        ("d10", "Basse", 1, 1, False, 0, loop_bass),
        ("d11", "Accords", 2, 1, False, 0, loop_chords),
        ("d12", "Arpège", 2, 1, False, 0, loop_arp),
    ]
    info = {"name": "Démo synthé", "localization": {"fr": "DÉMO SYNTHÉ", "en": "SYNTH DEMO"}, "genre": "Démo", "bpm": BPM,
            "artist": "bagues-musicales (généré)", "id": "demo",
            "presets": {"p": {"id": "p", "name": "Default", "soundIDs": [s[0] for s in sounds]}}, "sounds": {}}
    files = {}
    for sid, name, cat, typ, sus, q, gen in sounds:
        fn = f"{sid}.wav"
        info["sounds"][sid] = {"id": sid, "name": name, "category": cat, "type": typ, "sustainable": sus, "quantization": q, "soundPath": f"demo/{fn}"}
        files[fn] = wav_b64(gen())
    files["nil_sound.wav"] = wav_b64(tone(220, .12, (1,), .002, .03))
    return {"info": info, "files": files}

if __name__ == "__main__":
    p = demo_pack(); print(json.dumps(p["info"], ensure_ascii=False)[:200], sum(len(v) for v in p["files"].values()) // 1024, "Ko")
