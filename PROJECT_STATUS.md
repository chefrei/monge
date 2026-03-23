# 📊 Estado del Proyecto: POS Profesional - Cachapeate

Este documento proporciona una visión detallada de la arquitectura, el estado actual y los próximos pasos del sistema POS.

## 🏗️ Arquitectura del Sistema
El proyecto ha evolucionado hacia una aplicación web moderna con arquitectura cliente-servidor:
- **`app.py`**: Servidor Backend (Flask). Gestiona los endpoints de la API, el manejo de sesión y la subida de imágenes.
- **`static/`**: Recursos estáticos (CSS, JS, Imágenes). Incluye el motor visual del POS.
- **`templates/`**: Interfaz HTML5 dinámica y responsiva.
- **`data_manager.py`**: Capa de persistencia robusta para CSVs, generación de PDF y envío de correos.
- **`data/`**: Almacenamiento local para ventas, inventario, cierres y clientes.
- **`config/`**: Configuración de negocio adaptable vía web.

## ✅ Funcionalidades Implementadas
1.  **Venta Web Multi-moneda**: Soporte para USD y VES con conversión automática.
2.  **Facturación Fiscal Dinámica**: Numeración secuencial y diseño premium en PDF.
3.  **Gestión de Clientes Web**: Registro fluido con autocompletado de datos.
4.  **Facturación Digital Automatizada**:
    - Envío por Email vía SMTP (con panel de configuración).
    - Generación de PDF asíncrona.
5.  **Administración Integral**: 
    - **Subida de Imágenes**: Carga directa de fotos desde el modal de administración.
    - **Cierre de Caja**: Con histórico filtrable por fecha y protección de datos.
    - **Control Total**: Edición, creación y eliminación segura de productos y tickets.

## 🛠️ Estado Técnico
- **Framework**: Flask (Servidor), JS (Frontend).
- **Dependencias**: `Pillow` (Logos/Imágenes), `fpdf2` (PDFs).
- **Seguridad**: Reglas de negocio para evitar eliminación accidental tras el cierre de caja.

## 🚀 Próximos Pasos (Hoja de Ruta)
1.  **Migración a SQLite**: Para mayor escalabilidad.
2.  **Dashboard de Gastos**: Seguimiento de egresos para cálculo de beneficios.
3.  **Analíticas Visuales**: Gráficos de tendencias directamente en la web.

---
*Última actualización: 23 de marzo de 2026*
