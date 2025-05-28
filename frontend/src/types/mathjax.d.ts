interface MathJax {
  typesetPromise: (elements: HTMLElement[]) => Promise<void>;
}

declare global {
  interface Window {
    MathJax?: MathJax;
  }
} 