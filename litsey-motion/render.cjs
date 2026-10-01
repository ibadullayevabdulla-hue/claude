#!/usr/bin/env node
// Renders index.html frame-by-frame into an MP4 (Playwright + ffmpeg), in
// parallel chunks, then muxes in the soundtrack from soundtrack.py.
//
//   node render.cjs                     # out/litsey-video.mp4
//   node render.cjs --workers=4 --fps=30
//   node render.cjs --mux               # keep the rendered video, redo only the audio
//   node render.cjs --stills=5,12.3     # PNG stills only, for checking frames
//   node render.cjs --thumb             # out/thumbnail.jpg (YouTube thumbnail)
"use strict";
const http = require("node:http");
const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");
const { spawn, spawnSync } = require("node:child_process");
const { once } = require("node:events");

const args = Object.fromEntries(process.argv.slice(2).map(a => {
  const [k, v = "1"] = a.replace(/^--/, "").split("=");
  return [k, v];
}));
const fps = Number(args.fps || 30);
const workers = Number(args.workers || Math.max(1, os.cpus().length));
const outDir = path.join(__dirname, "out");
const out = args.out || path.join(outDir, "litsey-video.mp4");
const silent = path.join(outDir, ".video.mp4");
fs.mkdirSync(outDir, { recursive: true });

function run(cmd, argv) {
  const r = spawnSync(cmd, argv, { stdio: ["ignore", "pipe", "inherit"], encoding: "utf8" });
  if (r.status !== 0) throw new Error(`${cmd} exited with ${r.status ?? r.error}`);
  return r.stdout.trim();
}

function mux() {
  if (args["no-audio"]) { fs.renameSync(silent, out); return; }
  const wav = run("python3", [path.join(__dirname, "soundtrack.py")]);
  run("ffmpeg", ["-y", "-loglevel", "error", "-i", silent, "-i", wav,
    "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
    "-shortest", "-movflags", "+faststart", out]);
  run("ffmpeg", ["-y", "-loglevel", "error", "-i", wav, "-c:a", "libmp3lame", "-b:a", "192k", path.join(outDir, "soundtrack.mp3")]);
  fs.unlinkSync(silent);
}

if (args.mux) {
  run("ffmpeg", ["-y", "-loglevel", "error", "-i", out, "-map", "0:v", "-c", "copy", silent]);
  mux();
  console.log(out);
  process.exit(0);
}

let chromium;
try { ({ chromium } = require("playwright")); }
catch { console.error("playwright not found — run `npm install` in this folder first"); process.exit(1); }

const TYPES = { ".html": "text/html; charset=utf-8", ".json": "application/json", ".woff2": "font/woff2", ".png": "image/png", ".jpg": "image/jpeg", ".webp": "image/webp", ".mp3": "audio/mpeg" };
const server = http.createServer((req, res) => {
  const p = path.join(__dirname, decodeURIComponent(new URL(req.url, "http://x").pathname));
  if (!p.startsWith(__dirname) || !fs.existsSync(p) || fs.statSync(p).isDirectory()) { res.writeHead(404); return res.end(); }
  res.writeHead(200, { "content-type": TYPES[path.extname(p)] || "application/octet-stream" });
  fs.createReadStream(p).pipe(res);
});

async function openPage(browser, url) {
  const page = await browser.newPage({ viewport: { width: 1920, height: 1080 }, deviceScaleFactor: 1 });
  await page.goto(url);
  await page.evaluate(() => window.__ready);
  return page;
}

(async () => {
  server.listen(0);
  await once(server, "listening");
  const url = `http://127.0.0.1:${server.address().port}/index.html?render`;
  const browser = await chromium.launch(process.env.CHROMIUM_PATH ? { executablePath: process.env.CHROMIUM_PATH } : {});

  if (args.thumb) {  // YouTube thumbnail, 1280x720
    const page = await browser.newPage({ viewport: { width: 1280, height: 720 }, deviceScaleFactor: 1 });
    await page.goto(url.replace("index.html?render", "thumb.html"));
    await page.evaluate(() => document.fonts.ready);
    await page.waitForTimeout(300);
    const file = path.join(outDir, "thumbnail.jpg");
    await page.screenshot({ path: file, type: "jpeg", quality: 92 });
    console.log(file);
  } else if (args.stills) {
    const page = await openPage(browser, url);
    for (const t of args.stills.split(",").map(Number)) {
      await page.evaluate(t => window.__seek(t), t);
      const file = path.join(outDir, `still-${t.toFixed(2).padStart(6, "0")}.png`);
      await page.screenshot({ path: file });
      console.log(file);
    }
  } else {
    const probe = await openPage(browser, url);
    const frames = Math.round(await probe.evaluate(() => window.__duration) * fps);
    await probe.close();
    const per = Math.ceil(frames / workers), t0 = Date.now(), done = new Array(workers).fill(0);
    const parts = await Promise.all(Array.from({ length: workers }, async (_, w) => {
      const a = w * per, b = Math.min(frames, a + per), part = path.join(outDir, `.part${w}.mp4`);
      const page = await openPage(browser, url);
      // JPEG frames: the browser's PNG encoder is the bottleneck, JPEG q95 is ~2× faster and visually lossless here
      const ff = spawn("ffmpeg", ["-y", "-loglevel", "error", "-f", "image2pipe", "-c:v", "mjpeg", "-framerate", String(fps), "-i", "-",
        "-c:v", "libx264", "-preset", "slow", "-crf", "20", "-pix_fmt", "yuv420p", "-r", String(fps), part], { stdio: ["pipe", "inherit", "inherit"] });
      for (let f = a; f < b; f++) {
        await page.evaluate(t => window.__seek(t), f / fps);
        const buf = await page.screenshot({ type: "jpeg", quality: 95 });
        if (!ff.stdin.write(buf)) await once(ff.stdin, "drain");
        done[w] = f - a + 1;
        if (w === 0 && f % fps === 0) process.stdout.write(`\r${done.reduce((x, y) => x + y)}/${frames} frames  (${((Date.now() - t0) / 1000).toFixed(0)}s)`);
      }
      ff.stdin.end();
      const [code] = await once(ff, "close");
      if (code !== 0) throw new Error(`ffmpeg (part ${w}) exited with ${code}`);
      await page.close();
      return part;
    }));
    const list = path.join(outDir, ".parts.txt");
    fs.writeFileSync(list, parts.map(p => `file '${p}'`).join("\n"));
    run("ffmpeg", ["-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", list, "-c", "copy", "-movflags", "+faststart", silent]);
    parts.forEach(p => fs.unlinkSync(p)); fs.unlinkSync(list);
    mux();
    console.log(`\n${out}  (${((Date.now() - t0) / 1000).toFixed(0)}s)`);
  }
  await browser.close();
  server.close();
})().catch(e => { console.error(e); process.exit(1); });
