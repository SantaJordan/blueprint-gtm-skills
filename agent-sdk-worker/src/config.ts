/**
 * Configuration for the Agent SDK Worker
 * Loads environment variables and provides typed config
 */

export interface Config {
  // Anthropic
  anthropicApiKey: string;

  // Supabase
  supabaseUrl: string;
  supabaseServiceKey: string;

  // GitHub
  githubToken: string;
  githubOwner: string;
  githubRepo: string;

  // Skills repository
  skillsRepoUrl: string;
  skillsRepoPath: string;

  // Worker settings
  maxExecutionTimeMs: number;
  logLevel: "debug" | "info" | "warn" | "error";
}

function requireEnv(name: string): string {
  const value = process.env[name];
  if (!value) {
    throw new Error(`Missing required environment variable: ${name}`);
  }
  return value;
}

function optionalEnv(name: string, defaultValue: string): string {
  return process.env[name] || defaultValue;
}

export function loadConfig(): Config {
  return {
    // Anthropic
    anthropicApiKey: requireEnv("ANTHROPIC_API_KEY"),

    // Supabase
    supabaseUrl: requireEnv("SUPABASE_URL"),
    supabaseServiceKey: requireEnv("SUPABASE_SERVICE_KEY"),

    // GitHub
    githubToken: requireEnv("GITHUB_TOKEN"),
    githubOwner: optionalEnv("GITHUB_OWNER", "SantaJordan"),
    githubRepo: optionalEnv("GITHUB_REPO", "blueprint-gtm-playbooks"),

    // Skills repository
    skillsRepoUrl: optionalEnv(
      "SKILLS_REPO_URL",
      "https://github.com/SantaJordan/Blueprint-GTM-Skills.git"
    ),
    skillsRepoPath: optionalEnv("SKILLS_REPO_PATH", "/tmp/blueprint-skills"),

    // Worker settings
    maxExecutionTimeMs: parseInt(
      optionalEnv("MAX_EXECUTION_TIME_MS", "1800000"), // 30 minutes
      10
    ),
    logLevel: optionalEnv("LOG_LEVEL", "info") as Config["logLevel"],
  };
}

// Singleton config instance
let configInstance: Config | null = null;

export function getConfig(): Config {
  if (!configInstance) {
    configInstance = loadConfig();
  }
  return configInstance;
}
