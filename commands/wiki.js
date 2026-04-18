// /wiki slash command: LLM-driven wiki ingest, query, lint
// Integrates with bin/loppy subcommands to provide LLM-driven workflows

const { execSync } = require('child_process');
const path = require('path');
const fs = require('fs');
const os = require('os');

/**
 * Load Loppy config from XDG_CONFIG_HOME/loppy/config.json
 * @returns {Object|null} Config object or null if not found
 */
function loadConfig() {
  const configDir = path.join(
    process.env.XDG_CONFIG_HOME || path.join(os.homedir(), '.config'),
    'loppy'
  );
  const configFile = path.join(configDir, 'config.json');

  if (!fs.existsSync(configFile)) {
    return null;
  }

  try {
    return JSON.parse(fs.readFileSync(configFile, 'utf8'));
  } catch (err) {
    return null;
  }
}

/**
 * Execute bin/loppy command and return stdout
 * @param {string[]} args - Arguments to pass to loppy
 * @param {string} stdin - Optional stdin to pass
 * @returns {string} Command output
 */
function runLoppy(args, stdin = null) {
  const config = loadConfig();
  if (!config) {
    throw new Error('Loppy config not found. Run: loppy setup');
  }

  const loppyBin = path.join(__dirname, '..', 'bin', 'loppy');
  const cmd = `${loppyBin} ${args.map(arg => `'${arg.replace(/'/g, "'\\''")}'`).join(' ')}`;

  try {
    let result;
    if (stdin) {
      // Write stdin to temp file and use process substitution
      const tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), 'loppy-'));
      const stdinFile = path.join(tmpDir, 'stdin');
      fs.writeFileSync(stdinFile, stdin);
      const cmdWithStdin = `cat '${stdinFile}' | ${cmd}`;
      result = execSync(cmdWithStdin, {
        encoding: 'utf8',
        env: {
          ...process.env,
          XDG_CONFIG_HOME: process.env.XDG_CONFIG_HOME || path.join(os.homedir(), '.config'),
        },
      });
      fs.rmSync(tmpDir, { recursive: true });
    } else {
      result = execSync(cmd, {
        encoding: 'utf8',
        env: {
          ...process.env,
          XDG_CONFIG_HOME: process.env.XDG_CONFIG_HOME || path.join(os.homedir(), '.config'),
        },
      });
    }
    return result.trim();
  } catch (err) {
    throw new Error(err.stderr ? err.stderr.toString().trim() : err.message);
  }
}

/**
 * Handle /wiki ingest subcommand
 * @param {string[]} args - [mode, count] where mode is 'single' or 'batch'
 * @returns {Promise<string>} User-facing output
 */
async function handleIngest(args) {
  const mode = args[0] || 'single';
  const count = parseInt(args[1]) || 1;

  if (!['single', 'batch'].includes(mode)) {
    return `Invalid mode: ${mode}. Use: single or batch`;
  }

  try {
    const countArg = mode === 'batch' ? count.toString() : '1';
    const sourcesList = runLoppy(['next', countArg]);

    if (!sourcesList) {
      return 'No unprocessed sources found. Place raw .md or .txt files in sources_dir/.';
    }

    if (mode === 'batch') {
      return (
        `Ready to ingest ${count} sources in batch mode:\n\n` +
        sourcesList +
        `\n\n` +
        `I will process each source:\n` +
        `1. Read the raw source content\n` +
        `2. Extract key knowledge and structure it\n` +
        `3. Create wiki page with proper frontmatter (title, type, domain, tags, links, updated)\n` +
        `4. Merge page into index.md with summary and metadata\n` +
        `5. Move source to processed/ directory\n` +
        `6. Log the operation to log.md`
      );
    } else {
      // Single mode
      return (
        `Next source to ingest:\n\n` +
        sourcesList +
        `\n\n` +
        `I will:\n` +
        `1. Read the source content\n` +
        `2. Extract key knowledge\n` +
        `3. Create wiki page with frontmatter\n` +
        `4. Merge into index.md\n` +
        `5. Move to processed/\n` +
        `6. Log the operation`
      );
    }
  } catch (err) {
    return `Ingest error: ${err.message}`;
  }
}

/**
 * Handle /wiki query subcommand
 * @param {string[]} args - Query terms
 * @returns {Promise<string>} Search results
 */
async function handleQuery(args) {
  const query = args.join(' ').trim();

  if (!query) {
    return 'Usage: /wiki query <term>\n\nSearch by keyword, tag, type, or domain.';
  }

  try {
    const config = loadConfig();
    if (!config) {
      return 'Loppy config not found. Run: loppy setup';
    }

    const indexPath = path.join(config.wiki_dir, 'index.md');

    if (!fs.existsSync(indexPath)) {
      return `Wiki index not found at ${indexPath}. Run /wiki ingest to add sources.`;
    }

    // Read index and search
    const index = fs.readFileSync(indexPath, 'utf8');
    const lines = index.split('\n');

    // Simple search: match query in lines containing wiki page links
    const results = lines
      .filter(
        (line) =>
          line.includes('[[wiki/') &&
          (line.toLowerCase().includes(query.toLowerCase()) ||
            line.includes(query))
      )
      .slice(0, 5);

    if (results.length === 0) {
      return `No wiki pages matching "${query}" found.\n\nTry: keyword, tag:value, type:value, or domain:value`;
    }

    return (
      `Found ${results.length} matching pages:\n\n` +
      results.join('\n') +
      `\n\nI can fetch full pages and synthesize answers from their content.`
    );
  } catch (err) {
    return `Query error: ${err.message}`;
  }
}

/**
 * Handle /wiki lint subcommand
 * @param {string[]} args - Optional [page] filter
 * @returns {Promise<string>} Lint results
 */
async function handleLint(args) {
  const pageFilter = args[0] || '';

  try {
    const findings = runLoppy(['lint-frontmatter']);

    if (!findings || findings === '[]') {
      return 'Wiki schema is valid. No issues found.';
    }

    let parsed;
    try {
      parsed = JSON.parse(findings);
    } catch (err) {
      return `Lint error: Could not parse findings: ${err.message}`;
    }

    if (!Array.isArray(parsed) || parsed.length === 0) {
      return 'Wiki schema is valid. No issues found.';
    }

    // Filter by page if specified
    const filtered = pageFilter
      ? parsed.filter((item) => item.path && item.path.includes(pageFilter))
      : parsed;

    if (filtered.length === 0) {
      return pageFilter
        ? `No issues found for page matching "${pageFilter}".`
        : 'Wiki schema is valid. No issues found.';
    }

    // Format findings
    const summary = filtered
      .map((item) => {
        const path = item.path || 'unknown';
        const findingsList = (item.findings || [])
          .map((f) => {
            if (f.rule === 'missing-field') {
              return `  - Missing required field: ${f.field}`;
            } else if (f.rule === 'bad-enum') {
              return `  - Invalid ${f.field}: "${f.value}"`;
            } else if (f.rule === 'broken-link') {
              return `  - Broken link: ${f.target}`;
            } else if (f.rule === 'stale') {
              return `  - Stale (${f.age_days} days old)`;
            } else if (f.rule === 'orphan') {
              return `  - Orphaned (not in index.md)`;
            }
            return `  - ${f.rule}`;
          })
          .join('\n');
        return `${path}:\n${findingsList}`;
      })
      .join('\n\n');

    return (
      `Found ${filtered.length} schema issue${filtered.length === 1 ? '' : 's'}:\n\n` +
      summary
    );
  } catch (err) {
    return `Lint error: ${err.message}`;
  }
}

/**
 * Main handler function for /wiki slash command
 * @param {string} name - Command name ('wiki')
 * @param {string[]} args - Subcommand and arguments
 * @param {Object} tools - Available tools (not used in this impl)
 * @returns {Promise<string>} Result message
 */
async function handler(name, args, tools) {
  if (!args || args.length === 0) {
    return (
      `Loppy /wiki command\n\n` +
      `Usage:\n` +
      `  /wiki ingest [mode] [count]  - Ingest sources (mode: single|batch)\n` +
      `  /wiki query <term>           - Search wiki pages\n` +
      `  /wiki lint [page]            - Validate wiki schema`
    );
  }

  const subcommand = args[0];
  const subargs = args.slice(1);

  try {
    switch (subcommand) {
      case 'ingest':
        return await handleIngest(subargs);
      case 'query':
        return await handleQuery(subargs);
      case 'lint':
        return await handleLint(subargs);
      default:
        return `Unknown subcommand: ${subcommand}\n\nUse: ingest | query | lint`;
    }
  } catch (err) {
    return `Error: ${err.message}`;
  }
}

module.exports = {
  name: 'wiki',
  description: 'LLM-driven wiki management',
  handler,
  subcommands: [
    {
      name: 'ingest',
      description: 'Ingest sources into wiki',
    },
    {
      name: 'query',
      description: 'Query wiki knowledge base',
    },
    {
      name: 'lint',
      description: 'Validate wiki schema and frontmatter',
    },
  ],
};
