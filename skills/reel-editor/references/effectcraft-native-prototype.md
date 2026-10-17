# Native EffectCraft reel smoke test

Tested official Linux x86_64 EffectCraft CLI 0.10.0 release on 2026-10-17. The prebuilt CLI ran without installing Rust; source builds still require the toolchain. Both upstream checkouts stayed unmodified. Use the release from storytold/effectcraft, not third-party download sites. No runtime binary belongs in this repository.

## Build a project

Use `scripts/effectcraft_reel_test.py --binary /path/effectcraft-cli --spec /path/local.json --out-dir /path/output --render`. Its docstring documents the manifest. Prepare 1080x1920 PNG stills, continuous matching WAV audio, integer frame intervals and installed fonts. All paths resolve against the spec; basenames must be unique. Inspect fonts with fontconfig and render a preview before full export. For this smoke test Montserrat Medium gave cleaner results than a stroked Cormorant Garamond Bold Italic setup; the cause of the italic artifacts is not isolated.

## Verified command patterns

- `comp.new` accepts width, height, frameRate and duration.
- `file.import` with `sequence:false` imports separate stills. Explicitly inspect returned import errors.
- `layer.addItem` creates the footage layer. Use `layer.rename`, not `layer.settings`, to rename footage: settings rejects this layer kind.
- `layer.timing` sets `start`, `in` and `out` in seconds. Set keyframes with `prop.addKey` and `timeBase:'comp'` to preserve one absolute timeline across late in-points.
- `effect.apply` returns paths such as `effects/#1`. Glow uses `ec.stylize.glow`: threshold72, radius22, intensity0.26 were starting values in the sample. Radial zoom uses `ec.blur.radial`, type1; animate amount14→0 over five frames and scale112→102 percent. These are prototype settings, not recovered reference values.
- Build captions separately over footage. Animate opacity, position and scale without restarting captions at picture cuts. Preserve the user's requested handle.
- `effectcraft-cli --project p.ecproj render --out result.mp4 --format h264 --fps 30 --resolution full --quality best --bitrate 10000 --audio on --json` performs native rendering and encoding. `RAYON_NUM_THREADS=2` bounded the CPU test. FFmpeg was used only outside the app for input preparation and output inspection.

## Actual evidence and limits

A six-second, seven-shot portrait composition with native glow, radial zoom blur, transform keys, cream captions and original song audio exported as H.264 yuv420p at1080x1920/30fps:180 video frames. Native AAC duration6.016s versus video6s; decoded source correlation0.99995 and no measurable offset at8kHz. CPU exports took about46–51s before the final asset-repair pass; do not promise real-time rendering.

Cut candidates at2.1s and3.8s came from a separate Python spectral-flux analysis, not FilmCraft's Rust beat analyzer. The other short montage cuts were editorial decisions. Do not call the whole sample verified beat tracking. FilmCraft DSP and GPU rendering remain untested.

Validate every prepared image by fully decoding it before project import. A truncated PNG produced a blank native scene while export still completed; a successful exit and frame count are insufficient. Recreate only the damaged intermediate from its intact source, reopen the renderer and inspect every scene plus dense transition frames. Run an independent complete-video decode and verify both stream endings before delivery. Keep assets, songs, rendered media and local projects out of git.
