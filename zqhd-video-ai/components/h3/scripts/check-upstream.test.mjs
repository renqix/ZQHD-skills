import assert from "node:assert/strict";
import { mkdtemp, mkdir, copyFile, writeFile, readFile, stat, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { spawnSync } from "node:child_process";
import { createHash } from "node:crypto";
import { test } from "node:test";

const blobHash = text => createHash("sha1").update(`blob ${Buffer.byteLength(text)}\0`).update(text).digest("hex");

test("更新检查只读，校验失败保留原文件，显式同步才落盘", async () => {
  const root = await mkdtemp(join(tmpdir(), "h3-sync-test-"));
  try {
    await mkdir(join(root, "scripts"));
    await mkdir(join(root, "references"));
    await mkdir(join(root, "bin"));
    await copyFile(new URL("./check-upstream.sh", import.meta.url), join(root, "scripts/check-upstream.sh"));
    const original = "原始规范\n";
    const updated = "更新规范\n";
    const originalHash = blobHash(original);
    const state = `SKILL_MD_REMOTE_SHA=skillhash\nBASE_EN_REMOTE_SHA=${originalHash}\nREF_EN_REMOTE_SHA=${originalHash}\n`;
    await writeFile(join(root, ".upstream-state"), state);
    for (const file of ["base-en.txt", "ref-en.txt"]) await writeFile(join(root, "references", file), original);
    const mock = `#!/usr/bin/env node
const fs = require('node:fs');
const args = process.argv.slice(2);
const url = args.at(-1);
if (process.env.TEST_NETWORK_FAIL) process.exit(22);
if (url.includes('/commits?')) console.log(JSON.stringify([{sha:'fixedcommit',commit:{committer:{date:'2026-09-19'},message:'测试'}}]));
else if (url.includes('/contents/')) {
  if (!url.endsWith('?ref=fixedcommit')) process.exit(23);
  console.log(JSON.stringify({sha:url.includes('SKILL.md')?'skillhash':process.env.TEST_REMOTE_HASH}));
} else {
  if (!url.includes('/fixedcommit/')) process.exit(24);
  fs.writeFileSync(args[args.indexOf('-o')+1], process.env.TEST_DOWNLOAD);
}
`;
    await writeFile(join(root, "bin/curl"), mock, { mode: 0o755 });
    const run = (args = [], env = {}) => spawnSync("bash", [join(root, "scripts/check-upstream.sh"), ...args], {
      encoding: "utf8", env: { ...process.env, PATH: `${root}/bin:${process.env.PATH}`, TEST_REMOTE_HASH: originalHash, TEST_DOWNLOAD: updated, ...env },
    });
    const before = await stat(join(root, ".upstream-state"));
    assert.equal(run().status, 0);
    assert.equal(await readFile(join(root, ".upstream-state"), "utf8"), state);
    assert.equal((await stat(join(root, ".upstream-state"))).mtimeMs, before.mtimeMs);
    assert.equal(run([], { TEST_NETWORK_FAIL: "1" }).status, 2);
    assert.equal(run(["--apply"], { TEST_REMOTE_HASH: blobHash(updated), TEST_DOWNLOAD: "损坏下载" }).status, 2);
    assert.equal(await readFile(join(root, "references/base-en.txt"), "utf8"), original);
    assert.equal(await readFile(join(root, ".upstream-state"), "utf8"), state);
    assert.equal(run(["--apply"], { TEST_REMOTE_HASH: blobHash(updated) }).status, 0);
    assert.equal(await readFile(join(root, "references/base-en.txt"), "utf8"), updated);
    await writeFile(join(root, "references/base-en.txt"), "用户修改");
    assert.equal(run(["--apply"], { TEST_REMOTE_HASH: originalHash, TEST_DOWNLOAD: original }).status, 1);
    assert.equal(await readFile(join(root, "references/base-en.txt"), "utf8"), "用户修改");
  } finally {
    await rm(root, { recursive: true, force: true });
  }
});
