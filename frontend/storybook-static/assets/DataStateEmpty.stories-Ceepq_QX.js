import{j as e}from"./jsx-runtime-DF2Pcvd1.js";import{b as E}from"./Button-09BGjp1W.js";import{c as q}from"./cn-C0Y9tLwQ.js";import"./index-B2-qRKKC.js";import"./_commonjsHelpers-Cpj98o6Y.js";const N=({title:S,description:A,action:o,icon:c,className:D,...B})=>e.jsxs("div",{...B,role:"status","aria-live":"polite",className:q("flex flex-col items-center justify-center gap-4 rounded-lg border border-dashed border-border bg-surface px-8 py-10 text-center",D),children:[c?e.jsx("span",{className:"text-4xl text-brand-primary","aria-hidden":"true",children:c}):null,e.jsxs("div",{className:"space-y-2",children:[e.jsx("h3",{className:"text-lg font-semibold text-text-primary",children:S}),e.jsx("p",{className:"text-sm text-text-secondary max-w-prose",children:A})]}),o?e.jsx("div",{className:"mt-2 flex flex-wrap justify-center gap-2",children:o}):null]});N.__docgenInfo={description:"",methods:[],displayName:"DataStateEmpty",props:{title:{required:!0,tsType:{name:"string"},description:"Título do estado vazio, normalmente uma frase curta."},description:{required:!0,tsType:{name:"string"},description:"Descrição com instruções ou contexto adicional."},action:{required:!1,tsType:{name:"ReactNode"},description:"Ação opcional (botão, link). Deve ser um elemento interativo acessível."},icon:{required:!1,tsType:{name:"ReactNode"},description:"Ícone ilustrativo, sempre tratado como decorativo."}},composes:["HTMLAttributes"]};const k={title:"Shared/UI/Data States/Empty",component:N,parameters:{layout:"centered",tenants:["tenant-default","tenant-alfa","tenant-beta"]},args:{title:"Nenhum resultado encontrado",description:"Ajuste os filtros ou crie um novo item para começar.",icon:e.jsx("span",{className:"text-4xl",children:"✨"}),action:e.jsx(E,{size:"sm",variant:"primary",children:"Criar item"})}},a={},t={args:{action:void 0}},r={name:"Tenant default",parameters:{tenant:"tenant-default"}},n={name:"Tenant Alfa",parameters:{tenant:"tenant-alfa"}},s={name:"Tenant Beta",parameters:{tenant:"tenant-beta"}};var i,m,d;a.parameters={...a.parameters,docs:{...(i=a.parameters)==null?void 0:i.docs,source:{originalSource:"{}",...(d=(m=a.parameters)==null?void 0:m.docs)==null?void 0:d.source}}};var l,p,u;t.parameters={...t.parameters,docs:{...(l=t.parameters)==null?void 0:l.docs,source:{originalSource:`{
  args: {
    action: undefined
  }
}`,...(u=(p=t.parameters)==null?void 0:p.docs)==null?void 0:u.source}}};var f,x,T;r.parameters={...r.parameters,docs:{...(f=r.parameters)==null?void 0:f.docs,source:{originalSource:`{
  name: 'Tenant default',
  parameters: {
    tenant: 'tenant-default'
  }
}`,...(T=(x=r.parameters)==null?void 0:x.docs)==null?void 0:T.source}}};var y,g,h;n.parameters={...n.parameters,docs:{...(y=n.parameters)==null?void 0:y.docs,source:{originalSource:`{
  name: 'Tenant Alfa',
  parameters: {
    tenant: 'tenant-alfa'
  }
}`,...(h=(g=n.parameters)==null?void 0:g.docs)==null?void 0:h.source}}};var b,j,v;s.parameters={...s.parameters,docs:{...(b=s.parameters)==null?void 0:b.docs,source:{originalSource:`{
  name: 'Tenant Beta',
  parameters: {
    tenant: 'tenant-beta'
  }
}`,...(v=(j=s.parameters)==null?void 0:j.docs)==null?void 0:v.source}}};const C=["Default","SemAcao","TenantDefault","TenantAlfa","TenantBeta"];export{a as Default,t as SemAcao,n as TenantAlfa,s as TenantBeta,r as TenantDefault,C as __namedExportsOrder,k as default};
