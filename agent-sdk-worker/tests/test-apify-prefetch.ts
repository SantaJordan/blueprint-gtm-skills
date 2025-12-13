/**
 * Test script for Apify pre-fetch integration
 *
 * Usage:
 *   APIFY_API_TOKEN=apify_api_xxx npx tsx tests/test-apify-prefetch.ts https://owner.com
 */

interface PrefetchResult {
  success: boolean;
  webPages?: Array<{ url: string; markdown: string }>;
  searchResults?: Array<{ title: string; url: string; snippet: string }>;
  error?: string;
  timing?: {
    webPagesMs: number;
    searchMs: number;
    totalMs: number;
  };
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
    throw new Error("APIFY_API_TOKEN environment variable is required");
  }

  console.log(`[Apify] Starting actor: ${actorId}`);
  const startTime = Date.now();

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
    const errorText = await runResponse.text();
    throw new Error(`Apify run failed: ${runResponse.status} - ${errorText}`);
  }

  const runData = await runResponse.json() as { data?: { id?: string } };
  const runId = runData.data?.id;
  if (!runId) {
    throw new Error("No run ID returned from Apify");
  }

  console.log(`[Apify] Run started: ${runId}`);

  // Poll for completion
  while (Date.now() - startTime < timeoutMs) {
    await new Promise(resolve => setTimeout(resolve, 3000)); // Wait 3 seconds

    const statusResponse = await fetch(
      `https://api.apify.com/v2/actor-runs/${runId}?token=${apifyToken}`
    );
    const statusData = await statusResponse.json() as { data?: { status?: string } };
    const status = statusData.data?.status;

    const elapsed = ((Date.now() - startTime) / 1000).toFixed(1);
    console.log(`[Apify] Status: ${status} (${elapsed}s)`);

    if (status === "SUCCEEDED") {
      break;
    } else if (status === "FAILED" || status === "ABORTED" || status === "TIMED-OUT") {
      throw new Error(`Apify run failed with status: ${status}`);
    }
  }

  // Get the dataset items
  const datasetResponse = await fetch(
    `https://api.apify.com/v2/actor-runs/${runId}/dataset/items?token=${apifyToken}`
  );
  const items = await datasetResponse.json() as any[];

  const elapsed = ((Date.now() - startTime) / 1000).toFixed(1);
  console.log(`[Apify] Completed in ${elapsed}s, ${items.length} items`);

  return items;
}

/**
 * Pre-fetch company data using Apify actors
 */
async function prefetchCompanyData(companyUrl: string): Promise<PrefetchResult> {
  const totalStart = Date.now();
  console.log(`\n[Prefetch] Starting for ${companyUrl}`);

  try {
    const domain = new URL(companyUrl).hostname.replace(/^www\./, "");
    console.log(`[Prefetch] Domain: ${domain}`);

    // Run both actors in parallel
    const webPagesStart = Date.now();
    const searchStart = Date.now();

    const [webPages, searchResults] = await Promise.all([
      // RAG Web Browser for the main website pages
      runApifyActor("apify/rag-web-browser", {
        query: companyUrl,
        maxResults: 5,
        outputFormats: ["markdown"],
        requestTimeoutSecs: 30,
      }).then(result => {
        console.log(`[Prefetch] Web pages completed in ${((Date.now() - webPagesStart) / 1000).toFixed(1)}s`);
        return result;
      }),

      // Google Search for context (queries must be newline-separated string)
      runApifyActor("apify/google-search-scraper", {
        queries: `${domain} products services\n${domain} customers case studies\n${domain} reviews`,
        maxPagesPerQuery: 3,
        resultsPerPage: 10,
      }).then(result => {
        console.log(`[Prefetch] Search completed in ${((Date.now() - searchStart) / 1000).toFixed(1)}s`);
        return result;
      }),
    ]);

    const totalMs = Date.now() - totalStart;
    console.log(`\n[Prefetch] Total time: ${(totalMs / 1000).toFixed(1)}s`);

    // Format results
    const formattedPages = webPages.map((item: any) => ({
      url: item.url || item.sourceUrl || companyUrl,
      markdown: item.markdown || item.text || item.content || "",
    }));

    const formattedSearch = searchResults.flatMap((result: any) => {
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
      timing: {
        webPagesMs: Date.now() - webPagesStart,
        searchMs: Date.now() - searchStart,
        totalMs,
      },
    };
  } catch (error) {
    console.error(`[Prefetch] Error: ${error}`);
    return {
      success: false,
      error: String(error),
    };
  }
}

// Main execution
async function main() {
  const testUrl = process.argv[2] || "https://owner.com";

  console.log("=".repeat(60));
  console.log("Apify Pre-Fetch Integration Test");
  console.log("=".repeat(60));
  console.log(`\nTest URL: ${testUrl}`);
  console.log(`APIFY_API_TOKEN: ${process.env.APIFY_API_TOKEN ? "Set (hidden)" : "NOT SET"}`);

  if (!process.env.APIFY_API_TOKEN) {
    console.error("\nError: APIFY_API_TOKEN environment variable is required");
    console.error("Usage: APIFY_API_TOKEN=apify_api_xxx npx tsx tests/test-apify-prefetch.ts <url>");
    process.exit(1);
  }

  const result = await prefetchCompanyData(testUrl);

  console.log("\n" + "=".repeat(60));
  console.log("Results Summary");
  console.log("=".repeat(60));

  if (result.success) {
    console.log(`\nSuccess: ${result.success}`);
    console.log(`Web pages retrieved: ${result.webPages?.length || 0}`);
    console.log(`Search results retrieved: ${result.searchResults?.length || 0}`);

    if (result.timing) {
      console.log(`\nTiming:`);
      console.log(`  Total: ${(result.timing.totalMs / 1000).toFixed(1)}s`);
    }

    if (result.webPages && result.webPages.length > 0) {
      console.log(`\n--- Sample Web Page Content ---`);
      const sample = result.webPages[0];
      console.log(`URL: ${sample.url}`);
      console.log(`Markdown length: ${sample.markdown.length} chars`);
      console.log(`Preview (first 500 chars):`);
      console.log(sample.markdown.substring(0, 500));
      console.log("...");
    }

    if (result.searchResults && result.searchResults.length > 0) {
      console.log(`\n--- Sample Search Results (first 5) ---`);
      for (const sr of result.searchResults.slice(0, 5)) {
        console.log(`\n  Title: ${sr.title}`);
        console.log(`  URL: ${sr.url}`);
        console.log(`  Snippet: ${sr.snippet.substring(0, 100)}...`);
      }
    }
  } else {
    console.log(`\nFailed: ${result.error}`);
    process.exit(1);
  }

  console.log("\n" + "=".repeat(60));
  console.log("Test Complete");
  console.log("=".repeat(60));
}

main().catch(error => {
  console.error("Fatal error:", error);
  process.exit(1);
});
