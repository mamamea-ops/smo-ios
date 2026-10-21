# smo-ios

Cloud build harness and DualSense layer for running **your own** Super Mario Odyssey dump on iOS with [nxnative](https://github.com/seedds/nxnative). You supply the NSPs and `prod.keys` in one zip; a Mac runner does the build. Nothing from any game is in this repository.

## Read this first

- **nxnative does not support Odyssey yet.** Its supported list has no Odyssey profile, and its docs describe adding one as a bring-up on a Mac (host fixes, shader tables, device testing). This repo does not contain that work, so it cannot produce a playable build today.
- What it does now: runs nxnative's **survey** on your files in the cloud (the documented first step of adding a game), and, once nxnative has an Odyssey profile, builds the IPA.
- **Not yet verified:** nothing here has run on a real Mac runner or an iPhone. The Python and C parts have unit tests; the Objective-C DualSense code is only checked by CI on first run.

## Use it

1. Create a **private** repo from this code. The workflow refuses to run in a public repo, because the IPA embeds your game files.
2. On your computer, pack your files (plain `.nsp` only; convert XCI first):
   ```
   python3 scripts/pack_inputs.py --nsp-dir ~/Games/SMO --keys ~/keys/prod.keys -o smo-inputs.zip
   ```
3. Put the zip somewhere only you can reach and get a download URL. Add repo secrets:
   - `INPUT_ZIP_URL` (required)
   - `INPUT_ZIP_SHA256` (printed by the pack script; recommended)
   - `OUTPUT_PUT_URL` (optional; also uploads the IPA there with an HTTP PUT)
4. **Actions → Build IPA → Run workflow.** Start with `mode: survey`. Use `build` once nxnative supports the game.
5. Download the `diagnostics` artifact (and `ipa` in build mode).

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
