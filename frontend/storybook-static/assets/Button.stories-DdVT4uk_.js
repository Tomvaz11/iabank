import{j as h}from"./jsx-runtime-DF2Pcvd1.js";import{w as A,e as a}from"./index-DfMQMhH_.js";import{B as x,a as C,b as p}from"./Button-VVySRL8m.js";import"./index-B2-qRKKC.js";import"./_commonjsHelpers-Cpj98o6Y.js";import"./cn-C0Y9tLwQ.js";const v={"tenant-default":{background:"rgb(30, 58, 138)",foreground:"rgb(248, 250, 252)"},"tenant-alfa":{background:"rgb(15, 118, 110)",foreground:"rgb(240, 253, 250)"},"tenant-beta":{background:"rgb(124, 58, 237)",foreground:"rgb(245, 243, 255)"}},N={title:"Shared/UI/Button",component:p,parameters:{layout:"centered",chromatic:{disableSnapshot:!1}},args:{children:"Continuar",variant:"primary",size:"md"},render:({tenant:r,...o})=>h.jsx(p,{...o}),argTypes:{variant:{control:"inline-radio",options:C},size:{control:"inline-radio",options:x},tenant:{control:!1}}},s=r=>async({canvasElement:o,args:l})=>{const c=await A(o).findByRole("button",{name:l.children});a(document.documentElement.dataset.tenant).toBe(r),a(c.dataset.variant).toBe(l.variant??"primary");const d=window.getComputedStyle(c),m=v[r];a(d.backgroundColor).toBe(m.background),a(d.color).toBe(m.foreground)},n={name:"Tenant default",args:{tenant:"tenant-default"},parameters:{tenant:"tenant-default"},play:s("tenant-default")},t={name:"Tenant Alfa",args:{tenant:"tenant-alfa",children:"Continuar (Alfa)"},parameters:{tenant:"tenant-alfa"},play:s("tenant-alfa")},e={name:"Tenant Beta",args:{tenant:"tenant-beta",children:"Continuar (Beta)"},parameters:{tenant:"tenant-beta"},play:s("tenant-beta")};var i,u,f;n.parameters={...n.parameters,docs:{...(i=n.parameters)==null?void 0:i.docs,source:{originalSource:`{
  name: 'Tenant default',
  args: {
    tenant: 'tenant-default'
  },
  parameters: {
    tenant: 'tenant-default'
  },
  play: playStoryForTenant('tenant-default')
}`,...(f=(u=n.parameters)==null?void 0:u.docs)==null?void 0:f.source}}};var g,T,b;t.parameters={...t.parameters,docs:{...(g=t.parameters)==null?void 0:g.docs,source:{originalSource:`{
  name: 'Tenant Alfa',
  args: {
    tenant: 'tenant-alfa',
    children: 'Continuar (Alfa)'
  },
  parameters: {
    tenant: 'tenant-alfa'
  },
  play: playStoryForTenant('tenant-alfa')
}`,...(b=(T=t.parameters)==null?void 0:T.docs)==null?void 0:b.source}}};var y,B,S;e.parameters={...e.parameters,docs:{...(y=e.parameters)==null?void 0:y.docs,source:{originalSource:`{
  name: 'Tenant Beta',
  args: {
    tenant: 'tenant-beta',
    children: 'Continuar (Beta)'
  },
  parameters: {
    tenant: 'tenant-beta'
  },
  play: playStoryForTenant('tenant-beta')
}`,...(S=(B=e.parameters)==null?void 0:B.docs)==null?void 0:S.source}}};const O=["TenantDefault","TenantAlfa","TenantBeta"];export{t as TenantAlfa,e as TenantBeta,n as TenantDefault,O as __namedExportsOrder,N as default};
