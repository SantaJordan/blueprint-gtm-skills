#!/usr/bin/env node

/**
 * Installer for Blueprint Worker LaunchAgent
 *
 * This script installs the worker as a macOS LaunchAgent so it runs
 * automatically on system startup.
 */

import { execSync } from 'child_process';
import { existsSync, mkdirSync, copyFileSync } from 'fs';
import { homedir } from 'os';
import { join } from 'path';

const HOME = homedir();
const LAUNCH_AGENTS_DIR = join(HOME, 'Library', 'LaunchAgents');
const PLIST_NAME = 'com.blueprint.worker.plist';
const SOURCE_PLIST = join(process.cwd(), PLIST_NAME);
const TARGET_PLIST = join(LAUNCH_AGENTS_DIR, PLIST_NAME);
const LOGS_DIR = join(process.cwd(), '..', 'logs');

console.log('Blueprint Worker LaunchAgent Installer\n');

// Step 1: Create logs directory if it doesn't exist
if (!existsSync(LOGS_DIR)) {
  console.log('Creating logs directory...');
  mkdirSync(LOGS_DIR, { recursive: true });
  console.log('✓ Logs directory created');
} else {
  console.log('✓ Logs directory already exists');
}

// Step 2: Ensure LaunchAgents directory exists
if (!existsSync(LAUNCH_AGENTS_DIR)) {
  console.log('Creating LaunchAgents directory...');
  mkdirSync(LAUNCH_AGENTS_DIR, { recursive: true });
  console.log('✓ LaunchAgents directory created');
} else {
  console.log('✓ LaunchAgents directory exists');
}

// Step 3: Unload existing service if it exists
if (existsSync(TARGET_PLIST)) {
  console.log('Unloading existing LaunchAgent...');
  try {
    execSync(`launchctl unload ${TARGET_PLIST}`, { stdio: 'inherit' });
    console.log('✓ Existing LaunchAgent unloaded');
  } catch (error) {
    console.log('⚠ No existing LaunchAgent was running');
  }
}

// Step 4: Copy plist file to LaunchAgents directory
console.log('Installing LaunchAgent plist...');
copyFileSync(SOURCE_PLIST, TARGET_PLIST);
console.log('✓ Plist file copied to', TARGET_PLIST);

// Step 5: Load the new LaunchAgent
console.log('Loading LaunchAgent...');
try {
  execSync(`launchctl load ${TARGET_PLIST}`, { stdio: 'inherit' });
  console.log('✓ LaunchAgent loaded successfully');
} catch (error) {
  console.error('✗ Failed to load LaunchAgent:', error.message);
  process.exit(1);
}

// Step 6: Verify the service is running
console.log('\nVerifying service status...');
try {
  execSync(`launchctl list | grep com.blueprint.worker`, { stdio: 'inherit' });
  console.log('✓ Service is running');
} catch (error) {
  console.error('✗ Service is not running');
  process.exit(1);
}

console.log('\n✅ Installation complete!');
console.log('\nThe Blueprint Worker will now:');
console.log('  • Start automatically when you log in');
console.log('  • Run continuously in the background');
console.log('  • Poll Supabase every 30 seconds for new jobs');
console.log('  • Execute /blueprint-turbo when jobs are found');
console.log('\nLogs location:');
console.log('  • Output:', join(LOGS_DIR, 'blueprint-worker.log'));
console.log('  • Errors:', join(LOGS_DIR, 'blueprint-worker-error.log'));
console.log('\nTo stop the service:');
console.log(`  launchctl unload ${TARGET_PLIST}`);
console.log('\nTo start the service again:');
console.log(`  launchctl load ${TARGET_PLIST}`);
console.log('\nTo view logs:');
console.log(`  tail -f ${join(LOGS_DIR, 'blueprint-worker.log')}`);
