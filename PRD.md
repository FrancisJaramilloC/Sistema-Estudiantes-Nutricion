# CONTEXTO MAESTRO DE INGENIERÍA Y PRD EXPANDIDO — NUTRIA (ITERACIÓN 1)
> **Módulos:** Autenticación RBAC, Expedientes Clínicos y Motor Antropométrico Interactivo.
> **Enfoque Visual Exigido:** Interfaz médica avanzada, informativa, densa en datos y altamente estética (Verde Bosque #1E3F20 y Crema #FDFBF7).
> **Entorno:** Local independiente (Agnóstico a AWS, desplegado 100% vía Docker Compose).

---

## CONSIGNAS METODOLÓGICAS PARA EL AGENTE DE IA
Actúa como Ingeniero de Software Senior UI/UX y Arquitecto de Software. Tu objetivo es generar el código completo de la Iteración 1. 

**CRÍTICO - Complejidad de la Interfaz:** Se ha observado que la aplicación luce muy simple. Para solucionar esto, debes diseñar vistas enriquecidas. No te limites a formularios básicos: incluye sidebars de navegación, tarjetas con resúmenes estadísticos, tooltips de ayuda clínica para las fórmulas, indicadores de progreso visual, estados dinámicos para los errores de validación, y tablas con componentes interactivos. Todo el sistema debe ser denso en información técnica y visualmente profesional.

---

## 1. ARQUITECTURA DE CÓDIGO Y ESQUEMA DE DIRECTORIOS
Genera y organiza las clases, hooks y componentes bajo la siguiente estructura modular:

```text
nutria-workspace/
├── docker-compose.yml
├── frontend/
│   ├── Dockerfile
│   ├── package.json
│   ├── vite.config.js
│   └── src/
│       ├── main.jsx
│       ├── App.jsx
│       ├── index.css
│       ├── hooks/
│       │   └── useAntropometria.js (Cálculos instantáneos en cliente)
│       └── components/
│           ├── Sidebar.jsx (Navegación médica lateral expandida)
│           ├── RegisterForm.jsx (Formulario denso con feedback dinámico)
│           ├── LoginForm.jsx
│           └── AntropometriaDashboard.jsx (Panel clínico con analíticas e indicadores)
└── backend/
    ├── Dockerfile
    ├── requirements.txt
    └── app/
        ├── main.py
        ├── config.py (Configuración de firma de tokens y claves secretas JWT locales)
        ├── auth.py (Middleware JWT local y decoradores de políticas RBAC)
        └── routes/
            ├── auth.py (Login, Registro y hashing con Bcrypt)
            └── clinical.py (Persistencia e interpretación del motor clínico NoSQL)

```

---

## 2. CONFIGURACIÓN DEL ENTORNO LOCAL (docker-compose.yml)

* **Frontend SPA (React + Vite):** Expuesto en el puerto `3000`.
* **Backend API (FastAPI):** Expuesto en el puerto `8000`.
* **Políticas CORS:** Configurar de forma mandatoria `CORSMiddleware` en FastAPI apuntando explícitamente a `http://localhost:3000` para autorizar las solicitudes síncronas de red.

---

## 3. CONTRATO FORMAL DE INTERFACES DE API (OPENAPI SPECS)

### 3.1 POST /api/v1/auth/register

* **Entrada (JSON):**

```json
{
  "nombre_completo": "Francisco Javier Jaramillo Castro",
  "cedula": "1104273415",
  "fecha_nacimiento": "2000-05-21",
  "email": "francisco.jaramillo@unl.edu.ec",
  "password": "PasswordStrong123!",
  "role": "Estudiante"
}

```

* **Comportamiento Backend:** Almacena el hash de la contraseña (Bcrypt) y el rol dentro del documento del usuario de la base de datos NoSQL local. Devuelve un código `HTTP 201 Created`.

### 3.2 POST /api/v1/auth/login

* **Entrada (JSON):** `email` y `password`.
* **Respuesta Exitosa (HTTP 200):** Retorna `access_token` (JWT local firmado por el servidor).

### 3.3 POST /api/v1/clinical/calculate

* **Seguridad:** Requiere la cabecera `Authorization: Bearer <JWT>` verificando la claim de rol `Estudiante`.
* **Entrada (JSON):**

```json
{
  "peso_kg": 70.00,
  "estatura_m": 1.75,
  "perimetro_cintura_cm": 100.00,
  "perimetro_cadera_cm": 90.00,
  "sexo_biologico": "Masculino"
}

```

* **Respuesta Exitosa (HTTP 200):**

```json
{
  "imc": 22.86,
  "imc_clasificacion": "Normal",
  "icc": 1.11,
  "icc_riesgo": "Alto",
  "distribucion_grasa": "Obesidad Androide (Manzana)"
}

```

---

## 4. REGLAS DE VALIDACIÓN REQUERIDAS (CLIENT-SIDE EN REACT)

El componente `RegisterForm.jsx` debe incluir indicadores interactivos que validen en tiempo real:

1. **Nombre Completo:** Bloquear caracteres numéricos o símbolos. Mínimo 3 letras.
2. **Cédula de Identidad Ecuatoriana (Módulo 10):** Validar longitud exacta de 10 caracteres. Implementar la multiplicación alternada por los coeficientes 2 y 1 sobre los 9 primeros dígitos, aplicar la resta de la decena superior y comprobar el dígito verificador. El sistema debe pintar un check box verde de éxito o una cruz de error conforme escribe el usuario.
3. **Mayoría de Edad:** Evaluar que el usuario sea mayor o igual a 18 años de forma estricta. Si es menor, bloquear dinámicamente el botón y desplegar un banner informativo crema con borde rojo.

---

## 5. DISEÑO DE LA INTERFAZ COMPLETA (EVITANDO LA SIMPLICIDAD UI/UX)

### 5.1 Dashboard Antropométrico Clínico (`AntropometriaDashboard.jsx`)

Para asegurar un diseño profesional e interactivo, la vista de la consulta clínica no debe ser una simple lista de inputs planos. Debe renderizar:

* **Sección Izquierda (Sidebar):** Menú lateral estructurado que resalte el rol del usuario (Estudiante o Docente) mediante una credencial digital color verde bosque de grado médico.
* **Sección Central (Formulario de Captura):** Campos numéricos con sliders adaptativos para Peso, Estatura, Cintura y Cadera. Cada input debe incluir tooltips que expliquen la base científica de la medida.
* **Sección Derecha (Resultados Analíticos Dinámicos):** Conforme el estudiante altera los valores, la interfaz debe invocar a `useAntropometria.js` para renderizar:
* Un velocímetro o barra de rango de color que ubique el **IMC** del paciente (Bajo Peso, Normal, Sobrepeso, Obesidad).
* Una tarjeta de alerta destacada si el **ICC** computado arroja un riesgo cardiovascular alto.
* Un contenedor dinámico con un icono descriptivo que cambie entre una silueta de **Manzana (Obesidad Androide)** o **Pera (Obesidad Ginoide)** según la fórmula biológica de la OMS.



---

## 6. PARAMETRIZACIÓN DE SEGURIDAD, PRIVACIDAD Y PERSISTENCIA

### 6.1 Control de Accesos por Rol (RBAC)

* El backend en FastAPI debe implementar una validación por middleware sobre la firma del token JWT. Si un token con claim de rol `Estudiante` realiza una llamada de red a endpoints administrativos de auditoría global, la API bloqueará la ejecución de inmediato devolviendo un código `HTTP 403 Forbidden`.

### 6.2 Seudonimización Estricta (ISO 25000)

* Al salvar el resultado antropométrico en la base de datos local, la IA debe asegurar que **ningún** campo de log, auditoría o expediente relacione datos en texto plano del paciente (como nombre o cédula).
* Todo registro médico debe quedar enlazado de forma unívoca e inmutable mediante un identificador autogenerado aleatorio `Patient_ID` bajo el estándar **UUIDv4**.

---

## 7. MENSURABILIDAD DE CALIDAD (MÉTRICAS TÉCNICAS)

* **Eficiencia (RNF1):** El motor matemático síncrono del backend debe procesar y retornar la estructura JSON en un tiempo límite inferior a los 300 milisegundos.
* **Reactividad (RNF2):** El refresco de los componentes interactivos del frontend tras modificar porciones o gramos no debe bloquear el hilo principal de renderizado y debe ejecutarse en menos de 100 milisegundos.

```