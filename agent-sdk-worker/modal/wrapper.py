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

# Create a custom image with Node.js and required packages
image = (
    modal.Image.debian_slim(python_version="3.11")
    # Install Node.js 20
    .apt_install("curl", "git")
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
        "npm install -g @sequentialthinking/mcp-server",
    ])
    # Install Python dependencies for Supabase health checks
    .pip_install(["supabase", "httpx"])
)

# Modal secrets - uses the same secrets as the existing blueprint-worker
secrets = [
    modal.Secret.from_name("blueprint-secrets"),
]

# Mount the agent-sdk-worker directory
agent_worker_mount = modal.Mount.from_local_dir(
    local_path=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    remote_path="/app/agent-sdk-worker",
    condition=lambda path: not any(
        x in path for x in ["node_modules", "dist", ".git", "__pycache__"]
    ),
)


@app.function(
    image=image,
    secrets=secrets,
    mounts=[agent_worker_mount],
    timeout=1800,  # 30 minutes
    cpu=2,
    memory=4096,
    retries=0,  # No automatic retries - we handle errors ourselves
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

    # Extract job from webhook payload
    record = request.get("record", request)
    job_id = record.get("id")
    company_url = record.get("company_url")

    if not job_id or not company_url:
        logger.error(f"Invalid request - missing id or company_url: {request}")
        return {"success": False, "error": "Invalid request - missing id or company_url"}

    logger.info(f"Processing job {job_id} for {company_url}")

    # Install npm dependencies
    logger.info("Installing npm dependencies...")
    try:
        subprocess.run(
            ["npm", "install"],
            cwd="/app/agent-sdk-worker",
            check=True,
            capture_output=True,
            timeout=120,
        )
    except subprocess.TimeoutExpired:
        logger.error("npm install timed out")
        return {"success": False, "error": "npm install timed out"}
    except subprocess.CalledProcessError as e:
        logger.error(f"npm install failed: {e.stderr.decode()}")
        return {"success": False, "error": f"npm install failed: {e.stderr.decode()[:500]}"}

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
            timeout=1500,  # 25 minutes
        )

        logger.info(f"Worker stdout: {result.stdout[-2000:]}")
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
            error_msg = result.stderr or result.stdout[-500:]
            logger.error(f"Worker failed with code {result.returncode}: {error_msg}")
            return {"success": False, "error": error_msg}

    except subprocess.TimeoutExpired:
        logger.error("Worker execution timed out")
        return {"success": False, "error": "Execution timed out after 25 minutes"}
    except Exception as e:
        logger.error(f"Worker exception: {str(e)}")
        return {"success": False, "error": str(e)}


@app.function(
    image=image,
    secrets=secrets,
    mounts=[agent_worker_mount],
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

    # Install npm dependencies
    try:
        subprocess.run(
            ["npm", "install"],
            cwd="/app/agent-sdk-worker",
            check=True,
            capture_output=True,
            timeout=120,
        )
    except Exception as e:
        logger.error(f"npm install failed: {e}")
        return {"success": False, "error": str(e)}

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
    if url:
        # Create a mock job
        result = process_blueprint_job.remote({
            "id": "test-" + str(hash(url))[:8],
            "company_url": url,
            "status": "pending",
        })
        print(f"Result: {result}")
    elif job_id:
        result = process_blueprint_job.remote({
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
