import type { SidebarsConfig } from '@docusaurus/plugin-content-docs'

const sidebars: SidebarsConfig = {
  docsSidebar: [
    'intro',
    {
      type: 'category',
      label: 'Research',
      items: [
        'research/stellar-streams-overview',
        'research/discovery-methods',
        'research/persistent-homology-gap',
        'research/scaling-persistent-homology',
        'research/references'
      ]
    },
    {
      type: 'category',
      label: 'Data Access',
      items: [
        'data-access/gaia-catalog',
        'data-access/processed-catalogs',
        'data-access/storage-estimates'
      ]
    },
    {
      type: 'category',
      label: 'Guides',
      items: ['guides/getting-started', 'guides/explore-cli']
    },
    {
      type: 'category',
      label: 'Project',
      items: [
        'project/architecture',
        'project/stream-finder',
        'project/explore',
        'project/worker',
        'project/cuda-kernels',
        'project/infrastructure'
      ]
    }
  ]
}

export default sidebars
