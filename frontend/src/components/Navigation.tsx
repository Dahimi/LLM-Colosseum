'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';

export function Navigation() {
  const pathname = usePathname();
  
  const isActive = (path: string) => {
    if (path === '/' && pathname === '/') return true;
    if (path !== '/' && pathname.startsWith(path)) return true;
    return false;
  };

  return (
    <nav className="bg-white border-b border-gray-300 shadow-sm sticky top-0 z-50">
      <div className="max-w-6xl mx-auto px-8">
        <div className="flex justify-between items-center h-16">
          {/* Logo */}
          <Link href="/" className="flex items-center gap-2 hover:opacity-80 transition-opacity">
            <span className="text-2xl font-bold text-gray-900">LLM Colosseum</span>
          </Link>
          
          {/* Navigation Links */}
          <div className="flex items-center gap-4">
            <Link 
              href="/"
              className={`px-4 py-2 rounded-lg transition-all duration-200 ${
                isActive('/') 
                  ? 'bg-blue-600 text-white shadow-sm' 
                  : 'text-gray-700 hover:text-blue-600 hover:bg-blue-50'
              }`}
            >
              👑 Kingdom
            </Link>
            <Link 
              href="/matches"
              className={`px-4 py-2 rounded-lg transition-all duration-200 flex items-center gap-1 ${
                isActive('/matches') 
                  ? 'bg-blue-600 text-white shadow-sm' 
                  : 'text-gray-700 hover:text-blue-600 hover:bg-blue-50'
              }`}
            >
              🎮 Playground
            </Link>
            <Link 
              href="/support"
              className={`px-3 py-2 rounded-lg transition-all duration-200 text-sm ${
                isActive('/support') 
                  ? 'bg-pink-600 text-white shadow-sm' 
                  : 'text-gray-700 hover:text-pink-600 hover:bg-pink-50'
              }`}
            >
              💝 Support
            </Link>
          </div>
        </div>
      </div>
    </nav>
  );
} 