/**
 * Core Worker using Claude Agent SDK
 * Executes Blueprint Turbo via the Agent SDK query() function
 */

import { execSync } from "child_process";
import { existsSync, readFileSync } from "fs";
import path from "path";
import { createClient } from "@supabase/supabase-js";
import { getConfig } from "./config.js";
import {
  BlueprintJob,
  CheckpointData,
  markJobProcessing,
  markJobCompleted,
  markJobFailed,
  saveCheckpoint,
  loadCheckpoint,
  clearCheckpoint,
} from "./supabase.js";
import { getBlueprintTurboPrompt } from "./prompt.js";

// Note: The actual Agent SDK import will be:
// import { query, ClaudeAgentOptions } from "@anthropic-ai/claude-agent-sdk";
// For now, we'll implement with the expected interface

interface AgentMessage {
  type: "assistant" | "user" | "result" | "system";
  subtype?: string;  // SDK has multiple error subtypes
  message?: {
    content: Array<{ type: "text"; text: string } | { type: "tool_use"; name: string; id?: string }>;
  };
  error?: string;
  // Additional fields from SDK result messages
  total_cost_usd?: number;
  result?: string;
}

/**
 * Execution metrics for observability
 * Tracks tool calls, wave timings, and overall execution stats
 */
interface ExecutionMetrics {
  startTime: number;
  waves: Map<string, { startTime: number; endTime?: number; toolCalls: number }>;
  toolCalls: Map<string, number>;  // tool name -> count
  toolErrors: Map<string, number>; // tool name -> error count
  totalMessages: number;
  totalToolCalls: number;
  currentWave: string;
}

/**
 * Create a new metrics tracker
 */
function createMetrics(): ExecutionMetrics {
  return {
    startTime: Date.now(),
    waves: new Map(),
    toolCalls: new Map(),
    toolErrors: new Map(),
    totalMessages: 0,
    totalToolCalls: 0,
    currentWave: "init",
  };
}

/**
 * Detect which wave we're in based on text content
 */
function detectWave(text: string): string | null {
  const wavePatterns = [
    { pattern: /wave\s*0\.?5|product\s*(value\s*)?analysis/i, wave: "wave-0.5-product" },
    { pattern: /wave\s*1\.?5|niche\s*qualification|vertical\s*qualification/i, wave: "wave-1.5-niche" },
    { pattern: /wave\s*1[^.]|company\s*research|intelligence\s*gathering/i, wave: "wave-1-research" },
    { pattern: /wave\s*2\.?5|situation.*fallback/i, wave: "wave-2.5-fallback" },
    { pattern: /wave\s*2[^.]|data\s*landscape|database.*scan/i, wave: "wave-2-data" },
    { pattern: /synthesis|segment.*generation|sequential.*thinking/i, wave: "synthesis" },
    { pattern: /hard\s*gates?|validation|validator/i, wave: "validation" },
    { pattern: /wave\s*3|message.*generation|buyer.*critique/i, wave: "wave-3-messaging" },
    { pattern: /wave\s*4\.?[56]?|html.*assembly|playbook.*output/i, wave: "wave-4-output" },
  ];

  for (const { pattern, wave } of wavePatterns) {
    if (pattern.test(text)) {
      return wave;
    }
  }
  return null;
}

/**
 * Categorize tool by type for summary
 */
function categorizeToolCall(toolName: string): string {
  if (toolName.includes("browser-mcp") || toolName.includes("chrome")) return "browser-mcp";
  if (toolName.includes("WebFetch")) return "WebFetch";
  if (toolName.includes("WebSearch")) return "WebSearch";
  if (toolName.includes("sequential-thinking")) return "sequential-thinking";
  if (toolName.includes("Read") || toolName.includes("Write") || toolName.includes("Edit")) return "file-ops";
  if (toolName.includes("Bash") || toolName.includes("Glob") || toolName.includes("Grep")) return "system";
  if (toolName.includes("Task")) return "sub-agent";
  return "other";
}

/**
 * Log metrics summary
 */
function logMetricsSummary(metrics: ExecutionMetrics): void {
  const elapsed = (Date.now() - metrics.startTime) / 1000;

  console.log(`\n[Metrics] ========== EXECUTION SUMMARY ==========`);
  console.log(`[Metrics] Total time: ${elapsed.toFixed(1)}s (${(elapsed / 60).toFixed(1)} min)`);
  console.log(`[Metrics] Total messages: ${metrics.totalMessages}`);
  console.log(`[Metrics] Total tool calls: ${metrics.totalToolCalls}`);

  // Wave timings
  console.log(`[Metrics] --- Wave Timings ---`);
  for (const [wave, data] of metrics.waves) {
    const duration = data.endTime
      ? ((data.endTime - data.startTime) / 1000).toFixed(1)
      : "ongoing";
    console.log(`[Metrics]   ${wave}: ${duration}s, ${data.toolCalls} tool calls`);
  }

  // Tool call breakdown
  console.log(`[Metrics] --- Tool Call Breakdown ---`);
  const toolCategories = new Map<string, number>();
  for (const [tool, count] of metrics.toolCalls) {
    const category = categorizeToolCall(tool);
    toolCategories.set(category, (toolCategories.get(category) || 0) + count);
  }
  for (const [category, count] of toolCategories) {
    console.log(`[Metrics]   ${category}: ${count} calls`);
  }

  // Errors
  if (metrics.toolErrors.size > 0) {
    console.log(`[Metrics] --- Tool Errors ---`);
    for (const [tool, count] of metrics.toolErrors) {
      console.log(`[Metrics]   ${tool}: ${count} errors`);
    }
  }

  // Key insights
  console.log(`[Metrics] --- Key Insights ---`);
  const browserCalls = toolCategories.get("browser-mcp") || 0;
  const webFetchCalls = toolCategories.get("WebFetch") || 0;
  if (browserCalls === 0 && webFetchCalls > 0) {
    console.log(`[Metrics]   ⚠️  NO browser-mcp calls detected (${webFetchCalls} WebFetch calls)`);
    console.log(`[Metrics]   → Browser MCP may not be working - this causes slowdown`);
  } else if (browserCalls > 0) {
    console.log(`[Metrics]   ✓ Browser MCP active: ${browserCalls} calls`);
  }

  const avgTimePerMessage = elapsed / metrics.totalMessages;
  if (avgTimePerMessage > 5) {
    console.log(`[Metrics]   ⚠️  Slow execution: ${avgTimePerMessage.toFixed(1)}s per message`);
  }

  console.log(`[Metrics] =======================================\n`);
}

// ============================================================================
// APIFY PRE-FETCH FUNCTIONS
// Pre-fetch company data before agent execution to reduce tool-loop variance
// ============================================================================

interface PrefetchResult {
  success: boolean;
  artifactPath?: string;
  webPages?: Array<{ url: string; markdown: string }>;
  searchResults?: Array<{ title: string; url: string; snippet: string }>;
  error?: string;
}

/**
 * Run an Apify actor and wait for results
 */
async function runApifyActor(
  actorId: string,
  input: Record<string, any>,
  timeoutMs: number = 120000
): Promise<any[]> {
  const apifyToken = process.env.APIFY_API_TOKEN;
  if (!apifyToken) {
    console.log(`[Prefetch] APIFY_API_TOKEN not set, skipping Apify actor`);
    return [];
  }

  try {
    console.log(`[Prefetch] Running Apify actor: ${actorId}`);

    // Start the actor run (encode actorId for URL safety - slashes need encoding)
    const encodedActorId = encodeURIComponent(actorId);
    const runResponse = await fetch(
      `https://api.apify.com/v2/acts/${encodedActorId}/runs?token=${apifyToken}`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(input),
      }
    );

    if (!runResponse.ok) {
      console.error(`[Prefetch] Apify run failed: ${runResponse.status}`);
      return [];
    }

    const runData = await runResponse.json() as { data?: { id?: string } };
    const runId = runData.data?.id;
    if (!runId) {
      console.error(`[Prefetch] No run ID returned from Apify`);
      return [];
    }

    console.log(`[Prefetch] Apify run started: ${runId}`);

    // Poll for completion
    const startTime = Date.now();
    while (Date.now() - startTime < timeoutMs) {
      await new Promise(resolve => setTimeout(resolve, 3000)); // Wait 3 seconds

      const statusResponse = await fetch(
        `https://api.apify.com/v2/actor-runs/${runId}?token=${apifyToken}`
      );
      const statusData = await statusResponse.json() as { data?: { status?: string } };
      const status = statusData.data?.status;

      if (status === "SUCCEEDED") {
        console.log(`[Prefetch] Apify run completed: ${runId}`);
        break;
      } else if (status === "FAILED" || status === "ABORTED" || status === "TIMED-OUT") {
        console.error(`[Prefetch] Apify run failed with status: ${status}`);
        return [];
      }
    }

    // Get the dataset items
    const datasetResponse = await fetch(
      `https://api.apify.com/v2/actor-runs/${runId}/dataset/items?token=${apifyToken}`
    );
    const items = await datasetResponse.json() as any[];
    console.log(`[Prefetch] Retrieved ${items.length} items from Apify`);
    return items;
  } catch (error) {
    console.error(`[Prefetch] Apify error: ${error}`);
    return [];
  }
}

/**
 * Pre-fetch company data using Apify actors
 * Returns web pages and search results for the agent to use
 */
async function prefetchCompanyData(companyUrl: string): Promise<PrefetchResult> {
  const startTime = Date.now();
  console.log(`[Prefetch] Starting pre-fetch for ${companyUrl}`);

  try {
    const domain = new URL(companyUrl).hostname.replace(/^www\./, "");

    // Run both actors in parallel
    const [webPages, searchResults] = await Promise.all([
      // RAG Web Browser for the main website pages
      runApifyActor("apify/rag-web-browser", {
        query: companyUrl,
        maxResults: 5,
        outputFormats: ["markdown"],
        requestTimeoutSecs: 30,
      }),

      // Google Search for context (queries must be newline-separated string)
      runApifyActor("apify/google-search-scraper", {
        queries: `${domain} products services\n${domain} customers case studies\n${domain} reviews`,
        maxPagesPerQuery: 3,
        resultsPerPage: 10,
      }),
    ]);

    const elapsed = (Date.now() - startTime) / 1000;
    console.log(`[Prefetch] Completed in ${elapsed.toFixed(1)}s: ${webPages.length} pages, ${searchResults.length} search results`);

    // Format results for the agent
    const formattedPages = webPages.map((item: any) => ({
      url: item.url || item.sourceUrl || companyUrl,
      markdown: item.markdown || item.text || item.content || "",
    }));

    const formattedSearch = searchResults.flatMap((result: any) => {
      // Handle different result formats
      if (result.organicResults) {
        return result.organicResults.map((r: any) => ({
          title: r.title || "",
          url: r.url || r.link || "",
          snippet: r.description || r.snippet || "",
        }));
      }
      return [{
        title: result.title || "",
        url: result.url || result.link || "",
        snippet: result.description || result.snippet || "",
      }];
    });

    return {
      success: true,
      webPages: formattedPages,
      searchResults: formattedSearch,
    };
  } catch (error) {
    console.error(`[Prefetch] Error: ${error}`);
    return {
      success: false,
      error: String(error),
    };
  }
}

/**
 * Format prefetch results as context for the agent prompt
 */
function formatPrefetchContext(prefetch: PrefetchResult): string {
  if (!prefetch.success) {
    return "";
  }

  let context = "\n\n=== PRE-FETCHED COMPANY DATA ===\n";
  context += "(Use this data to save time. Avoid re-fetching these pages.)\n\n";

  if (prefetch.webPages && prefetch.webPages.length > 0) {
    context += "## WEBSITE CONTENT\n\n";
    for (const page of prefetch.webPages.slice(0, 5)) {
      context += `### ${page.url}\n`;
      // Truncate to avoid overwhelming the context
      const truncatedMarkdown = page.markdown.substring(0, 3000);
      context += `${truncatedMarkdown}\n\n`;
    }
  }

  if (prefetch.searchResults && prefetch.searchResults.length > 0) {
    context += "## SEARCH RESULTS\n\n";
    for (const result of prefetch.searchResults.slice(0, 15)) {
      context += `- **${result.title}**\n`;
      context += `  URL: ${result.url}\n`;
      context += `  ${result.snippet}\n\n`;
    }
  }

  context += "=== END PRE-FETCHED DATA ===\n\n";
  return context;
}

// ============================================================================
// QUERY OPTIONS & CORE WORKER
// ============================================================================

interface QueryOptions {
  prompt: string;
  options: {
    cwd: string;  // SDK uses 'cwd' not 'workingDirectory'
    settingSources: ("user" | "project")[];
    permissionMode: "acceptEdits" | "bypassPermissions";
    systemPrompt?: {
      type: "preset";
      preset: "claude_code";
    };
    mcpServers?: Record<string, {
      type: "stdio";
      command: string;
      args: string[];
      env?: Record<string, string>;
    }>;
    allowedTools?: string[];
    maxTurns?: number;
    maxBudgetUsd?: number;
  };
}

/**
 * Ensure the skills repository is available
 * In Modal, skills are pre-populated in the image at /app/blueprint-skills
 * For local dev, clone the repo if not present
 */
export async function ensureSkillsRepo(): Promise<string> {
  const config = getConfig();
  const repoPath = config.skillsRepoPath;
  const claudeDir = `${repoPath}/.claude`;

  console.log(`[Worker] Ensuring skills repo at ${repoPath}`);

  // Check if .claude directory already exists (pre-populated in Modal image)
  if (existsSync(claudeDir)) {
    console.log(`[Worker] Skills directory found at ${claudeDir} - using pre-populated skills`);
    return repoPath;
  }

  // Clone repo if not present (for local development)
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
  // Pattern 1: GitHub Pages URL (primary target)
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

  // Pattern 3: Local playbook file path (for constructing URL)
  // Matches patterns like: playbooks/blueprint-gtm-playbook-owner.html
  const localPathMatch = text.match(
    /playbooks\/blueprint-gtm-playbook-[a-z0-9-]+\.html/i
  );
  if (localPathMatch) {
    // Convert to GitHub Pages URL
    const filename = localPathMatch[0].replace("playbooks/", "");
    return `https://santajordan.github.io/blueprint-gtm-playbooks/${filename}`;
  }

  // Pattern 4: Just the filename (e.g., "blueprint-gtm-playbook-owner.html")
  const filenameMatch = text.match(
    /blueprint-gtm-playbook-[a-z0-9-]+\.html/i
  );
  if (filenameMatch) {
    return `https://santajordan.github.io/blueprint-gtm-playbooks/${filenameMatch[0]}`;
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

// ============================================================================
// TWO-PASS QUALITY STRATEGY
// Pass 1: Generate complete playbook (may have some 7.0-7.9 messages)
// Pass 2: If any messages < 8.0, run targeted improvement pass
// ============================================================================

interface MessageScore {
  type: "PQS" | "PVP" | "unknown";
  title: string;
  score: number;
  rawText: string;
}

/**
 * Extract message scores from agent output
 * Looks for patterns like "Strong PQS at 7.4-8.6/10" or individual message scores
 */
function extractMessageScores(fullOutput: string): MessageScore[] {
  const scores: MessageScore[] = [];

  // Pattern 1: Summary format "N TRUE PVPs at X+, N Strong PQS at Y-Z/10"
  const summaryMatch = fullOutput.match(/(\d+)\s*(?:TRUE\s*)?PVPs?\s*(?:at\s*)?(\d+\.?\d*)[\+\-]?/gi);
  const pqsSummaryMatch = fullOutput.match(/(\d+)\s*Strong\s*PQS\s*at\s*(\d+\.?\d*)\s*[-–]\s*(\d+\.?\d*)/i);

  if (pqsSummaryMatch) {
    const count = parseInt(pqsSummaryMatch[1]);
    const lowScore = parseFloat(pqsSummaryMatch[2]);
    const highScore = parseFloat(pqsSummaryMatch[3]);
    // Add placeholders for each PQS message
    for (let i = 0; i < count; i++) {
      scores.push({
        type: "PQS",
        title: `PQS Message ${i + 1}`,
        score: (lowScore + highScore) / 2, // Use average as estimate
        rawText: "",
      });
    }
  }

  // Pattern 2: Individual message scores "Score: X.X/10" or "scored X.X"
  const individualScores = fullOutput.matchAll(/(?:Score|scored|rating)[\s:]*(\d+\.?\d*)\s*(?:\/10)?/gi);
  for (const match of individualScores) {
    const score = parseFloat(match[1]);
    if (score >= 1 && score <= 10) {
      // Try to find context around this score
      const contextStart = Math.max(0, match.index! - 200);
      const context = fullOutput.substring(contextStart, match.index! + 50);

      const isPVP = /PVP|permissionless/i.test(context);
      const isPQS = /PQS|pain.qualified/i.test(context);

      scores.push({
        type: isPVP ? "PVP" : isPQS ? "PQS" : "unknown",
        title: context.match(/Subject:\s*([^\n]+)/i)?.[1] || `Message`,
        score,
        rawText: context,
      });
    }
  }

  // Deduplicate by removing scores that are too similar
  const uniqueScores: MessageScore[] = [];
  for (const score of scores) {
    const isDuplicate = uniqueScores.some(
      s => Math.abs(s.score - score.score) < 0.1 && s.type === score.type
    );
    if (!isDuplicate) {
      uniqueScores.push(score);
    }
  }

  return uniqueScores;
}

/**
 * Check if two-pass improvement is needed
 * Returns messages that scored below the threshold
 */
function getWeakMessages(scores: MessageScore[], threshold: number = 8.0): MessageScore[] {
  return scores.filter(s => s.score < threshold && s.score >= 6.0);
}

/**
 * Extract playbook file path from agent output
 * Agent outputs: PLAYBOOK_PATH: playbooks/blueprint-gtm-playbook-owner.html
 */
function extractPlaybookPath(text: string): string | null {
  // Pattern 1: Explicit marker (most reliable)
  const markerMatch = text.match(/PLAYBOOK_PATH:\s*([^\s\n]+\.html)/i);
  if (markerMatch) {
    return markerMatch[1];
  }

  // Pattern 2: Write/saved file path
  const writeMatch = text.match(/(?:wrote|saved|created|generated).*?(playbooks\/[^\s"']+\.html)/i);
  if (writeMatch) {
    return writeMatch[1];
  }

  // Pattern 3: File path in output
  const pathMatch = text.match(/(playbooks\/blueprint-gtm-playbook-[a-z0-9-]+\.html)/i);
  if (pathMatch) {
    return pathMatch[1];
  }

  return null;
}

// ============================================================================
// PUBLISHING FLOW (agent-sdk-worker / cloud):
// 1. Agent generates playbook HTML at /app/blueprint-skills/playbooks/
// 2. Worker finds the file and reads content
// 3. Worker uploads to Vercel via REST API
// 4. Final URL: https://playbooks.blueprintgtm.com/{company-slug}
//
// NOTE: Local CLI uses GitHub Pages via .claude/skills/blueprint-github-publish
// ============================================================================

/**
 * Upload playbook HTML to Vercel for proper Content-Type serving.
 * Uses Vercel REST API v13 - see https://vercel.com/docs/rest-api/endpoints/deployments
 */
async function uploadPlaybookToVercel(
  htmlContent: string,
  companySlug: string,
  vercelToken: string,
  projectName: string = "blueprint-playbooks"
): Promise<{ success: boolean; url?: string; error?: string }> {
  // Use simplified filename for pretty URLs (e.g., "owner-com.html")
  const filename = `${companySlug}.html`;

  console.log(`[Vercel] Uploading playbook: ${filename}`);

  // Vercel.json configuration for clean URLs (/:slug -> /:slug.html)
  const vercelConfig = JSON.stringify({
    rewrites: [
      { source: "/:slug", destination: "/:slug.html" }
    ]
  });

  try {
    // Vercel REST API v13 - files array format per official docs
    const response = await fetch("https://api.vercel.com/v13/deployments", {
      method: "POST",
      headers: {
        "Authorization": `Bearer ${vercelToken}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        name: projectName,
        // Files array format: { file: "path", data: "content", encoding: "utf-8" }
        files: [
          {
            file: filename,
            data: htmlContent,
            encoding: "utf-8"
          },
          {
            file: "vercel.json",
            data: vercelConfig,
            encoding: "utf-8"
          }
        ],
        target: "production",
        projectSettings: {
          framework: null,  // Static file, no framework
        }
      }),
    });

    if (!response.ok) {
      const errorText = await response.text();
      console.error(`[Vercel] Upload failed: ${response.status} - ${errorText}`);
      return { success: false, error: `Vercel API error: ${response.status}` };
    }

    const data = await response.json();
    // Return pretty URL with custom domain (e.g., playbooks.blueprintgtm.com/owner-com)
    const deployedUrl = `https://playbooks.blueprintgtm.com/${companySlug}`;

    console.log(`[Vercel] Playbook deployed: ${deployedUrl}`);

    return { success: true, url: deployedUrl };
  } catch (e) {
    console.error(`[Vercel] Upload exception: ${e}`);
    return { success: false, error: String(e) };
  }
}

/**
 * Extract company slug from URL for pretty Vercel URLs.
 * Includes TLD with dashes.
 * e.g., "https://owner.com" -> "owner-com"
 * e.g., "https://www.canvas-medical.com" -> "canvas-medical-com"
 * e.g., "https://www.example.co.uk" -> "example-co-uk"
 */
function extractCompanySlug(companyUrl: string): string {
  try {
    const url = new URL(companyUrl);
    // Remove www. prefix
    let hostname = url.hostname.replace(/^www\./, "");
    // Replace dots with dashes (includes TLD)
    return hostname.toLowerCase().replace(/\./g, "-").replace(/[^a-z0-9-]/g, "");
  } catch {
    // Fallback: extract from URL string
    return companyUrl
      .replace(/^https?:\/\/(www\.)?/i, "")
      .split('/')[0]
      .toLowerCase()
      .replace(/\./g, "-")
      .replace(/[^a-z0-9-]/g, "");
  }
}

/**
 * Extract OLD-format company slug for finding files created by the agent.
 * Agent still uses the old format (without TLD).
 * e.g., "https://owner.com" -> "owner"
 * e.g., "https://www.canvas-medical.com" -> "canvas-medical"
 */
function extractOldCompanySlug(companyUrl: string): string {
  try {
    const url = new URL(companyUrl);
    // Remove www. prefix and get hostname without TLD
    let hostname = url.hostname.replace(/^www\./, "");
    // Remove common TLDs
    hostname = hostname.replace(/\.(com|net|org|io|co|ai|health|edu)$/i, "");
    // Convert to slug format
    return hostname.toLowerCase().replace(/[^a-z0-9-]/g, "-");
  } catch {
    // Fallback: extract from URL string
    return companyUrl
      .replace(/^https?:\/\/(www\.)?/i, "")
      .replace(/\.(com|net|org|io|co|ai|health|edu).*/i, "")
      .toLowerCase()
      .replace(/[^a-z0-9-]/g, "-");
  }
}

/**
 * Find playbook file anywhere under /app using find command.
 * Handles cwd mismatch between Agent SDK and worker subprocess.
 *
 * Agent SDK runs with cwd: /app/blueprint-skills
 * Worker subprocess runs from /app/agent-sdk-worker
 */
function findPlaybookFile(filename: string): string | null {
  try {
    // Find files modified in last 30 minutes (fresh from this run)
    const findResult = execSync(
      `find /app -name "${filename}" -type f -mmin -30 2>/dev/null | head -1`,
      { encoding: 'utf-8', timeout: 10000 }
    ).trim();

    if (findResult && existsSync(findResult)) {
      console.log(`[File] Found playbook via find: ${findResult}`);
      return findResult;
    }
  } catch (e) {
    console.log(`[File] find command failed: ${e}`);
  }

  return null;
}

/**
 * Run Blueprint Turbo via Agent SDK
 * This is the core function that invokes the /blueprint-turbo command
 *
 * @param companyUrl - The company URL to analyze
 * @param workingDirectory - Working directory for the agent
 * @param jobId - Optional job ID for checkpoint operations (enables resume on timeout)
 */
export async function runBlueprintTurbo(
  companyUrl: string,
  workingDirectory: string,
  jobId?: string
): Promise<{ playbookUrl: string; companyName?: string }> {
  const config = getConfig();
  const startTime = Date.now();
  const maxExecutionMs = 60 * 60 * 1000; // 60 minutes hard limit (increased for comprehensive output)

  console.log(`[Worker] Starting Blueprint Turbo for ${companyUrl}`);
  console.log(`[Worker] Working directory: ${workingDirectory}`);
  console.log(`[Worker] Job ID: ${jobId || "none (no checkpointing)"}`);
  console.log(`[Worker] Max execution time: ${maxExecutionMs / 60000} minutes`);

  // ============================================================================
  // CHECKPOINT LOADING
  // If resuming from a previous run, load checkpoint data
  // ============================================================================
  let existingCheckpoint: CheckpointData | null = null;
  let resumeContext = "";

  if (jobId) {
    existingCheckpoint = await loadCheckpoint(jobId);
    if (existingCheckpoint) {
      console.log(`[Worker] Resuming from checkpoint: ${existingCheckpoint.wave}`);
      console.log(`[Worker] Checkpoint timestamp: ${existingCheckpoint.timestamp}`);

      // Build resume context from checkpoint data
      resumeContext = `
=== RESUMING FROM CHECKPOINT ===
Previous run completed wave: ${existingCheckpoint.wave}
Checkpoint saved at: ${existingCheckpoint.timestamp}

PREVIOUSLY COLLECTED DATA (use this, don't re-fetch):
`;

      if (existingCheckpoint.company_context) {
        resumeContext += `
Company Context:
- Name: ${existingCheckpoint.company_context.name}
- Offering: ${existingCheckpoint.company_context.offering}
- Differentiators: ${existingCheckpoint.company_context.differentiators.join(", ")}
`;
      }

      if (existingCheckpoint.icp) {
        resumeContext += `
ICP:
- Industries: ${existingCheckpoint.icp.industries.join(", ")}
- Company Types: ${existingCheckpoint.icp.company_types.join(", ")}
- Context: ${existingCheckpoint.icp.operational_context}
`;
      }

      if (existingCheckpoint.segments && existingCheckpoint.segments.length > 0) {
        resumeContext += `
Validated Segments:
${existingCheckpoint.segments.map(s => `- ${s.name} (${s.type}, ${s.confidence}% confidence)`).join("\n")}
`;
      }

      if (existingCheckpoint.messages && existingCheckpoint.messages.length > 0) {
        resumeContext += `
Generated Messages:
${existingCheckpoint.messages.map(m => `- ${m.type}: "${m.subject}" (${m.score}/10)`).join("\n")}
`;
      }

      resumeContext += `
=== RESUME INSTRUCTIONS ===
Skip to the NEXT wave after "${existingCheckpoint.wave}".
Use the data above instead of re-fetching.
Continue from where the previous run stopped.
=========================
`;
    }
  }

  // Log directory contents for debugging
  try {
    const { readdirSync, existsSync } = await import("fs");
    console.log(`[Worker] Working dir exists: ${existsSync(workingDirectory)}`);
    if (existsSync(workingDirectory)) {
      console.log(`[Worker] Working dir contents: ${readdirSync(workingDirectory).join(", ")}`);
    }
    const claudeDir = `${workingDirectory}/.claude`;
    console.log(`[Worker] .claude dir exists: ${existsSync(claudeDir)}`);
    if (existsSync(claudeDir)) {
      console.log(`[Worker] .claude contents: ${readdirSync(claudeDir).join(", ")}`);
      const commandsDir = `${claudeDir}/commands`;
      if (existsSync(commandsDir)) {
        console.log(`[Worker] commands contents: ${readdirSync(commandsDir).join(", ")}`);
      }
    }
  } catch (e) {
    console.log(`[Worker] Dir listing error: ${e}`);
  }

  // Import the Agent SDK dynamically to handle cases where it's not installed yet
  // Note: Using 'any' for query function because SDK types are complex and we handle messages generically
  let query: any;

  try {
    const sdk = await import("@anthropic-ai/claude-agent-sdk");
    query = sdk.query;
  } catch (error) {
    throw new Error(
      `Claude Agent SDK not installed. Run: npm install @anthropic-ai/claude-agent-sdk\nError: ${error}`
    );
  }

  let playbookUrl: string | null = null;
  let playbookPath: string | null = null;
  let companyName: string | null = null;
  let lastOutput = "";
  let allOutputText = "";  // Accumulate all text for two-pass quality analysis
  let errorOutput = "";

  // Initialize metrics tracking
  const metrics = createMetrics();

  // Pre-fetch company data using Apify (if APIFY_API_TOKEN is set)
  // Note: prefetchResult is declared outside if block so it's accessible in checkpoint save code
  let prefetchContext = "";
  let prefetchResult: PrefetchResult | null = null;
  if (process.env.APIFY_API_TOKEN) {
    console.log(`[Worker] Pre-fetching company data via Apify...`);
    prefetchResult = await prefetchCompanyData(companyUrl);
    if (prefetchResult.success) {
      prefetchContext = formatPrefetchContext(prefetchResult);
      console.log(`[Worker] Pre-fetch successful: ${prefetchResult.webPages?.length || 0} pages, ${prefetchResult.searchResults?.length || 0} search results`);
    } else {
      console.log(`[Worker] Pre-fetch failed or skipped: ${prefetchResult.error || "unknown"}`);
    }
  } else {
    console.log(`[Worker] Skipping pre-fetch (APIFY_API_TOKEN not set)`);
  }

  // CRITICAL: Use full prompt content directly (not slash command)
  // Slash commands don't expand properly in Agent SDK batch mode.
  // The agent would call SlashCommand tool then wait for expansion that never happens.
  // Solution: Read the full blueprint-turbo.md content and embed it in the prompt.
  //
  // Add timing constraints to prevent infinite research behavior
  const timeboxInstructions = `
IMPORTANT TIMING CONSTRAINTS FOR CLOUD EXECUTION:
You have a maximum of 25 minutes total. Stick to these wave budgets:
- Wave 0.5 (Product Analysis): max 2 minutes
- Wave 1 (Company Research): max 4 minutes
- Wave 1.5 (Niche Qualification): max 2 minutes
- Wave 2 (Data Landscape): max 6 minutes
- Synthesis: max 3 minutes
- Wave 3 (Messaging): max 5 minutes
- Wave 4 (HTML Assembly): max 2 minutes

CRITICAL RULES:
1. If data is thin after reasonable attempts, proceed with best-effort output
2. Prefer fewer high-quality segments over exhaustive research that times out
3. Do NOT retry failed web fetches more than twice per domain
4. If a database portal is blocked or slow, skip it and use alternative sources
5. Generate a COMPLETE playbook even if some sections are thinner than ideal
${prefetchContext ? "\n6. USE THE PRE-FETCHED DATA BELOW - avoid re-fetching the company website" : ""}
${prefetchContext}
${resumeContext}
`;

  // Get the full blueprint-turbo prompt from the command file
  // This reads .claude/commands/blueprint-turbo.md and substitutes $ARGUMENTS with the URL
  const blueprintPrompt = getBlueprintTurboPrompt(companyUrl);
  const prompt = `${timeboxInstructions}\n\n${blueprintPrompt}`;
  console.log(`[Worker] Using full embedded prompt (${prompt.length} chars)${prefetchContext ? " + pre-fetched data" : ""}`);

  const queryOptions: QueryOptions = {
    prompt,
    options: {
      cwd: workingDirectory,
      // Include user-level skills for Linux discovery workaround (Modal copies to /root/.claude).
      settingSources: ["project", "user"],
      permissionMode: "acceptEdits",  // SDK option - use acceptEdits for now

      // CRITICAL: Use claude_code preset for same harness as local Claude Code
      systemPrompt: {
        type: "preset",
        preset: "claude_code",
      },

      mcpServers: {
        "sequential-thinking": {
          type: "stdio",
          command: "npx",
          args: ["@modelcontextprotocol/server-sequential-thinking"],
        },
        "browser-mcp": {
          type: "stdio",
          command: "npx",
          args: ["browser-mcp"],
          env: {
            CHROME_PATH: process.env.CHROME_PATH || "/usr/bin/chromium",
            PUPPETEER_HEADLESS: "true",
          },
        },
      },

      // No allowedTools restriction - bypassPermissions allows all tools

      maxTurns: 300,        // Increased for comprehensive output
      maxBudgetUsd: 35.0,   // Increased for comprehensive output
    },
  };

  console.log(`[Worker] Invoking Agent SDK with claude_code preset`);
  console.log(`[Worker] ANTHROPIC_API_KEY present: ${!!process.env.ANTHROPIC_API_KEY}`);

  let messageCount = 0;
  try {
    console.log(`[Worker] Starting query iteration...`);
    for await (const message of query(queryOptions)) {
      messageCount++;
      metrics.totalMessages++;

      // Wall-clock timeout check
      const elapsed = Date.now() - startTime;
      if (elapsed > maxExecutionMs) {
        console.error(`[Worker] Wall-clock timeout after ${elapsed / 60000} minutes`);
        logMetricsSummary(metrics);  // Log summary before timeout
        throw new Error(`Wall-clock timeout: execution exceeded ${maxExecutionMs / 60000} minutes`);
      }

      console.log(`[Worker] Message #${messageCount}, type: ${message.type}, elapsed: ${Math.round(elapsed / 1000)}s`);

      // Process different message types
      if (message.type === "assistant" && message.message?.content) {
        for (const block of message.message.content) {
          if (block.type === "text") {
            lastOutput = block.text;
            allOutputText += block.text + "\n";  // Accumulate for two-pass analysis

            // Detect wave transitions for timing
            const detectedWave = detectWave(block.text);
            if (detectedWave && detectedWave !== metrics.currentWave) {
              // End previous wave
              const prevWaveData = metrics.waves.get(metrics.currentWave);
              if (prevWaveData) {
                prevWaveData.endTime = Date.now();
              }

              // Save checkpoint after completing a wave (if job ID is available)
              if (jobId && metrics.currentWave !== "init") {
                const checkpointData: Partial<CheckpointData> = {
                  prefetch_data: prefetchResult?.success ? {
                    webPages: prefetchResult.webPages || [],
                    searchResults: prefetchResult.searchResults || [],
                  } : undefined,
                };

                // Extract company name if found
                if (companyName) {
                  checkpointData.company_context = {
                    name: companyName,
                    offering: "", // Will be populated as we parse more output
                    differentiators: [],
                  };
                }

                // Save checkpoint asynchronously (don't await to avoid blocking)
                saveCheckpoint(jobId, metrics.currentWave, checkpointData).catch(err => {
                  console.warn(`[Worker] Checkpoint save failed: ${err}`);
                });
                console.log(`[Checkpoint] 💾 Saved after ${metrics.currentWave}`);
              }

              // Start new wave
              metrics.currentWave = detectedWave;
              metrics.waves.set(detectedWave, {
                startTime: Date.now(),
                toolCalls: 0,
              });
              console.log(`[Metrics] 🌊 Wave transition: ${metrics.currentWave} → ${detectedWave}`);
            }

            // Log progress indicators
            if (block.text.includes("Wave") || block.text.includes("wave")) {
              console.log(`[Worker] Progress: ${block.text.substring(0, 150)}...`);
            }

            // Try to extract URL
            const url = extractPlaybookUrl(block.text);
            if (url) {
              playbookUrl = url;
              console.log(`[Worker] Found playbook URL: ${playbookUrl}`);
            }

            // Try to extract local file path (for Vercel upload)
            const foundPath = extractPlaybookPath(block.text);
            if (foundPath && !playbookPath) {
              playbookPath = foundPath;
              console.log(`[Worker] Found playbook path: ${playbookPath}`);
            }

            // Try to extract company name
            const name = extractCompanyName(block.text);
            if (name && !companyName) {
              companyName = name;
              console.log(`[Worker] Found company name: ${companyName}`);
            }
          }

          // Track tool calls
          if (block.type === "tool_use") {
            const toolName = block.name;
            metrics.totalToolCalls++;
            metrics.toolCalls.set(toolName, (metrics.toolCalls.get(toolName) || 0) + 1);

            // Update current wave tool count
            const waveData = metrics.waves.get(metrics.currentWave);
            if (waveData) {
              waveData.toolCalls++;
            }

            // Log tool calls with categorization
            const category = categorizeToolCall(toolName);
            console.log(`[Metrics] 🔧 Tool call #${metrics.totalToolCalls}: ${toolName} (${category})`);
          }
        }
      }

      // Track tool errors
      if (message.type === "result" && message.subtype === "error_tool_execution") {
        const errorText = message.error || "";
        // Try to extract tool name from error
        const toolMatch = errorText.match(/tool[:\s]+(\w+)/i);
        const toolName = toolMatch ? toolMatch[1] : "unknown";
        metrics.toolErrors.set(toolName, (metrics.toolErrors.get(toolName) || 0) + 1);
        console.log(`[Metrics] ❌ Tool error: ${toolName} - ${errorText.substring(0, 100)}`);
      }

      if (message.type === "result") {
        if (message.subtype === "success") {
          console.log(`[Worker] Agent SDK completed successfully`);
          console.log(`[Worker] Result cost: $${message.total_cost_usd || "unknown"}`);
        } else if (message.subtype?.includes("error")) {
          errorOutput = message.error || message.result || lastOutput;
          console.error(`[Worker] Agent SDK error (${message.subtype}): ${errorOutput}`);
        }
      }
    }
  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : String(error);
    console.error(`[Worker] Exception during Agent SDK execution:`, errorMessage);
    console.error(`[Worker] Total messages received before error: ${messageCount}`);
    logMetricsSummary(metrics);  // Log summary on error
    throw new Error(`Agent SDK execution failed: ${errorMessage}`);
  }

  // Log final metrics summary
  logMetricsSummary(metrics);
  console.log(`[Worker] Query finished. Total messages: ${messageCount}, elapsed: ${Math.round((Date.now() - startTime) / 1000)}s`);

  // ============================================================================
  // TWO-PASS QUALITY IMPROVEMENT
  // If any messages scored below 8.0, run a targeted improvement pass
  // ============================================================================

  const messageScores = extractMessageScores(allOutputText);
  const weakMessages = getWeakMessages(messageScores, 8.0);

  if (weakMessages.length > 0) {
    console.log(`[Worker] ========== TWO-PASS QUALITY CHECK ==========`);
    console.log(`[Worker] Found ${messageScores.length} scored messages`);
    console.log(`[Worker] ${weakMessages.length} messages below 8.0 threshold:`);
    for (const msg of weakMessages) {
      console.log(`[Worker]   - ${msg.type} "${msg.title}": ${msg.score}/10`);
    }

    // Check if we have time budget for improvement pass (max 45 min total)
    const elapsedMinutes = (Date.now() - startTime) / 60000;
    const timeRemaining = 45 - elapsedMinutes;

    if (timeRemaining > 5) {
      console.log(`[Worker] Time remaining: ${timeRemaining.toFixed(1)} min - running improvement pass`);

      // Run improvement pass
      try {
        const improvementPrompt = `You previously generated a Blueprint GTM playbook for ${companyUrl}.

The following messages scored below 8.0 and need improvement:
${weakMessages.map(m => `- ${m.type} "${m.title}": ${m.score}/10`).join('\n')}

TASK: Regenerate ONLY these weak messages to achieve 8.5+ scores.

Requirements for improved messages:
1. Add more specific data points (exact numbers, dates, record IDs)
2. Strengthen the non-obvious insight (what they don't already know)
3. Make the call-to-action lower friction (one-word answer possible)
4. Ensure all claims are verifiable from the data sources

Output each improved message in this format:

IMPROVED_MESSAGE_START
Type: PQS or PVP
Subject: [2-4 word subject line]
Body: [Full message text, under 75 words for PQS, under 100 for PVP]
New_Score: [Your honest assessment, must be 8.0+]
IMPROVED_MESSAGE_END

Generate improved versions now:`;

        console.log(`[Worker] Running improvement agent...`);
        let improvementOutput = "";

        for await (const message of query({
          prompt: improvementPrompt,
          options: {
            cwd: workingDirectory,
            settingSources: ["project", "user"],
            permissionMode: "acceptEdits",
            maxTurns: 20,
            maxBudgetUsd: 3.0, // Lower budget for focused improvement
          },
        })) {
          if (message.type === "assistant" && message.message?.content) {
            for (const block of message.message.content) {
              if (block.type === "text") {
                improvementOutput += block.text;
              }
            }
          }
        }

        // Parse improved messages
        const improvedMatches = improvementOutput.matchAll(
          /IMPROVED_MESSAGE_START[\s\S]*?Type:\s*(PQS|PVP)[\s\S]*?Subject:\s*([^\n]+)[\s\S]*?Body:\s*([\s\S]*?)[\s\S]*?New_Score:\s*(\d+\.?\d*)[\s\S]*?IMPROVED_MESSAGE_END/gi
        );

        const improvedMessages = [...improvedMatches];
        console.log(`[Worker] Improvement pass generated ${improvedMessages.length} improved messages`);

        // TODO: In future, merge improved messages into the playbook HTML
        // For now, just log what was improved
        for (const match of improvedMessages) {
          console.log(`[Worker]   ✓ Improved ${match[1]} "${match[2].trim()}": ${match[4]}/10`);
        }
      } catch (improvementError) {
        console.warn(`[Worker] Improvement pass failed: ${improvementError}`);
        // Continue with original playbook
      }
    } else {
      console.log(`[Worker] Time remaining: ${timeRemaining.toFixed(1)} min - skipping improvement pass (need 5+ min)`);
    }
    console.log(`[Worker] ============================================`);
  } else if (messageScores.length > 0) {
    console.log(`[Worker] All ${messageScores.length} messages scored 8.0+ - no improvement needed`);
  }

  // UPLOAD STRATEGY:
  // 1. Check explicit paths first (Agent SDK writes to /app/blueprint-skills/playbooks/)
  // 2. Fall back to findPlaybookFile() with `find` command
  // 3. Upload to GitHub Pages (serves HTML correctly with proper Content-Type)
  const companySlug = extractCompanySlug(companyUrl);  // Format with TLD (e.g., owner-com)
  const oldCompanySlug = extractOldCompanySlug(companyUrl);  // Old format for file lookup (e.g., owner)
  const expectedFilenameOld = `blueprint-gtm-playbook-${oldCompanySlug}.html`;  // Agent creates files with OLD format
  const expectedFilenameNew = `blueprint-gtm-playbook-${companySlug}.html`;    // Fallback if agent includes TLD

  // Debug logging for upload strategy
  console.log(`[Worker] ========== UPLOAD CONFIG ==========`);
  console.log(`[Worker] Publishing to: GitHub Pages (SantaJordan/blueprint-gtm-playbooks)`);
  console.log(`[Worker] companySlug: ${companySlug}`);
  console.log(`[Worker] oldCompanySlug (file lookup): ${oldCompanySlug}`);
  console.log(`[Worker] expectedFilenameOld: ${expectedFilenameOld}`);
  console.log(`[Worker] expectedFilenameNew: ${expectedFilenameNew}`);
  console.log(`[Worker] workingDirectory: ${workingDirectory}`);
  console.log(`[Worker] =====================================`);

  // Step 1: Find the playbook file
  // Priority order matches where Agent SDK actually writes files:
  // - Agent SDK cwd is /app/blueprint-skills
  // - Agent writes to playbooks/xxx.html (relative to cwd)
  // - So file lands at /app/blueprint-skills/playbooks/xxx.html
  let foundPath: string | null = null;

  // PRIMARY: Check explicit paths where Agent SDK writes files
  const expectedFilenames = [expectedFilenameOld, expectedFilenameNew];
  const explicitPaths: string[] = [];
  for (const expectedFilename of expectedFilenames) {
    explicitPaths.push(
      `/app/blueprint-skills/playbooks/${expectedFilename}`,
      path.join(workingDirectory, `playbooks/${expectedFilename}`),
      `/app/agent-sdk-worker/playbooks/${expectedFilename}`,
    );
  }

  // Add paths from extracted playbookPath if available
  if (playbookPath) {
    const extractedPaths = [
      path.join(workingDirectory, playbookPath),
      path.join("/app/blueprint-skills", playbookPath),
      path.join("/app/agent-sdk-worker", playbookPath),
      playbookPath,
      path.resolve(playbookPath),
    ];
    if (path.isAbsolute(playbookPath)) {
      extractedPaths.unshift(playbookPath);
    }
    explicitPaths.push(...extractedPaths);
  }

  // Deduplicate paths
  const uniquePaths = [...new Set(explicitPaths)];

  console.log(`[Worker] Searching for playbook file...`);
  console.log(`[Worker] Checking ${uniquePaths.length} explicit paths:`);

  for (const loc of uniquePaths) {
    const exists = existsSync(loc);
    console.log(`[Worker]   ${exists ? "✓ FOUND" : "✗ not found"}: ${loc}`);
    if (exists && !foundPath) {
      foundPath = loc;
      // Continue logging to show all checked paths for debugging
    }
  }

  // If not found via explicit paths, use find command as last resort
  if (!foundPath) {
    console.log(`[Worker] Explicit paths failed, using find command...`);
    for (const expectedFilename of expectedFilenames) {
      foundPath = findPlaybookFile(expectedFilename);
      if (foundPath) break;
    }
  }

  // Step 2: Upload to Vercel if file found
  if (foundPath) {
    const htmlContent = readFileSync(foundPath, "utf-8");
    console.log(`[Worker] Found playbook at ${foundPath}, size: ${htmlContent.length} bytes`);

    // Upload to Vercel for proper HTML serving
    // Final URL: https://playbooks.blueprintgtm.com/{company-slug}
    const vercelToken = process.env.VERCEL_TOKEN;
    if (vercelToken) {
      console.log(`[Worker] Publishing to Vercel: ${companySlug}`);
      try {
        const result = await uploadPlaybookToVercel(htmlContent, companySlug, vercelToken);
        if (result.success && result.url) {
          playbookUrl = result.url;
          console.log(`[Worker] Vercel publish successful: ${playbookUrl}`);
        } else {
          console.error(`[Worker] Vercel publish failed: ${result.error}`);
        }
      } catch (vercelError) {
        console.error(`[Worker] Vercel publish exception: ${vercelError}`);
      }
    } else {
      console.error(`[Worker] VERCEL_TOKEN not set - cannot publish playbook`);
    }
  } else {
    console.warn(`[Worker] Playbook file not found. Checked:`);
    console.warn(`[Worker]   - Direct paths from playbookPath: ${playbookPath || "(not extracted)"}`);
    console.warn(`[Worker]   - find /app -name "${expectedFilenameOld}"`);
    console.warn(`[Worker]   - find /app -name "${expectedFilenameNew}"`);
    console.log(`[Worker] Using extracted URL as fallback: ${playbookUrl}`);
  }

  if (!playbookUrl) {
    // If no URL was extracted, check if there was an error
    if (errorOutput) {
      throw new Error(`Blueprint Turbo failed: ${errorOutput}`);
    }
    if (messageCount === 0) {
      throw new Error(`Agent SDK returned no messages. Check ANTHROPIC_API_KEY and SDK configuration.`);
    }
    throw new Error(
      `Blueprint Turbo completed but no playbook URL was found in output. Messages: ${messageCount}, Last output: ${lastOutput.substring(0, 500)}`
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

    // Run Blueprint Turbo (pass job.id for checkpoint operations)
    const result = await runBlueprintTurbo(job.company_url, workingDirectory, job.id);

    // Clear checkpoint on successful completion (no longer needed)
    await clearCheckpoint(job.id);

    // Mark job as completed
    await markJobCompleted(job.id, result.playbookUrl, result.companyName);

    // If this job was created via Stripe (manual capture), trigger capture after delivery.
    const paymentIntentId = job.stripe_payment_intent_id;
    if (paymentIntentId) {
      const vercelApiUrl = process.env.VERCEL_API_URL;
      const modalWebhookSecret = process.env.MODAL_WEBHOOK_SECRET;
      if (vercelApiUrl && modalWebhookSecret) {
        try {
          console.log(`[Worker] Capturing payment for job ${job.id}...`);
          const resp = await fetch(`${vercelApiUrl}/api/capture-payment`, {
            method: "POST",
            headers: {
              "Authorization": `Bearer ${modalWebhookSecret}`,
              "Content-Type": "application/json",
            },
            body: JSON.stringify({
              job_id: job.id,
              playbook_url: result.playbookUrl,
            }),
          });
          if (!resp.ok) {
            const text = await resp.text();
            console.warn(`[Worker] Payment capture failed: ${resp.status} ${text}`);
          } else {
            console.log(`[Worker] Payment capture request succeeded`);
          }
        } catch (e) {
          console.warn(`[Worker] Payment capture request errored: ${e}`);
        }
      } else {
        console.log(`[Worker] Payment capture skipped - missing VERCEL_API_URL or MODAL_WEBHOOK_SECRET`);
      }
    }

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

// Expose internal helpers for test suite (no runtime behavior change).
export const __test__ = {
  extractPlaybookUrl,
  extractPlaybookPath,
  extractCompanySlug,
  extractOldCompanySlug,
};
