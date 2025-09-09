import Link from 'next/link';

const buyMeACoffeeLink = process.env.BUY_ME_A_COFFEE_LINK;
const githubSponsorsLink = process.env.GITHUB_SPONSORS_LINK;

export default function SupportPage() {
  return (
    <main className="min-h-screen p-8">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold text-gray-500 mb-4">💝 Support LLM Colosseum</h1>
          <p className="text-xl text-gray-300 max-w-2xl mx-auto">
            Help us grow the most comprehensive AI intelligence testing platform. 
            Your support helps cover LLM API costs and keeps the platform running 24/7.
          </p>
        </div>

        {/* Impact Stats */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">
          <div className="bg-gradient-to-br from-blue-50 to-indigo-50 p-6 rounded-xl text-center">
            <div className="text-3xl font-bold text-blue-600 mb-2">100+</div>
            <div className="text-gray-700">Matches Completed</div>
          </div>
          <div className="bg-gradient-to-br from-green-50 to-emerald-50 p-6 rounded-xl text-center">
            <div className="text-3xl font-bold text-green-600 mb-2">24/7</div>
            <div className="text-gray-700">Platform Uptime</div>
          </div>
          <div className="bg-gradient-to-br from-purple-50 to-pink-50 p-6 rounded-xl text-center">
            <div className="text-3xl font-bold text-purple-600 mb-2">Open</div>
            <div className="text-gray-700">Source & Free</div>
          </div>
        </div>

        {/* Support Options */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-12">
          {/* GitHub Sponsors - Primary */}
          <div className="bg-white border-2 border-gray-900 rounded-xl p-8 shadow-lg relative">
            <div className="absolute -top-3 left-6 bg-gray-900 text-white px-3 py-1 rounded-full text-sm font-medium">
              Recommended
            </div>
            
            <div className="flex items-center mb-6">
              <svg className="w-8 h-8 mr-3" fill="currentColor" viewBox="0 0 24 24">
                <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/>
              </svg>
              <div>
                <h3 className="text-xl font-semibold text-gray-900">GitHub Sponsors</h3>
                <p className="text-gray-600 text-sm">Professional sponsorship platform</p>
              </div>
            </div>

            <div className="mb-6">
              <p className="text-gray-700 text-sm">
                Support the project through GitHub's official sponsorship platform. Perfect for recurring support and business sponsorships.
              </p>
            </div>

            <a
              href={githubSponsorsLink}
              target="_blank"
              rel="noopener noreferrer"
              className="block w-full bg-gray-900 hover:bg-gray-700 text-white text-center py-3 px-6 rounded-lg transition-colors font-medium"
            >
              💖 Sponsor on GitHub
            </a>
          </div>

          {/* Buy Me a Coffee - Secondary */}
          <div className="bg-gradient-to-br from-yellow-50 to-orange-50 border border-orange-200 rounded-xl p-8">
            <div className="flex items-center mb-6">
              <div className="w-8 h-8 mr-3 bg-yellow-500 rounded-full flex items-center justify-center">
                ☕
              </div>
              <div>
                <h3 className="text-xl font-semibold text-gray-900">Buy Me a Coffee</h3>
                <p className="text-gray-600 text-sm">Quick & easy one-time support</p>
              </div>
            </div>

            <div className="mb-6">
              <p className="text-gray-700 text-sm">
                Show your appreciation with a quick one-time donation. No account required and supports multiple payment methods.
              </p>
            </div>

            <a
              href={buyMeACoffeeLink}
              target="_blank"
              rel="noopener noreferrer"
              className="block w-full bg-yellow-500 hover:bg-yellow-600 text-white text-center py-3 px-6 rounded-lg transition-colors font-medium"
            >
              ☕ Buy Me a Coffee
            </a>
          </div>
        </div>

        {/* How Funds Are Used */}
        <div className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-xl p-8 mb-12">
          <h2 className="text-2xl font-semibold text-gray-900 mb-6 text-center">🚀 How Your Support Helps</h2>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            <div>
              <h3 className="text-lg font-medium text-gray-900 mb-4">🎯 Current Focus</h3>
              <div className="space-y-2">
                <div className="flex items-center text-gray-700">
                  <svg className="w-4 h-4 mr-2 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                  <span className="text-sm">Keep the platform running 24/7</span>
                </div>
                <div className="flex items-center text-gray-700">
                  <svg className="w-4 h-4 mr-2 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                  <span className="text-sm">Support multiple LLM models</span>
                </div>
                <div className="flex items-center text-gray-700">
                  <svg className="w-4 h-4 mr-2 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                  <span className="text-sm">Maintain database and infrastructure</span>
                </div>
              </div>
            </div>

            <div>
              <h3 className="text-lg font-medium text-gray-900 mb-4">🚀 Future Plans</h3>
              <div className="space-y-2">
                <div className="flex items-center text-gray-700">
                  <svg className="w-4 h-4 mr-2 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                  <span className="text-sm">More LLM models (Claude Opus, etc.)</span>
                </div>
                <div className="flex items-center text-gray-700">
                  <svg className="w-4 h-4 mr-2 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                  <span className="text-sm">Advanced analytics & insights</span>
                </div>
                <div className="flex items-center text-gray-700">
                  <svg className="w-4 h-4 mr-2 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                  <span className="text-sm">Tournament system and leaderboard</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Other Ways to Help */}
        <div className="bg-white border border-gray-200 rounded-xl p-8 mb-12">
          <h2 className="text-2xl font-semibold text-gray-900 mb-6 text-center">🤝 Other Ways to Help</h2>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="text-center">
              <div className="w-12 h-12 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-3">
                🎯
              </div>
              <h3 className="font-medium text-gray-900 mb-2">Contribute Challenges</h3>
              <p className="text-sm text-gray-600">Create interesting challenges for our models to solve</p>
            </div>
            
            <div className="text-center">
              <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-3">
                ⭐
              </div>
              <h3 className="font-medium text-gray-900 mb-2">Star on GitHub</h3>
              <p className="text-sm text-gray-600">Help us gain visibility in the developer community</p>
            </div>
            
            <div className="text-center">
              <div className="w-12 h-12 bg-purple-100 rounded-full flex items-center justify-center mx-auto mb-3">
                📢
              </div>
              <h3 className="font-medium text-gray-900 mb-2">Spread the Word</h3>
              <p className="text-sm text-gray-600">Share LLM Colosseum with researchers and AI enthusiasts</p>
            </div>
          </div>
        </div>

        {/* Thank You */}
        <div className="text-center">
          <h2 className="text-2xl font-semibold text-gray-500 mb-4">🙏 Thank You!</h2>
          <p className="text-gray-300 max-w-2xl mx-auto">
            Every contribution, no matter the size, helps us build the most comprehensive 
            AI intelligence testing platform. Together, we're advancing AI research and 
            making it accessible to everyone.
          </p>
        </div>
      </div>
    </main>
  );
} 