import AxeBuilder from "@axe-core/playwright";
import { expect, test } from "@playwright/test";

// S-20 (code-buildable slice): automated WCAG 2.2 AA scan of every public
// page, wired into the same Playwright run as P1-17's critical-flow suite.
// This catches critical/serious violations (missing labels, contrast,
// landmark structure) on every CI run — it does NOT replace the human
// usability testing S-20 also calls for (screen-reader walkthroughs, real
// assistive-tech users), which is out of scope for automation.
const PAGES_TO_AUDIT = ["/", "/search", "/admin/schemas", "/tur-alba"];

for (const path of PAGES_TO_AUDIT) {
  test(`WCAG 2.2 AA: ${path} has no critical/serious violations`, async ({ page }) => {
    await page.goto(path);
    const results = await new AxeBuilder({ page }).withTags(["wcag22aa"]).analyze();

    const blocking = results.violations.filter((v) => v.impact === "critical" || v.impact === "serious");
    expect(blocking, JSON.stringify(blocking, null, 2)).toEqual([]);
  });
}
