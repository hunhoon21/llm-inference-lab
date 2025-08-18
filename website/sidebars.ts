import type {SidebarsConfig} from '@docusaurus/plugin-content-docs';

// This runs in Node.js - Don't use client-side code here (browser APIs, JSX...)

/**
 * Creating a sidebar enables you to:
 - create an ordered group of docs
 - render a sidebar for each doc of that group
 - provide next/previous navigation

 The sidebars can be generated from the filesystem, or explicitly defined here.

 Create as many sidebars as you want.
 */
const sidebars: SidebarsConfig = {
  // Manual sidebar for LLM Inference Lab
  tutorialSidebar: [
    'intro',
    {
      type: 'category',
      label: '시작하기',
      items: [
        'getting-started/prerequisites',
        'getting-started/account-setup',
      ],
    },
    {
      type: 'category',
      label: '튜토리얼',
      items: [
        'tutorials/gcp-basic-setup',
        'tutorials/llm-inference-setup',
        'tutorials/client-integration',
      ],
    },
    {
      type: 'category',
      label: '가이드',
      items: [
        'guides/gpu-management',
        'guides/cost-optimization',
        'guides/troubleshooting',
      ],
    },
  ],
};

export default sidebars;
