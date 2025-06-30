// /app/api/automaton/route.ts (example)
import { NextResponse } from 'next/server';

export async function POST(request: Request) {
  try {
    // 1️⃣  Parse the incoming JSON only once
    const { formula } = await request.json();
    // https://thesis-hhd5.onrender.com/automaton/dot
    const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL;
    // 2️⃣  Forward only the formula
    const backendRes = await fetch(`${BACKEND_URL}/automaton/dot`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ formula }),
    });

    if (!backendRes.ok) {
      const errorText = await backendRes.text();
      return new NextResponse(errorText, {
        status: backendRes.status,
        headers: { 'Content-Type': 'text/plain' },
      });
    }

    const data = await backendRes.json();
    // Return all fields from the backend response
    return NextResponse.json({
      dot: data.dot,
      variables: data.variables,
      example_solutions: data.example_solutions,
      mata: data.mata,
      num_states: data.num_states,
      num_final_states: data.num_final_states
    });
  } catch (error) {
    console.error('API route error:', error);
    return new NextResponse('Failed to fetch from presburger_converter', { status: 500 });
  }
}