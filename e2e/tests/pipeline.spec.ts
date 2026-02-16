import { expect, test } from "./fixtures";

test.describe("Pipeline end-to-end", () => {
  test.beforeEach(async ({ authRequest }) => {
    // Clean up submissions first (they reference problems)
    const subRes = await authRequest.get("/api/v1/submissions/");
    const submissions = await subRes.json();
    for (const s of submissions) {
      await authRequest.delete(`/api/v1/submissions/${s.uuid}`);
    }
    // Then clean up problems
    const probRes = await authRequest.get("/api/v1/problems/");
    const problems = await probRes.json();
    for (const p of problems) {
      await authRequest.delete(`/api/v1/problems/${p.uuid}`);
    }
  });

  test("submit correct code and verify it passes on monitor", async ({
    authedPage: page,
    authRequest,
  }) => {
    test.slow(); // triple timeout — worker + runner + grader containers need time

    // 1. Create a problem with test cases via API
    const problemRes = await authRequest.post("/api/v1/problems/", {
      data: {
        title: "Add Numbers",
        statement: "Return the sum of two integers.",
        function_signature: "def add(a, b):",
        test_cases: [
          { input: [1, 2], output: 3 },
          { input: [0, 0], output: 0 },
        ],
      },
    });
    expect(problemRes.ok()).toBeTruthy();
    const problem = await problemRes.json();

    // 2. Navigate to submissions and create via UI
    await page.goto("/submissions");
    await page.getByRole("button", { name: "New Submission" }).click();
    await page.getByRole("combobox").selectOption({ label: "Add Numbers" });

    const editor = page.locator(".cm-content");
    await editor.click();
    await editor.fill("def add(a, b): return a + b");

    await page.getByRole("button", { name: "Submit" }).click();

    // 3. Verify the submission appears
    await expect(
      page.getByRole("row").filter({ hasText: "Add Numbers" }),
    ).toBeVisible();

    // 4. Navigate to monitor and wait for pipeline to complete
    await page.getByRole("link", { name: "Monitor" }).click();
    await expect(page.getByRole("heading", { name: "Monitor" })).toBeVisible();

    const monitorRow = page.getByRole("row").filter({ hasText: "Add Numbers" });

    // Monitor polls every 5s — wait for status badge to show "passed"
    await expect(monitorRow.getByText("passed")).toBeVisible({ timeout: 60_000 });

    // 5. Verify attempt count is 1
    await expect(monitorRow.getByRole("cell", { name: "1", exact: true })).toBeVisible();
  });
});
