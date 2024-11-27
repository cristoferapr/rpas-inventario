import re
import pandas as pd
import pytesseract
from PIL import Image
import cv2
import os

# Configuración de Tesseract OCR
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
custom_config = r'--oem 3 --psm 6'

# Función para extraer el número de orden de la factura
def extraer_numero_orden(texto_extraido):
    """
    Busca el número de orden en el texto extraído de la factura.
    Utiliza dos patrones clave para diferentes formatos.
    """
    print("\nBuscando número de orden...")

    # Lista de patrones seleccionados
    patrones = [
        r"\bN[°oº*]?\s*(\d{4,})\b",  # Genérico: "N° 43564893" o "N 12345"
        r"\bN[°oº*]?\s*\d*\s*(\d{4,})\b",  # Más flexible: "N2 43564893"
    ]

    # Probar cada patrón hasta encontrar una coincidencia
    for patron in patrones:
        match = re.search(patron, texto_extraido, re.IGNORECASE)
        if match:
            numero_orden = match.group(1)  # Capturar solo el número
            print(f"Número de orden encontrado: {numero_orden}")
            return numero_orden

    # Si no encuentra coincidencias
    print("No se encontró un número de orden en el texto extraído.")
    return None



# Procesar factura y extraer texto
def procesar_factura(imagen_path):
    print("Procesando factura desde imagen...")
    try:
        # Leer y preprocesar la imagen
        img = cv2.imread(imagen_path, cv2.IMREAD_GRAYSCALE)

        img = cv2.threshold(img, 128, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]

        texto_extraido = pytesseract.image_to_string(img, lang="spa", config=custom_config)
        print("Texto extraído de la factura (crudo):")
        print(texto_extraido)
        return texto_extraido

    except Exception as e:
        print(f"Error procesando la factura: {e}")
        return None

def procesar_orden_compra(archivo_excel):
    print("Procesando archivo Excel...")
    try:
        # Leer el archivo Excel
        df = pd.read_excel(archivo_excel)

        # Dividir en dos categorías: productos y datos únicos
        productos = df[df["CODIGO"].apply(lambda x: str(x).isdigit())]  # Filtrar filas con códigos de productos
        datos_unicos = df[~df["CODIGO"].apply(lambda x: str(x).isdigit())]  # Filtrar las demás filas

        # Procesar filas únicas (NETO, IVA, TOTAL, etc.)
        datos_unicos = datos_unicos.dropna(how="all").reset_index(drop=True)  # Eliminar filas totalmente vacías
        if not datos_unicos.empty:
            # Ajustar columnas de datos únicos si hay al menos dos
            if len(datos_unicos.columns) >= 2:
                datos_unicos = datos_unicos.iloc[:, :2]  # Tomar solo las dos primeras columnas
                datos_unicos.columns = ["Nombre", "Valor"]  # Renombrar columnas

        # Imprimir los datos separados
        print("\nTabla de productos:")
        if not productos.empty:
            print(productos)
        else:
            print("No se encontraron productos.")

        print("\nInformación adicional:")
        if not datos_unicos.empty:
            print(datos_unicos)
        else:
            print("No se encontró información adicional (NETO, IVA, TOTAL, etc.).")

        return productos, datos_unicos

    except Exception as e:
        print(f"Error procesando el archivo Excel: {e}")
        return None, None
    
def validar_factura_vs_excel(texto_factura, productos, datos_adicionales):
    print("\nValidando factura contra el Excel...")
    try:
        # Convertir texto de factura en líneas
        lineas_factura = texto_factura.split("\n")
        
        # Inicializar subtotal
        subtotal_factura = 0
        total_errores = 0
        
        # Buscar productos en la factura
        for _, producto in productos.iterrows():
            codigo_producto = str(producto["CODIGO"])
            total_excel = float(producto["TOTAL"])  # Total esperado según Excel
            encontrado = False

            for linea in lineas_factura:
                if codigo_producto in linea:  # Buscar línea que contenga el código del producto
                    print(f"Línea encontrada para código {codigo_producto}: {linea}")
                    encontrado = True

                    # Capturar todos los números en la línea
                    numeros = re.findall(r"[\d]+(?:[.,][\d]+)?", linea)
                    numeros = [num for num in numeros if num != codigo_producto]
                    print(f"???????\n{numeros}")  # Depuración: Mostrar los números capturados
                    
                    if numeros:
                        # Convertir los números al formato estándar
                        totales = [float(num.replace(".", "").replace(",", ".")) for num in numeros]
                        # Tomar el número mayor como el total
                        total_factura = max(totales)  # Asumir que el total es el número mayor
                        
                        # Validar contra el Excel
                        if abs(total_factura - total_excel) < 0.01:  # Tolerancia mínima
                            print(f"Producto validado: Código={codigo_producto}, Total={total_factura}")
                            subtotal_factura += total_factura
                        else:
                            print(f"Discrepancia detectada: Código={codigo_producto}, Total en factura={total_factura}, Total en Excel={total_excel}")
                            total_errores += 1
                    else:
                        print(f"No se pudo extraer ningún número para el producto con código {codigo_producto}. Línea: {linea}")
                    break

            if not encontrado:
                print(f"Producto con código {codigo_producto} no encontrado en la factura.")
        
        print(f"\nSubtotal de productos validados en la factura: {subtotal_factura:.2f}")
        
        # Calcular IVA y total esperado
        iva_calculado = subtotal_factura * 0.19
        total_calculado = subtotal_factura + iva_calculado
        print(f"IVA calculado (19%): {iva_calculado:.2f}")
        print(f"Total calculado: {total_calculado:.2f}")
        
        # Validar contra el total del Excel
        total_excel = float(datos_adicionales.loc[datos_adicionales["Nombre"] == "TOTAL", "Valor"].values[0])
        if abs(total_calculado - total_excel) < 0.01:  # Comparar con tolerancia mínima
            print("\nLa factura coincide con el Excel. Validación exitosa.")
        else:
            print("\nDiscrepancia detectada:")
            print(f"Total en factura calculado: {total_calculado:.2f}")
            print(f"Total en Excel: {total_excel:.2f}")
        
        # Reportar errores
        if total_errores > 0:
            print(f"\nNúmero de productos con discrepancias: {total_errores}")
        else:
            print("\nTodos los productos coinciden correctamente.")
    except Exception as e:
        print(f"Error validando la factura: {e}")

# Flujo principal ajustado
def app(imagen_factura, carpeta_excel):
    # Paso 1: Procesar la factura para extraer texto
    texto_extraido = procesar_factura(imagen_factura)
    if texto_extraido is None:
        print("No se pudo procesar la factura.")
        return

    # Paso 2: Extraer número de orden
    numero_orden = extraer_numero_orden(texto_extraido)
    if numero_orden is None:
        print("No se pudo encontrar el número de orden.")
        return

    # Paso 3: Buscar el archivo Excel correspondiente
    archivo_excel = os.path.join(carpeta_excel, f"{numero_orden}.xlsx")
    if not os.path.exists(archivo_excel):
        print(f"No se encontró el archivo Excel: {archivo_excel}")
        return

    # Paso 4: Procesar el archivo Excel para obtener productos e información adicional
    productos, datos_adicionales = procesar_orden_compra(archivo_excel)
    if productos is None or datos_adicionales is None:
        print("No se pudo procesar la orden de compra.")
        return

    # Paso 5: Validar los datos de la factura contra el Excel
    validar_factura_vs_excel(texto_extraido, productos, datos_adicionales)


# Ejecutar flujo con ejemplos
app("facturas/8.jpg", "ordenes")
