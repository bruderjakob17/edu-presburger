import { NextResponse } from 'next/server';

export async function POST(request: Request) {
  try {
    const body = await request.text();
    const API_BASE_URL = "http://91.99.103.129:8000";
    const response = await fetch(`${API_BASE_URL}/automaton/pdf`, {
      method: 'POST',
      headers: {
        'Content-Type': 'text/plain',
      },
      body,
    });

    if (!response.ok) {
      const errorText = await response.text();
      return new NextResponse(errorText, { status: response.status });
    }

    const pdfBuffer = await response.arrayBuffer();

    return new NextResponse(pdfBuffer, {
      status: 200,
      headers: {
        'Content-Type': 'application/pdf',
        'Content-Disposition': 'inline; filename=automaton.pdf'
      },
    });
  } catch (error) {
    console.error('Error proxying to backend:', error);
    return new NextResponse(
      error instanceof Error ? error.message : 'An unexpected error occurred',
      { status: 500 }
    );
  }
} 