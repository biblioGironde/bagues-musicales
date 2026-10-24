#!/usr/bin/env python3
"""Construit la webapp « Bagues musicales » (fichier HTML unique) à partir de votre propre APK Specdrums Mix.

Aucune ressource Sphero (sons, police, images) n'est versionnée dans ce dépôt : ce script les lit
directement dans l'APK que vous possédez et les intègre dans dist/specdrums-mix.html.

Usage :
    python3 tools/build.py --apk Specdrums_Mix_1_2_2.apk
    python3 tools/build.py --apk Specdrums_Mix_1_2_2.apk --out dist/specdrums-mix.html

Dépendance optionnelle : Pillow (pip install pillow) pour alléger les grandes images.
"""
import argparse, base64, io, json, os, re, sys, zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Nom utilisé dans src/index.html  ->  chemin dans l'APK Specdrums Mix 1.2.2 (ressources obfusquées)
APK_ASSETS = {
    "BlockGothicRRLightCond.ttf": "assets/fonts/BlockGothicRRLightCond.ttf",
    "BlockGothicRRMediumCond.ttf": "assets/fonts/BlockGothicRRMediumCond.ttf",
    "background_facets_bottom.webp": "res/QW1.png",
    "background_facets_top.webp": "res/jn.png",
    "how_to_play_1.jpg": "res/DW.png",
    "how_to_play_2.jpg": "res/La.png",
    "how_to_play_3.jpg": "res/Dq.png",
    "ic_close.png": "res/xr.png",
    "ic_muted.png": "res/pK.png",
    "ic_pad_edited.png": "res/nI.png",
    "ic_sample_recording_delete.png": "res/3V.png",
    "ic_sample_recording_play.png": "res/I2.png",
    "ic_sample_recording_save.png": "res/47.png",
    "ic_sample_recording_stop.png": "res/Vz.png",
    "ic_tab_editor.png": "res/vo.png",
    "ic_tab_library.png": "res/Bo.png",
    "ic_tab_my_music.png": "res/EE.png",
    "ic_tab_record.png": "res/hb.png",
    "ic_tab_record_stop.png": "res/qY.png",
    "ic_unmuted.png": "res/6N.png",
    "icon_battery_green.png": "res/M3.png",
    "icon_battery_red.png": "res/RN.png",
    "icon_battery_unknown.png": "res/Sv.png",
    "icon_battery_yellow.png": "res/OW.png",
    "icon_connect.png": "res/2v.png",
    "icon_reset_colors.png": "res/nU.png",
    "icon_settings.png": "res/Rr.png",
    "intro.jpg": "res/SA1.jpg",
    "logo_specdrums.png": "res/Na1.png",
    "tap_finger.png": "res/JN.png",
}
MIME = {".ttf": "font/ttf", ".webp": "image/webp", ".jpg": "image/jpeg", ".png": "image/png"}


def convert(name, raw):
    """Allège les grandes images (fonds -> webp 1400 px, illustrations -> jpg 640 px) si Pillow est présent."""
    ext = os.path.splitext(name)[1]
    try:
        from PIL import Image
    except ImportError:
        return raw, ("image/png" if ext in (".webp", ".jpg") and raw[:4] == b"\x89PNG" else MIME[ext])
    if name.startswith("background_facets"):
        im = Image.open(io.BytesIO(raw)); im = im.resize((1400, int(im.height * 1400 / im.width)), Image.LANCZOS)
        out = io.BytesIO(); im.save(out, "WEBP", quality=82); return out.getvalue(), "image/webp"
    if name.startswith("how_to_play"):
        im = Image.open(io.BytesIO(raw)).convert("RGB"); im.thumbnail((640, 640))
        out = io.BytesIO(); im.save(out, "JPEG", quality=80); return out.getvalue(), "image/jpeg"
    return raw, MIME[ext]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--apk", required=True, help="chemin vers Specdrums_Mix_*.apk")
    ap.add_argument("--out", default=os.path.join(ROOT, "dist", "specdrums-mix.html"))
    a = ap.parse_args()

    apk = zipfile.ZipFile(a.apk)
    names = set(apk.namelist())
    src = open(os.path.join(ROOT, "src", "index.html"), encoding="utf-8").read()

    cache = {}
    def asset(m):
        name = m.group(1)
        if name not in cache:
            path = APK_ASSETS.get(name)
            if not path or path not in names:
                sys.exit(f"Ressource introuvable dans l'APK : {name} ({path}). Version d'APK différente de 1.2.2 ?")
            data, mime = convert(name, apk.read(path))
            cache[name] = f"data:{mime};base64," + base64.b64encode(data).decode()
        return cache[name]
    src = re.sub(r"%%A:([^%]+)%%", asset, src)

    # pack de sons intégré « Intro Mix » + son « couleur inconnue »
    info = json.loads(apk.read("assets/defaultSoundPack/info.json"))
    files = {os.path.basename(n): base64.b64encode(apk.read(n)).decode()
             for n in names if n.startswith("assets/defaultSoundPack/Sounds/") and not n.endswith("/")}
    src = src.replace("/*%%PACK%%*/null", json.dumps({"info": info, "files": files}))

    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    open(a.out, "w", encoding="utf-8").write(src)
    print(f"OK : {a.out} ({len(src) // 1024} Ko)")


if __name__ == "__main__":
    main()
