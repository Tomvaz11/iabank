const budgets = [
  {
    path: '/',
    options: {
      preset: 'desktop'
    },
    timings: [
      { metric: 'interactive', target: 3000 },
      { metric: 'largest-contentful-paint', target: 2500 },
      { metric: 'total-blocking-time', target: 200 },
      { metric: 'cumulative-layout-shift', target: 0.1 }
    ],
    resourceSizes: [
      { resourceType: 'script', budget: 300 },
      { resourceType: 'image', budget: 400 },
      { resourceType: 'font', budget: 150 }
    ],
    resourceCounts: [
      { resourceType: 'third-party', budget: 0 }
    ]
  }
];

export default {
  ci: {
    collect: {
      url: ['http://localhost:4173/'],
      numberOfRuns: 1,
      settings: {
        preset: 'desktop',
        formFactor: 'desktop',
        throttlingMethod: 'devtools',
        screenEmulation: { mobile: false, width: 1366, height: 768, deviceScaleFactor: 1 }
      }
    },
    assert: {
      assertions: {
        'categories:performance': ['error', { minScore: 0.9 }],
        'largest-contentful-paint': ['error', { maxNumericValue: 2500 }],
        'total-blocking-time': ['error', { maxNumericValue: 200 }],
        'interactive': ['error', { maxNumericValue: 3000 }],
        'cumulative-layout-shift': ['error', { maxNumericValue: 0.1 }]
      }
    },
    lighthouse: {
      budgets
    }
  }
};
// CI: validação prática da issue #86 (canário) — alteração sem efeito funcional
