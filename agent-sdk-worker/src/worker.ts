/**
 * Core Worker using Claude Agent SDK
 * Executes Blueprint Turbo via the Agent SDK query() function
 */

import { execSync } from "child_process";
import { existsSync } from "fs";
import { getConfig } from "./config.js";
import {
  BlueprintJob,
  markJobProcessing,
  markJobCompleted,
  markJobFailed,
} from "./supabase.js";

// Note: The actual Agent SDK import will be:
// import { query, ClaudeAgentOptions } from "@anthropic-ai/claude-agent-sdk";
// For now, we'll implement with the expected interface

interface AgentMessage {
  type: "assistant" | "user" | "result" | "system";
  subtype?: "success" | "error_during_execution" | "error_tool_execution";
  message?: {
    content: Array<{ type: "text"; text: string } | { type: "tool_use"; name: string }>;
  };
  error?: string;
}

interface QueryOptions {
  prompt: string;
  options: {
    workingDirectory: string;
    settingSources: string[];
    permissionMode: string;
    mcpServers?: Record<string, { command: string; args: string[] }>;
    allowedTools?: string[];
    maxTurns?: number;
    maxBudgetUsd?: number;
  };
}

/**
 * Ensure the skills repository is cloned and up to date
 */
export async function ensureSkillsRepo(): Promise<string> {
  const config = getConfig();
  const repoPath = config.skillsRepoPath;

  console.log(`[Worker] Ensuring skills repo at ${repoPath}`);

  if (!existsSync(repoPath)) {
    console.log(`[Worker] Cloning skills repo...`);
    execSync(`git clone ${config.skillsRepoUrl} ${repoPath}`, {
      stdio: "inherit",
      env: {
        ...process.env,
        GIT_TERMINAL_PROMPT: "0",
      },
    });
  } else {
    console.log(`[Worker] Updating skills repo...`);
    try {
      execSync("git pull --ff-only", {
        cwd: repoPath,
        stdio: "inherit",
        env: {
          ...process.env,
          GIT_TERMINAL_PROMPT: "0",
        },
      });
    } catch (error) {
      console.warn(`[Worker] Git pull failed, continuing with existing repo`);
    }
  }

  return repoPath;
}

/**
 * Extract playbook URL from agent output
 */
function extractPlaybookUrl(text: string): string | null {
  // Pattern 1: GitHub Pages URL
  const githubPagesMatch = text.match(
    /https:\/\/santajordan\.github\.io\/blueprint-gtm-playbooks\/[^\s"'<>]+\.html/i
  );
  if (githubPagesMatch) {
    return githubPagesMatch[0];
  }

  // Pattern 2: Any GitHub Pages URL format
  const genericGithubMatch = text.match(
    /https:\/\/[a-z0-9-]+\.github\.io\/[^\s"'<>]+\.html/i
  );
  if (genericGithubMatch) {
    return genericGithubMatch[0];
  }

  return null;
}

/**
 * Extract company name from agent output
 */
function extractCompanyName(text: string): string | null {
  // Look for patterns like "Company: X" or "playbook for X"
  const companyMatch = text.match(/(?:Company|playbook for|analyzing)\s*[:\-]?\s*([A-Z][^\n.!?]{1,50})/i);
  if (companyMatch) {
    return companyMatch[1].trim();
  }
  return null;
}

/**
 * Run Blueprint Turbo via Agent SDK
 * This is the core function that invokes the /blueprint-turbo command
 */
export async function runBlueprintTurbo(
  companyUrl: string,
  workingDirectory: string
): Promise<{ playbookUrl: string; companyName?: string }> {
  const config = getConfig();

  console.log(`[Worker] Starting Blueprint Turbo for ${companyUrl}`);
  console.log(`[Worker] Working directory: ${workingDirectory}`);

  // Import the Agent SDK dynamically to handle cases where it's not installed yet
  let query: (options: QueryOptions) => AsyncIterable<AgentMessage>;

  try {
    const sdk = await import("@anthropic-ai/claude-agent-sdk");
    query = sdk.query;
  } catch (error) {
    throw new Error(
      `Claude Agent SDK not installed. Run: npm install @anthropic-ai/claude-agent-sdk\nError: ${error}`
    );
  }

  let playbookUrl: string | null = null;
  let companyName: string | null = null;
  let lastOutput = "";
  let errorOutput = "";

  const queryOptions: QueryOptions = {
    prompt: `/blueprint-turbo ${companyUrl}`,
    options: {
      workingDirectory,
      settingSources: ["project"], // Loads CLAUDE.md and .claude/skills/
      permissionMode: "acceptEdits", // Allow file writes without prompting
      mcpServers: {
        "sequential-thinking": {
          command: "npx",
          args: ["@sequentialthinking/mcp-server"],
        },
      },
      allowedTools: [
        "WebFetch",
        "WebSearch",
        "Read",
        "Write",
        "Edit",
        "Bash",
        "Glob",
        "Grep",
        "mcp__sequential-thinking__sequentialthinking",
      ],
      maxTurns: 100, // Blueprint Turbo can take many turns
      maxBudgetUsd: 10.0, // Cost limit
    },
  };

  console.log(`[Worker] Invoking Agent SDK with options:`, JSON.stringify(queryOptions, null, 2));

  try {
    for await (const message of query(queryOptions)) {
      // Process different message types
      if (message.type === "assistant" && message.message?.content) {
        for (const block of message.message.content) {
          if (block.type === "text") {
            lastOutput = block.text;

            // Log progress indicators
            if (block.text.includes("Wave")) {
              console.log(`[Worker] Progress: ${block.text.substring(0, 100)}...`);
            }

            // Try to extract URL
            const url = extractPlaybookUrl(block.text);
            if (url) {
              playbookUrl = url;
              console.log(`[Worker] Found playbook URL: ${playbookUrl}`);
            }

            // Try to extract company name
            const name = extractCompanyName(block.text);
            if (name && !companyName) {
              companyName = name;
              console.log(`[Worker] Found company name: ${companyName}`);
            }
          }
        }
      }

      if (message.type === "result") {
        if (message.subtype === "success") {
          console.log(`[Worker] Agent SDK completed successfully`);
        } else if (message.subtype === "error_during_execution") {
          errorOutput = message.error || lastOutput;
          console.error(`[Worker] Agent SDK error: ${errorOutput}`);
        }
      }
    }
  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : String(error);
    console.error(`[Worker] Exception during Agent SDK execution:`, errorMessage);
    throw new Error(`Agent SDK execution failed: ${errorMessage}`);
  }

  if (!playbookUrl) {
    // If no URL was extracted, check if there was an error
    if (errorOutput) {
      throw new Error(`Blueprint Turbo failed: ${errorOutput}`);
    }
    throw new Error(
      `Blueprint Turbo completed but no playbook URL was found in output. Last output: ${lastOutput.substring(0, 500)}`
    );
  }

  return {
    playbookUrl,
    companyName: companyName || undefined,
  };
}

/**
 * Process a single Blueprint job
 */
export async function processJob(job: BlueprintJob): Promise<{
  success: boolean;
  playbookUrl?: string;
  error?: string;
}> {
  console.log(`[Worker] Processing job ${job.id} for ${job.company_url}`);

  try {
    // Mark job as processing
    await markJobProcessing(job.id);

    // Ensure skills repo is available
    const workingDirectory = await ensureSkillsRepo();

    // Run Blueprint Turbo
    const result = await runBlueprintTurbo(job.company_url, workingDirectory);

    // Mark job as completed
    await markJobCompleted(job.id, result.playbookUrl, result.companyName);

    console.log(`[Worker] Job ${job.id} completed successfully`);
    return {
      success: true,
      playbookUrl: result.playbookUrl,
    };
  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : String(error);
    console.error(`[Worker] Job ${job.id} failed:`, errorMessage);

    // Mark job as failed
    await markJobFailed(job.id, errorMessage);

    return {
      success: false,
      error: errorMessage,
    };
  }
}
