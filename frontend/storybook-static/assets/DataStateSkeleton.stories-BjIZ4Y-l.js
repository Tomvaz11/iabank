import{j as e}from"./jsx-runtime-DF2Pcvd1.js";import{c as w}from"./cn-C0Y9tLwQ.js";import"./index-B2-qRKKC.js";import"./_commonjsHelpers-Cpj98o6Y.js";const D=t=>Array.from({length:Math.max(1,t)},(c,a)=>{const d=`skeleton-line-${a}`,k=a===0?"w-full":a===t-1?"w-2/3":"w-[85%]";return e.jsx("div",{"data-testid":"data-state-skeleton-line",className:w("h-3 rounded-full bg-border opacity-60",k)},d)}),N=({className:t,lines:c=3,showAvatar:a=!1,...d})=>e.jsxs("div",{...d,role:"status","aria-live":"polite","aria-busy":"true","aria-label":"Carregando conteúdo",className:w("animate-pulse space-y-4 rounded-lg border border-dashed border-border bg-surface px-4 py-6",t),children:[a&&e.jsxs("div",{className:"flex items-center gap-3",children:[e.jsx("div",{className:"h-10 w-10 rounded-full bg-border opacity-60","data-testid":"data-state-skeleton-avatar"}),e.jsxs("div",{className:"flex-1 space-y-2",children:[e.jsx("div",{className:"h-3 rounded-full bg-border opacity-60"}),e.jsx("div",{className:"h-3 w-3/4 rounded-full bg-border opacity-60"})]})]}),e.jsx("div",{className:"space-y-2",children:D(c)}),e.jsx("span",{className:"sr-only",children:"Carregando conteúdo"})]});N.__docgenInfo={description:"",methods:[],displayName:"DataStateSkeleton",props:{lines:{required:!1,tsType:{name:"number"},description:"Quantidade de linhas exibidas após o avatar opcional.",defaultValue:{value:"3",computed:!1}},showAvatar:{required:!1,tsType:{name:"boolean"},description:"Exibe placeholder circular, útil para listas com avatar.",defaultValue:{value:"false",computed:!1}}},composes:["HTMLAttributes"]};const q={title:"Shared/UI/Data States/Skeleton",component:N,parameters:{layout:"centered",tenants:["tenant-default","tenant-alfa","tenant-beta"]},args:{lines:3,showAvatar:!0}},r={},s={args:{showAvatar:!1,lines:5}},n={name:"Tenant default",parameters:{tenant:"tenant-default"}},o={name:"Tenant Alfa",parameters:{tenant:"tenant-alfa"}},l={name:"Tenant Beta",parameters:{tenant:"tenant-beta"}};var i,m,p;r.parameters={...r.parameters,docs:{...(i=r.parameters)==null?void 0:i.docs,source:{originalSource:"{}",...(p=(m=r.parameters)==null?void 0:m.docs)==null?void 0:p.source}}};var u,f,b;s.parameters={...s.parameters,docs:{...(u=s.parameters)==null?void 0:u.docs,source:{originalSource:`{
  args: {
    showAvatar: false,
    lines: 5
  }
}`,...(b=(f=s.parameters)==null?void 0:f.docs)==null?void 0:b.source}}};var h,v,g;n.parameters={...n.parameters,docs:{...(h=n.parameters)==null?void 0:h.docs,source:{originalSource:`{
  name: 'Tenant default',
  parameters: {
    tenant: 'tenant-default'
  }
}`,...(g=(v=n.parameters)==null?void 0:v.docs)==null?void 0:g.source}}};var x,y,T;o.parameters={...o.parameters,docs:{...(x=o.parameters)==null?void 0:x.docs,source:{originalSource:`{
  name: 'Tenant Alfa',
  parameters: {
    tenant: 'tenant-alfa'
  }
}`,...(T=(y=o.parameters)==null?void 0:y.docs)==null?void 0:T.source}}};var S,A,j;l.parameters={...l.parameters,docs:{...(S=l.parameters)==null?void 0:S.docs,source:{originalSource:`{
  name: 'Tenant Beta',
  parameters: {
    tenant: 'tenant-beta'
  }
}`,...(j=(A=l.parameters)==null?void 0:A.docs)==null?void 0:j.source}}};const I=["Default","WithoutAvatar","TenantDefault","TenantAlfa","TenantBeta"];export{r as Default,o as TenantAlfa,l as TenantBeta,n as TenantDefault,s as WithoutAvatar,I as __namedExportsOrder,q as default};
