import type { PluginOption } from 'vite';

import { resolveTrustedTypesDisposition } from './src/shared/security/trustedTypes';
import type { TrustedTypesDisposition } from './src/shared/security/trustedTypes';

type BuildHeaderOptions = {
  nonce: string;
  trustedTypesPolicy: string;
  enforceTrustedTypes: boolean;
  reportUri?: string | null;
  connectSrc?: string[];
  styleSrc?: string[];
  imgSrc?: string[];
  fontSrc?: string[];
};

const joinDirective = (name: string, values: string[]): string => {
  const items = values.filter(Boolean);
  return `${name} ${items.join(' ')}`.trim();
};

export const applyNonceToHtml = (html: string, nonce: string): string => {
  if (!nonce) {
    return html;
  }

  return html.replace(/<script\b(?![^>]*\bnonce=)([^>]*)>/gi, (_match, attrs) => {
    return `<script nonce="${nonce}"${attrs}>`;
  });
};

const buildDirectives = (options: BuildHeaderOptions): string[] => {
  const scriptSrc = ["'self'", "'strict-dynamic'", `'nonce-${options.nonce}'`];
  const connectSrc = options.connectSrc ?? ["'self'"];
  const styleSrc = options.styleSrc ?? ["'self'"];
  const imgSrc = options.imgSrc ?? ["'self'", 'data:'];
  const fontSrc = options.fontSrc ?? ["'self'"];

  const directives = [
    "default-src 'none'",
    "base-uri 'self'",
    joinDirective('script-src', scriptSrc),
    joinDirective('connect-src', connectSrc),
    joinDirective('style-src', styleSrc),
    joinDirective('img-src', imgSrc),
    joinDirective('font-src', fontSrc),
    "object-src 'none'",
    "frame-ancestors 'none'",
    `trusted-types ${options.trustedTypesPolicy}`,
  ];

  if (options.enforceTrustedTypes) {
    directives.push("require-trusted-types-for 'script'");
  }

  if (options.reportUri) {
    directives.push(`report-uri ${options.reportUri}`);
  }

  return directives;
};

export const buildCspHeader = (options: BuildHeaderOptions): string =>
  buildDirectives(options).join('; ');

export const buildTrustedTypesReportHeader = (
  options: Omit<BuildHeaderOptions, 'enforceTrustedTypes'>,
): string =>
  buildDirectives({
    ...options,
    enforceTrustedTypes: true,
  }).join('; ');

type PluginOptions = {
  nonce: string;
  trustedTypesPolicy: string;
  trustedTypesRolloutStart: string;
  reportUri?: string | null;
  connectSrc?: string[];
  styleSrc?: string[];
  imgSrc?: string[];
  fontSrc?: string[];
  now?: () => Date;
  trustedTypesModeOverride?: TrustedTypesDisposition;
};

const buildTrustedTypesHeaders = (
  options: PluginOptions,
  now: Date,
): {
  mode: ReturnType<typeof resolveTrustedTypesDisposition>['mode'];
  expiresAt: Date;
  cspHeader: string;
  cspHeaderEnforced: string;
  cspHeaderReportOnly: string;
  trustedTypesReportHeader: string | null;
} => {
  const disposition = resolveTrustedTypesDisposition({
    startedAt: options.trustedTypesRolloutStart,
    now,
  });
  const mode: TrustedTypesDisposition =
    options.trustedTypesModeOverride ?? disposition.mode;

  const cspHeaderEnforced = buildCspHeader({
    nonce: options.nonce,
    trustedTypesPolicy: options.trustedTypesPolicy,
    enforceTrustedTypes: true,
    reportUri: options.reportUri ?? null,
    connectSrc: options.connectSrc,
    styleSrc: options.styleSrc,
    imgSrc: options.imgSrc,
    fontSrc: options.fontSrc,
  });

  const cspHeaderReportOnly = buildCspHeader({
    nonce: options.nonce,
    trustedTypesPolicy: options.trustedTypesPolicy,
    enforceTrustedTypes: false,
    reportUri: options.reportUri ?? null,
    connectSrc: options.connectSrc,
    styleSrc: options.styleSrc,
    imgSrc: options.imgSrc,
    fontSrc: options.fontSrc,
  });

  const trustedTypesReportHeader =
    mode === 'report-only'
      ? buildTrustedTypesReportHeader({
          nonce: options.nonce,
          trustedTypesPolicy: options.trustedTypesPolicy,
          reportUri: options.reportUri ?? null,
          connectSrc: options.connectSrc,
          styleSrc: options.styleSrc,
          imgSrc: options.imgSrc,
          fontSrc: options.fontSrc,
        })
      : null;

  return {
    mode,
    expiresAt: disposition.expiresAt,
    cspHeader: mode === 'enforce' ? cspHeaderEnforced : cspHeaderReportOnly,
    cspHeaderEnforced,
    cspHeaderReportOnly,
    trustedTypesReportHeader,
  };
};

const buildTrustedTypesRuntimeScript = (params: {
  nonce: string;
  enforceAt: Date;
  enforcePolicy: string;
  reportPolicy: string;
  reportOnlyHeader?: string | null;
}): string => {
  const script = `(function(){
    const enforceAt = new Date(${JSON.stringify(params.enforceAt.toISOString())});
    const now = new Date();
    const enforcePolicy = ${JSON.stringify(params.enforcePolicy)};
    const reportPolicy = ${JSON.stringify(params.reportPolicy)};
    const reportOnlyPolicy = ${JSON.stringify(params.reportOnlyHeader ?? '')};
    const head = document.head || document.getElementsByTagName('head')[0];
    if (!head) return;

    const findMeta = (httpEquiv) => head.querySelector('meta[http-equiv=\"' + httpEquiv + '\"]');
    const setMeta = (httpEquiv, content) => {
      if (!content) return;
      let tag = findMeta(httpEquiv);
      if (!tag) {
        tag = document.createElement('meta');
        tag.setAttribute('http-equiv', httpEquiv);
        head.prepend(tag);
      }
      tag.setAttribute('content', content);
    };
    const removeMeta = (httpEquiv) => {
      const tag = findMeta(httpEquiv);
      if (tag) tag.remove();
    };

    if (now >= enforceAt) {
      setMeta('Content-Security-Policy', enforcePolicy);
      removeMeta('Content-Security-Policy-Report-Only');
    } else {
      setMeta('Content-Security-Policy', reportPolicy);
      if (reportOnlyPolicy) {
        setMeta('Content-Security-Policy-Report-Only', reportOnlyPolicy);
      }
    }
  })();`;

  return `<script nonce="${params.nonce}">${script}</script>`;
};

export const createFoundationCspPlugin = (options: PluginOptions): PluginOption => {
  const resolveNow = options.now ?? (() => new Date());
  const applyHeaders = (
    _req: unknown,
    res: { setHeader: (key: string, value: string) => void },
    next: () => void,
  ) => {
    const headers = buildTrustedTypesHeaders(options, resolveNow());
    res.setHeader('Content-Security-Policy', headers.cspHeader);
    if (headers.trustedTypesReportHeader) {
      res.setHeader('Content-Security-Policy-Report-Only', headers.trustedTypesReportHeader);
    }
    next();
  };

  const injectMetaTags = (html: string): string => {
    const headers = buildTrustedTypesHeaders(options, resolveNow());
    const metaTags = [
      `<meta http-equiv="Content-Security-Policy" content="${headers.cspHeader}">`,
      headers.trustedTypesReportHeader
        ? `<meta http-equiv="Content-Security-Policy-Report-Only" content="${headers.trustedTypesReportHeader}">`
        : null,
      buildTrustedTypesRuntimeScript({
        nonce: options.nonce,
        enforceAt: headers.expiresAt,
        enforcePolicy: headers.cspHeaderEnforced,
        reportPolicy: headers.cspHeaderReportOnly,
        reportOnlyHeader: headers.trustedTypesReportHeader,
      }),
    ]
      .filter(Boolean)
      .join('\n    ');

    if (!metaTags || !html.includes('<head>')) {
      return html;
    }

    return html.replace('<head>', `<head>\n    ${metaTags}`);
  };

  return {
    name: 'foundation-csp',
    configureServer(server) {
      server.middlewares.use(applyHeaders);
    },
    configurePreviewServer(server) {
      server.middlewares.use(applyHeaders);
    },
    transformIndexHtml(html) {
      const withNonce = applyNonceToHtml(html, options.nonce);
      return injectMetaTags(withNonce);
    },
  };
};
