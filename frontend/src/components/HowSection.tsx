// src/components/HowSection.tsx
"use client";

import React from 'react';
import ScrollReveal from './ScrollReveal';

export default function HowSection(): React.ReactElement {
  return (
    <section id="how" className="min-h-screen flex items-center justify-center px-4 py-20">
      <div className="max-w-6xl mx-auto">
        <ScrollReveal variant="fade-up" duration={700}>
          <h2 className="section-title mb-6">
            How It Works
          </h2>
        </ScrollReveal>
        
        <ScrollReveal variant="fade-up" delay={150} duration={700}>
          <p className="text-center text-gray-300 text-lg mb-16 max-w-3xl mx-auto leading-relaxed">
            Our AI-powered platform analyzes YouTube comments using advanced multilingual sentiment analysis 
            to help you understand audience reactions and feedback at scale.
          </p>
        </ScrollReveal>

        {/* 3 Process Cards with Staggered Scroll Animations */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-16">
          <ScrollReveal variant="scale-up" delay={200} duration={650}>
            <div className="chart-container text-center h-full">
              <div className="text-5xl mb-6 transition-transform duration-300 hover:scale-110">📝</div>
              <h3 className="text-xl font-semibold text-white mb-4">
                1. Input YouTube URL
              </h3>
              <p className="text-gray-300 leading-relaxed text-sm">
                Simply paste your YouTube video URL and we&apos;ll automatically fetch public comments 
                for analysis using the YouTube Data API.
              </p>
            </div>
          </ScrollReveal>
          
          <ScrollReveal variant="scale-up" delay={350} duration={650}>
            <div className="chart-container text-center h-full">
              <div className="text-5xl mb-6 transition-transform duration-300 hover:scale-110">🤖</div>
              <h3 className="text-xl font-semibold text-white mb-4">
                2. AI Sentiment Engine
              </h3>
              <p className="text-gray-300 leading-relaxed text-sm">
                Powered by Google Gemini 3.5 Flash-Lite, our AI engine analyzes comments in batches 
                with high multilingual accuracy across Indonesian, English, and local slang.
              </p>
            </div>
          </ScrollReveal>
          
          <ScrollReveal variant="scale-up" delay={500} duration={650}>
            <div className="chart-container text-center h-full">
              <div className="text-5xl mb-6 transition-transform duration-300 hover:scale-110">📊</div>
              <h3 className="text-xl font-semibold text-white mb-4">
                3. Interactive Visuals
              </h3>
              <p className="text-gray-300 leading-relaxed text-sm">
                Explore interactive Donut Charts, Word Clouds, categorized sample feedback, 
                and downloadable CSV reports.
              </p>
            </div>
          </ScrollReveal>
        </div>

        {/* Feature Badges with Scroll Animation */}
        <ScrollReveal variant="blur-in" delay={600} duration={800}>
          <div className="text-center">
            <div className="inline-flex flex-wrap items-center justify-center gap-6 text-sm text-gray-300 bg-white/5 border border-white/10 px-8 py-3 rounded-full backdrop-blur-md">
              <div className="flex items-center space-x-2">
                <div className="w-2.5 h-2.5 bg-green-400 rounded-full animate-pulse"></div>
                <span className="font-medium">Gemini 3.5 Flash-Lite</span>
              </div>
              <div className="flex items-center space-x-2">
                <div className="w-2.5 h-2.5 bg-blue-400 rounded-full animate-pulse"></div>
                <span className="font-medium">Multilingual &amp; Slang Support</span>
              </div>
              <div className="flex items-center space-x-2">
                <div className="w-2.5 h-2.5 bg-purple-400 rounded-full animate-pulse"></div>
                <span className="font-medium">Real-time SSE Streaming</span>
              </div>
            </div>
          </div>
        </ScrollReveal>
      </div>
    </section>
  );
}
