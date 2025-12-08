/**
 * Agent SDK Worker Entry Point
 * Handles both webhook requests (Modal) and CLI invocation
 */

import { processJob } from "./worker.js";
import { getJob, claimPendingJob, getOldestPendingJob, BlueprintJob } from "./supabase.js";
import { getConfig } from "./config.js";

/**
 * Handle a webhook request from Modal/Supabase
 * Expects job data in JOB_DATA environment variable (JSON string)
 * or processes the oldest pending job if no specific job is provided
 */
async function handleWebhook(): Promise<void> {
  const jobData = process.env.JOB_DATA;

  let job: BlueprintJob | null = null;

  if (jobData) {
    // Parse job from webhook payload
    try {
      const payload = JSON.parse(jobData);
      // Handle Supabase webhook format (record in nested structure)
      const record = payload.record || payload;

      if (record.id && record.company_url) {
        // Claim the job atomically
        job = await claimPendingJob(record.id);
        if (!job) {
          console.log("[Index] Job already claimed by another worker");
          process.exit(0);
        }
      } else {
        console.error("[Index] Invalid job data format:", record);
        process.exit(1);
      }
    } catch (error) {
      console.error("[Index] Failed to parse JOB_DATA:", error);
      process.exit(1);
    }
  } else {
    // Poll for oldest pending job
    console.log("[Index] No JOB_DATA provided, polling for pending jobs...");
    const pendingJob = await getOldestPendingJob();
    if (pendingJob) {
      job = await claimPendingJob(pendingJob.id);
    }
  }

  if (!job) {
    console.log("[Index] No pending jobs to process");
    process.exit(0);
  }

  console.log(`[Index] Processing job ${job.id}`);
  const result = await processJob(job);

  if (result.success) {
    console.log(`[Index] Job completed: ${result.playbookUrl}`);
    // Output result for Modal to capture
    console.log(JSON.stringify({ success: true, playbookUrl: result.playbookUrl }));
    process.exit(0);
  } else {
    console.error(`[Index] Job failed: ${result.error}`);
    console.log(JSON.stringify({ success: false, error: result.error }));
    process.exit(1);
  }
}

/**
 * Handle CLI invocation for testing
 * Usage: npm run process-job -- <job-id>
 *    or: npm run process-job -- --url <company-url>
 */
async function handleCli(): Promise<void> {
  const args = process.argv.slice(2);

  if (args.length === 0) {
    console.log(`
Agent SDK Worker CLI

Usage:
  npm run process-job -- <job-id>         Process a specific job by ID
  npm run process-job -- --url <url>      Create and process a job for a URL
  npm run process-job -- --poll           Poll for pending jobs

Examples:
  npm run process-job -- abc123-def456
  npm run process-job -- --url https://owner.com
  npm run process-job -- --poll
`);
    process.exit(0);
  }

  if (args[0] === "--url" && args[1]) {
    // Create a mock job for testing
    const companyUrl = args[1];
    console.log(`[CLI] Testing with URL: ${companyUrl}`);

    // Import worker directly for testing (bypasses Supabase)
    const { ensureSkillsRepo, runBlueprintTurbo } = await import("./worker.js");

    try {
      const workingDirectory = await ensureSkillsRepo();
      const result = await runBlueprintTurbo(companyUrl, workingDirectory);
      console.log(`[CLI] Success!`);
      console.log(`[CLI] Playbook URL: ${result.playbookUrl}`);
      if (result.companyName) {
        console.log(`[CLI] Company Name: ${result.companyName}`);
      }
      process.exit(0);
    } catch (error) {
      console.error(`[CLI] Failed:`, error);
      process.exit(1);
    }
  }

  if (args[0] === "--poll") {
    // Poll for pending jobs
    console.log("[CLI] Polling for pending jobs...");
    await handleWebhook();
    return;
  }

  // Assume first arg is a job ID
  const jobId = args[0];
  console.log(`[CLI] Processing job: ${jobId}`);

  const job = await getJob(jobId);
  if (!job) {
    console.error(`[CLI] Job not found: ${jobId}`);
    process.exit(1);
  }

  const result = await processJob(job);
  if (result.success) {
    console.log(`[CLI] Success! Playbook: ${result.playbookUrl}`);
    process.exit(0);
  } else {
    console.error(`[CLI] Failed: ${result.error}`);
    process.exit(1);
  }
}

/**
 * Main entry point
 */
async function main(): Promise<void> {
  console.log("[Index] Agent SDK Worker starting...");

  // Check if running from Modal webhook (JOB_DATA env var present)
  // or from CLI (process.argv has arguments)
  const isWebhook = !!process.env.JOB_DATA;
  const hasCLIArgs = process.argv.length > 2;

  try {
    if (isWebhook || !hasCLIArgs) {
      await handleWebhook();
    } else {
      await handleCli();
    }
  } catch (error) {
    console.error("[Index] Unhandled error:", error);
    process.exit(1);
  }
}

// Run main
main().catch((error) => {
  console.error("[Index] Fatal error:", error);
  process.exit(1);
});
