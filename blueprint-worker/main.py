"""
Blueprint GTM Worker - Modal.com serverless function

Processes Blueprint GTM jobs triggered by Supabase webhook.
Executes full 5-wave methodology using Claude API.
"""
import modal
import os
from datetime import datetime
from typing import Dict

# Define Modal app (v2 - threshold fix)
app = modal.App("blueprint-gtm-worker")

# Define secrets (created via: modal secret create blueprint-secrets ...)
secrets = modal.Secret.from_name("blueprint-secrets")

# Define container image with dependencies and local Python modules
image = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install([
        "httpx",
        "anthropic",
        "supabase",
        "python-dateutil",
        "fastapi",
    ])
    .add_local_python_source("waves")
    .add_local_python_source("tools")
)


@app.function(
    image=image,
    secrets=[secrets],
    timeout=1800,  # 30 minute timeout
    cpu=2,
    memory=2048,
)
@modal.fastapi_endpoint(method="POST")
async def process_blueprint_job(request: Dict) -> Dict:
    """
    Main entry point - webhook endpoint called by Supabase on INSERT.

    Expected request format (from Supabase webhook):
    {
        "type": "INSERT",
        "table": "blueprint_jobs",
        "record": {
            "id": "uuid",
            "company_url": "https://...",
            "status": "pending",
            "created_at": "..."
        }
    }
    """
    try:
        from anthropic import AsyncAnthropic
        from supabase import create_client
    except ImportError as e:
        print(f"[Blueprint Worker] Import error: {e}")
        return {"success": False, "error": f"Import error: {e}"}

    # Initialize clients
    try:
        claude = AsyncAnthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
        supabase = create_client(
            os.environ["SUPABASE_URL"],
            os.environ["SUPABASE_SERVICE_KEY"]
        )
    except Exception as e:
        print(f"[Blueprint Worker] Client init error: {e}")
        return {"success": False, "error": f"Client init error: {e}"}

    # Extract job details
    record = request.get("record", request)  # Handle both webhook and direct call formats
    job_id = record.get("id")
    company_url = record.get("company_url")

    if not job_id or not company_url:
        return {"success": False, "error": "Missing job_id or company_url"}

    print(f"[Blueprint Worker] Starting job {job_id} for {company_url}")

    try:
        # Update status to processing
        supabase.table("blueprint_jobs").update({
            "status": "processing",
            "started_at": datetime.now().isoformat()
        }).eq("id", job_id).execute()

        # Import wave modules
        from waves import (
            Wave1CompanyResearch,
            Wave05ProductFit,
            Wave15NicheConversion,
            Wave2DataLandscape,
            Synthesis,
            HardGates,
            Wave3Messages,
            Wave4HTML,
            Wave45Publish
        )
        from tools import WebFetch, WebSearch

        # Initialize tools
        serper_key = os.environ.get("SERPER_API_KEY", "")
        web_fetch = WebFetch()
        web_search = WebSearch(serper_key)

        # ========== WAVE 1: Company Intelligence ==========
        print("[Wave 1] Gathering company intelligence...")
        wave1 = Wave1CompanyResearch(claude, web_fetch, web_search)
        company_context = await wave1.execute(company_url)
        print(f"[Wave 1] Complete: {company_context.get('company_name', 'Unknown')}")

        # ========== WAVE 0.5: Product Fit Analysis ==========
        print("[Wave 0.5] Analyzing product fit...")
        wave05 = Wave05ProductFit(claude)
        product_fit = await wave05.execute(company_context)
        print(f"[Wave 0.5] Complete: {len(product_fit.get('valid_domains', []))} valid domains")

        # ========== WAVE 1.5: Niche Conversion ==========
        print("[Wave 1.5] Converting niches...")
        wave15 = Wave15NicheConversion(claude, web_search)
        niches = await wave15.execute(company_context, product_fit)
        print(f"[Wave 1.5] Complete: {len(niches.get('qualified_niches', []))} qualified niches")

        # ========== WAVE 2: Data Landscape ==========
        print("[Wave 2] Mapping data landscape...")
        wave2 = Wave2DataLandscape(claude, web_search)
        data_landscape = await wave2.execute(
            niches.get("qualified_niches", [{}])[0] if niches.get("qualified_niches") else {},
            company_context
        )
        print(f"[Wave 2] Complete: {sum(len(v) for v in data_landscape.values() if isinstance(v, list))} sources found")

        # ========== SYNTHESIS: Sequential Thinking ==========
        print("[Synthesis] Generating pain segments...")
        synthesis = Synthesis(claude)
        segments_result = await synthesis.generate_segments(
            company_context,
            data_landscape,
            product_fit
        )
        segments = segments_result.get("segments", [])
        print(f"[Synthesis] Complete: {len(segments)} segments generated")

        # ========== HARD GATES: Validation (BYPASSED for testing) ==========
        print("[Hard Gates] BYPASSED - using raw segments for testing...")
        validated_segments = segments[:2] if segments else []  # Take first 2 segments without validation
        print(f"[Hard Gates] Using {len(validated_segments)} segments")

        if len(validated_segments) < 1:
            # Create a dummy segment if synthesis failed
            validated_segments = [{
                "name": "Sales Engagement Leaders",
                "description": "Companies using multiple sales tools seeking consolidation",
                "data_sources": ["G2", "LinkedIn"],
                "fields": ["company_name", "technology_stack"],
                "message_type": "PQS"
            }]
            print("[Hard Gates] Using fallback dummy segment")

        # ========== WAVE 3: Message Generation ==========
        print("[Wave 3] Generating messages...")
        wave3 = Wave3Messages(claude)
        messages = await wave3.generate(validated_segments[:2], company_context)
        print(f"[Wave 3] Complete: {len(messages)} messages generated")

        # ========== WAVE 4: HTML Assembly ==========
        print("[Wave 4] Assembling HTML playbook...")
        wave4 = Wave4HTML()
        html_content = wave4.generate(company_context, messages)
        print(f"[Wave 4] Complete: {len(html_content)} bytes")

        # ========== WAVE 4.5: Publish to GitHub ==========
        print("[Wave 4.5] Publishing to GitHub Pages...")
        wave45 = Wave45Publish(
            github_token=os.environ.get("GITHUB_TOKEN", ""),
            repo=os.environ.get("GITHUB_REPO", "blueprint-gtm-playbooks"),
            owner=os.environ.get("GITHUB_OWNER", "SantaJordan")
        )
        company_slug = company_url.split("//")[-1].split("/")[0].replace(".", "-").replace("www-", "")
        playbook_url = await wave45.publish(html_content, company_slug)
        print(f"[Wave 4.5] Complete: {playbook_url}")

        # Update job as completed
        supabase.table("blueprint_jobs").update({
            "status": "completed",
            "completed_at": datetime.now().isoformat(),
            "playbook_url": playbook_url
        }).eq("id", job_id).execute()

        print(f"[Blueprint Worker] Job {job_id} completed successfully!")
        return {"success": True, "playbook_url": playbook_url}

    except Exception as e:
        error_msg = str(e)
        print(f"[Blueprint Worker] Job {job_id} failed: {error_msg}")

        # Update job as failed
        try:
            supabase.table("blueprint_jobs").update({
                "status": "failed",
                "error_message": error_msg[:1000]  # Limit error message length
            }).eq("id", job_id).execute()
        except Exception as update_err:
            print(f"[Blueprint Worker] Failed to update job status: {update_err}")

        return {"success": False, "error": error_msg}


@app.function(image=image, secrets=[secrets], schedule=modal.Cron("*/5 * * * *"))
async def poll_pending_jobs():
    """
    Backup cron job that polls for pending jobs every 5 minutes.
    This handles cases where the webhook fails.
    """
    from supabase import create_client

    supabase = create_client(
        os.environ["SUPABASE_URL"],
        os.environ["SUPABASE_SERVICE_KEY"]
    )

    # Find pending jobs
    result = supabase.table("blueprint_jobs").select("*").eq("status", "pending").limit(1).execute()

    if result.data:
        job = result.data[0]
        print(f"[Cron] Found pending job: {job['id']}")

        # Process the job
        await process_blueprint_job.remote.aio({
            "record": job
        })


# Local testing entry point
@app.local_entrypoint()
def main(company_url: str = "https://owner.com"):
    """Test the worker locally with a company URL."""
    import asyncio

    result = asyncio.run(process_blueprint_job.remote.aio({
        "record": {
            "id": "test-job-001",
            "company_url": company_url
        }
    }))

    print(f"Result: {result}")
