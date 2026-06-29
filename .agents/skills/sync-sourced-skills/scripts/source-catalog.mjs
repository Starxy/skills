#!/usr/bin/env node
import { readFile } from "node:fs/promises";
import path from "node:path";
import process from "node:process";

function usage() {
  console.log(`Usage: node .agents/skills/sync-sourced-skills/scripts/source-catalog.mjs [options]

Options:
  --root <dir>     Repository root. Defaults to the current working directory.
  --skill <name>   Show only one skill.
  --include-local  Include catalog entries without URL sources.
  --json           Print JSON instead of a text table.
  --help           Show this help.
`);
}

function parseArgs(argv) {
  const args = { root: process.cwd(), skill: null, includeLocal: false, json: false, help: false };

  for (let i = 0; i < argv.length; i += 1) {
    const arg = argv[i];

    if (arg === "--help" || arg === "-h") {
      args.help = true;
    } else if (arg === "--json") {
      args.json = true;
    } else if (arg === "--include-local") {
      args.includeLocal = true;
    } else if (arg === "--root") {
      args.root = argv[++i];
    } else if (arg === "--skill") {
      args.skill = argv[++i];
    } else {
      throw new Error(`Unknown argument: ${arg}`);
    }
  }

  return args;
}

function cleanCell(cell) {
  return cell.trim().replace(/^`|`$/g, "");
}

function parseSource(cell) {
  const link = cell.match(/^\[([^\]]+)\]\(([^)]+)\)$/);
  if (link) {
    return { label: link[1], url: link[2], raw: cell };
  }

  const cleaned = cleanCell(cell);
  return { label: cleaned, url: cleaned.startsWith("http") ? cleaned : null, raw: cell };
}

function parseCatalog(readme) {
  const entries = [];

  for (const line of readme.split(/\r?\n/)) {
    if (!line.startsWith("|")) {
      continue;
    }

    const cells = line
      .split("|")
      .slice(1, -1)
      .map((cell) => cell.trim());

    if (cells.length < 4 || cells[0] === "Skill" || cells[0].includes("---")) {
      continue;
    }

    const name = cleanCell(cells[0]);
    const skillPath = cleanCell(cells[1]).replace(/\/$/, "");
    if (!/^[a-z0-9][a-z0-9-]{0,62}$/.test(name) || !skillPath.startsWith("skills/")) {
      continue;
    }

    entries.push({
      name,
      path: skillPath,
      source: parseSource(cells[2]),
      description: cells.slice(3).join(" | ").trim(),
    });
  }

  return entries;
}

function printTable(entries) {
  const rows = entries.map((entry) => ({
    name: entry.name,
    path: entry.path,
    source: entry.source.url ? `${entry.source.label} (${entry.source.url})` : entry.source.label,
  }));

  const widths = {
    name: Math.max("Skill".length, ...rows.map((row) => row.name.length)),
    path: Math.max("Path".length, ...rows.map((row) => row.path.length)),
    source: Math.max("Source".length, ...rows.map((row) => row.source.length)),
  };

  console.log(
    `${"Skill".padEnd(widths.name)}  ${"Path".padEnd(widths.path)}  ${"Source".padEnd(widths.source)}`,
  );
  console.log(`${"-".repeat(widths.name)}  ${"-".repeat(widths.path)}  ${"-".repeat(widths.source)}`);
  for (const row of rows) {
    console.log(
      `${row.name.padEnd(widths.name)}  ${row.path.padEnd(widths.path)}  ${row.source.padEnd(widths.source)}`,
    );
  }
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  if (args.help) {
    usage();
    return;
  }

  const readmePath = path.join(args.root, "README.md");
  const readme = await readFile(readmePath, "utf8");
  let entries = parseCatalog(readme).filter((entry) => args.includeLocal || entry.source.url);

  if (args.skill) {
    entries = entries.filter((entry) => entry.name === args.skill);
  }

  if (entries.length === 0) {
    throw new Error(args.skill ? `No README catalog source found for ${args.skill}` : "No README catalog sources found");
  }

  if (args.json) {
    console.log(JSON.stringify(entries, null, 2));
  } else {
    printTable(entries);
  }
}

main().catch((error) => {
  console.error(`source-catalog: ${error.message}`);
  process.exit(1);
});
