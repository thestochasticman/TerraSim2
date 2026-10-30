// Start the Python service and the Next.js dev server together.
// Usage: npm run dev:all   (from app/visualiser, with the borevitz_lab conda env active)
// Stops both when either exits or on Ctrl-C.
import { spawn } from "node:child_process";
import { fileURLToPath } from "node:url";
import path from "node:path";

const here = path.dirname(fileURLToPath(import.meta.url));
const repoRoot = path.resolve(here, "..", "..", "..");
const apiPort = process.env.TERRASIM2_API_PORT ?? "8000";
const python = process.env.PYTHON ?? "python";

const api = spawn(python, ["-m", "app.api.f.serve", apiPort], { cwd: repoRoot, stdio: "inherit" });
const next = spawn("npx", ["next", "dev"], {
  cwd: path.resolve(here, ".."),
  stdio: "inherit",
  env: { ...process.env, TERRASIM2_API_URL: `http://127.0.0.1:${apiPort}` },
});

function stopAll() {
  for (const child of [api, next]) if (child.exitCode === null) child.kill("SIGTERM");
}
api.on("exit", (code) => { console.log(`[dev] api exited (${code})`); stopAll(); });
next.on("exit", (code) => { console.log(`[dev] next exited (${code})`); stopAll(); });
process.on("SIGINT", stopAll);
process.on("SIGTERM", stopAll);
