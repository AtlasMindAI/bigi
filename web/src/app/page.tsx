"use client";
import React, { useState } from 'react';
import { useRouter } from 'next/navigation';

export default function Home() {
  const [repoUrl, setRepoUrl] = useState('');
  const router = useRouter();

  const handleAnalyze = (e: React.FormEvent) => {
    e.preventDefault();
    if (!repoUrl) return;

    // Extract owner and repo from URL
    // e.g. https://github.com/BDB-Genomics/BiGI -> owner=BDB-Genomics, repo=BiGI
    let url = repoUrl.trim();
    if (url.includes('github.com')) {
      const parts = url.split('github.com/')[1].split('/');
      if (parts.length >= 2) {
        router.push(`/${parts[0]}/${parts[1]}`);
        return;
      }
    }
    
    // Fallback: assume the user just typed "owner/repo"
    if (url.includes('/')) {
      router.push(`/${url}`);
    } else {
      alert("Please enter a valid GitHub URL or owner/repo format.");
    }
  };

  return (
    <main className="min-h-screen bg-[#0a0a0f] text-white flex flex-col items-center justify-center p-8 relative overflow-hidden">
      {/* Abstract Background Gradients */}
      <div className="absolute top-[-20%] left-[-10%] w-[50%] h-[50%] bg-indigo-600/30 blur-[120px] rounded-full pointer-events-none" />
      <div className="absolute bottom-[-20%] right-[-10%] w-[50%] h-[50%] bg-emerald-600/20 blur-[120px] rounded-full pointer-events-none" />

      <div className="z-10 flex flex-col items-center text-center max-w-3xl">
        <h1 className="text-6xl md:text-8xl font-black tracking-tighter mb-4 bg-clip-text text-transparent bg-gradient-to-r from-indigo-400 via-purple-400 to-emerald-400 drop-shadow-sm">
          BiGIGitHub
        </h1>
        <p className="text-xl md:text-2xl text-gray-400 font-light mb-12 max-w-2xl leading-relaxed">
          Instantly generate interactive dependency graphs for any pipeline repository. <br/>
          Just prefix any GitHub URL with <strong className="text-white bg-white/10 px-2 py-1 rounded">bigi</strong>.
        </p>

        <form onSubmit={handleAnalyze} className="w-full relative group">
          <div className="absolute -inset-1 bg-gradient-to-r from-indigo-500 to-purple-600 rounded-2xl blur opacity-25 group-hover:opacity-50 transition duration-1000 group-hover:duration-200" />
          <div className="relative flex items-center bg-[#13131a] rounded-2xl p-2 shadow-2xl border border-white/10 ring-1 ring-black/5">
            <span className="pl-4 pr-2 text-gray-500 font-medium select-none hidden sm:block">
              bigigithub.com/
            </span>
            <input
              type="text"
              placeholder="BDB-Genomics/BiGI"
              value={repoUrl}
              onChange={(e) => setRepoUrl(e.target.value)}
              className="flex-1 bg-transparent border-none outline-none text-white px-2 py-4 text-lg font-mono placeholder-gray-600 focus:ring-0"
            />
            <button
              type="submit"
              className="ml-2 bg-gradient-to-r from-indigo-500 to-purple-600 hover:from-indigo-400 hover:to-purple-500 text-white font-semibold py-4 px-8 rounded-xl shadow-lg transform transition hover:scale-105 active:scale-95"
            >
              Analyze
            </button>
          </div>
        </form>

        <div className="mt-16 flex gap-6 text-sm text-gray-500 font-medium">
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
            No Setup Required
          </div>
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 rounded-full bg-indigo-400 animate-pulse delay-75" />
            Snakemake & Nextflow
          </div>
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 rounded-full bg-purple-400 animate-pulse delay-150" />
            Cross-Layer Analysis
          </div>
        </div>
      </div>
    </main>
  );
}
