#!/usr/bin/env python3
"""Sauvegarde locale des groupes de sons Specdrums Mix (usage privé).

L'application d'origine téléchargeait ses groupes de sons depuis le projet Firebase de Sphero
(`sphero-specdrums-mix`). Tant que ce service reste en ligne, ce script récupère le catalogue
(`m4aSoundPacks`) et les fichiers audio/pochettes, puis prépare des archives .zip à importer dans
la webapp (onglet BIBLIOTHÈQUE > IMPORTER DES PACKS).

Les fichiers obtenus restent la propriété de Sphero : ne les publiez pas.

Usage :
    python3 tools/fetch_packs.py                 # -> packs/specdrums-packs-N.zip
    python3 tools/fetch_packs.py --out mes-packs --max-zip-mb 37

ffmpeg (optionnel) convertit les quelques fichiers WAV (piano) en FLAC sans perte.
"""
import argparse, collections, concurrent.futures as cf, json, os, shutil, subprocess, sys, urllib.parse, urllib.request, zipfile

DB = "https://sphero-specdrums-mix.firebaseio.com/m4aSoundPacks.json"
STORAGE = "https://firebasestorage.googleapis.com/v0/b/sphero-specdrums-mix.appspot.com/o/{}?alt=media"


def get(url, tries=3):
    for i in range(tries):
        try:
            with urllib.request.urlopen(url, timeout=60) as r:
                return r.read()
        except Exception as e:  # noqa: BLE001
            if i == tries - 1:
                raise
    return b""


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default="packs")
    ap.add_argument("--max-zip-mb", type=float, default=37)
    a = ap.parse_args()
    cache = os.path.join(a.out, "files"); os.makedirs(cache, exist_ok=True)

    print("Catalogue…")
    packs = json.loads(get(DB))
    paths = set()
    for p in packs.values():
        if p.get("artworkPath"): paths.add(p["artworkPath"])
        for s in p.get("sounds", {}).values():
            if s.get("soundPath"): paths.add(s["soundPath"])
    print(f"{len(packs)} groupes de sons, {len(paths)} fichiers")

    def dl(path):
        dst = os.path.join(cache, path)
        if os.path.exists(dst) and os.path.getsize(dst): return None
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        try:
            open(dst, "wb").write(get(STORAGE.format(urllib.parse.quote(path, safe=""))))
        except Exception as e:  # noqa: BLE001
            return f"{path} : {e}"
    with cf.ThreadPoolExecutor(12) as ex:
        fails = [f for f in ex.map(dl, sorted(paths)) if f]
    if fails:
        print("Échecs :", *fails, sep="\n  ")

    # WAV -> FLAC (sans perte) si ffmpeg est disponible
    if shutil.which("ffmpeg"):
        for p in packs.values():
            for s in p.get("sounds", {}).values():
                sp = s.get("soundPath", "")
                if sp.endswith(".wav"):
                    src, dst = os.path.join(cache, sp), os.path.join(cache, sp[:-4] + ".flac")
                    if os.path.exists(src) and not os.path.exists(dst):
                        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", src, "-c:a", "flac", dst], check=True)
                    if os.path.exists(dst): s["soundPath"] = sp[:-4] + ".flac"

    catalog = os.path.join(a.out, "packs.json")
    json.dump({"version": 1, "source": "sphero-specdrums-mix (Firebase m4aSoundPacks)", "packs": packs},
              open(catalog, "w", encoding="utf-8"), ensure_ascii=False)

    # regroupe les familles de packs (Hip-Hop 1..4 partagent les mêmes sons) dans des zips de taille bornée
    fam = collections.defaultdict(set)
    for k, p in packs.items():
        key = (p.get("localization", {}).get("fr") or p["name"]).strip().rstrip("0123456789 ").strip()
        fam[key] |= {s["soundPath"] for s in p.get("sounds", {}).values()} | ({p["artworkPath"]} if p.get("artworkPath") else set())
    size = lambda f: os.path.getsize(os.path.join(cache, f)) if os.path.exists(os.path.join(cache, f)) else 0
    bins = []
    for k in sorted(fam, key=lambda k: -sum(map(size, fam[k]))):
        s = sum(map(size, fam[k]))
        for b in bins:
            if b["size"] + s <= a.max_zip_mb * 1e6: b["fams"].append(k); b["size"] += s; break
        else:
            bins.append({"fams": [k], "size": s})
    for i, b in enumerate(bins, 1):
        zn = os.path.join(a.out, f"specdrums-packs-{i}.zip"); written = set()
        with zipfile.ZipFile(zn, "w") as z:
            z.write(catalog, "specdrums-packs/packs.json", compress_type=zipfile.ZIP_DEFLATED)
            for k in b["fams"]:
                for f in sorted(fam[k]):
                    if f in written or not size(f): continue
                    written.add(f); z.write(os.path.join(cache, f), "specdrums-packs/" + f, compress_type=zipfile.ZIP_STORED)
        print(f"{zn} : {os.path.getsize(zn) / 1e6:.1f} Mo, {len(written)} fichiers — {', '.join(b['fams'])}")


if __name__ == "__main__":
    sys.exit(main())
