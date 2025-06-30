import React from 'react';

interface ExampleSolution {
  path_int: number[];
  path_bits: string[];
  variables: string[];
  var_bits: { [key: string]: string };
  var_ints: { [key: string]: number };
}

interface ExampleSolutionsProps {
  solutions: ExampleSolution[];
  allSolutions: ExampleSolution[];
  bufferSolutions: ExampleSolution[];
  kSolutions: number;
  onAddExample: () => void;
  loading: boolean;
  isFullSolutionSet: boolean;
  isRefillingBuffer: boolean;
  isButtonDisabled: boolean;
}

export default function ExampleSolutions({ 
  solutions, 
  allSolutions, 
  bufferSolutions,
  kSolutions, 
  onAddExample, 
  loading, 
  isFullSolutionSet, 
  isRefillingBuffer, 
  isButtonDisabled 
}: ExampleSolutionsProps) {
  if (!solutions || solutions.length === 0) return null;

  // Determine if we should show the + button
  const showAddButton = bufferSolutions.length > 0;

  return (
    <div className="mb-8">
      <h2 className="text-xl font-semibold mb-4">
        {isFullSolutionSet ? 'Full Solution Set' : 'Example Solutions'}
      </h2>
      <div className="grid gap-4 grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4">
        {solutions.map((solution, index) => (
          <div
            key={index}
            className="bg-white rounded-lg shadow-md p-4 border border-gray-200 flex flex-col"
          >
            <div className="mb-2">
              <span className="font-semibold text-gray-700">Solution {index + 1}</span>
            </div>
            {/* Path Information (only show if path_bits is not empty) */}
            {solution.path_bits && solution.path_bits.length > 0 && (
              <div className="mb-2">
                <div className="text-sm font-medium text-gray-600 mb-1">Path (binary):</div>
                <div className="flex flex-wrap items-center gap-1">
                  {solution.path_bits.map((bit, i) => (
                    <span
                      key={i}
                      className="px-2 py-1 bg-blue-100 text-blue-800 rounded font-mono text-sm"
                    >
                      {bit}
                    </span>
                  ))}
                </div>
              </div>
            )}
            {/* Variable Values */}
            <div>
              <div className="text-sm font-medium text-gray-600 mb-1">Variable Values:</div>
              <div className="grid grid-cols-1 gap-1">
                {solution.variables.map((varName) => (
                  <div key={varName} className="flex flex-col gap-0.5">
                    <div className="font-medium text-gray-700">{varName}:</div>
                    <div className="flex items-center gap-2">
                      <div className="flex items-center gap-1">
                        <span className="text-gray-500 text-sm">Binary:</span>
                        <span className="px-2 py-1 bg-blue-100 text-blue-800 rounded font-mono text-sm">
                          {solution.var_bits[varName] || 'ε'}
                        </span>
                      </div>
                      <div className="flex items-center gap-1">
                        <span className="text-gray-500 text-sm">Integer:</span>
                        <span className="px-2 py-1 bg-green-100 text-green-800 rounded font-mono text-sm">
                          {solution.var_ints[varName]}
                        </span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        ))}
        {/* Add Example Button */}
        {showAddButton && (
          <button
            type="button"
            onClick={onAddExample}
            disabled={isButtonDisabled}
            className="bg-gray-100 border-2 border-dashed border-gray-300 rounded-lg shadow-md p-4 flex flex-col items-center justify-center cursor-pointer hover:bg-gray-200 transition-colors min-h-[180px] disabled:opacity-50 disabled:cursor-not-allowed"
            style={{ minHeight: '180px' }}
            aria-label="Generate another example"
          >
            {isButtonDisabled ? (
              <>
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-400 mb-2"></div>
                <span className="text-gray-500 font-medium">Loading more examples...</span>
              </>
            ) : (
              <>
                <span className="text-4xl text-gray-400 mb-2">+</span>
                <span className="text-gray-500 font-medium">Generate another example</span>
              </>
            )}
          </button>
        )}
        
        {/* Completion Tile */}
        {!showAddButton && isFullSolutionSet && (
          <div className="bg-green-50 border-2 border-green-200 rounded-lg shadow-md p-4 flex flex-col items-center justify-center min-h-[180px]">
            <svg xmlns="http://www.w3.org/2000/svg" className="h-12 w-12 text-green-500 mb-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <span className="text-green-700 font-medium text-center">Solution set completed</span>
          </div>
        )}
      </div>
    </div>
  );
} 