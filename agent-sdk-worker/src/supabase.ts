/**
 * Supabase integration for Blueprint Jobs
 * Handles job status updates and playbook URL storage
 */

import { createClient, SupabaseClient } from "@supabase/supabase-js";
import { getConfig } from "./config.js";

export interface BlueprintJob {
  id: string;
  company_url: string;
  status: "pending" | "processing" | "completed" | "failed";
  playbook_url: string | null;
  company_name: string | null;
  error_message: string | null;
  stripe_payment_intent_id?: string | null;
  payment_status?: string | null;
  created_at: string;
  started_at: string | null;
  completed_at: string | null;
  // Checkpoint fields for resume capability
  checkpoint_wave?: string | null;
  checkpoint_data?: CheckpointData | null;
}

/**
 * Checkpoint data structure for resume capability
 * Saved after each wave to enable resumption on timeout
 */
export interface CheckpointData {
  wave: string;  // Current wave identifier
  timestamp: string;
  company_context?: {
    name: string;
    offering: string;
    differentiators: string[];
  };
  icp?: {
    industries: string[];
    company_types: string[];
    operational_context: string;
  };
  persona?: {
    title: string;
    responsibilities: string[];
    kpis: string[];
  };
  data_sources?: Array<{
    name: string;
    category: string;
    feasibility: "HIGH" | "MEDIUM" | "LOW";
    url?: string;
    fields?: string[];
  }>;
  segments?: Array<{
    name: string;
    data_combination: string[];
    confidence: number;
    type: "PQS" | "PVP";
  }>;
  messages?: Array<{
    type: "PQS" | "PVP";
    subject: string;
    body: string;
    score: number;
  }>;
  prefetch_data?: {
    webPages: Array<{ url: string; markdown: string }>;
    searchResults: Array<{ title: string; url: string; snippet: string }>;
  };
}

let supabaseClient: SupabaseClient | null = null;

function getSupabase(): SupabaseClient {
  if (!supabaseClient) {
    const config = getConfig();
    supabaseClient = createClient(config.supabaseUrl, config.supabaseServiceKey);
  }
  return supabaseClient;
}

/**
 * Get a job by ID
 */
export async function getJob(jobId: string): Promise<BlueprintJob | null> {
  const { data, error } = await getSupabase()
    .from("blueprint_jobs")
    .select("*")
    .eq("id", jobId)
    .single();

  if (error) {
    console.error(`[Supabase] Error fetching job ${jobId}:`, error);
    return null;
  }

  return data as BlueprintJob;
}

/**
 * Get the oldest pending job (for polling mode)
 */
export async function getOldestPendingJob(): Promise<BlueprintJob | null> {
  const { data, error } = await getSupabase()
    .from("blueprint_jobs")
    .select("*")
    .eq("status", "pending")
    .order("created_at", { ascending: true })
    .limit(1)
    .single();

  if (error) {
    if (error.code === "PGRST116") {
      // No rows found
      return null;
    }
    console.error("[Supabase] Error fetching pending job:", error);
    return null;
  }

  return data as BlueprintJob;
}

/**
 * Mark job as processing
 */
export async function markJobProcessing(jobId: string): Promise<boolean> {
  const { error } = await getSupabase()
    .from("blueprint_jobs")
    .update({
      status: "processing",
      started_at: new Date().toISOString(),
    })
    .eq("id", jobId);

  if (error) {
    console.error(`[Supabase] Error marking job ${jobId} as processing:`, error);
    return false;
  }

  console.log(`[Supabase] Job ${jobId} marked as processing`);
  return true;
}

/**
 * Mark job as completed with playbook URL
 */
export async function markJobCompleted(
  jobId: string,
  playbookUrl: string,
  companyName?: string
): Promise<boolean> {
  const { error } = await getSupabase()
    .from("blueprint_jobs")
    .update({
      status: "completed",
      playbook_url: playbookUrl,
      company_name: companyName || null,
      completed_at: new Date().toISOString(),
    })
    .eq("id", jobId);

  if (error) {
    console.error(`[Supabase] Error marking job ${jobId} as completed:`, error);
    return false;
  }

  console.log(`[Supabase] Job ${jobId} completed with URL: ${playbookUrl}`);
  return true;
}

/**
 * Mark job as failed with error message
 */
export async function markJobFailed(
  jobId: string,
  errorMessage: string
): Promise<boolean> {
  const { error } = await getSupabase()
    .from("blueprint_jobs")
    .update({
      status: "failed",
      error_message: errorMessage,
      completed_at: new Date().toISOString(),
    })
    .eq("id", jobId);

  if (error) {
    console.error(`[Supabase] Error marking job ${jobId} as failed:`, error);
    return false;
  }

  console.error(`[Supabase] Job ${jobId} failed: ${errorMessage}`);
  return true;
}

/**
 * Claim a pending job atomically (to prevent race conditions)
 * Uses a compare-and-swap pattern
 */
export async function claimPendingJob(
  jobId: string
): Promise<BlueprintJob | null> {
  // First, try to update only if status is still 'pending'
  const { data, error } = await getSupabase()
    .from("blueprint_jobs")
    .update({
      status: "processing",
      started_at: new Date().toISOString(),
    })
    .eq("id", jobId)
    .eq("status", "pending")
    .select()
    .single();

  if (error) {
    if (error.code === "PGRST116") {
      // No rows updated - job was already claimed
      console.log(`[Supabase] Job ${jobId} already claimed by another worker`);
      return null;
    }
    console.error(`[Supabase] Error claiming job ${jobId}:`, error);
    return null;
  }

  console.log(`[Supabase] Successfully claimed job ${jobId}`);
  return data as BlueprintJob;
}

// ============================================================================
// CHECKPOINT FUNCTIONS FOR RESUME CAPABILITY
// ============================================================================

/**
 * Save checkpoint data for a job
 * Called after each wave completes to enable resume on timeout
 */
export async function saveCheckpoint(
  jobId: string,
  wave: string,
  data: Partial<CheckpointData>
): Promise<boolean> {
  const checkpointData: CheckpointData = {
    wave,
    timestamp: new Date().toISOString(),
    ...data,
  };

  const { error } = await getSupabase()
    .from("blueprint_jobs")
    .update({
      checkpoint_wave: wave,
      checkpoint_data: checkpointData,
    })
    .eq("id", jobId);

  if (error) {
    console.error(`[Supabase] Error saving checkpoint for job ${jobId}:`, error);
    return false;
  }

  console.log(`[Supabase] Checkpoint saved: ${wave} for job ${jobId}`);
  return true;
}

/**
 * Load checkpoint data for a job
 * Returns null if no checkpoint exists
 */
export async function loadCheckpoint(
  jobId: string
): Promise<CheckpointData | null> {
  const { data, error } = await getSupabase()
    .from("blueprint_jobs")
    .select("checkpoint_wave, checkpoint_data")
    .eq("id", jobId)
    .single();

  if (error) {
    console.error(`[Supabase] Error loading checkpoint for job ${jobId}:`, error);
    return null;
  }

  if (data?.checkpoint_data) {
    console.log(`[Supabase] Loaded checkpoint: ${data.checkpoint_wave} for job ${jobId}`);
    return data.checkpoint_data as CheckpointData;
  }

  return null;
}

/**
 * Clear checkpoint data after successful completion
 */
export async function clearCheckpoint(jobId: string): Promise<boolean> {
  const { error } = await getSupabase()
    .from("blueprint_jobs")
    .update({
      checkpoint_wave: null,
      checkpoint_data: null,
    })
    .eq("id", jobId);

  if (error) {
    console.error(`[Supabase] Error clearing checkpoint for job ${jobId}:`, error);
    return false;
  }

  console.log(`[Supabase] Checkpoint cleared for job ${jobId}`);
  return true;
}
