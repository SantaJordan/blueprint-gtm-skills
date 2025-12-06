import { createClient } from '@supabase/supabase-js';

// Initialize Supabase client
const supabase = createClient(
  process.env.SUPABASE_URL,
  process.env.SUPABASE_ANON_KEY
);

export default async function handler(req, res) {
  // Enable CORS for requests from iOS Shortcuts
  res.setHeader('Access-Control-Allow-Credentials', 'true');
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET,OPTIONS,POST');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  // Handle preflight OPTIONS request
  if (req.method === 'OPTIONS') {
    res.status(200).end();
    return;
  }

  // Only allow POST requests
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    const { companyUrl } = req.body;

    // Validate company URL
    if (!companyUrl || typeof companyUrl !== 'string') {
      return res.status(400).json({ error: 'companyUrl is required and must be a string' });
    }

    // Basic URL validation
    try {
      new URL(companyUrl);
    } catch (e) {
      return res.status(400).json({ error: 'Invalid URL format' });
    }

    // Insert job into Supabase queue
    const { data, error } = await supabase
      .from('blueprint_jobs')
      .insert([{
        company_url: companyUrl,
        status: 'pending'
      }])
      .select()
      .single();

    if (error) {
      console.error('Supabase error:', error);
      return res.status(500).json({ error: 'Failed to queue job', details: error.message });
    }

    // Generate domain slug for clean URL
    const domainSlug = companyUrl
      .replace(/^https?:\/\//, '')
      .replace(/^www\./, '')
      .split('/')[0]
      .replace(/\./g, '-');

    // Return success response with job details and clean URL
    return res.status(200).json({
      success: true,
      job: {
        id: data.id,
        companyUrl: data.company_url,
        status: data.status,
        createdAt: data.created_at
      },
      statusUrl: `/${domainSlug}`,
      message: 'Job queued successfully! Redirecting to status page...'
    });

  } catch (error) {
    console.error('Unexpected error:', error);
    return res.status(500).json({ error: 'Internal server error', details: error.message });
  }
}
