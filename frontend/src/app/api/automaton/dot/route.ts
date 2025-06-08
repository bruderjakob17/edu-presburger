// /app/api/automaton/route.ts (example)
import { NextResponse } from 'next/server';

export async function POST(request: Request) {
  try {
    // 1️⃣  Parse the incoming JSON only once
    const { formula, variable_order = [], k_solutions = 3 } = await request.json();

    // 2️⃣  Forward all fields including k_solutions
    const backendRes = await fetch('https://thesis-hhd5.onrender.com/automaton/dot', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ formula, variable_order, k_solutions }),
    });

    if (!backendRes.ok) {
      const errorText = await backendRes.text();
      return new NextResponse(errorText, {
        status: backendRes.status,
        headers: { 'Content-Type': 'text/plain' },
      });
    }

    const data = await backendRes.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error('API route error:', error);
    return new NextResponse('Failed to fetch from backend', { status: 500 });
  }
}