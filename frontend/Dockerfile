# Dockerfile para el frontend React
FROM node:18-alpine

# Directorio de trabajo
WORKDIR /app

# Copiar package files
COPY package*.json ./

# Instalar dependencias
RUN npm install

# Copiar código
COPY . .

# Exponer puerto
EXPOSE 5173

# Comando de desarrollo
CMD ["npm", "run", "dev", "--", "--host"]

