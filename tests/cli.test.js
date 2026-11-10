import { test } from 'node:test';
import assert from 'node:assert/strict';
import { mkdtempSync, readFileSync, existsSync, statSync, rmSync, writeFileSync, mkdirSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join, resolve } from 'node:path';
import { spawnSync } from 'node:child_process';

const cli = resolve('bin/caseplay.js');
function run(args, env = {}) {
  return spawnSync(process.execPath, [cli, ...args], { encoding: 'utf8', env: { ...process.env, ...env } });
}
test('init, configure providers privately, and dispatch Docker from deployment directory', () => {
  const temp = mkdtempSync(join(tmpdir(), 'caseplay-cli-'));
  const dir = join(temp, 'deployment with spaces');
  try {
    assert.equal(run(['init', dir]).status, 0);
    assert.ok(existsSync(join(dir, 'LMT_UI/package-lock.json')));
    assert.ok(existsSync(join(dir, 'LMT_Server/main.py')));
    assert.equal(existsSync(join(dir, 'LMT_UI/node_modules')), false);
    const initial = readFileSync(join(dir, '.env'), 'utf8');
    assert.doesNotMatch(initial, /change-this-password/);
    if (process.platform !== 'win32') assert.equal(statSync(join(dir, '.env')).mode & 0o777, 0o600);
    assert.notEqual(run(['init', dir]).status, 0);
    assert.equal(readFileSync(join(dir, '.env'), 'utf8'), initial);
    const key = 'test-secret-never-print';
    const configured = run(['config', '--dir', dir, '--provider', 'custom', '--model', 'example', '--base-url', 'https://example.test/v1'], { CASEPLAY_API_KEY: key });
    assert.equal(configured.status, 0, configured.stderr);
    assert.ok(!configured.stdout.includes(key));
    assert.match(readFileSync(join(dir, '.env'), 'utf8'), /AI_BASE_URL="https:\/\/example.test\/v1"/);
    const switched = run(['config', '--dir', dir, '--provider', 'deepseek'], { CASEPLAY_API_KEY: key });
    assert.equal(switched.status, 0, switched.stderr);
    const saved = readFileSync(join(dir, '.env'), 'utf8');
    assert.match(saved, /DEEPSEEK_API_KEY=/);
    assert.doesNotMatch(saved, /AI_BASE_URL=|AI_MODEL=/);
    const invalid = run(['config', '--dir', dir, '--provider', 'invalid'], { CASEPLAY_API_KEY: key });
    assert.notEqual(invalid.status, 0);
    assert.equal(readFileSync(join(dir, '.env'), 'utf8'), saved);
    if (process.platform !== 'win32') {
      const bin = join(temp, 'bin'); mkdirSync(bin);
      const output = join(temp, 'docker-args.json');
      writeFileSync(join(bin, 'docker'), `#!${process.execPath}\nrequire('node:fs').writeFileSync(process.env.CASEPLAY_TEST_OUTPUT, JSON.stringify(process.argv.slice(2)));\n`, { mode: 0o755 });
      const result = run(['up', '--dir', dir], { PATH: `${bin}:${process.env.PATH}`, CASEPLAY_TEST_OUTPUT: output });
      assert.equal(result.status, 0, result.stderr);
      assert.deepEqual(JSON.parse(readFileSync(output)), ['compose', '--project-directory', dir, '--env-file', join(dir, '.env'), '-f', join(dir, 'compose.yaml'), 'up', '-d', '--build']);
    }
  } finally { rmSync(temp, { recursive: true, force: true }); }
});
