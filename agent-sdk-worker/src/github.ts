/**
 * GitHub Publishing Integration
 * Fallback for publishing playbooks when git operations fail
 */

import { Octokit } from "@octokit/rest";
import { getConfig } from "./config.js";

let octokitInstance: Octokit | null = null;

function getOctokit(): Octokit {
  if (!octokitInstance) {
    const config = getConfig();
    octokitInstance = new Octokit({ auth: config.githubToken });
  }
  return octokitInstance;
}

/**
 * Publish an HTML playbook to GitHub Pages
 * This is a fallback method when the skill's native git push fails
 */
export async function publishPlaybook(
  htmlContent: string,
  filename: string
): Promise<string> {
  const config = getConfig();
  const octokit = getOctokit();

  console.log(`[GitHub] Publishing ${filename} to ${config.githubOwner}/${config.githubRepo}`);

  // Check if file already exists (to get SHA for update)
  let existingSha: string | undefined;
  try {
    const { data } = await octokit.repos.getContent({
      owner: config.githubOwner,
      repo: config.githubRepo,
      path: filename,
    });

    if (!Array.isArray(data) && "sha" in data) {
      existingSha = data.sha;
      console.log(`[GitHub] File exists, will update (SHA: ${existingSha})`);
    }
  } catch (error: unknown) {
    if ((error as { status?: number }).status !== 404) {
      throw error;
    }
    console.log(`[GitHub] File does not exist, will create`);
  }

  // Create or update file
  const { data } = await octokit.repos.createOrUpdateFileContents({
    owner: config.githubOwner,
    repo: config.githubRepo,
    path: filename,
    message: `Publish playbook: ${filename}`,
    content: Buffer.from(htmlContent).toString("base64"),
    sha: existingSha,
  });

  console.log(`[GitHub] File committed: ${data.commit.sha}`);

  // Construct GitHub Pages URL
  const playbookUrl = `https://${config.githubOwner.toLowerCase()}.github.io/${config.githubRepo}/${filename}`;
  console.log(`[GitHub] Playbook URL: ${playbookUrl}`);

  return playbookUrl;
}

/**
 * Ensure .nojekyll file exists for faster GitHub Pages builds
 */
export async function ensureNoJekyll(): Promise<void> {
  const config = getConfig();
  const octokit = getOctokit();

  try {
    await octokit.repos.getContent({
      owner: config.githubOwner,
      repo: config.githubRepo,
      path: ".nojekyll",
    });
    console.log(`[GitHub] .nojekyll already exists`);
  } catch (error: unknown) {
    if ((error as { status?: number }).status === 404) {
      // Create .nojekyll file
      await octokit.repos.createOrUpdateFileContents({
        owner: config.githubOwner,
        repo: config.githubRepo,
        path: ".nojekyll",
        message: "Add .nojekyll to disable Jekyll processing",
        content: Buffer.from("").toString("base64"),
      });
      console.log(`[GitHub] Created .nojekyll file`);
    } else {
      throw error;
    }
  }
}

/**
 * List recent playbooks in the repository
 */
export async function listPlaybooks(limit: number = 10): Promise<string[]> {
  const config = getConfig();
  const octokit = getOctokit();

  const { data } = await octokit.repos.getContent({
    owner: config.githubOwner,
    repo: config.githubRepo,
    path: "",
  });

  if (!Array.isArray(data)) {
    return [];
  }

  const playbooks = data
    .filter((file) => file.name.startsWith("blueprint-gtm-playbook-") && file.name.endsWith(".html"))
    .map((file) => file.name)
    .slice(0, limit);

  return playbooks;
}
