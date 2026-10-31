#!/usr/bin/env node
// 使用本地浏览器渲染已有 SVG；不调用生成服务，不改源照片。
const fs = require('node:fs/promises');
const path = require('node:path');
const { pathToFileURL } = require('node:url');
const crypto = require('node:crypto');

async function main() {
  const args = process.argv.slice(2);
  const directory = args.shift();
  const options = {};
  while (args.length) {
    const key = args.shift();
    if (!['--module-dir', '--browser-executable', '--max-edge'].includes(key) || !args.length) {
      throw new Error('参数应为：输出目录 [--module-dir 本地Node模块目录] [--browser-executable 浏览器路径] [--max-edge 像素]');
    }
    options[key] = args.shift();
  }
  if (!directory) throw new Error('请提供 build_boards.py 生成的看板目录。');
  const dir = path.resolve(directory);
  const modulePath = require.resolve('playwright', options['--module-dir'] ? { paths: [path.resolve(options['--module-dir'])] } : undefined);
  const { chromium } = require(modulePath);
  const maxEdge = Number(options['--max-edge'] || 0);
  if (!Number.isInteger(maxEdge) || maxEdge < 0) throw new Error('--max-edge 必须是非负整数，0表示原始排版尺寸。');
  const files = (await fs.readdir(dir)).filter(name => /^(sources|details|details-clean|multiview|multiview-clean|detail-\d+|view-[A-Z0-9]+)\.svg$/.test(name)).sort();
  if (!files.length) throw new Error('目录中没有本 Skill 生成的 SVG。');
  const browser = await chromium.launch({ headless: true, ...(options['--browser-executable'] ? { executablePath: path.resolve(options['--browser-executable']) } : {}) });
  const records = [];
  try {
    const context = await browser.newContext({ deviceScaleFactor: 1 });
    // 仅允许本地文件与内嵌图像，避免排版渲染访问外部资源。
    await context.route('**/*', route => {
      const url = route.request().url();
      return url.startsWith('file:') || url.startsWith('data:') ? route.continue() : route.abort();
    });
    const page = await context.newPage();
    for (const file of files) {
      const source = path.join(dir, file);
      const svg = await fs.readFile(source, 'utf8');
      const header = svg.match(/<svg\b[^>]*>/)?.[0];
      const width = Number(header?.match(/\bwidth="(\d+)"/)?.[1]);
      const height = Number(header?.match(/\bheight="(\d+)"/)?.[1]);
      if (!(width > 0 && height > 0)) throw new Error(`${file} 缺少有效排版尺寸。`);
      const factor = maxEdge ? Math.min(1, maxEdge / Math.max(width, height)) : 1;
      const outputWidth = Math.max(1, Math.round(width * factor));
      const outputHeight = Math.max(1, Math.round(height * factor));
      const output = path.join(dir, file.replace(/\.svg$/, '.png'));
      const existing = await fs.lstat(output).catch(error => error.code === 'ENOENT' ? null : Promise.reject(error));
      if (existing) throw new Error(`目标已存在，请使用新版本输出目录：${output}`);
      await page.setViewportSize({ width: outputWidth, height: outputHeight });
      await page.goto(pathToFileURL(source).href, { waitUntil: 'load' });
      await page.evaluate(async ({ outputWidth, outputHeight }) => {
        const svgRoot = document.documentElement;
        svgRoot.style.width = `${outputWidth}px`;
        svgRoot.style.height = `${outputHeight}px`;
        await document.fonts.ready;
        const images = Array.from(document.querySelectorAll('image'));
        await Promise.all(images.map(element => new Promise((resolve, reject) => {
          const probe = new Image();
          probe.onload = resolve;
          probe.onerror = () => reject(new Error('内嵌图像无法解码'));
          probe.src = element.getAttribute('href');
        })));
      }, { outputWidth, outputHeight });
      await page.screenshot({ path: output, clip: { x: 0, y: 0, width: outputWidth, height: outputHeight } });
      records.push({ file: path.basename(output), size: [outputWidth, outputHeight], layout_size: [width, height], svg_sha256: crypto.createHash('sha256').update(svg).digest('hex'), png_sha256: crypto.createHash('sha256').update(await fs.readFile(output)).digest('hex') });
    }
  } finally {
    await browser.close();
  }
  const receiptPath = path.join(dir, 'png-export-receipt.json');
  await fs.writeFile(receiptPath, JSON.stringify({ renderer: 'Playwright Chromium，本地SVG栅格渲染；不增加原始细节', outputs: records }, null, 2) + '\n', { flag: 'wx' });
  console.log(JSON.stringify({ exported_count: records.length, receipt: receiptPath }, null, 2));
}

main().catch(error => { console.error(`错误：${error.message}`); process.exitCode = 2; });
