/**
 * Shared test helpers for component/view tests.
 * Not a test file itself (no *.test.js suffix), so Vitest won't pick it up as a suite.
 */

// AppShell renders three named slots (page-title, page-subtitle, topbar-left) plus a
// default slot. Views under test only care about their own content, not the real nav
// chrome (which needs router links, auth state, i18n, etc.) — this stub renders all
// slot content flatly so tests can query it, without mounting the real shell.
export const AppShellStub = {
  name: 'AppShell',
  template: `
    <div>
      <div data-testid="page-title"><slot name="page-title" /></div>
      <div data-testid="page-subtitle"><slot name="page-subtitle" /></div>
      <div data-testid="topbar-left"><slot name="topbar-left" /></div>
      <slot />
    </div>
  `,
}

export const SyncStatusBadgeStub = { name: 'SyncStatusBadge', template: '<div />' }
