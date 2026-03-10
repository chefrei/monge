# POS PROFESIONAL - CACHAPEATE 🚀

Sistema de Punto de Venta (POS) optimizado para "Cachapeate - Las Cachapas de Aroa", diseñado para una gestión rápida, eficiente y profesional.

## 🌟 Características Principales

-   **Multi-moneda (USD/VES)**: Manejo dual de bolívares y dólares con tasa de cambio configurable en tiempo real.
-   **Facturación Profesional**: Generación de tickets con numeración secuencial (F-00000) y datos fiscales personalizables.
-   **Base de Datos de Clientes**: Registro integrado de Cédula/RIF, Dirección y Email con búsqueda inteligente.
-   **Facturación Digital (PDF & Email)**: Generación automática de facturas en PDF y envío automatizado por correo.
-   **Control de Inventario**: Grilla visual por categorías con gestión directa de productos y precios.
-   **Reportes y Cierres**: Consultas detalladas por fecha y reporte de cierre de caja optimizado.
-   **Multi-Plataforma**: Soporte para impresión directa tanto en Windows como en Linux (CUPS/lp).

## 🛠️ Instalación y Uso

### En Windows 🪟
1.  **Doble Clic** en `ejecutar_pos.bat`. El sistema creará el entorno virtual e instalará las dependencias (`Pillow`, `fpdf2`) automáticamente.
2.  **Acceso Directo**: Se recomienda crear un acceso directo de `ejecutar_pos.bat` en el escritorio para mayor comodidad.

### En Linux 🐧
1.  **Dependencias**:
    ```bash
    pip install -r requirements.txt
    ```
    *(Nota: Asegúrate de tener `python3-tk` instalado).*
2.  **Impresión**: Configura tu impresora en el sistema como "Predeterminada" para habilitar la impresión de tickets vía `lp`.

## 📧 Configuración de Correo Electrónico

Para habilitar el envío automático de facturas:
1.  Haz clic en **"Configurar Email"** en el panel lateral.
2.  Ingresa los datos de tu servidor SMTP (Gmail, Outlook, etc.).
3.  **Gmail Note**: Usa una **"Contraseña de Aplicación"** de 16 caracteres (generada en tu cuenta de Google) en lugar de tu contraseña normal.
4.  Usa el botón **"PROBAR ENVÍO"** para verificar la conexión antes de cobrar.

## 📊 Estructura de Datos
-   `data/ventas.csv`: Registro histórico detallado (incluye IDs únicos para migración SQL).
-   `data/clientes.csv`: Base de datos persistente de clientes.
-   `data/facturas_pdf/`: Repositorio de facturas digitales generadas.
-   `config/settings.json`: Configuración de datos fiscales, logo y tasa.

---
Para más detalles técnicos sobre la arquitectura y el futuro del proyecto, consulta: [PROJECT_STATUS.md](PROJECT_STATUS.md)

© 2026 - Desarrollado para Cachapeate. Listo para producción.
