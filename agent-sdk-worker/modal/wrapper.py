"""
Modal Python Wrapper for Agent SDK Worker

This wrapper deploys the TypeScript Agent SDK worker to Modal.
It spawns Node.js as a subprocess to run the TypeScript code.
"""

import modal
import subprocess
import os
import json
import sys

# Define the Modal app
app = modal.App("blueprint-agent-sdk-worker")

# Get the agent-sdk-worker directory path and parent (Blueprint-GTM-Skills)
AGENT_WORKER_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BLUEPRINT_SKILLS_DIR = os.path.dirname(AGENT_WORKER_DIR)  # Parent directory with .claude/

# Create a custom image with Node.js, Chromium, and required packages
image = (
    modal.Image.debian_slim(python_version="3.11")
    # Install Node.js 20 and Chromium with dependencies
    .apt_install(
        "curl",
        "git",
        # Chromium and its dependencies for browser-mcp
        "chromium",
        "libgbm1",
        "libnss3",
        "libatk1.0-0",
        "libatk-bridge2.0-0",
        "libcups2",
        "libxkbcommon0",
        "libxcomposite1",
        "libxdamage1",
        "libxrandr2",
        "libasound2",
    )
    .run_commands([
        # Install Node.js 20 via NodeSource
        "curl -fsSL https://deb.nodesource.com/setup_20.x | bash -",
        "apt-get install -y nodejs",
        # Verify installation
        "node --version",
        "npm --version",
    ])
    # Install global npm packages
    .run_commands([
        "npm install -g tsx",
        "npm install -g @modelcontextprotocol/server-sequential-thinking",
        "npm install -g browser-mcp",  # Add browser-mcp for Wave 1-2 research
    ])
    # Set Chromium environment variables for browser-mcp
    .env({
        "CHROME_PATH": "/usr/bin/chromium",
        "PUPPETEER_EXECUTABLE_PATH": "/usr/bin/chromium",
        "PUPPETEER_SKIP_CHROMIUM_DOWNLOAD": "true",
    })
    # Install Python dependencies for Supabase health checks and web endpoints
    .pip_install(["supabase", "httpx", "fastapi"])
    # Add the agent-sdk-worker source code to the image (copy=True to allow npm install after)
    .add_local_dir(
        AGENT_WORKER_DIR,
        remote_path="/app/agent-sdk-worker",
        ignore=["node_modules", "dist", ".git", "__pycache__", "*.pyc"],
        copy=True,
    )
    # Add the .claude/ skills directory (from parent Blueprint-GTM-Skills)
    .add_local_dir(
        os.path.join(BLUEPRINT_SKILLS_DIR, ".claude"),
        remote_path="/app/blueprint-skills/.claude",
        copy=True,
    )
    # Add CLAUDE.md from parent
    .add_local_file(
        os.path.join(BLUEPRINT_SKILLS_DIR, "CLAUDE.md"),
        remote_path="/app/blueprint-skills/CLAUDE.md",
        copy=True,
    )
    # Pre-install Node dependencies into the image to avoid per-job npm install.
    .run_commands([
        "cd /app/agent-sdk-worker && npm install --omit=dev",
    ])
)

# Modal secrets - uses blueprint-secrets plus blueprint-vercel for Vercel deployment
secrets = [
    modal.Secret.from_name("blueprint-secrets"),
    modal.Secret.from_name("blueprint-vercel"),  # Contains VERCEL_TOKEN for HTML hosting
    modal.Secret.from_name("apify-token"),  # Contains APIFY_API_TOKEN for pre-fetch
]


def update_job_status_timeout(job_id: str, logger):
    """Mark job as failed due to timeout - prevents orphaned jobs"""
    from supabase import create_client
    from datetime import datetime

    supabase_url = os.environ.get("SUPABASE_URL")
    supabase_key = os.environ.get("SUPABASE_SERVICE_KEY")

    if not supabase_url or not supabase_key:
        logger.error("Missing Supabase credentials for timeout handler")
        return

    try:
        client = create_client(supabase_url, supabase_key)
        client.table("blueprint_jobs").update({
            "status": "failed",
            "error_message": f"Wall-clock timeout at {datetime.utcnow().isoformat()}",
            "completed_at": datetime.utcnow().isoformat(),
        }).eq("id", job_id).execute()
        logger.info(f"Marked job {job_id} as failed due to timeout")
    except Exception as e:
        logger.error(f"Failed to update job on timeout: {e}")


def _run_job_internal(request: dict, logger):
    """Internal job processing logic - shared by webhook and test function."""
    # Extract job from webhook payload
    record = request.get("record", request)
    job_id = record.get("id")
    company_url = record.get("company_url")

    if not job_id or not company_url:
        logger.error(f"Invalid request - missing id or company_url: {request}")
        return {"success": False, "error": "Invalid request - missing id or company_url"}

    logger.info(f"Processing job {job_id} for {company_url}")

    # CRITICAL FIX: On Linux, project-level skills (.claude/skills/) don't auto-discover
    # Only user-level skills (~/.claude/skills/) work on Linux (GitHub Issue #268)
    # Copy skills to user-level location instead of project-level symlinks
    logger.info("Setting up USER-LEVEL skills for Linux compatibility...")
    try:
        # Create user-level .claude directories
        subprocess.run(["mkdir", "-p", "/root/.claude/skills"], check=True, capture_output=True)
        subprocess.run(["mkdir", "-p", "/root/.claude/commands"], check=True, capture_output=True)

        # Copy skills to user-level location
        subprocess.run(
            ["cp", "-r", "/app/blueprint-skills/.claude/skills/.", "/root/.claude/skills/"],
            check=True,
            capture_output=True,
        )
        # Copy commands to user-level location
        subprocess.run(
            ["cp", "-r", "/app/blueprint-skills/.claude/commands/.", "/root/.claude/commands/"],
            check=True,
            capture_output=True,
        )
        logger.info("User-level skills copied successfully to /root/.claude/")

        # List what was copied for debugging
        skills_result = subprocess.run(["ls", "-la", "/root/.claude/skills/"], capture_output=True, text=True)
        logger.info(f"User skills: {skills_result.stdout}")
        commands_result = subprocess.run(["ls", "-la", "/root/.claude/commands/"], capture_output=True, text=True)
        logger.info(f"User commands: {commands_result.stdout}")

        # Also keep project-level symlinks as fallback
        subprocess.run(
            ["ln", "-sf", "/app/blueprint-skills/.claude", "/app/agent-sdk-worker/.claude"],
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["ln", "-sf", "/app/blueprint-skills/CLAUDE.md", "/app/agent-sdk-worker/CLAUDE.md"],
            check=True,
            capture_output=True,
        )
        logger.info("Project-level symlinks also created as fallback")
    except subprocess.CalledProcessError as e:
        logger.warning(f"Skills setup failed: {e}")

    # Create playbooks directory for agent output
    # (Vercel publishing reads from this directory)
    try:
        subprocess.run(
            ["mkdir", "-p", "/app/blueprint-skills/playbooks"],
            check=True,
            capture_output=True,
        )
        logger.info("Created playbooks directory at /app/blueprint-skills/playbooks")
    except subprocess.CalledProcessError as e:
        logger.warning(f"Failed to create playbooks directory: {e}")

    # Dependencies are installed in the image; avoid per-job npm install.
    logger.info("Node dependencies preinstalled in image; skipping npm install")

    # Run the TypeScript worker via tsx
    logger.info("Running Agent SDK worker...")
    env = os.environ.copy()
    env["JOB_DATA"] = json.dumps(record)

    try:
        result = subprocess.run(
            ["npx", "tsx", "src/index.ts"],
            cwd="/app/agent-sdk-worker",
            env=env,
            capture_output=True,
            text=True,
            timeout=4200,  # 70 minutes (leave 5 min buffer for cleanup)
        )

        logger.info(f"Worker stdout (full): {result.stdout}")
        if result.stderr:
            logger.warning(f"Worker stderr: {result.stderr[-1000:]}")

        if result.returncode == 0:
            # Try to parse the JSON output
            try:
                # Look for JSON in the last few lines of output
                for line in reversed(result.stdout.strip().split("\n")):
                    line = line.strip()
                    if line.startswith("{") and "playbookUrl" in line:
                        output = json.loads(line)
                        logger.info(f"Job completed: {output}")
                        return output
            except json.JSONDecodeError:
                pass

            # If no JSON found, return success with last output
            return {"success": True, "output": result.stdout[-500:]}
        else:
            # Include both stdout and stderr in error for debugging
            error_msg = f"STDOUT:\n{result.stdout}\n\nSTDERR:\n{result.stderr}"
            logger.error(f"Worker failed with code {result.returncode}: {error_msg[-2000:]}")
            return {"success": False, "error": error_msg[-3000:]}

    except subprocess.TimeoutExpired:
        logger.error("Worker execution timed out after 36 minutes")
        # CRITICAL: Mark job as failed before returning to prevent orphaned jobs
        update_job_status_timeout(job_id, logger)
        return {"success": False, "error": "Execution timed out after 36 minutes"}
    except Exception as e:
        logger.error(f"Worker exception: {str(e)}")
        return {"success": False, "error": str(e)}


@app.function(
    image=image,
    secrets=secrets,
    timeout=4500,  # 75 minutes (comprehensive Blueprint Turbo + overhead)
    cpu=2,
    memory=4096,
)
def test_job(request: dict):
    """Non-webhook function for CLI testing."""
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("agent-sdk-worker-test")
    logger.info(f"Test job request: {json.dumps(request, indent=2)[:500]}")
    return _run_job_internal(request, logger)


@app.function(
    image=image,
    secrets=secrets,
    timeout=4500,  # 75 minutes (comprehensive Blueprint Turbo + overhead)
    cpu=2,
    memory=4096,
)
@modal.fastapi_endpoint(method="POST")
async def process_blueprint_job(request: dict):
    """
    Webhook endpoint for Supabase to trigger job processing.

    Expects a Supabase webhook payload with the job record.
    """
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("agent-sdk-worker")
    logger.info(f"Received webhook request: {json.dumps(request, indent=2)[:500]}")
    return _run_job_internal(request, logger)


@app.function(
    image=image,
    secrets=secrets,
    timeout=1800,
    cpu=2,
    memory=4096,
    schedule=modal.Period(minutes=5),  # Poll every 5 minutes as backup
)
async def poll_pending_jobs():
    """
    Cron job to poll for pending jobs that weren't triggered by webhook.
    This is a backup in case the webhook fails.
    """
    import logging

    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("agent-sdk-worker-cron")

    logger.info("Polling for pending jobs...")

    # CRITICAL FIX: On Linux, project-level skills (.claude/skills/) don't auto-discover
    # Only user-level skills (~/.claude/skills/) work on Linux (GitHub Issue #268)
    logger.info("Setting up USER-LEVEL skills for Linux compatibility...")
    try:
        # Create user-level .claude directories
        subprocess.run(["mkdir", "-p", "/root/.claude/skills"], check=True, capture_output=True)
        subprocess.run(["mkdir", "-p", "/root/.claude/commands"], check=True, capture_output=True)

        # Copy skills to user-level location
        subprocess.run(
            ["cp", "-r", "/app/blueprint-skills/.claude/skills/.", "/root/.claude/skills/"],
            check=True,
            capture_output=True,
        )
        # Copy commands to user-level location
        subprocess.run(
            ["cp", "-r", "/app/blueprint-skills/.claude/commands/.", "/root/.claude/commands/"],
            check=True,
            capture_output=True,
        )
        logger.info("User-level skills copied successfully to /root/.claude/")

        # Also keep project-level symlinks as fallback
        subprocess.run(
            ["ln", "-sf", "/app/blueprint-skills/.claude", "/app/agent-sdk-worker/.claude"],
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["ln", "-sf", "/app/blueprint-skills/CLAUDE.md", "/app/agent-sdk-worker/CLAUDE.md"],
            check=True,
            capture_output=True,
        )
    except subprocess.CalledProcessError as e:
        logger.warning(f"Skills setup failed: {e}")

    # Install npm dependencies
    logger.info("Node dependencies preinstalled in image; skipping npm install")

    # Run the worker in poll mode (no JOB_DATA = poll for oldest pending)
    env = os.environ.copy()

    try:
        result = subprocess.run(
            ["npx", "tsx", "src/index.ts"],
            cwd="/app/agent-sdk-worker",
            env=env,
            capture_output=True,
            text=True,
            timeout=1500,
        )

        logger.info(f"Poll result: {result.stdout[-500:]}")
        return {"success": result.returncode == 0, "output": result.stdout[-500:]}

    except Exception as e:
        logger.error(f"Poll exception: {e}")
        return {"success": False, "error": str(e)}


@app.local_entrypoint()
def main(job_id: str = None, url: str = None, poll: bool = False):
    """
    Local CLI for testing the Modal functions.

    Usage:
        modal run modal/wrapper.py --job-id <job-id>
        modal run modal/wrapper.py --url https://example.com
        modal run modal/wrapper.py --poll
    """
    import uuid

    if url:
        # Create a mock job with proper UUID - use test_job.remote() to run in Modal container
        # Use direct=true to bypass Supabase claim check for test jobs
        test_uuid = str(uuid.uuid4())
        print(f"Generated test job ID: {test_uuid}")
        result = test_job.remote({
            "id": test_uuid,
            "company_url": url,
            "status": "pending",
            "direct": True,  # Bypass Supabase claim check
        })
        print(f"Result: {result}")
    elif job_id:
        result = test_job.remote({
            "id": job_id,
            "company_url": "placeholder",  # Will be fetched from Supabase
            "status": "pending",
        })
        print(f"Result: {result}")
    elif poll:
        result = poll_pending_jobs.remote()
        print(f"Poll result: {result}")
    else:
        print("Usage:")
        print("  modal run modal/wrapper.py --job-id <job-id>")
        print("  modal run modal/wrapper.py --url https://example.com")
        print("  modal run modal/wrapper.py --poll")


if __name__ == "__main__":
    # For local testing without Modal
    print("This script should be run via Modal:")
    print("  modal deploy modal/wrapper.py")
    print("  modal run modal/wrapper.py --help")
