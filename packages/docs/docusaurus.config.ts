import type * as Preset from '@docusaurus/preset-classic'
import type { Config } from '@docusaurus/types'
import { themes as prismThemes } from 'prism-react-renderer'
import rehypeKatex from 'rehype-katex'
import remarkMath from 'remark-math'

const baseUrl = process.env.DOCS_BASE_URL ?? '/topology-streams/'

const config: Config = {
  title: 'TopoStreams',
  tagline: 'Stellar stream discovery with persistent homology',
  favicon: 'img/favicon.svg',

  url: 'https://cavera.github.io',
  baseUrl,

  organizationName: 'cavera',
  projectName: 'topology-streams',

  onBrokenLinks: 'throw',
  onBrokenMarkdownLinks: 'warn',

  i18n: {
    defaultLocale: 'en',
    locales: ['en']
  },

  markdown: {
    mermaid: true
  },

  presets: [
    [
      'classic',
      {
        docs: {
          routeBasePath: '/',
          sidebarPath: './sidebars.ts',
          remarkPlugins: [remarkMath],
          rehypePlugins: [rehypeKatex]
        },
        blog: false,
        theme: {
          customCss: './src/css/custom.css'
        }
      } satisfies Preset.Options
    ]
  ],

  themeConfig: {
    navbar: {
      title: 'TopoStreams',
      logo: { alt: 'TopoStreams', src: 'img/logo.svg' },
      items: [
        {
          type: 'docSidebar',
          sidebarId: 'docsSidebar',
          position: 'left',
          label: 'Docs'
        },
        {
          href: 'https://github.com/caverac/topology-streams',
          label: 'GitHub',
          position: 'right'
        }
      ]
    },
    footer: {
      style: 'dark',
      copyright: `TopoStreams. Built with Docusaurus.`
    },
    prism: {
      additionalLanguages: ['python', 'sql', 'bash'],
      theme: prismThemes.github,
      darkTheme: prismThemes.dracula
    },
    colorMode: {
      defaultMode: 'dark',
      respectPrefersColorScheme: true
    }
  } satisfies Preset.ThemeConfig,

  themes: [
    '@docusaurus/theme-mermaid',
    [
      '@easyops-cn/docusaurus-search-local',
      {
        hashed: true
      }
    ]
  ]
}

export default config
