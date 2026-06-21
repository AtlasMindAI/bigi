import { NextRequest, NextResponse } from 'next/server';
import { exec } from 'child_process';
import { promisify } from 'util';
import fs from 'fs';
import path from 'path';
import os from 'os';

const execAsync = promisify(exec);

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ owner: string; repo: string }> }
) {
  const resolvedParams = await params;
  const { owner, repo } = resolvedParams;
  const repoUrl = `https://github.com/${owner}/${repo}`;
  
  // Create a unique temporary file for the HTML output
  const tempDir = os.tmpdir();
  const htmlOutput = path.join(tempDir, `bigi_${owner}_${repo}_${Date.now()}.html`);
  
  try {
    // We assume the environment running this Next app has `bigi` CLI installed.
    const cmd = `bigi analyze ${repoUrl} --html ${htmlOutput}`;
    console.log(`Running: ${cmd}`);
    
    // Allow up to 120 seconds for cloning and analyzing large repos
    await execAsync(cmd, { timeout: 120000 });
    
    // Read the generated HTML
    const htmlContent = fs.readFileSync(htmlOutput, 'utf-8');
    
    // Clean up
    fs.unlinkSync(htmlOutput);
    
    // Return HTML response
    return new NextResponse(htmlContent, {
      headers: {
        'Content-Type': 'text/html; charset=utf-8',
      },
    });
  } catch (error: any) {
    console.error('Error generating graph:', error);
    
    // Clean up if it exists
    if (fs.existsSync(htmlOutput)) {
      fs.unlinkSync(htmlOutput);
    }

    return new NextResponse(
      `<html><body style="font-family:sans-serif;padding:2rem;">
        <h1>Error analyzing repository</h1>
        <p>Could not analyze <strong>${repoUrl}</strong>. Ensure it is a public repository.</p>
        <pre style="background:#eee;padding:1rem;overflow-x:auto;">${error.message || error}</pre>
      </body></html>`,
      {
        status: 500,
        headers: { 'Content-Type': 'text/html; charset=utf-8' },
      }
    );
  }
}
