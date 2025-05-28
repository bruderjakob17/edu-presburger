declare module 'cytoscape-dagre' {
  import { Core } from 'cytoscape';
  
  function register(cytoscape: typeof Core): void;
  export = register;
} 