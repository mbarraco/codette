import { expect, test } from "./fixtures";

test.describe("Problem CRUD", () => {
  test.beforeEach(async ({ authRequest }) => {
    // Clean up: delete all existing problems via API
    const response = await authRequest.get("/api/v1/problems/");
    const problems = await response.json();
    for (const p of problems) {
      await authRequest.delete(`/api/v1/problems/${p.uuid}`);
    }
  });

  test("create, list, edit, and delete a problem", async ({ authedPage: page }) => {
    // 1. Navigate to problems page — empty state
    await page.goto("/problems");
    await expect(page.getByText("No problems yet.")).toBeVisible();

    // 2. Create a problem
    await page.getByRole("button", { name: "Create Problem" }).click();
    await expect(
      page.getByRole("heading", { name: "Create Problem" }),
    ).toBeVisible();

    await page.getByLabel("Title").fill("Two Sum");
    await page.getByLabel("Function Signature").fill("def add(a, b):");
    await page.getByLabel("Statement").fill(
      "Return the sum of two integers.",
    );
    await page.getByLabel("Hints").fill("Think about the + operator.");
    await page.getByLabel("Examples").fill("add(1, 2) == 3");
    // Add two test cases via the form rows
    await page.getByRole("button", { name: "Add Test Case" }).click();
    await page.getByRole("button", { name: "Add Test Case" }).click();

    const inputs = page.getByLabel("Input");
    const outputs = page.getByLabel("Output");

    await inputs.nth(0).fill("[1, 2]");
    await outputs.nth(0).fill("3");

    await inputs.nth(1).fill("[0, 0]");
    await outputs.nth(1).fill("0");
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
