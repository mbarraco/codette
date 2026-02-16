import { expect, test } from "./fixtures";

test.describe("Submission CRUD", () => {
  test.beforeEach(async ({ authRequest }) => {
    // Clean up: delete all existing submissions via API
    const subRes = await authRequest.get("/api/v1/submissions/");
    const submissions = await subRes.json();
    for (const s of submissions) {
      await authRequest.delete(`/api/v1/submissions/${s.uuid}`);
    }
    // Clean up problems too
    const probRes = await authRequest.get("/api/v1/problems/");
    const problems = await probRes.json();
    for (const p of problems) {
      await authRequest.delete(`/api/v1/problems/${p.uuid}`);
    }
  });

  test("list, create via API, and delete a submission", async ({
    authedPage: page,
    authRequest,
  }) => {
    // 1. Navigate to submissions page — empty state
    await page.goto("/submissions");
    await expect(page.getByText("No submissions yet.")).toBeVisible();

    // 2. Create a problem via API
    const problemRes = await authRequest.post("/api/v1/problems/", {
      data: {
        title: "Add Numbers",
        statement: "Return the sum of two integers.",
        function_signature: "def add(a, b):",
      },
    });
    const problem = await problemRes.json();

    // 3. Create a submission via API
    await authRequest.post("/api/v1/submissions/", {
      data: {
        problem_uuid: problem.uuid,
        code: "def add(a, b): return a + b",
      },
    });

    // 4. Refresh and verify row appears
    await page.reload();
    const row = page.getByRole("row").filter({ hasText: "Add Numbers" });
    await expect(row).toBeVisible();

    // 5. Delete the submission
    page.on("dialog", (dialog) => dialog.accept());
    await row.getByRole("button", { name: "Delete" }).click();

    // 6. Verify empty state returns
    await expect(page.getByText("No submissions yet.")).toBeVisible();
  });

  test("create submission via UI and verify queue entry on monitor", async ({
    authedPage: page,
    authRequest,
  }) => {
    // 1. Create a problem via API
    const problemRes = await authRequest.post("/api/v1/problems/", {
      data: {
        title: "FizzBuzz",
        statement: "Return FizzBuzz sequence.",
        function_signature: "def fizzbuzz(n):",
      },
    });
    const problem = await problemRes.json();

    // 2. Navigate to submissions page and open the form
    await page.goto("/submissions");
    await page.getByRole("button", { name: "New Submission" }).click();

    // 3. Fill in the form
    await page.getByRole("combobox").selectOption({ label: "FizzBuzz" });
    // CodeMirror renders a contenteditable div — click it and type
    const editor = page.locator(".cm-content");
    await editor.click();
    await editor.fill("def fizzbuzz(n): return list(range(1, n+1))");

    // 4. Submit
    await page.getByRole("button", { name: "Submit" }).click();

    // 5. Verify the submission appears in the list
    await expect(
      page.getByRole("row").filter({ hasText: "FizzBuzz" }),
    ).toBeVisible();

    // 6. Navigate to monitor page and verify the submission appears
    await page.getByRole("link", { name: "Monitor" }).click();
    await expect(page.getByRole("heading", { name: "Monitor" })).toBeVisible();

    const monitorRow = page.getByRole("row").filter({ hasText: "FizzBuzz" });
    await expect(monitorRow).toBeVisible();

    // 7. Verify the row links back to the problem
    const problemLink = monitorRow.getByRole("link", { name: "FizzBuzz" });
    await expect(problemLink).toHaveAttribute(
      "href",
      `/problem/${problem.uuid}`,
    );
  });
});
