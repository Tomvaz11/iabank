import type { PluginOption } from 'vite';

type BuildHeaderOptions = {
  nonce: string;
  trustedTypesPolicy: string;
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

export const buildDevCspHeader = (options: BuildHeaderOptions): string => {
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
    "require-trusted-types-for 'script'",
    `trusted-types ${options.trustedTypesPolicy}`,
  ];

  if (options.reportUri) {
    directives.push(`report-uri ${options.reportUri}`);
  }

  return directives.join('; ');
};

type PluginOptions = {
  nonce: string;
  trustedTypesPolicy: string;
  reportUri?: string | null;
  connectSrc?: string[];
  styleSrc?: string[];
  imgSrc?: string[];
  fontSrc?: string[];
};

export const createFoundationCspPlugin = (options: PluginOptions): PluginOption => {
  const headerValue = buildDevCspHeader({
    nonce: options.nonce,
    trustedTypesPolicy: options.trustedTypesPolicy,
    reportUri: options.reportUri ?? null,
    connectSrc: options.connectSrc,
    styleSrc: options.styleSrc,
    imgSrc: options.imgSrc,
    fontSrc: options.fontSrc,
  });

  return {
    name: 'foundation-csp-dev',
    apply: 'serve',
    configureServer(server) {
      server.middlewares.use((_req, res, next) => {
        res.setHeader('Content-Security-Policy-Report-Only', headerValue);
        next();
      });
    },
    transformIndexHtml(html) {
      return applyNonceToHtml(html, options.nonce);
    },
  };
};
