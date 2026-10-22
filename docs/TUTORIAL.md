# Tutorial: from your game files to an IPA

Checked against nxnative's README and docs on 22 October 2026.

> **Status of Super Mario Odyssey.** nxnative's supported-games list does not include Odyssey, and there is no `dm/games/0100000000010000/` profile in it. Until there is, you cannot get a playable Odyssey IPA from nxnative or from this repo. What works today: everything below for the games nxnative does support, and a **survey** for Odyssey. The workflow detects a profile automatically, so this tutorial will work for Odyssey unchanged once nxnative adds one.
>
> To test the whole pipeline now, use a supported game you own (for example Super Mario Bros. Wonder, title ID `010015100B514000`) and set the `title_id` input in step B5.

Use only dumps from your own Switch. Never commit, paste or share your keys or game files.

---

## 1. Prepare your files (needed for both routes)

You need, for one game:

- the **base game** as a plain `.nsp`
- the **update** `.nsp` (and any DLC the game's row in nxnative's README mentions)
- your **`prod.keys`**

Rules that avoid the usual failures:

- **NSP only.** XCI, NSZ and XCZ are not read. Convert them to NSP first.
- **Keep the `[title ID]` in the file names**, as in `Game [010015100B514000][v0].nsp`. nxnative finds the game profile from it (it falls back to the ticket inside the NSP).
- **Use the update version nxnative lists** for that game. When Odyssey is added, its README row will say which one.
- Updates carry the base title ID plus `0x800`. For Odyssey that is base `0100000000010000`, update `0100000000010800`. For Wonder: `010015100B514000` and `010015100B514800`.
- Put one game's files in one folder:

```
~/Games/SMO/
  Super Mario Odyssey [0100000000010000][v0].nsp
  Super Mario Odyssey [0100000000010800][v...].nsp
```

---

## Route A: build on a Mac you control

This is nxnative's own documented flow. You need a Mac with [Xcode](https://apps.apple.com/app/xcode/id497799835) and [Homebrew](https://brew.sh), and free disk space of about twice the NSPs' size plus 10 GB.

**A1. Get nxnative and its tools** (once):

```
git clone https://github.com/seedds/nxnative.git && cd nxnative
brew install xcodegen zstd spirv-cross
brew install --cask dotnet-sdk
python3 -m pip install lz4 capstone fonttools
```

**A2. Build:**

```
python3 scripts/build_ipa_from_nsp.py ~/Games/SMO -k ~/keys/prod.keys
```

The IPA appears in the same folder as the NSPs. The first build takes 30 to 60 minutes, later ones about 10. `-h` lists the options (`-o` output path, `--app-name` home-screen name).

**A3. If nxnative has no profile for the game**, the script does not produce a normal build. It writes `<title ID>_survey/survey.md` next to your NSPs (modules, SDK, engine, rewrite sites, imports compared with the host). That survey is the first step of adding a game, not a playable result. `--survey-only` stops there.

Then go to step 3 (install).

---

## Route B: build in the cloud with this repo

Everything runs on a Mac runner. Steps B1 to B3 need a **computer**: the files are several GB, which is impractical to handle from a phone. Steps B4 to B6 work from a phone browser.

**B1. Create your private repo.** Put this code in a new **private** repository. The workflow refuses to run in a public one, because the IPA contains your game files and public-repo artifacts can be downloaded by anyone.

**B2. Pack your files into one zip** (on your computer, in a clone of this repo):

```
python3 scripts/pack_inputs.py --nsp-dir ~/Games/SMO --keys ~/keys/prod.keys -o smo-inputs.zip
```

It checks the NSPs and the keys file (it never prints key values), writes the zip, and prints a `sha256:` line. Copy that line's hash for B4. It warns if the update NSP is missing and stops if the title ID does not match.

**B3. Host the zip privately and get a direct download URL.** The URL must return the file itself, not a web page. A pre-signed link from your own storage works well. With the AWS CLI, for example:

```
aws s3 cp smo-inputs.zip s3://YOUR-PRIVATE-BUCKET/smo-inputs.zip
aws s3 presign s3://YOUR-PRIVATE-BUCKET/smo-inputs.zip --expires-in 86400
```

That link is valid for 24 hours. Delete the object when the build is done. (GitHub release assets are capped at 2 GB per file, so they cannot hold this zip. File-sharing pages from consumer cloud drives usually return a web page instead of the file.)

**B4. Add the secrets.** In your repo: **Settings, Secrets and variables, Actions, New repository secret.**

| Secret | Required | Value |
| --- | --- | --- |
| `INPUT_ZIP_URL` | yes | the download URL from B3 |
| `INPUT_ZIP_SHA256` | recommended | the hash printed in B2; the build stops if the download differs |
| `OUTPUT_PUT_URL` | no | a pre-signed upload URL; the IPA is also uploaded there |

**B5. Run it.** **Actions, Build IPA, Run workflow.** Inputs:

- `mode`: leave on `auto`. It builds if nxnative has a profile for the game and runs a survey if not. `survey` and `build` force one or the other.
- `title_id`: `0100000000010000` for Odyssey, or another base title ID such as `010015100B514000` to test with Wonder.
- `nxnative_ref`: `main`, or a full commit SHA to pin a version. The run summary shows which commit was used.
- `runner`: `macos-26` by default. If the run stops with a disk-space message, use a larger or self-hosted Mac.

The run summary also says `profile <id>: found` or `missing`.

**B6. Download the results** from the run page, under **Artifacts**:

- `diagnostics`: the survey, logs, and the report for the DualSense wiring. Always uploaded.
- `ipa`: only when a build produced one.

Extracted game files and rewritten code are never uploaded. Everything the build unpacked is deleted from the runner when it finishes.

Other Macs (EC2 Mac, MacStadium, your own): run `scripts/cloud_build.sh` there with `INPUT_ZIP_PATH=/path/to/smo-inputs.zip` instead of `INPUT_ZIP_URL`. Output goes to `./out`.

---

## 3. Install the IPA

The IPA is unsigned. Install it with a sideloading tool such as AltStore, Sideloadly or LiveContainer. The device needs iOS or iPadOS 26 or later. Several games are 3 to 16 GB, so check your free storage first.

## 4. Play

- Tap **2D** or **3D** at the top for the touch layout.
- A connected controller hides the touch controls and keeps every button. The DualSense extras in this repo (rumble, gyro, light bar) are not wired in yet; see `dualsense/README.md`.
- Saves and logs are in the Files app under the app's name: `save/` and `log.txt`. If something goes wrong, `log.txt` (and `log.prev.txt`) is what to look at.
- Settings without rebuilding go in `Documents/env.txt`, one `KEY=VALUE` per line.

## 5. When something fails

| Symptom | Cause and fix |
| --- | --- |
| Workflow says the repository is public | Make the repo private (Settings, Danger Zone). |
| `INPUT_ZIP_URL` error or empty download | The secret is missing, expired, or points to a web page. Re-create the link (B3). |
| SHA-256 mismatch | The zip changed or the download was cut off. Re-pack, and update `INPUT_ZIP_SHA256`. |
| "Wrong game" | The NSP names carry a different title ID than the `title_id` input. |
| "not enough free disk space" | Use a runner with more disk (the `runner` input). |
| Run ends with a survey and no IPA | nxnative has no profile for that title ID yet (`profile ...: missing` in the summary). |
| Upload of the `ipa` artifact fails | The IPA is larger than your artifact storage quota. Use `OUTPUT_PUT_URL`, or a plan or runner setup that allows it. |
| Build fails inside nxnative | Open `diagnostics/nxnative-build.log`. Check the nxnative issues page before filing anything, and never post keys. |

## Checking whether Odyssey has been added

Any of these tells you:

- The **Games** table in [nxnative's README](https://github.com/seedds/nxnative) lists it.
- A run of this workflow on `main` shows `profile 0100000000010000: found`.
- In a clone of nxnative: `python3 dm/games/game.py list` shows `0100000000010000`.

Adding a game is an engineering project (host fixes, shader tables, testing on a device), described in nxnative's `docs/agents/README.md`. The survey this repo produces is its first input.
