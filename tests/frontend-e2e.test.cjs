const path = require("path");
const fs = require("fs");
const net = require("net");
const { spawn, spawnSync } = require("child_process");
const { before, after, test } = require("node:test");
const assert = require("node:assert/strict");


function resolvePlaywright() {
  try {
    return require("playwright");
  } catch (error) {
    const bundledRoot = path.join(
      process.env.USERPROFILE || process.env.HOME || "",
      ".cache",
      "codex-runtimes",
      "codex-primary-runtime",
      "dependencies",
      "node",
      "node_modules",
    );
    const bundled = path.join(bundledRoot, "playwright");

    try {
      return require(bundled);
    } catch (bundledError) {
      const pnpmRoot = path.join(bundledRoot, ".pnpm");
      const playwrightEntry = fs.existsSync(pnpmRoot)
        ? fs.readdirSync(pnpmRoot).find((entry) => entry.indexOf("playwright@") === 0)
        : null;

      if (!playwrightEntry) {
        throw bundledError;
      }

      return require(path.join(pnpmRoot, playwrightEntry, "node_modules", "playwright"));
    }
  }
}

const { chromium } = resolvePlaywright();
const repoRoot = path.resolve(__dirname, "..");
const pythonExe = path.join(repoRoot, ".venv", "Scripts", "python.exe");

let frontendProcess;
let backendProcess;
let browser;
let frontendBase;
let apiBase;
let tempDbPath;
let frontendLogs = "";
let backendLogs = "";


function appendLogs(stream, assign) {
  stream.on("data", (chunk) => {
    assign(chunk.toString("utf8"));
  });
}

async function getFreePort() {
  const server = net.createServer();
  await new Promise((resolve, reject) => {
    server.listen(0, "127.0.0.1", resolve);
    server.on("error", reject);
  });
  const { port } = server.address();
  await new Promise((resolve, reject) => server.close((error) => (error ? reject(error) : resolve())));
  return port;
}

async function waitForUrl(url, label) {
  for (let attempt = 0; attempt < 120; attempt += 1) {
    try {
      const response = await fetch(url);
      if (response.ok || response.status < 500) {
        return;
      }
    } catch (error) {
      // Service not ready yet.
    }
    await new Promise((resolve) => setTimeout(resolve, 500));
  }
  throw new Error(`Timed out waiting for ${label} at ${url}.\nFrontend logs:\n${frontendLogs}\nBackend logs:\n${backendLogs}`);
}

function cleanupProcess(child) {
  if (!child || child.killed) {
    return;
  }
  child.kill();
}

async function waitForExit(child) {
  if (!child || child.exitCode !== null) {
    return;
  }
  await Promise.race([
    new Promise((resolve) => child.once("exit", resolve)),
    new Promise((resolve) => setTimeout(resolve, 2000)),
  ]);
}

async function newPage() {
  const context = await browser.newContext();
  const page = await context.newPage();
  await page.goto(frontendBase);
  await page.evaluate((base) => {
    localStorage.setItem("labib-api-base", base);
    localStorage.removeItem("mortgage-monitor-state");
  }, apiBase);
  return page;
}

async function goToWizardStepThree(page) {
  await page.goto(`${frontendBase}/pages/onboarding.html`);
  await page.waitForSelector("[data-wizard-next]");

  await page.fill('[data-bind="basic.propertySettlement"]', "Haifa");
  await page.fill('[data-bind="basic.propertyValue"]', "1650000");
  await page.selectOption('[data-bind="basic.propertyType"]', { index: 0 });
  await page.fill('[data-bind="basic.currentMonthlyPayment"]', "7800");
  await page.selectOption('[data-bind="lender.lenderName"]', { index: 1 });
  await page.fill('[data-bind="basic.yearsSinceOrigin"]', "6");
  await page.fill('[data-bind="basic.remainingTermYears"]', "20");
  await page.click("[data-wizard-next]");
  await page.waitForTimeout(250);

  const tracks = [
    { balance: "420000", rate: "4.5", months: "240" },
    { balance: "280000", rate: "4.1", months: "180" },
    { balance: "190000", rate: "3.8", months: "120" },
  ];

  for (const [index, track] of tracks.entries()) {
    await page.selectOption(`[data-bind="tracks.${index}.type"]`, "fixed_non_linked");
    await page.waitForTimeout(100);
    await page.fill(`[data-bind="tracks.${index}.outstandingBalance"]`, track.balance);
    await page.fill(`[data-bind="tracks.${index}.currentRate"]`, track.rate);
    await page.fill(`[data-bind="tracks.${index}.remainingTermMonths"]`, track.months);
    await page.selectOption(`[data-bind="tracks.${index}.amortizationMethod"]`, { index: 0 });
    await page.fill(`[data-bind="tracks.${index}.prepaymentPenaltyRule"]`, "bank policy");
  }

  await page.click("[data-wizard-next]");
  await page.waitForSelector('[data-testid="wizard-total-costs-value"]');
}

function parseCurrency(text) {
  const numeric = Number(String(text).replace(/[^\d.-]/g, ""));
  if (Number.isNaN(numeric)) {
    throw new Error(`Unable to parse currency from "${text}"`);
  }
  return numeric;
}

async function fillWizardAndSubmit(page, email) {
  await goToWizardStepThree(page);

  await page.fill('[data-bind="costs.prepaymentFee"]', "11000");
  await page.fill('[data-bind="costs.advisor"]', "8200");
  await page.fill('[data-bind="costs.bankFees"]', "4100");
  await page.check('[data-bind="costs.appraisalRequired"]');
  await page.click("[data-wizard-next]");
  await page.waitForTimeout(250);

  await page.fill('[data-bind="preferences.holdingPeriodYears"]', "9");
  await page.selectOption('[data-bind="preferences.riskTolerance"]', "balanced");
  await page.selectOption('[data-bind="preferences.paymentSensitivity"]', "medium");
  await page.selectOption('[data-bind="preferences.goal"]', "monthly_payment");
  await page.selectOption('[data-bind="preferences.inflationAversion"]', "high");
  await page.selectOption('[data-bind="preferences.resetRiskAversion"]', "medium");
  await page.click("[data-wizard-next]");
  await page.waitForTimeout(250);

  await page.fill('[data-bind="account.username"]', "flow-user");
  await page.fill('[data-bind="account.email"]', email);
  await page.fill('[data-bind="account.phone"]', "0501234567");
  await page.fill('[data-bind="account.password"]', "Secure123!");
  await page.fill('[data-bind="account.confirmPassword"]', "Secure123!");
  await page.check('[data-bind="account.terms"]');
  await page.check('[data-bind="account.privacy"]');
  await page.fill('[data-bind="demographics.age"]', "38");
  await page.selectOption('[data-bind="demographics.gender"]', "female");
  await page.selectOption('[data-bind="demographics.maritalStatus"]', "married");
  await page.fill('[data-bind="demographics.occupation"]', "Engineer");
  await page.waitForTimeout(1000);
  await page.click("[data-wizard-next]");
  await page.waitForTimeout(250);

  await page.check('[data-bind="review.confirm"]');
  await page.click("[data-wizard-submit]");
  await page.waitForURL("**/pages/dashboard.html", { timeout: 20000 });
  await page.waitForSelector('[data-testid="dashboard-metrics"]');
  await page.waitForSelector('[data-testid="dashboard-urgency"]');
}

function queryDatabaseByEmail(email) {
  const script = `
import json
import sqlite3
import sys

conn = sqlite3.connect(sys.argv[1])
conn.row_factory = sqlite3.Row
user = conn.execute("select id, email from users where email = ?", (sys.argv[2],)).fetchone()
mortgage = None
if user:
    mortgage = conn.execute(
        "select id, user_id, property_city, estimated_refinance_cost from mortgages where user_id = ? order by id desc limit 1",
        (user["id"],),
    ).fetchone()
print(json.dumps({
    "user": dict(user) if user else None,
    "mortgage": dict(mortgage) if mortgage else None,
}, ensure_ascii=False))
`;

  const result = spawnSync(pythonExe, ["-c", script, tempDbPath, email], {
    cwd: repoRoot,
    encoding: "utf8",
  });

  assert.equal(
    result.status,
    0,
    `SQLite query failed.\nstdout:\n${result.stdout}\nstderr:\n${result.stderr}`
  );

  return JSON.parse(result.stdout.trim());
}

before(async () => {
  const frontendPort = await getFreePort();
  const backendPort = await getFreePort();
  frontendBase = `http://127.0.0.1:${frontendPort}`;
  apiBase = `http://127.0.0.1:${backendPort}/api/v1`;
  tempDbPath = path.join(repoRoot, `.tmp-frontend-e2e-${Date.now()}.db`);

  browser = await chromium.launch({ headless: true, channel: "msedge" });

  frontendProcess = spawn(process.execPath, ["server.js"], {
    cwd: repoRoot,
    env: { ...process.env, PORT: String(frontendPort) },
    stdio: ["ignore", "pipe", "pipe"],
  });
  appendLogs(frontendProcess.stdout, (text) => {
    frontendLogs += text;
  });
  appendLogs(frontendProcess.stderr, (text) => {
    frontendLogs += text;
  });

  backendProcess = spawn(pythonExe, ["-u", "-m", "uvicorn", "backend.app.main:app", "--port", String(backendPort)], {
    cwd: repoRoot,
    env: {
      ...process.env,
      DATABASE_URL: `sqlite+aiosqlite:///${tempDbPath.replace(/\\/g, "/")}`,
      FRONTEND_URL: frontendBase,
    },
    stdio: ["ignore", "pipe", "pipe"],
  });
  appendLogs(backendProcess.stdout, (text) => {
    backendLogs += text;
  });
  appendLogs(backendProcess.stderr, (text) => {
    backendLogs += text;
  });

  await waitForUrl(`${frontendBase}/pages/onboarding.html`, "frontend");
  await waitForUrl(`${apiBase.replace("/api/v1", "")}/docs`, "backend");

  const refreshResponse = await fetch(`${apiBase}/admin/data-refresh`, { method: "POST" });
  assert.equal(
    refreshResponse.status,
    200,
    `Market data refresh failed.\nFrontend logs:\n${frontendLogs}\nBackend logs:\n${backendLogs}`
  );
});

after(async () => {
  if (browser) {
    await browser.close();
  }
  cleanupProcess(frontendProcess);
  cleanupProcess(backendProcess);
  await waitForExit(frontendProcess);
  await waitForExit(backendProcess);
  if (tempDbPath && fs.existsSync(tempDbPath)) {
    for (let attempt = 0; attempt < 5; attempt += 1) {
      try {
        fs.unlinkSync(tempDbPath);
        break;
      } catch (error) {
        if (attempt === 4) {
          throw error;
        }
        await new Promise((resolve) => setTimeout(resolve, 300));
      }
    }
  }
});

test("step 3 total cost updates when refinance fees change", async () => {
  const page = await newPage();
  try {
    await goToWizardStepThree(page);

    await page.fill('[data-testid="costs-prepayment-input"]', "12000");
    await page.fill('[data-testid="costs-advisor-input"]', "8200");
    await page.fill('[data-testid="costs-bank-input"]', "4100");
    await page.check('[data-testid="costs-appraisal-checkbox"]');
    await page.waitForTimeout(250);

    const prepaymentValue = Number(await page.locator('[data-testid="costs-prepayment-input"]').inputValue());
    const advisorValue = Number(await page.locator('[data-testid="costs-advisor-input"]').inputValue());
    const bankValue = Number(await page.locator('[data-testid="costs-bank-input"]').inputValue());
    const withAppraisal = parseCurrency(await page.locator('[data-testid="wizard-total-costs-value"]').innerText());
    assert.equal(withAppraisal, prepaymentValue + advisorValue + bankValue + 2500);

    await page.uncheck('[data-testid="costs-appraisal-checkbox"]');
    await page.waitForTimeout(250);

    const withoutAppraisal = parseCurrency(await page.locator('[data-testid="wizard-total-costs-value"]').innerText());
    assert.equal(withoutAppraisal, prepaymentValue + advisorValue + bankValue);
    assert.equal(withAppraisal - withoutAppraisal, 2500);
  } finally {
    await page.context().close();
  }
});

test("onboarding wizard persists the mortgage and lands on a dashboard with analysis", async () => {
  const page = await newPage();
  const email = `wizard-${Date.now()}@example.com`;

  try {
    await fillWizardAndSubmit(page, email);

    const session = await page.evaluate(() => JSON.parse(localStorage.getItem("mortgage-monitor-state")).session);
    assert.equal(session.authenticated, true);
    assert.equal(session.email, email);
    assert.ok(session.userId);

    const dbState = queryDatabaseByEmail(email);
    assert.ok(dbState.user, "Expected the user to be written to SQLite.");
    assert.ok(dbState.mortgage, "Expected the mortgage to be written to SQLite.");
    assert.equal(dbState.mortgage.user_id, dbState.user.id);
    assert.equal(dbState.mortgage.property_city, "Haifa");
    assert.equal(Number(dbState.mortgage.estimated_refinance_cost), 25800);

    const dashboardEnvelope = await page.evaluate(async () => {
      const sessionState = JSON.parse(localStorage.getItem("mortgage-monitor-state")).session;
      const base = localStorage.getItem("labib-api-base");
      const response = await fetch(`${base}/mortgages/dashboard?user_id=${sessionState.userId}`);
      return response.json();
    });

    assert.ok(dashboardEnvelope.dashboard, "Expected the dashboard API to return a payload.");
    assert.ok(dashboardEnvelope.dashboard.recommendationSummary, "Expected dashboard analysis to be present.");
    assert.ok(
      dashboardEnvelope.dashboard.currentMonthlyPayment > 0 &&
        dashboardEnvelope.dashboard.estimatedRefinancePayment > 0,
      "Expected dashboard payment metrics to be populated."
    );
    assert.ok(
      await page.locator('[data-testid="dashboard-metrics"]').isVisible(),
      "Expected the dashboard metrics section to be visible."
    );
    assert.ok(
      await page.locator('[data-testid="dashboard-urgency"]').isVisible(),
      "Expected the dashboard urgency card to be visible."
    );
  } finally {
    await page.context().close();
  }
});
