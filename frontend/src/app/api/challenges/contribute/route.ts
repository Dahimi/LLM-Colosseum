import { NextRequest, NextResponse } from 'next/server';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL;
const API_KEY = process.env.NEXT_PUBLIC_API_KEY;

export async function POST(request: NextRequest) {
  try {
    const challengeData = await request.json();
    
    // Forward the request to the backend
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    };
    
    if (API_KEY) {
      headers['X-API-Key'] = API_KEY;
    }

    const response = await fetch(`${API_BASE_URL}/challenges/contribute`, {
      method: 'POST',
      headers,
      body: JSON.stringify(challengeData),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      return NextResponse.json(
        { 
          error: 'Failed to submit challenge',
          detail: errorData.detail || errorData.message || 'Unknown error'
        },
        { status: response.status }
      );
    }

    const result = await response.json();
    return NextResponse.json(result);

  } catch (error) {
    console.error('Error in challenge contribution API:', error);
    return NextResponse.json(
      { 
        error: 'Internal server error',
        detail: error instanceof Error ? error.message : 'Unknown error'
      },
      { status: 500 }
    );
  }
} 