import { expect, test } from "@playwright/test";

test.describe("Problem CRUD", () => {
  test.beforeEach(async ({ request }) => {
    // Clean up: delete all existing problems via API
    const response = await request.get("/api/v1/problems/");
    const problems = await response.json();
    for (const p of problems) {
      await request.delete(`/api/v1/problems/${p.uuid}`);
    }
  });

  test("create, list, edit, and delete a problem", async ({ page }) => {
    // 1. Navigate to problems page — empty state
    await page.goto("/problems");
    await expect(page.getByText("No problems yet.")).toBeVisible();

    // 2. Create a problem
    await page.getByRole("button", { name: "Create Problem" }).click();
    await expect(
      page.getByRole("heading", { name: "Create Problem" }),
    ).toBeVisible();

    await page.getByLabel("Title").fill("Two Sum");
    await page.getByLabel("Statement").fill(
      "Return the sum of two integers.",
    );
    await page.getByLabel("Hints").fill("Think about the + operator.");
    await page.getByLabel("Examples").fill("add(1, 2) == 3");
    await page.getByLabel("Test Cases").fill(
      JSON.stringify([
        { input: [1, 2], output: 3 },
        { input: [0, 0], output: 0 },
      ]),
    );
    await page.getByRole("button", { name: "Save" }).click();

    // 3. Verify problem appears in the table
    const row = page.getByRole("row").filter({ hasText: "Two Sum" });
    await expect(row).toBeVisible();
    // Test count column should show 2
    await expect(row.getByRole("cell", { name: "2", exact: true })).toBeVisible();

    // 4. Edit the problem
    await row.getByRole("button", { name: "Edit" }).click();
    await expect(
      page.getByRole("heading", { name: "Edit Problem" }),
    ).toBeVisible();

    const titleInput = page.getByLabel("Title");
    await titleInput.clear();
    await titleInput.fill("Two Sum v2");
    await page.getByRole("button", { name: "Save" }).click();

    // 5. Verify updated title in the table
    const updatedRow = page.getByRole("row").filter({ hasText: "Two Sum v2" });
    await expect(updatedRow).toBeVisible();

    // 6. Delete the problem
    page.on("dialog", (dialog) => dialog.accept());
    await updatedRow.getByRole("button", { name: "Delete" }).click();

    // 7. Verify empty state returns
    await expect(page.getByText("No problems yet.")).toBeVisible();
  });
});
