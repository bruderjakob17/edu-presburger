import { NextResponse } from 'next/server';

export async function POST(request: Request) {
  try {
    const { aut, k_solutions, original_variable_order, new_variable_order } = await request.json();
    const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL;
    
    const backendRes = await fetch(`${BACKEND_URL}/automaton/update`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ aut, k_solutions, original_variable_order, new_variable_order }),
    });

    if (!backendRes.ok) {
      const errorText = await backendRes.text();
      return new NextResponse(errorText, {
        status: backendRes.status,
        headers: { 'Content-Type': 'text/plain' },
      });
    }

    const data = await backendRes.json();
    return NextResponse.json({
      dot: data.dot,
      solution_set_full: data.solution_set_full,
      example_solutions: data.example_solutions
    });
  } catch (error) {
    console.error('API route error:', error);
    return new NextResponse('Failed to fetch from presburger_converter', { status: 500 });
  }
} 