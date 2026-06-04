FROM node:20-alpine

WORKDIR /app

# Copiar archivos de dependencias
COPY package*.json ./

# Instalar dependencias
RUN npm install

# Copiar el código del frontend
COPY . .

# Exponer el puerto por defecto de Vite
EXPOSE 5173

# Correr el servidor de desarrollo de Vite escuchando en todas las interfaces (0.0.0.0)
CMD ["npm", "run", "dev", "--", "--host"]
