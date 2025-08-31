FROM node:18-alpine

# Configurações de ambiente
ENV NODE_ENV=development

# Instala dependências do sistema
RUN apk add --no-cache git

# Cria diretório de trabalho
WORKDIR /app

# Copia arquivos de dependências
COPY package*.json ./

# Instala dependências
RUN npm ci

# Copia código fonte
COPY . .

# Cria usuário não-root
RUN addgroup -g 1001 -S nodejs
RUN adduser -S nextjs -u 1001

# Ajusta permissões
RUN chown -R nextjs:nodejs /app
USER nextjs

# Expõe porta
EXPOSE 5173

# Comando padrão
CMD ["npm", "run", "dev"]