import test from 'node:test';
import assert from 'node:assert/strict';
import { probePi } from '../pi_probe.mjs';

function fixture(overrides = {}) {
  const calls = [];
  const composer = {
    waitFor: async () => { if (overrides.missing) throw new Error('sensitive URL'); },
    isVisible: async () => true, isEnabled: async () => !overrides.disabled,
    isEditable: async () => true,
  };
  const page = {
    goto: async (url, options) => { calls.push(['goto', url, options]); return { status: () => overrides.status ?? 200 }; },
    title: async () => overrides.title ?? 'Pi',
    locator: () => ({ count: async () => overrides.challenge ? 1 : 0 }),
    getByTestId: id => id === 'chat-composer-textbox' ? composer : { isVisible: async () => !!overrides.modal },
    waitForTimeout: async () => {},
  };
  const context = { newPage: async () => page, close: async () => calls.push(['context.close']) };
  const browser = { newContext: async options => { calls.push(['context', options]); return context; }, close: async () => calls.push(['browser.close']) };
  const browserType = { launch: async options => { calls.push(['launch', options]); if (overrides.launchError) throw new Error('secret-value'); return browser; } };
  return { calls, browserType };
}

test('headless bundled Chromium probes only talk with supplied state, closes resources', async () => {
  const f = fixture();
  assert.deepEqual(await probePi({ storageState: 'private-session.json', browserType: f.browserType }), { status: 'available' });
  assert.deepEqual(f.calls[0], ['launch', { headless: true }]);
  assert.equal(f.calls[1][1].storageState, 'private-session.json');
  assert.deepEqual(f.calls.filter(c => c[0] === 'goto').map(c => c[1]), ['https://pi.ai/talk']);
  assert.deepEqual(f.calls.slice(-2), [['context.close'], ['browser.close']]);
});

test('challenge, access denial, missing composer and onboarding fail closed', async () => {
  for (const options of [{ status: 403 }, { status: 401 }, { status: 429 }, { title: 'Just a moment...' }, { title: '请稍候…' }, { challenge: true }, { missing: true }, { disabled: true }, { modal: true }]) {
    const f = fixture(options);
    assert.deepEqual(await probePi({ storageState: 'private', browserType: f.browserType }), { status: 'needs_login' });
    assert.deepEqual(f.calls.slice(-2), [['context.close'], ['browser.close']]);
  }
});

test('missing state never launches; operational errors reveal no raw error', async () => {
  const f = fixture({ launchError: true });
  assert.deepEqual(await probePi({ storageState: '', browserType: f.browserType }), { status: 'needs_login' });
  assert.equal(f.calls.length, 0);
  assert.deepEqual(await probePi({ storageState: 'private', browserType: f.browserType }), { status: 'probe_error' });
  const unavailable = fixture({ status: 503 });
  assert.deepEqual(await probePi({ storageState: 'private', browserType: unavailable.browserType }), { status: 'probe_error' });
});
