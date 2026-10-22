# smo-ios

Cloud build harness and DualSense layer for running **your own** Super Mario Odyssey dump on iOS with [nxnative](https://github.com/seedds/nxnative). You supply the NSPs and `prod.keys` in one zip; a Mac runner does the build. Nothing from any game is in this repository.

## Read this first

- **nxnative does not support Odyssey yet** (checked 22 October 2026: its supported-games list has no Odyssey, and there is no `dm/games/0100000000010000/` profile). This repo does not contain a profile, because one has to be brought up and tested on a Mac and an iPhone. It cannot produce a playable Odyssey build today.
- What it does now: builds an IPA for any game nxnative supports, and runs nxnative's **survey** for games it does not (the first step of adding a game). In `auto` mode it checks the nxnative commit for a profile and builds as soon as one exists, with no changes to this repo.
- **Not yet verified:** nothing here has run on a real Mac runner or an iPhone. The Python, shell and C parts have unit tests; the Objective-C DualSense code is only checked by CI on first run.

## Use it

Full walkthrough: **[docs/TUTORIAL.md](docs/TUTORIAL.md)** (prepare the files, build on your own Mac or in the cloud, install, troubleshoot). Short version of the cloud route:

1. Create a **private** repo from this code. The workflow refuses to run in a public repo, because the IPA embeds your game files.
2. On a computer, pack your files (plain `.nsp` only; convert XCI first):
   ```
   python3 scripts/pack_inputs.py --nsp-dir ~/Games/SMO --keys ~/keys/prod.keys -o smo-inputs.zip
   ```
3. Put the zip somewhere only you can reach and get a direct download URL. Add repo secrets:
   - `INPUT_ZIP_URL` (required)
   - `INPUT_ZIP_SHA256` (printed by the pack script; recommended)
   - `OUTPUT_PUT_URL` (optional; also uploads the IPA there with an HTTP PUT)
4. **Actions, Build IPA, Run workflow.** Leave `mode` on `auto`. Set `title_id` if the game is not Odyssey.
5. Download the `diagnostics` artifact (and `ipa` when one was built).

## Limits to check before running

- **Disk:** nxnative needs about twice the NSPs' size plus 10 GB free. The script checks this and fails early. Standard GitHub Mac runners list only 14 GB of storage, so you will likely need a larger or self-hosted Mac (`runner` input).
- **Cost and quota:** private repos bill macOS minutes at a multiplier, and the IPA is several GB, which may exceed your artifact storage quota. Check your plan; `OUTPUT_PUT_URL` is the escape hatch (a single PUT may be capped, for example at 5 GB on S3).
- **Other Macs:** `scripts/cloud_build.sh` runs on any Mac (EC2 Mac, MacStadium). Set `INPUT_ZIP_PATH` instead of `INPUT_ZIP_URL`.
- `nxnative_ref` defaults to `main`; pin a commit SHA for reproducible builds. The resolved commit is shown in the run summary.

## What gets uploaded

Only small text files (survey, provisional profile, logs) and, in build mode, the IPA. Extracted game files, rewritten code and shader libraries are never uploaded. Game data and keys are deleted from the runner on exit. Key contents are never printed.

## DualSense

See [dualsense/README.md](dualsense/README.md). Short version: rumble, gyro and light bar are implemented as a separate module but not wired into nxnative yet; each run produces a report showing where to wire it.

## Tests

```
python3 -m unittest discover -s tests -v
cc -std=c11 -Wall -Wextra -fsanitize=address,undefined tests/test_ds_core.c dualsense/dm_ds_core.c -lm -o /tmp/t && /tmp/t
```

## License

MIT (this repo only). nxnative is cloned at build time and keeps its own license.
