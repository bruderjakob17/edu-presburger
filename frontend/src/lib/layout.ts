export function placeEdgeLabelsWithoutOverlap(labels: HTMLDivElement[]) {
  const boxes: DOMRect[] = [];
  
  labels.forEach(div => {
    let tries = 0;
    const originalTop = parseFloat(div.style.top);
    
    while (tries < 20) {
      const currentRect = div.getBoundingClientRect();
      const hasOverlap = boxes.some(box => {
        return !(
          currentRect.right < box.left ||
          currentRect.left > box.right ||
          currentRect.bottom < box.top ||
          currentRect.top > box.bottom
        );
      });
      
      if (!hasOverlap) {
        break;
      }
      
      div.style.top = `${originalTop + (tries + 1) * 8}px`;
      tries++;
    }
    
    boxes.push(div.getBoundingClientRect());
  });
} 