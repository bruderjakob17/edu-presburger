'use client';

import React, { useEffect, useState, useRef } from 'react';
import { Graphviz } from '@hpcc-js/wasm';

export default function GraphvizViewer({ dot }: { dot: string }) {
  const [svg, setSvg] = useState<string | null>(null);
  const [scale, setScale] = useState(1);
  const [position, setPosition] = useState({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });
  const [isFullscreen, setIsFullscreen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const renderGraph = async () => {
      try {
        const graphviz = await Graphviz.load();
        const svgStr = await graphviz.layout(dot, "svg", "dot");
        // Add viewBox and preserveAspectRatio to the SVG
        const modifiedSvg = svgStr.replace('<svg', '<svg preserveAspectRatio="xMidYMid meet" style="width: 100%; height: 100%;"');
        setSvg(modifiedSvg);
      } catch (err) {
        console.error('Error rendering graph:', err);
      }
    };

    renderGraph();
  }, [dot]);

  const handleWheel = (e: React.WheelEvent) => {
    if (!isFullscreen) return;
    e.preventDefault();
    const delta = e.deltaY;
    const zoomFactor = delta > 0 ? 0.9 : 1.1;
    const newScale = Math.min(Math.max(0.1, scale * zoomFactor), 5);
    setScale(newScale);
  };

  const handleMouseDown = (e: React.MouseEvent) => {
    if (!isFullscreen) return;
    if (e.button === 0) { // Left mouse button
      setIsDragging(true);
      setDragStart({ x: e.clientX - position.x, y: e.clientY - position.y });
    }
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    if (!isFullscreen) return;
    if (isDragging) {
      setPosition({
        x: e.clientX - dragStart.x,
        y: e.clientY - dragStart.y
      });
    }
  };

  const handleMouseUp = () => {
    setIsDragging(false);
  };

  const handleDoubleClick = () => {
    if (!isFullscreen) return;
    // Reset zoom and position
    setScale(1);
    setPosition({ x: 0, y: 0 });
  };

  const toggleFullscreen = async () => {
    if (!containerRef.current) return;

    try {
      if (!isFullscreen) {
        await containerRef.current.requestFullscreen();
        setIsFullscreen(true);
      } else {
        await document.exitFullscreen();
        setIsFullscreen(false);
        // Reset zoom and position when exiting fullscreen
        setScale(1);
        setPosition({ x: 0, y: 0 });
      }
    } catch (err) {
      console.error('Error toggling fullscreen:', err);
    }
  };

  // Listen for fullscreen change events
  useEffect(() => {
    const handleFullscreenChange = () => {
      setIsFullscreen(!!document.fullscreenElement);
      if (!document.fullscreenElement) {
        // Reset zoom and position when exiting fullscreen
        setScale(1);
        setPosition({ x: 0, y: 0 });
      }
    };

    document.addEventListener('fullscreenchange', handleFullscreenChange);
    return () => {
      document.removeEventListener('fullscreenchange', handleFullscreenChange);
    };
  }, []);

  return (
    <div 
      ref={containerRef}
      className="w-full h-full flex items-center justify-center overflow-hidden relative"
      onWheel={handleWheel}
      onMouseDown={handleMouseDown}
      onMouseMove={handleMouseMove}
      onMouseUp={handleMouseUp}
      onMouseLeave={handleMouseUp}
      onDoubleClick={handleDoubleClick}
    >
      <div
        dangerouslySetInnerHTML={{ __html: svg ?? 'Loading graph...' }}
        className="w-full h-full"
        style={{
          transform: isFullscreen ? `translate(${position.x}px, ${position.y}px) scale(${scale})` : 'none',
          transformOrigin: 'center',
          transition: isDragging ? 'none' : 'transform 0.1s ease-out',
        }}
      />
      <button
        onClick={toggleFullscreen}
        className="absolute top-2 right-2 p-2 bg-white/80 hover:bg-white rounded-lg shadow-lg transition-colors z-10"
        title={isFullscreen ? "Exit fullscreen" : "Enter fullscreen"}
      >
        {isFullscreen ? (
          <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 9V4.5M9 9H4.5M15 9H19.5M15 9V4.5M15 15v4.5M15 15H4.5M15 15h4.5M9 15v4.5" />
          </svg>
        ) : (
          <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5v-4m0 4h-4m4 0l-5-5" />
          </svg>
        )}
      </button>
    </div>
  );
} 