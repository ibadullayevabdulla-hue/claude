#!/usr/bin/env node
// Renders index.html frame-by-frame into an MP4 with Playwright + ffmpeg,
// then muxes in the soundtrack from soundtrack.py.
//
//   node render.cjs                      # uz, 30 fps -> out/claude-code-uz.mp4
//   node render.cjs --lang=en --fps=60
//   node render.cjs --mux                # keep the rendered video, redo only the audio
//   node render.cjs --no-audio           # silent video
//   node render.cjs --stills=0,5,12.3    # PNG stills only, for checking frames
"use strict";
const http = require("node:http");
const fs = require("node:fs");
const path = require("node:path");
const { spawn, spawnSync } = require("node:child_process");
const { once } = require("node:events");

const args = Object.fromEntries(process.argv.slice(2).map(a => {
  const [k, v = "1"] = a.replace(/^--/, "").split("=");
  return [k, v];
}));
const lang = args.lang || "uz";
const fps = Number(args.fps || 30);
const outDir = path.join(__dirname, "out");
const out = args.out || path.join(outDir, `claude-code-${lang}.mp4`);
const silent = path.join(outDir, `.video-${lang}.mp4`);
fs.mkdirSync(outDir, { recursive: true });

function run(cmd, argv) {
  const r = spawnSync(cmd, argv, { stdio: ["ignore", "pipe", "inherit"], encoding: "utf8" });
  if (r.status !== 0) throw new Error(`${cmd} exited with ${r.status ?? r.error}`);
  return r.stdout.trim();
}

// Synthesises the soundtrack and muxes it with the silent video into `out`.
function mux() {
  if (args["no-audio"]) { fs.renameSync(silent, out); return; }
  const wav = run("python3", [path.join(__dirname, "soundtrack.py"), `--lang=${lang}`]);
  run("ffmpeg", ["-y", "-loglevel", "error", "-i", silent, "-i", wav,
    "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
    "-shortest", "-movflags", "+faststart", out]);
  // MP3 copy for the live HTML player (plays in every browser)
  run("ffmpeg", ["-y", "-loglevel", "error", "-i", wav, "-c:a", "libmp3lame", "-b:a", "192k", path.join(outDir, `soundtrack-${lang}.mp3`)]);
  fs.unlinkSync(silent);
}

if (args.mux) {
  if (!fs.existsSync(out)) { console.error(`${out} not found — render the video first`); process.exit(1); }
  run("ffmpeg", ["-y", "-loglevel", "error", "-i", out, "-map", "0:v", "-c", "copy", silent]);
  mux();
  console.log(out);
  process.exit(0);
}

let chromium;
try { ({ chromium } = require("playwright")); }
catch { console.error("playwright not found — run `npm install` in this folder first"); process.exit(1); }

// Serve this folder over http so @font-face loads (file:// fonts are blocked by CORS).
const TYPES = { ".html": "text/html; charset=utf-8", ".woff2": "font/woff2", ".js": "text/javascript", ".mp3": "audio/mpeg" };
const server = http.createServer((req, res) => {
  const p = path.join(__dirname, decodeURIComponent(new URL(req.url, "http://x").pathname));
  if (!p.startsWith(__dirname) || !fs.existsSync(p) || fs.statSync(p).isDirectory()) { res.writeHead(404); return res.end(); }
  res.writeHead(200, { "content-type": TYPES[path.extname(p)] || "application/octet-stream" });
  fs.createReadStream(p).pipe(res);
});

(async () => {
  server.listen(0);
  await once(server, "listening");
  const url = `http://127.0.0.1:${server.address().port}/index.html?render&lang=${lang}`;

  const browser = await chromium.launch(process.env.CHROMIUM_PATH ? { executablePath: process.env.CHROMIUM_PATH } : {});
  const page = await browser.newPage({ viewport: { width: 1920, height: 1080 }, deviceScaleFactor: 1 });
  await page.goto(url);
  await page.evaluate(() => window.__ready);
  const duration = await page.evaluate(() => window.__duration);

  if (args.stills) {
    for (const t of args.stills.split(",").map(Number)) {
      await page.evaluate(t => window.__seek(t), t);
      const file = path.join(outDir, `still-${lang}-${t.toFixed(2)}.png`);
      await page.screenshot({ path: file });
      console.log(file);
    }
  } else {
    const ff = spawn("ffmpeg", [
      "-y", "-loglevel", "error",
      "-f", "image2pipe", "-framerate", String(fps), "-i", "-",
      "-c:v", "libx264", "-preset", "slow", "-crf", "17", "-pix_fmt", "yuv420p",
      "-movflags", "+faststart", silent
    ], { stdio: ["pipe", "inherit", "inherit"] });
    const frames = Math.round(duration * fps);
    const t0 = Date.now();
    for (let f = 0; f < frames; f++) {
      await page.evaluate(t => window.__seek(t), f / fps);
      const buf = await page.screenshot({ type: "png" });
      if (!ff.stdin.write(buf)) await once(ff.stdin, "drain");
      if (f % fps === 0) process.stdout.write(`\r${lang}: ${f}/${frames} frames  (${((Date.now() - t0) / 1000).toFixed(0)}s)`);
    }
    ff.stdin.end();
    const [code] = await once(ff, "close");
    if (code !== 0) throw new Error(`ffmpeg exited with ${code}`);
    mux();
    console.log(`\n${out}`);
  }
  await browser.close();
  server.close();
})().catch(e => { console.error(e); process.exit(1); });
