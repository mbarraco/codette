import { expect, test } from "@playwright/test";

test.describe("Submission CRUD", () => {
  test.beforeEach(async ({ request }) => {
    // Clean up: delete all existing submissions via API
    const subRes = await request.get("/api/v1/submissions/");
    const submissions = await subRes.json();
    for (const s of submissions) {
      await request.delete(`/api/v1/submissions/${s.uuid}`);
    }
    // Clean up problems too
    const probRes = await request.get("/api/v1/problems/");
    const problems = await probRes.json();
    for (const p of problems) {
      await request.delete(`/api/v1/problems/${p.uuid}`);
    }
  });

  test("list, create via API, and delete a submission", async ({
    page,
    request,
  }) => {
    // 1. Navigate to submissions page — empty state
    await page.goto("/submissions");
    await expect(page.getByText("No submissions yet.")).toBeVisible();

    // 2. Create a problem via API
    const problemRes = await request.post("/api/v1/problems/", {
      data: {
        title: "Two Sum",
        statement: "Return the sum of two integers.",
      },
    });
    const problem = await problemRes.json();

    // 3. Create a submission via API
    await request.post("/api/v1/submissions/", {
      data: {
        problem_uuid: problem.uuid,
        code: "def add(a, b): return a + b",
      },
    });

    // 4. Refresh and verify row appears
    await page.reload();
    const row = page.getByRole("row").filter({ hasText: "Two Sum" });
    await expect(row).toBeVisible();

    // 5. Delete the submission
    page.on("dialog", (dialog) => dialog.accept());
    await row.getByRole("button", { name: "Delete" }).click();

    // 6. Verify empty state returns
    await expect(page.getByText("No submissions yet.")).toBeVisible();
  });
});
