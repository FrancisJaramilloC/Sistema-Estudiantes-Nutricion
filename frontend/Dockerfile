FROM node:20-alpine

WORKDIR /app

# Copiar archivos de dependencias
COPY package*.json ./

# Instalar dependencias
RUN npm install

# Copiar el código del frontend
COPY . .

# Exponer el puerto 3000 para cumplir con el PRD
EXPOSE 3000

# Correr el servidor de desarrollo de Vite en el puerto 3000
CMD ["npm", "run", "dev", "--", "--host", "--port", "3000"]
