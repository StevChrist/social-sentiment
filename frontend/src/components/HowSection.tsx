// src/components/HowSection.tsx
"use client";

export default function HowSection() {
  return (
    <section id="how" className="min-h-screen flex items-center justify-center px-4 py-20">
      <div className="max-w-6xl mx-auto">
        <h2 className="section-title mb-8">
          How It Works
        </h2>
        
        <p className="text-center text-gray-300 text-lg mb-16 max-w-3xl mx-auto">
          Our AI-powered platform analyzes YouTube comments using advanced multilingual sentiment analysis 
          to help you understand audience reactions and feedback at scale.
        </p>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-16">
          <div className="chart-container text-center">
            <div className="text-5xl mb-6">📝</div>
            <h3 className="text-xl font-semibold text-white mb-4">
              Input YouTube URL
            </h3>
            <p className="text-gray-300 leading-relaxed">
              Simply paste your YouTube video URL and we&apos;ll automatically fetch all public comments 
              for analysis using the YouTube Data API.
            </p>
          </div>
          
          <div className="chart-container text-center">
            <div className="text-5xl mb-6">🤖</div>
            <h3 className="text-xl font-semibold text-white mb-4">
              AI Analysis
            </h3>
            <p className="text-gray-300 leading-relaxed">
              Our fine-tuned XLM-RoBERTa model analyzes each comment to determine sentiment 
              with high accuracy across multiple languages including Indonesian and English.
            </p>
          </div>
          
          <div className="chart-container text-center">
            <div className="text-5xl mb-6">📊</div>
            <h3 className="text-xl font-semibold text-white mb-4">
              Visual Results
            </h3>
            <p className="text-gray-300 leading-relaxed">
              Get beautiful charts, word clouds, and detailed sentiment statistics 
              with interactive visualizations and downloadable reports.
            </p>
          </div>
        </div>

        <div className="text-center">
          <div className="inline-flex items-center space-x-8 text-sm text-gray-400">
            <div className="flex items-center space-x-2">
              <div className="w-2 h-2 bg-green-400 rounded-full"></div>
              <span>83.2% Accuracy</span>
            </div>
            <div className="flex items-center space-x-2">
              <div className="w-2 h-2 bg-blue-400 rounded-full"></div>
              <span>Multilingual Support</span>
            </div>
            <div className="flex items-center space-x-2">
              <div className="w-2 h-2 bg-purple-400 rounded-full"></div>
              <span>Real-time Processing</span>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
