#!/usr/bin/env node

/**
 * Blueprint GTM Worker
 *
 * Polls Supabase for pending Blueprint analysis jobs and executes them
 * using Claude Code's /blueprint-turbo command.
 */

import { createClient } from '@supabase/supabase-js';
import { spawn } from 'child_process';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

// Configuration
const SUPABASE_URL = 'https://hvuwlhdaswixbkglnrxu.supabase.co';
const SUPABASE_KEY = 'sb_secret_0cX7akELvjfchOXhqNBe8g_XcLu22co';
const POLL_INTERVAL_MS = 30000; // 30 seconds
const PROJECT_DIR = '/Users/jordancrawford/Desktop/Blueprint-GTM-Skills';

// Initialize Supabase client
const supabase = createClient(SUPABASE_URL, SUPABASE_KEY);

// Logging helper
function log(message, data = null) {
  const timestamp = new Date().toISOString();
  console.log(`[${timestamp}] ${message}`);
  if (data) {
    console.log(JSON.stringify(data, null, 2));
  }
}

// Execute Blueprint Turbo analysis
async function executeBlueprintTurbo(job) {
  return new Promise((resolve, reject) => {
    log(`Starting Blueprint Turbo for job ${job.id}`, { companyUrl: job.company_url });

    // Update job status to processing
    supabase
      .from('blueprint_jobs')
      .update({
        status: 'processing',
        started_at: new Date().toISOString()
      })
      .eq('id', job.id)
      .then(() => {
        log(`Job ${job.id} marked as processing`);
      });

    // Spawn Claude Code process with slash command as prompt argument
    const claude = spawn('/Users/jordancrawford/.local/bin/claude', [
      'chat',
      `/blueprint-turbo ${job.company_url}`
    ], {
      cwd: PROJECT_DIR,
      stdio: ['pipe', 'pipe', 'pipe'],
      env: {
        ...process.env,
        // Ensure auto-approval settings are used
        CLAUDE_CODE_AUTO_APPROVE: 'true'
      }
    });

    let stdout = '';
    let stderr = '';

    claude.stdout.on('data', (data) => {
      const output = data.toString();
      stdout += output;
      // Log progress in real-time
      process.stdout.write(output);
    });

    claude.stderr.on('data', (data) => {
      const output = data.toString();
      stderr += output;
      process.stderr.write(output);
    });

    claude.on('close', async (code) => {
      if (code === 0) {
        log(`Job ${job.id} completed successfully`);

        // Extract GitHub Pages URL from output if available
        const urlMatch = stdout.match(/https:\/\/[^\s]+\.github\.io[^\s]*/);
        const playbookUrl = urlMatch ? urlMatch[0] : null;

        // Update job as completed
        const { error } = await supabase
          .from('blueprint_jobs')
          .update({
            status: 'completed',
            completed_at: new Date().toISOString(),
            playbook_url: playbookUrl
          })
          .eq('id', job.id);

        if (error) {
          log(`Error updating job ${job.id}:`, error);
          reject(error);
        } else {
          log(`Job ${job.id} marked as completed`, { playbookUrl });
          resolve({ success: true, playbookUrl });
        }
      } else {
        log(`Job ${job.id} failed with exit code ${code}`);

        // Update job as failed
        const { error } = await supabase
          .from('blueprint_jobs')
          .update({
            status: 'failed',
            completed_at: new Date().toISOString(),
            error_message: stderr || `Process exited with code ${code}`
          })
          .eq('id', job.id);

        if (error) {
          log(`Error updating failed job ${job.id}:`, error);
        }

        reject(new Error(`Blueprint Turbo failed with code ${code}`));
      }
    });

    claude.on('error', async (error) => {
      log(`Error spawning Claude Code for job ${job.id}:`, error);

      // Update job as failed
      await supabase
        .from('blueprint_jobs')
        .update({
          status: 'failed',
          completed_at: new Date().toISOString(),
          error_message: error.message
        })
        .eq('id', job.id);

      reject(error);
    });
  });
}

// Poll for pending jobs
async function pollJobs() {
  try {
    // Fetch the oldest pending job
    const { data: jobs, error } = await supabase
      .from('blueprint_jobs')
      .select('*')
      .eq('status', 'pending')
      .order('created_at', { ascending: true })
      .limit(1);

    if (error) {
      log('Error fetching jobs:', error);
      return;
    }

    if (!jobs || jobs.length === 0) {
      // No pending jobs, just wait for next poll
      return;
    }

    const job = jobs[0];
    log(`Found pending job ${job.id}`);

    try {
      await executeBlueprintTurbo(job);
    } catch (error) {
      log(`Failed to execute job ${job.id}:`, error);
    }

  } catch (error) {
    log('Unexpected error in poll cycle:', error);
  }
}

// Main loop
async function main() {
  log('Blueprint Worker started');
  log(`Polling interval: ${POLL_INTERVAL_MS}ms (${POLL_INTERVAL_MS / 1000}s)`);
  log(`Project directory: ${PROJECT_DIR}`);

  // Initial poll
  await pollJobs();

  // Set up polling interval
  setInterval(pollJobs, POLL_INTERVAL_MS);

  log('Worker is now polling for jobs...');
}

// Handle graceful shutdown
process.on('SIGINT', () => {
  log('Received SIGINT, shutting down gracefully...');
  process.exit(0);
});

process.on('SIGTERM', () => {
  log('Received SIGTERM, shutting down gracefully...');
  process.exit(0);
});

// Start the worker
main().catch((error) => {
  log('Fatal error:', error);
  process.exit(1);
});
