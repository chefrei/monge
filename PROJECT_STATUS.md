# 📊 Estado del Proyecto: POS Profesional - Cachapeate

Este documento proporciona una visión detallada de la arquitectura, el estado actual y los próximos pasos del sistema POS.

## 🏗️ Arquitectura del Sistema
El proyecto sigue un diseño modular para separar la interfaz de la lógica de datos:
- **`programa.py`**: Interfaz Gráfica (GUI) construida con `tkinter`. Gestiona eventos de usuario y flujo de caja.
- **`data_manager.py`**: Capa de persistencia. Maneja la lectura/escritura de CSVs y la lógica de negocio (secuencias, PDF, Email).
- **`constants.py`**: Configuración centralizada de rutas, colores y estilos.
- **`data/`**: Almacenamiento local en archivos CSV para ventas (`ventas.csv`), inventario (`inventario.csv`), cierres (`cierres.csv`) y clientes (`clientes.csv`).
- **`config/`**: Archivos de configuración de usuario (`settings.json`) y branding.

## ✅ Funcionalidades Implementadas
1.  **Venta Multi-moneda**: Soporte para USD y VES con tasa de cambio dinámica.
2.  **Facturación Fiscal**: Numeración secuencial y datos del emisor personalizables.
3.  **Gestión de Clientes**: Registro automático y búsqueda por Cédula/RIF.
4.  **Facturación Digital**:
    - Generación de PDF profesional (`fpdf2`).
    - Envío por Email vía SMTP con soporte para Gmail (App Passwords).
5.  **Administración de Inventario**: Interfaz para añadir/editar productos y categorías.
6.  **Reportes**: Cierre de caja detallado y consulta de ventas por fecha.
7.  **Multi-Plataforma**: Compatible con Windows (VENV automático) y Linux (impresión `lp`).

## 🛠️ Estado Técnico
- **Lenguaje**: Python 3.10+
- **Dependencias**: `Pillow` (Logos), `fpdf2` (PDFs).
- **Persistencia**: Archivos CSV (Preparado estructuralmente para migración a SQLite/PostgreSQL).
- **Seguridad**: Las credenciales SMTP se almacenan localmente en `settings.json`. Se recomienda usar variables de entorno para mayor seguridad en el futuro.

## 🚀 Próximos Pasos (Hoja de Ruta)
1.  **Migración a Base de Datos SQL**: Cambiar CSV por SQLite para mejorar el rendimiento en volúmenes grandes de datos.
2.  **Módulo de Gastos**: Implementar registro de gastos diarios para obtener utilidad neta.
3.  **Gráficos Estadísticos**: Añadir visualizaciones de ventas semanales/mensuales.
4.  **Respaldos en la Nube**: Sincronización automática de `data/` con servicios como Google Drive o Dropbox.

---
*Última actualización: 10 de marzo de 2026*
