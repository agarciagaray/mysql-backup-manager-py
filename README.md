# MySQL Backup Manager Pro

![MySQL Backup Manager](assets/icons/app_icon.png)

> **Solución profesional para la gestión y automatización de copias de seguridad de bases de datos MySQL**

---

## 📌 Descripción

**MySQL Backup Manager Pro** es una aplicación de escritorio diseñada para simplificar y automatizar la gestión de copias de seguridad de bases de datos MySQL.  
Desarrollada en Python con una interfaz gráfica moderna, ofrece una solución todo-en-uno para administradores de bases de datos y desarrolladores.

---

## 🌟 Características Destacadas

### 🔄 Automatización Avanzada
- Programación flexible de respaldos (diarios, semanales, mensuales)
- Ejecución de scripts personalizados pre/post backup
- Notificaciones por correo electrónico

### 🔒 Seguridad Mejorada
- Encriptación AES-256 para credenciales
- Gestión segura de contraseñas
- Registro detallado de auditoría

### 📊 Gestión Eficiente
- Interfaz intuitiva con panel de control
- Monitoreo en tiempo real de operaciones
- Historial detallado de respaldos
- Estadísticas de uso de almacenamiento

### 🛠 Herramientas Integradas
- Editor de consultas SQL
- Restauración de bases de datos
- Exportación/Importación de configuraciones
- Verificación de integridad de respaldos

---

## 🚀 Requisitos del Sistema

### 📋 Requisitos Mínimos
- **Sistema Operativo**: Windows 10/11, macOS 10.15+, Linux (Ubuntu 20.04+)
- **Python**: 3.8 o superior
- **MySQL Server**: 5.7 o superior
- **RAM**: 4 GB
- **Espacio en disco**: 500 MB (más espacio para respaldos)

### 🔌 Dependencias
- `ttkbootstrap >= 1.10.1`
- `mysql-connector-python >= 9.3.0`
- `APScheduler >= 3.11.0`
- `cryptography >= 42.0.5`
- `pillow >= 9.5.0`

---

## 🛠 Instalación Detallada

### 1. Clonar el Repositorio

```bash
git clone https://github.com/agarciagaray/mysql-backup-manager-py.git
cd mysql-backup-manager-py
```

### 2. Configuración del Entorno Virtual

```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# Linux/macOS
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Instalación de Dependencias

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Configuración Inicial

Ejecuta la aplicación:

```bash
python main.py
```

---

## 📖 Guía Rápida

### ➕ Agregar una Nueva Base de Datos

1. Navega a `Conexiones` en la barra lateral  
2. Haz clic en `Agregar Conexión`  
3. Completa el formulario con:  
   - Nombre descriptivo  
   - Host (ej: `localhost`)  
   - Puerto (`3306` por defecto)  
   - Usuario y contraseña  
   - Base de datos objetivo

### ⏱ Programar un Respaldo Automático

1. Ve a `Programador`  
2. Haz clic en `Nueva Tarea`  
3. Configura:  
   - Frecuencia (diaria, semanal, mensual)  
   - Hora de ejecución  
   - Retención de copias  
   - Opciones de compresión

### ♻ Restaurar una Base de Datos

1. Ve a `Historial`  
2. Selecciona el respaldo a restaurar  
3. Haz clic en `Restaurar`  
4. Sigue el asistente de restauración

---

## 🚨 Solución de Problemas Comunes

### ❗ Error de Conexión

```plaintext
"Error al conectar con el servidor MySQL"
```

**Solución:**
- Verifica que el servicio MySQL esté en ejecución
- Comprueba las credenciales de acceso
- Asegúrate de que el puerto `3306` esté accesible

---

### 📦 Problemas con Dependencias

```plaintext
ModuleNotFoundError: No module named 'ttkbootstrap'
```

**Solución:**

```bash
pip install -r requirements.txt --force-reinstall
```

---

### 🐢 Rendimiento Lento

**Recomendaciones:**
- Cierra otras aplicaciones que consuman recursos
- Reduce la frecuencia de los respaldos programados
- Considera aumentar los recursos del sistema

---

## 📊 Estructura del Proyecto

```
mysql-backup-manager/
├── assets/             # Recursos gráficos
├── src/
│   ├── models/         # Modelos de datos
│   ├── repositories/   # Acceso a datos
│   ├── services/       # Lógica de negocio
│   ├── utils/          # Utilidades
│   └── views/          # Interfaces de usuario
├── main.py             # Punto de entrada
└── requirements.txt    # Dependencias
```

---

## 🤝 Contribuciones

¡Las contribuciones son bienvenidas! Por favor, sigue estos pasos:

1. Haz un Fork del proyecto  
2. Crea una rama para tu feature  
   ```bash
   git checkout -b feature/AmazingFeature
   ```
3. Haz commit de tus cambios  
   ```bash
   git commit -m "Add some AmazingFeature"
   ```
4. Haz push a la rama  
   ```bash
   git push origin feature/AmazingFeature
   ```
5. Abre un Pull Request

---

## 📄 Licencia

Distribuido bajo la Licencia MIT. Consulta el archivo `LICENSE` para más información.

---

## 📧 Contacto

¿Preguntas o sugerencias? ¡Nos encantaría escucharte!

- **Email**: agarciagaray@pm.me  
- **Sitio Web**: [https://agarciagaray.dev](https://agarciagaray.dev)  
- **Twitter**: [@agarciagaray](https://twitter.com/agarciagaray)  

---

Desarrollado con ❤️ por [Alejandro García Garay] | [GitHub](https://github.com/agarciagaray)
