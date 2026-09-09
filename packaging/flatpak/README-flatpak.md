# Packaging yt-dlp-app as a Flatpak

Flatpak builds happen in a network-isolated sandbox, so you can't just
`pip install` at build time the way `uv sync` does locally - every
dependency has to be pre-declared as a source (a URL + checksum) that
flatpak-builder downloads *before* sealing off the network. That's the
main extra step compared to a normal Python project.

## 0. Rename the app ID first

Everything here uses the placeholder `io.github.franklin.YtDlpApp`.
Rename the manifest file, and every occurrence of that string inside
`io.github.franklin.YtDlpApp.yml`, `.desktop`, and `.metainfo.xml`, to
your own reverse-DNS id (e.g. `io.github.<your-username>.YtDlpApp`).
This only matters for publishing on Flathub eventually - for purely
local/personal use any id works, it's just the internal name Flatpak
uses to track the app.

## 1. Install the tooling

```bash
flatpak install flathub org.freedesktop.Platform//24.08 org.freedesktop.Sdk//24.08
sudo apt install flatpak-builder     # or your distro's equivalent
```

**Check the runtime's Python version before you commit to a branch:**

```bash
flatpak run --command=python3 org.freedesktop.Sdk//24.08 --version
```

Whatever that prints is the interpreter your app actually runs on
inside the Flatpak, independent of what your local `uv` venv uses. If
you want 3.14 specifically and `24.08` isn't there yet, check newer
branches (e.g. `25.08`) the same way, and update `runtime-version` in
the manifest to match. Note: freedesktop-sdk 25.08 also replaced the
`ffmpeg-full` extension with a new `codecs-extra` extension - if you
move to 25.08 you'll need to update the `add-extensions` block in the
manifest accordingly (check `docs.flathub.org` for the current name).

## 2. Generate the offline Python dependency list

Grab the generator script (a single Python file, no install needed):

```bash
curl -O https://raw.githubusercontent.com/flatpak/flatpak-builder-tools/master/pip/flatpak-pip-generator
python3 flatpak-pip-generator --output python3-requirements yt-dlp PyQt6
```

This produces `python3-requirements.json` - a flatpak-builder module
listing every package (including transitive deps) as a pinned
URL+sha256 source. Open `io.github.franklin.YtDlpApp.yml` and either:

- add `"python3-requirements.json"` to the manifest's top-level
  `modules:` list *before* the `yt-dlp-app` module (flatpak-builder
  supports referencing external module files directly by filename), or
- paste its contents in place of the commented-out
  `python3-requirements` placeholder module in the manifest.

Put it before the `yt-dlp-app` module - the app's own `pip3 install`
step needs `yt-dlp` and `PyQt6` already present.

## 3. Build

From the project root (one level up from `packaging/flatpak/`):

```bash
flatpak-builder --user --install --force-clean build-dir \
  packaging/flatpak/io.github.franklin.YtDlpApp.yml
```

`--install` puts it in your user Flatpak install so you can just run:

```bash
flatpak run io.github.franklin.YtDlpApp
```

## 4. Iterating

Every time you change `src/`, just re-run the same `flatpak-builder`
command - the `sources: type: dir` entry for the `yt-dlp-app` module
points at the live project directory, so it picks up edits without
regenerating the pip requirements (you only need to redo step 2 if you
change or add dependencies in `pyproject.toml`).

## Sanity checks if the build fails

- **"No module named PyQt6" at runtime but build succeeded:** usually
  means `python3-requirements.json` was generated against a different
  Python version/platform than the SDK's own `python3`. Regenerate it
  from *inside* the SDK: `flatpak run --command=python3
  org.freedesktop.Sdk//24.08 -m pip ...` style invocation, or check the
  generator's `--python3` flag options.
- **App launches but window is blank / crashes on a GL error:** try
  dropping `--device=dri` temporarily to see if it's a graphics-driver
  passthrough issue rather than an app bug.
- **ffmpeg not found at runtime:** confirm the extension's
  `version:` matches `runtime-version:` exactly, and that
  `add-ld-path` / `directory` match what the ffmpeg-full extension
  actually installs to (this has changed across freedesktop-sdk
  releases, per the 25.08 note above).
