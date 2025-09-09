'use client';

import { useState } from 'react';
import { Division } from '@/types/arena';

interface ChallengeContributionFormProps {
  onChallengeSubmit?: (challengeData: any) => void;
}

export function ChallengeContributionForm({ onChallengeSubmit }: ChallengeContributionFormProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    type: 'LOGICAL_REASONING',
    difficulty: 'INTERMEDIATE',
    division: Division.EXPERT,
    answer: '',
    tags: '',
    contributorName: '',
    contributorEmail: ''
  });
  
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const challengeTypes = [
    { value: 'LOGICAL_REASONING', label: 'Logical Reasoning' },
    { value: 'DEBATE', label: 'Debate Topic' },
    { value: 'CREATIVE_PROBLEM_SOLVING', label: 'Creative Problem Solving' },
    { value: 'MATHEMATICAL', label: 'Mathematical' },
    { value: 'ABSTRACT_THINKING', label: 'Abstract Thinking' }
  ];

  const difficulties = [
    { value: 'BEGINNER', label: 'Beginner (1)' },
    { value: 'INTERMEDIATE', label: 'Intermediate (2)' },
    { value: 'ADVANCED', label: 'Advanced (3)' },
    { value: 'EXPERT', label: 'Expert (4)' },
    { value: 'MASTER', label: 'Master (5)' }
  ];

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    setError(null);
    setSuccessMessage(null);

    try {
      // Prepare challenge data
      const challengeData = {
        ...formData,
        tags: formData.tags.split(',').map(tag => tag.trim()).filter(tag => tag.length > 0),
        source: 'community',
        metadata: {
          contributor_name: formData.contributorName,
          contributor_email: formData.contributorEmail,
          created_at: new Date().toISOString()
        }
      };

      // Submit challenge and start test match
      const response = await fetch('/api/challenges/contribute', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(challengeData),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || errorData.message || 'Failed to submit challenge');
      }

      const result = await response.json();
      
      setSuccessMessage(`Challenge "${formData.title}" submitted successfully! Test match started: ${result.match_id}`);
      onChallengeSubmit?.(result);
      
      // Reset form
      setFormData({
        title: '',
        description: '',
        type: 'LOGICAL_REASONING',
        difficulty: 'INTERMEDIATE',
        division: Division.EXPERT,
        answer: '',
        tags: '',
        contributorName: '',
        contributorEmail: ''
      });

    } catch (e) {
      console.error('Error submitting challenge:', e);
      setError(e instanceof Error ? e.message : 'Failed to submit challenge');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="bg-white border border-gray-200 rounded-lg shadow-sm">
      {/* Collapsible Header */}
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full p-6 text-left hover:bg-gray-50 transition-colors rounded-lg"
      >
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-xl font-semibold text-gray-900 mb-2 flex items-center">
              🎯 Create & Test Your Challenge
              <span className="ml-2 text-sm bg-gray-100 text-gray-700 px-2 py-1 rounded-full font-medium">
                Fun!
              </span>
            </h3>
            <p className="text-gray-600 text-sm font-medium">
              Design your own challenge and watch models battle it out instantly! Your challenge joins our permanent collection.
            </p>
          </div>
          <div className="flex-shrink-0 ml-4">
            <svg 
              className={`w-6 h-6 text-gray-500 transform transition-transform ${isExpanded ? 'rotate-180' : ''}`} 
              fill="none" 
              stroke="currentColor" 
              viewBox="0 0 24 24"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </div>
        </div>
      </button>

      {/* Expandable Form */}
      {isExpanded && (
        <div className="px-6 pb-6">
          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Contributor Info */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 p-4 bg-gray-50 rounded-lg">
              <div>
                <label htmlFor="contributorName" className="block text-sm font-medium text-gray-700 mb-1">
                  Your Name (optional)
                </label>
                <input
                  type="text"
                  id="contributorName"
                  name="contributorName"
                  value={formData.contributorName}
                  onChange={handleInputChange}
                  className="block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm text-gray-900"
                  placeholder="How should we credit you?"
                />
              </div>
              <div>
                <label htmlFor="contributorEmail" className="block text-sm font-medium text-gray-700 mb-1">
                  Email (optional)
                </label>
                <input
                  type="email"
                  id="contributorEmail"
                  name="contributorEmail"
                  value={formData.contributorEmail}
                  onChange={handleInputChange}
                  className="block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm text-gray-900"
                  placeholder="For updates about your challenge"
                />
              </div>
            </div>

            {/* Challenge Details */}
            <div>
              <label htmlFor="title" className="block text-sm font-medium text-gray-700 mb-1">
                Challenge Title *
              </label>
              <input
                type="text"
                id="title"
                name="title"
                value={formData.title}
                onChange={handleInputChange}
                required
                className="block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm text-gray-900"
                placeholder="Give your challenge a descriptive title"
              />
            </div>

            <div>
              <label htmlFor="description" className="block text-sm font-medium text-gray-700 mb-1">
                Challenge Description *
              </label>
              <textarea
                id="description"
                name="description"
                value={formData.description}
                onChange={handleInputChange}
                required
                rows={6}
                className="block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm text-gray-900"
                placeholder="Describe the challenge in detail. You can use Markdown and LaTeX formatting!"
              />
              <p className="text-xs text-gray-600 mt-1">
                💡 Tip: Use **bold**, *italic*, `code`, and $$LaTeX$$ for rich formatting
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label htmlFor="type" className="block text-sm font-medium text-gray-700 mb-1">
                  Challenge Type *
                </label>
                <select
                  id="type"
                  name="type"
                  value={formData.type}
                  onChange={handleInputChange}
                  required
                  className="block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm text-gray-900"
                >
                  {challengeTypes.map(type => (
                    <option key={type.value} value={type.value}>
                      {type.label}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label htmlFor="difficulty" className="block text-sm font-medium text-gray-700 mb-1">
                  Difficulty *
                </label>
                <select
                  id="difficulty"
                  name="difficulty"
                  value={formData.difficulty}
                  onChange={handleInputChange}
                  required
                  className="block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm text-gray-900"
                >
                  {difficulties.map(diff => (
                    <option key={diff.value} value={diff.value}>
                      {diff.label}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label htmlFor="division" className="block text-sm font-medium text-gray-700 mb-1">
                  Test Division *
                </label>
                <select
                  id="division"
                  name="division"
                  value={formData.division}
                  onChange={handleInputChange}
                  required
                  className="block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm text-gray-900"
                >
                  {Object.values(Division).filter(division => division !== Division.KING).map(division => (
                    <option key={division} value={division}>
                      {division.charAt(0).toUpperCase() + division.slice(1)}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            <div>
              <label htmlFor="answer" className="block text-sm font-medium text-gray-700 mb-1">
                Expected Answer/Solution (optional)
              </label>
              <textarea
                id="answer"
                name="answer"
                value={formData.answer}
                onChange={handleInputChange}
                rows={3}
                className="block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm text-gray-900"
                placeholder="What would be a good answer to this challenge?"
              />
            </div>

            <div>
              <label htmlFor="tags" className="block text-sm font-medium text-gray-700 mb-1">
                Tags (optional)
              </label>
              <input
                type="text"
                id="tags"
                name="tags"
                value={formData.tags}
                onChange={handleInputChange}
                className="block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm text-gray-900"
                placeholder="logic, math, reasoning (comma-separated)"
              />
            </div>

            {/* Submit Button */}
            <div className="flex flex-col gap-3">
              <button
                type="submit"
                disabled={isSubmitting}
                className="w-full bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed font-medium shadow-sm"
              >
                {isSubmitting ? (
                  <div className="flex items-center justify-center space-x-2">
                    <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                    <span>Creating Challenge & Starting Test Match...</span>
                  </div>
                ) : (
                  '🚀 Submit Challenge & Start Test Match'
                )}
              </button>

              {error && (
                <div className="bg-red-50 border border-red-200 rounded-md p-3">
                  <div className="flex items-start">
                    <div className="flex-shrink-0">
                      <svg className="h-5 w-5 text-red-400 mt-0.5" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                        <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.28 7.22a.75.75 0 00-1.06 1.06L8.94 10l-1.72 1.72a.75.75 0 101.06 1.06L10 11.06l1.72 1.72a.75.75 0 101.06-1.06L11.06 10l1.72-1.72a.75.75 0 00-1.06-1.06L10 8.94 8.28 7.22z" clipRule="evenodd" />
                      </svg>
                    </div>
                    <div className="ml-3">
                      <p className="text-sm text-red-800 font-medium">{error}</p>
                    </div>
                  </div>
                </div>
              )}

              {successMessage && (
                <div className="bg-green-50 border border-green-200 rounded-md p-3">
                  <div className="flex items-start">
                    <div className="flex-shrink-0">
                      <svg className="h-5 w-5 text-green-400 mt-0.5" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                        <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.857-9.809a.75.75 0 00-1.214-.882l-3.236 4.53L7.53 10.53a.75.75 0 00-1.06 1.061l2.5 2.5a.75.75 0 001.137-.089l4-5.5z" clipRule="evenodd" />
                      </svg>
                    </div>
                    <div className="ml-3">
                      <p className="text-sm text-green-800 font-medium">{successMessage}</p>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </form>
        </div>
      )}
    </div>
  );
} 