import {
  test as base,
  expect,
  type APIRequestContext,
  type Page,
} from "@playwright/test";

// Dev credentials from seed_dev_data.py
const DEV_PASSWORD = "password";

type AuthTokens = {
  admin: string;
  teacher: string;
  student: string;
};

let cachedTokens: AuthTokens | null = null;

async function login(
  request: APIRequestContext,
  email: string,
): Promise<string> {
  const maxAttempts = 5;
  for (let attempt = 1; attempt <= maxAttempts; attempt++) {
    try {
      const res = await request.post("/api/v1/auth/login", {
        data: { email, password: DEV_PASSWORD },
      });
      if (res.ok()) {
        const body = await res.json();
        return body.access_token;
      }
      if (attempt === maxAttempts) {
        throw new Error(
          `Login failed for ${email}: status ${res.status()} ${res.statusText()}`,
        );
      }
    } catch (e) {
      if (attempt === maxAttempts) throw e;
    }
    await new Promise((r) => setTimeout(r, 2_000));
  }
  throw new Error(`Login failed for ${email} after ${maxAttempts} attempts`);
}

async function getTokens(request: APIRequestContext): Promise<AuthTokens> {
  if (cachedTokens) return cachedTokens;
  const [admin, teacher, student] = await Promise.all([
    login(request, "admin@codette.dev"),
    login(request, "teacher@codette.dev"),
    login(request, "student@codette.dev"),
  ]);
  cachedTokens = { admin, teacher, student };
  return cachedTokens;
}

/**
 * Extended Playwright test with `authRequest` fixture.
 *
 * `authRequest` is an APIRequestContext that sends a Bearer token
 * with every request (defaults to admin for maximum permissions in cleanup/setup).
 */
export const test = base.extend<{
  tokens: AuthTokens;
  authRequest: APIRequestContext;
  authedPage: Page;
}>({
  tokens: async ({ request }, use) => {
    const tokens = await getTokens(request);
    await use(tokens);
  },

  authRequest: async ({ playwright, tokens, baseURL }, use) => {
    const ctx = await playwright.request.newContext({
      baseURL: baseURL!,
      extraHTTPHeaders: {
        Authorization: `Bearer ${tokens.admin}`,
      },
    });
    await use(ctx);
    await ctx.dispose();
  },

  authedPage: async ({ page, tokens, baseURL }, use) => {
    // Set the auth token in localStorage before navigating to protected pages.
    // We navigate to a blank page first so we have the right origin for localStorage.
    await page.goto(baseURL!);
    await page.evaluate(
      (token) => localStorage.setItem("auth_token", token),
      tokens.admin,
    );
    await use(page);
  },
});

export { expect };
