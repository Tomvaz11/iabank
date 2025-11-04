import{j as e}from"./jsx-runtime-DF2Pcvd1.js";import{b as j}from"./Button-09BGjp1W.js";import{c as E}from"./cn-C0Y9tLwQ.js";import"./index-B2-qRKKC.js";import"./_commonjsHelpers-Cpj98o6Y.js";const N=({title:S="Ocorreu um erro",message:A,onRetry:o,retryLabel:B="Tentar novamente",action:q,retryButtonType:D="button",className:R,...w})=>e.jsx("div",{...w,role:"alert","aria-live":"assertive",className:E("rounded-lg border border-status-danger bg-surface px-6 py-5 text-left shadow-sm",R),children:e.jsxs("div",{className:"flex flex-col gap-3 sm:flex-row sm:items-start sm:gap-4",children:[e.jsx("span",{"aria-hidden":"true",className:"inline-flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-full bg-status-danger text-status-danger-foreground font-semibold",children:"!"}),e.jsxs("div",{className:"flex-1 space-y-2",children:[e.jsxs("div",{className:"space-y-1",children:[e.jsx("h3",{className:"text-base font-semibold text-text-primary",children:S}),e.jsx("p",{className:"text-sm text-text-secondary",children:A})]}),e.jsxs("div",{className:"flex flex-wrap items-center gap-2",children:[o?e.jsx(j,{variant:"secondary",size:"sm",onClick:o,type:D,"data-testid":"retry-button",children:B}):null,q]})]})]})});N.__docgenInfo={description:"",methods:[],displayName:"DataStateError",props:{title:{required:!1,tsType:{name:"string"},description:`Título exibido no topo do alerta.
@default 'Ocorreu um erro'`,defaultValue:{value:"'Ocorreu um erro'",computed:!1}},message:{required:!0,tsType:{name:"string"},description:"Mensagem com detalhes sobre o erro ou orientação de próxima ação."},onRetry:{required:!1,tsType:{name:"signature",type:"function",raw:"() => void",signature:{arguments:[],return:{name:"void"}}},description:"Ação de retry para erros recuperáveis."},retryLabel:{required:!1,tsType:{name:"string"},description:`Texto exibido no botão de retry.
@default 'Tentar novamente'`,defaultValue:{value:"'Tentar novamente'",computed:!1}},action:{required:!1,tsType:{name:"ReactNode"},description:"Conteúdo adicional (ex.: link para suporte)."},retryButtonType:{required:!1,tsType:{name:"ButtonHTMLAttributes['type']",raw:"ButtonHTMLAttributes<HTMLButtonElement>['type']"},description:"Personaliza o tipo do botão de retry (ex.: submit em formulários).",defaultValue:{value:"'button'",computed:!1}}},composes:["HTMLAttributes"]};const _={title:"Shared/UI/Data States/Error",component:N,parameters:{layout:"centered",tenants:["tenant-default","tenant-alfa","tenant-beta"]},args:{title:"Não foi possível carregar os dados",message:"Verifique sua conexão com a internet e tente novamente. Persistindo o erro, entre em contato com o suporte.",onRetry:()=>{},action:e.jsx(j,{variant:"secondary",size:"sm",children:"Abrir suporte"})}},t={},a={args:{onRetry:void 0}},r={name:"Tenant default",parameters:{tenant:"tenant-default"}},n={name:"Tenant Alfa",parameters:{tenant:"tenant-alfa"}},s={name:"Tenant Beta",parameters:{tenant:"tenant-beta"}};var i,d,m;t.parameters={...t.parameters,docs:{...(i=t.parameters)==null?void 0:i.docs,source:{originalSource:"{}",...(m=(d=t.parameters)==null?void 0:d.docs)==null?void 0:m.source}}};var c,l,u;a.parameters={...a.parameters,docs:{...(c=a.parameters)==null?void 0:c.docs,source:{originalSource:`{
  args: {
    onRetry: undefined
  }
}`,...(u=(l=a.parameters)==null?void 0:l.docs)==null?void 0:u.source}}};var p,f,x;r.parameters={...r.parameters,docs:{...(p=r.parameters)==null?void 0:p.docs,source:{originalSource:`{
  name: 'Tenant default',
  parameters: {
    tenant: 'tenant-default'
  }
}`,...(x=(f=r.parameters)==null?void 0:f.docs)==null?void 0:x.source}}};var y,g,T;n.parameters={...n.parameters,docs:{...(y=n.parameters)==null?void 0:y.docs,source:{originalSource:`{
  name: 'Tenant Alfa',
  parameters: {
    tenant: 'tenant-alfa'
  }
}`,...(T=(g=n.parameters)==null?void 0:g.docs)==null?void 0:T.source}}};var b,v,h;s.parameters={...s.parameters,docs:{...(b=s.parameters)==null?void 0:b.docs,source:{originalSource:`{
  name: 'Tenant Beta',
  parameters: {
    tenant: 'tenant-beta'
  }
}`,...(h=(v=s.parameters)==null?void 0:v.docs)==null?void 0:h.source}}};const k=["Default","SemRetry","TenantDefault","TenantAlfa","TenantBeta"];export{t as Default,a as SemRetry,n as TenantAlfa,s as TenantBeta,r as TenantDefault,k as __namedExportsOrder,_ as default};
