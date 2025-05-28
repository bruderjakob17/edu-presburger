import React from 'react';

export default function Graph({ svg }: { svg: string }) {
  return (
    <div className="w-full h-[600px] relative overflow-auto">
      <div
        className="w-full h-full"
        dangerouslySetInnerHTML={{ __html: svg }}
      />
    </div>
  );
} 