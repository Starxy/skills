import { readdir, readFile, stat } from "node:fs/promises";
import path from "node:path";

const root = process.cwd();
const skillsDir = path.join(root, "skills");
const namePattern = /^[a-z0-9][a-z0-9-]{0,62}$/;
const errors = [];
const warnings = [];

async function exists(filePath) {
  try {
    await stat(filePath);
    return true;
  } catch {
    return false;
  }
}

async function findSkillFiles(dir) {
  if (!(await exists(dir))) {
    return [];
  }

  const entries = await readdir(dir, { withFileTypes: true });
  const files = [];

  for (const entry of entries) {
    const fullPath = path.join(dir, entry.name);

    if (entry.isDirectory()) {
      files.push(...(await findSkillFiles(fullPath)));
      continue;
    }

    if (entry.isFile() && entry.name === "SKILL.md") {
      files.push(fullPath);
    }
  }

  return files;
}

function parseFrontmatter(text, relativePath) {
  const match = text.match(/^---\r?\n([\s\S]*?)\r?\n---(?:\r?\n|$)/);

  if (!match) {
    errors.push(`${relativePath}: missing YAML frontmatter delimited by ---`);
    return {};
  }

  const frontmatter = {};
  for (const rawLine of match[1].split(/\r?\n/)) {
    const line = rawLine.trim();

    if (!line || line.startsWith("#") || line === "metadata:") {
      continue;
    }

    const pair = line.match(/^([A-Za-z0-9_.-]+):\s*(.*)$/);
    if (!pair) {
      continue;
    }

    const [, key, rawValue] = pair;
    frontmatter[key] = rawValue.replace(/^["']|["']$/g, "").trim();
  }

  return frontmatter;
}

function validateSkill(filePath, frontmatter) {
  const relativePath = path.relative(root, filePath).replaceAll(path.sep, "/");
  const skillDir = path.basename(path.dirname(filePath));
  const name = frontmatter.name ?? "";
  const description = frontmatter.description ?? "";

  if (!name) {
    errors.push(`${relativePath}: missing required frontmatter field "name"`);
  } else if (!namePattern.test(name)) {
    errors.push(
      `${relativePath}: "name" must use lowercase letters, digits, and hyphens only, with max length 63`,
    );
  } else if (skillDir !== name) {
    warnings.push(
      `${relativePath}: folder name "${skillDir}" does not match skill name "${name}"`,
    );
  }

  if (!description) {
    errors.push(`${relativePath}: missing required frontmatter field "description"`);
  }

  return name;
}

const skillFiles = await findSkillFiles(skillsDir);
const names = new Map();

for (const filePath of skillFiles) {
  const relativePath = path.relative(root, filePath).replaceAll(path.sep, "/");
  const text = await readFile(filePath, "utf8");
  const frontmatter = parseFrontmatter(text, relativePath);
  const name = validateSkill(filePath, frontmatter);

  if (name) {
    if (names.has(name)) {
      errors.push(`${relativePath}: duplicate skill name "${name}" also used by ${names.get(name)}`);
    } else {
      names.set(name, relativePath);
    }
  }
}

for (const warning of warnings) {
  console.warn(`Warning: ${warning}`);
}

if (errors.length > 0) {
  for (const error of errors) {
    console.error(`Error: ${error}`);
  }
  process.exit(1);
}

if (skillFiles.length === 0) {
  console.log("No skills found yet. Add one with: npx skills init skills/my-skill");
} else {
  console.log(`Validated ${skillFiles.length} skill${skillFiles.length === 1 ? "" : "s"}.`);
}
