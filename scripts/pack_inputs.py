#!/usr/bin/env python3
"""Pack your own NSP files and prod.keys into one zip for the cloud build.

    python3 scripts/pack_inputs.py --nsp-dir ~/Games/SMO --keys ~/keys/prod.keys -o smo-inputs.zip

Zip layout (what scripts/prepare_inputs.py expects):

    prod.keys
    nsp/<your files>.nsp

The zip contains your private game data and keys. Host it somewhere only you
can reach (see README) and never commit it. Key contents are never printed.
"""
import argparse
import hashlib
import re
import sys
import zipfile
from pathlib import Path

SMO_BASE = "0100000000010000"
SMO_UPDATE = "0100000000010800"  # updates use the base title ID + 0x800
TITLE_RE = re.compile(r"\[([0-9A-Fa-f]{16})\]")
KEY_LINE_RE = re.compile(r"^\s*([A-Za-z0-9_]+)\s*=\s*([0-9A-Fa-f]+)\s*$")


def title_ids(name):
    return {m.upper() for m in TITLE_RE.findall(name)}


def check_keys(path):
    """Return the number of valid 'name = hex' lines. Never returns key values."""
    count = 0
    names = set()
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            m = KEY_LINE_RE.match(line)
            if m:
                count += 1
                names.add(m.group(1))
    return count, names


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--nsp-dir", required=True, type=Path, help="folder with the base NSP, the update NSP (and DLC)")
    ap.add_argument("--keys", required=True, type=Path, help="path to your prod.keys")
    ap.add_argument("-o", "--output", default=Path("smo-inputs.zip"), type=Path)
    ap.add_argument("--title-id", default=SMO_BASE, help="base game title ID to require (default: Super Mario Odyssey)")
    args = ap.parse_args(argv)

    if not args.nsp_dir.is_dir():
        print(f"error: {args.nsp_dir} is not a folder", file=sys.stderr)
        return 1
    if not args.keys.is_file():
        print(f"error: {args.keys} not found", file=sys.stderr)
        return 1

    nsps = sorted(p for p in args.nsp_dir.iterdir() if p.is_file() and p.suffix.lower() == ".nsp")
    xcis = [p for p in args.nsp_dir.iterdir() if p.is_file() and p.suffix.lower() in (".xci", ".nsz", ".xcz")]
    if not nsps:
        if xcis:
            print("error: found XCI/NSZ/XCZ files but no .nsp. nxnative reads plain NSP files only;"
                  " convert them to NSP first.", file=sys.stderr)
        else:
            print(f"error: no .nsp files in {args.nsp_dir}", file=sys.stderr)
        return 1
    if xcis:
        print(f"note: ignoring {len(xcis)} XCI/NSZ/XCZ file(s); only .nsp is packed")

    named = [p for p in nsps if title_ids(p.name)]
    if named:
        wanted = args.title_id.upper()
        if not any(wanted in title_ids(p.name) for p in named):
            print(f"error: no NSP name carries the title ID [{wanted}]. Wrong game?", file=sys.stderr)
            return 1
        if wanted == SMO_BASE and not any(SMO_UPDATE in title_ids(p.name) for p in named):
            print(f"warning: no update NSP [{SMO_UPDATE}] found. The base game alone may not match nxnative's expectations.")
    else:
        print("warning: no NSP file name contains a [16-hex title ID]; nxnative will fall back to the ticket inside the NSP.")

    key_count, key_names = check_keys(args.keys)
    if key_count == 0:
        print("error: prod.keys has no 'name = hex' lines. Is it the right file?", file=sys.stderr)
        return 1
    if "master_key_00" not in key_names and "header_key" not in key_names:
        print("warning: prod.keys has neither master_key_00 nor header_key; it may be incomplete.")

    out = args.output
    if out.exists():
        print(f"error: {out} already exists; remove it first", file=sys.stderr)
        return 1

    # NSPs are already encrypted/compressed, so store them without recompression.
    with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_STORED, allowZip64=True) as zf:
        zf.write(args.keys, "prod.keys")
        for p in nsps:
            print(f"adding nsp/{p.name} ({p.stat().st_size / 1e9:.2f} GB)")
            zf.write(p, f"nsp/{p.name}")

    digest = sha256_file(out)
    print(f"\nwrote {out} ({out.stat().st_size / 1e9:.2f} GB), {len(nsps)} NSP(s), {key_count} key line(s)")
    print(f"sha256: {digest}")
    print("Put that sha256 in the INPUT_ZIP_SHA256 secret to have the build verify the download.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
