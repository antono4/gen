# AGENTS.md — Image-to-Video Web App

## What this project is
A 100% client-side web app that turns still images into a video using browser APIs
and ffmpeg.wasm. Single-file app at `index.html` + a small static server `serve.py`.

## Tech stack
- Pure HTML/CSS/JS (ES module), no build step.
- ffmpeg.wasm (`@ffmpeg/ffmpeg@0.12.10` + `@ffmpeg/core@0.12.6`) loaded from unpkg CDN.
- Canvas 2D for Ken Burns motion + transitions + captions; frames exported as PNG
  sequence and muxed by ffmpeg.wasm into MP4 (libx264/aac) or WebM (libvpx-vp9/opus).

## Critical: cross-origin isolation (COOP/COEP)
ffmpeg.wasm 0.12.x needs SharedArrayBuffer, which requires the page to be
cross-origin isolated. `serve.py` sends the required headers:
  Cross-Origin-Opener-Policy: same-origin
  Cross-Origin-Embedder-Policy: require-corp
A plain `python3 -m http.server` will NOT work — render will fail. Always use
`serve.py`.

unpkg sends both `Access-Control-Allow-Origin: *` and
`Cross-Origin-Resource-Policy: cross-origin`, so its subresources are loadable
under `require-corp`. (ffmpeg/ffmpeg `toBlobURL` fetches blobs same-origin.)

## Run locally
  python3 serve.py 12000 .
Then open the served URL. Work hosts map port 12000 → work-1, 12001 → work-2.
`serve.py` uses `allow_reuse_address` so it can rebind 12000 after TIME_WAIT.

## Render pipeline (verified)
The ffmpeg command in `index.html` was validated end-to-end against the native
ffmpeg core that ffmpeg.wasm uses:
- MP4: `-framerate N -i f%06d.png [-i a.<ext>] -c:v libx264 -pix_fmt yuv420p
  -preset veryfast -crf 23 -c:a aac -af volume=V -shortest -movflags +faststart out.mp4`
- WebM: `-c:v libvpx-vp9 ... -c:a libopus ...` (WebM container does NOT accept
  AAC — must use Opus/Vorbis for audio).

Gotcha fixed: WebM + aac fails with "Nothing was written into output file". Use
libopus for WebM audio.

## Code map (index.html)
- State: `clips[]` (each: id,file,img,dur,motion,trans,transdur,cap,capsize,
  capcolor,name), `audio`, `selectedId`, `ffmpeg`.
- `drawClip(ctx,W,H,c,t,prev)` — renders one frame (motion + transition-in +
  caption). Takes ctx/W/H explicitly so it works for both preview and an
  offscreen render canvas without resizing the visible canvas.
- `drawCover(ctx,W,H,img,ox,oy)` — cover-fit helper.
- Playback: `loop/findAt/seekTo/play/stop` over `totalDur()`.
- Render: `ensureFFmpeg()` loads core via blob URLs; per-frame PNGs written to
  MEMFS, then `ff.exec(args)`; result blob → `<video>` + download link. MEMFS
  files are deleted after render to avoid leaks on repeated renders.

## Testing notes
- The browser automation tool cannot fill `<input type=file>`, so end-to-end
  render was validated via the equivalent native ffmpeg command (imageio-ffmpeg
  binary, same core) rather than by driving the UI.
- JS syntax checked by extracting the `<script type="module">` block and
  `node --check`.
- COI confirmed live: `self.crossOriginIsolated === true` &&
  `typeof SharedArrayBuffer !== 'undefined'` on work-1.
