import { test, expect } from "./fixtures";

test.describe("Auth API", () => {
  test("login with valid credentials returns a token", async ({ request }) => {
    const res = await request.post("/api/v1/auth/login", {
      data: { email: "admin@codette.dev", password: "password" },
    });
    expect(res.ok()).toBeTruthy();
    const body = await res.json();
    expect(body.access_token).toBeTruthy();
    expect(body.token_type).toBe("bearer");
  });

  test("login with wrong password returns 401", async ({ request }) => {
    const res = await request.post("/api/v1/auth/login", {
      data: { email: "admin@codette.dev", password: "wrong" },
    });
    expect(res.status()).toBe(401);
  });

  test("me endpoint returns user info with valid token", async ({
    authRequest,
  }) => {
    const res = await authRequest.get("/api/v1/auth/me");
    expect(res.ok()).toBeTruthy();
    const body = await res.json();
    expect(body.email).toBe("admin@codette.dev");
    expect(body.role).toBe("admin");
    expect(body.uuid).toBeTruthy();
  });

  test("protected endpoint rejects unauthenticated requests", async ({
    request,
  }) => {
    const res = await request.get("/api/v1/problems/");
    expect(res.status()).toBeGreaterThanOrEqual(401);
  });

  test("register with valid invitation creates a user", async ({
    authRequest,
    request,
  }) => {
    const email = `e2e-test-${Date.now()}@codette.dev`;

    // Admin creates an invitation
    const invRes = await authRequest.post("/api/v1/invitations/", {
      data: { email, role: "student" },
    });
    expect(invRes.ok()).toBeTruthy();

    // Register with the invitation
    const regRes = await request.post("/api/v1/auth/register", {
      data: { email, password: "test-password" },
    });
    expect(regRes.status()).toBe(201);
    const user = await regRes.json();
    expect(user.email).toBe(email);
    expect(user.role).toBe("student");

    // Login with the new account
    const loginRes = await request.post("/api/v1/auth/login", {
      data: { email, password: "test-password" },
    });
    expect(loginRes.ok()).toBeTruthy();
  });

  test("register without invitation returns 400", async ({ request }) => {
    const res = await request.post("/api/v1/auth/register", {
      data: { email: "nobody@codette.dev", password: "test-password" },
    });
    expect(res.status()).toBe(400);
  });

  test("student cannot create invitations", async ({
    playwright,
    tokens,
    baseURL,
  }) => {
    const studentCtx = await playwright.request.newContext({
      baseURL: baseURL!,
      extraHTTPHeaders: { Authorization: `Bearer ${tokens.student}` },
    });
    const res = await studentCtx.post("/api/v1/invitations/", {
      data: { email: "shouldfail@codette.dev", role: "student" },
    });
    expect(res.status()).toBe(403);
    await studentCtx.dispose();
  });

  test("student cannot create problems", async ({
    playwright,
    tokens,
    baseURL,
  }) => {
    const studentCtx = await playwright.request.newContext({
      baseURL: baseURL!,
      extraHTTPHeaders: { Authorization: `Bearer ${tokens.student}` },
    });
    const res = await studentCtx.post("/api/v1/problems/", {
      data: {
        title: "Nope",
        statement: "Should fail.",
        function_signature: "def f():",
      },
    });
    expect(res.status()).toBe(403);
    await studentCtx.dispose();
  });
});
