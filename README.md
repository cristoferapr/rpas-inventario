
# Automatización RPA para Validación de Facturas y Actualización de Inventario

Este proyecto implementa un sistema RPA (Robotic Process Automation) que automatiza la validación de facturas escaneadas contra órdenes de compra almacenadas en archivos Excel. Además, actualiza un inventario en un archivo Excel basado en la información procesada de las facturas.

## Funcionalidades Principales

- **Extracción de Texto de Imágenes**: Utiliza OCR (Tesseract) para extraer información clave de las facturas escaneadas.
- **Validación de Facturas**:
  - Compara productos y totales de las facturas con la información de las órdenes de compra.
  - Identifica discrepancias y reporta errores.
- **Actualización de Inventario**:
  - Modifica automáticamente el inventario en un archivo Excel basado en los productos validados.
- **Compatibilidad con Archivos Excel**: Procesa órdenes de compra en formato Excel, separando datos de productos y valores adicionales (NETO, IVA, TOTAL).
- **Cálculo Automático de IVA**: Recalcula el IVA y valida totales con una tolerancia mínima.

## Requisitos

1. **Python** (versión 3.6 o superior)
2. Bibliotecas necesarias:
   - `pandas`
   - `numpy`
   - `pytesseract`
   - `Pillow`
   - `opencv-python`
3. **Tesseract OCR**: Asegúrate de instalar Tesseract y configurar su ruta correctamente.

### Instalación de Dependencias

Ejecuta el siguiente comando para instalar las bibliotecas requeridas:

```bash
pip install pandas numpy pytesseract pillow opencv-python
```

### Configuración de Tesseract

Descarga e instala [Tesseract OCR](https://github.com/tesseract-ocr/tesseract). Luego, ajusta la variable `pytesseract.pytesseract.tesseract_cmd` en el código para apuntar a la ubicación de tu instalación.

## Uso

1. **Estructura del Proyecto**:
   - `facturas/`: Carpeta que contiene las imágenes de las facturas.
   - `ordenes/`: Carpeta que contiene los archivos Excel de las órdenes de compra.
   - `inventario.xlsx`: Archivo Excel donde se actualiza el inventario.

2. **Ejecutar el Script**:

   ```bash
   python app.py <ruta_imagen_factura> <carpeta_ordenes>
   ```

   Ejemplo:

   ```bash
   python app.py facturas/8.jpg ordenes/
   ```

3. **Resultados**:
   - El sistema validará los datos de la factura contra la orden de compra correspondiente.
   - Reportará discrepancias en los productos o totales.
   - Actualizará el inventario en el archivo Excel `inventario.xlsx`.

## Detalles Técnicos

- **Extracción de Texto**: Utiliza Tesseract con configuración personalizada (`--oem 3 --psm 6`) para maximizar la precisión.
- **Procesamiento de Datos**:
  - Las órdenes de compra se dividen en dos tablas:
    - Productos con códigos únicos.
    - Datos adicionales como NETO, IVA y TOTAL.
- **Validación**:
  - Busca coincidencias entre los productos de la factura y la orden de compra.
  - Recalcula el subtotal, IVA y total para detectar discrepancias.
- **Inventario**:
  - Actualiza automáticamente las cantidades en el inventario basándose en los productos de la factura.

## Ejemplo de Resultados

Al procesar una factura, el sistema genera la siguiente salida:

- **Texto Extraído de la Factura**:
  ```
  N° 12345
  Producto A: 5 unidades - $50.00
  Producto B: 3 unidades - $30.00
  ```

- **Validación**:
  ```
  Producto validado: Código=123, Total=$50.00
  Producto validado: Código=124, Total=$30.00
  Subtotal: $80.00
  IVA: $15.20
  Total Calculado: $95.20
  ```

- **Inventario Actualizado**:
  El archivo `inventario.xlsx` refleja los cambios realizados en las cantidades disponibles de los productos.

## Futuras Mejoras

- Integración con bases de datos SQL para un manejo más robusto de órdenes e inventarios.
- Interfaz gráfica para facilitar el uso por parte de usuarios no técnicos.
- Generación de reportes automáticos en formato PDF o HTML.

## Contribución

Si deseas contribuir a este proyecto, por favor crea un fork del repositorio, realiza tus cambios y envía un pull request.

---

¡Gracias por usar este sistema RPA! Si tienes dudas o sugerencias, no dudes en contactarme.
