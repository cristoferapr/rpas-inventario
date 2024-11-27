import re
import pandas as pd
import pytesseract
import cv2
import os

# Configuración de Tesseract OCR
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
custom_config = r'--oem 3 --psm 6'

# Procesar factura y extraer texto
def procesar_factura(imagen_path):
    print("Procesando factura desde imagen...")
    try:
        img = cv2.imread(imagen_path, cv2.IMREAD_GRAYSCALE)
        img = cv2.threshold(img, 128, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]
        texto_extraido = pytesseract.image_to_string(img, lang="spa", config=custom_config)
        return texto_extraido
    except Exception as e:
        print(f"Error procesando la factura: {e}")
        return None

def procesar_orden_compra(archivo_excel):
    print("Procesando archivo Excel...")
    try:
        df = pd.read_excel(archivo_excel)
        productos = df[df["CODIGO"].apply(lambda x: str(x).isdigit())]
        datos_unicos = df[~df["CODIGO"].apply(lambda x: str(x).isdigit())]
        datos_unicos = datos_unicos.dropna(how="all").reset_index(drop=True)
        if not datos_unicos.empty and len(datos_unicos.columns) >= 2:
            datos_unicos = datos_unicos.iloc[:, :2]
            datos_unicos.columns = ["Nombre", "Valor"]

        if productos.empty:
            print("No se encontraron productos en la orden.")


        return productos, datos_unicos

    except Exception as e:
        print(f"Error procesando el archivo Excel: {e}")
        return None, None

def actualizar_inventario(productos, archivo_inventario="inventario.xlsx"):
    print("\nActualizando inventario...")

    # Verificar si el archivo existe
    if os.path.exists(archivo_inventario):
        inventario = pd.read_excel(archivo_inventario)
    else:
        # Crear un archivo vacío con las columnas necesarias
        inventario = pd.DataFrame(columns=["CODIGO", "PRODUCTO", "CANTIDAD", "ESTADO"])

    # Asegurar que la columna "CANTIDAD" sea numérica
    inventario["CANTIDAD"] = pd.to_numeric(inventario["CANTIDAD"], errors="coerce").fillna(0)

    for _, producto in productos.iterrows():
        codigo = producto["CODIGO"]
        nombre = producto["PRODUCTO"]
        cantidad_nueva = producto["CANTIDAD"]

        # Asegurar que la cantidad nueva sea numérica
        codigo = pd.to_numeric(codigo, errors="coerce")
        cantidad_nueva = pd.to_numeric(cantidad_nueva, errors="coerce")

        # Verificar si el producto ya existe en el inventario
        if codigo in inventario["CODIGO"].values:
            idx = inventario[inventario["CODIGO"] == codigo].index[0]
            inventario.at[idx, "CANTIDAD"] += cantidad_nueva  # Sumar cantidad
        else:
            # Agregar nuevo producto
            inventario = pd.concat([inventario, pd.DataFrame({
                "CODIGO": [codigo],
                "PRODUCTO": [nombre],
                "CANTIDAD": [cantidad_nueva],
                "ESTADO": [""]  # Se actualizará más tarde
            })], ignore_index=True)

    # Actualizar el estado de cada producto
    def calcular_estado(cantidad):
        if cantidad > 15:
            return "Disponible"
        elif 7 < cantidad <= 15:
            return "Medio"
        elif 3 < cantidad <= 7:
            return "Poco"
        elif 1 <= cantidad <= 3:
            return "Crítico"
        else:
            return "No disponible"

    inventario["ESTADO"] = inventario["CANTIDAD"].apply(calcular_estado)

    # Guardar cambios en el archivo
    inventario.to_excel(archivo_inventario, index=False)
    print("Inventario actualizado correctamente.")

def validar_factura_vs_excel(texto_factura, productos, datos_adicionales):
    """
    Valida los datos de la factura contra el Excel y maneja las discrepancias.
    """
    print("\nValidando factura contra el Excel...")
    try:
        # Convertir texto de factura en líneas
        lineas_factura = texto_factura.split("\n")
        
        # Convertir valores numéricos en el DataFrame de productos
        productos["PRECIO UNIDAD"] = productos["PRECIO UNIDAD"].apply(
            lambda x: float(str(x).replace(",", "."))
        )
        # Inicializar subtotal y variables para discrepancias
        subtotal_factura = 0
        total_errores = 0
        detalles_discrepancia = []
        cantidades_faltantes = {}

        # Buscar productos en la factura
        for _, producto in productos.iterrows():
            codigo_producto = str(producto["CODIGO"])
            nombre_producto = str(producto["PRODUCTO"])
            total_excel = float(producto["TOTAL"])  # Total esperado según Excel
            precio_unitario = float(producto["PRECIO UNIDAD"])
            encontrado = False

            for linea in lineas_factura:
                if codigo_producto in linea:  # Buscar línea que contenga el código del producto
                    ##print(f"Línea encontrada para código {codigo_producto}: {linea}")
                    encontrado = True

                    # Capturar todos los números en la línea
                    numeros = re.findall(r"[\d]+(?:[.,][\d]+)?", linea)
                    ##print(f"Números extraídos de la línea: {numeros}")
                    numeros = [num for num in numeros if num != codigo_producto]
                    
                    if numeros:
                        # Convertir los números al formato estándar
                        totales = [float(num.replace(".", "").replace(",", ".")) for num in numeros]
                        # Tomar el número mayor como el total
                        total_factura = max(totales)  # Asumir que el total es el número mayor

                        # Validar contra el Excel
                        if abs(total_factura - total_excel) < 0.01:  # Si no hay discrepancia
                            ##print(f"Producto validado: Código={codigo_producto}, Total={total_factura}")
                            subtotal_factura += total_factura
                        else:
                            ##print(f"Discrepancia detectada: Código={codigo_producto}, Total en factura={total_factura}, Total en Excel={total_excel}")
                            diferencia = total_excel - total_factura
                            unidades_faltantes = round(diferencia / precio_unitario)
                            cantidades_faltantes[codigo_producto] = unidades_faltantes
                            detalles_discrepancia.append(
                                f"Producto {codigo_producto} - {nombre_producto}: Faltan {unidades_faltantes} unidades (Total factura={total_factura}, Total Excel={total_excel})"
                            )
                            subtotal_factura += total_factura
                            total_errores += 1
                    else:
                        print(f"No se pudo extraer ningún número para el producto con código {codigo_producto}. Línea: {linea}")
                    break

            if not encontrado:
                print(f"Producto con código {codigo_producto} no encontrado en la factura.")
                detalles_discrepancia.append(f"Producto {codigo_producto} no encontrado en la factura.")
                total_errores += 1
        
        print(f"\nSubtotal de productos validados en la factura: {subtotal_factura:.2f}")
        
        # Calcular IVA y total esperado
        iva_calculado = subtotal_factura * 0.19
        total_calculado = subtotal_factura + iva_calculado
        print(f"IVA calculado (19%): {iva_calculado:.2f}")
        print(f"Total calculado en factura: {total_calculado:.2f}")
        
        # Validar contra el total del Excel
        total_excel_boleta = float(datos_adicionales.loc[datos_adicionales["Nombre"] == "TOTAL", "Valor"].values[0])
        if abs(total_calculado - total_excel_boleta) < 0.5 and total_errores == 0:  # Comparar con tolerancia mínima
            print("\nLa factura coincide con el Excel. Validación exitosa.")
            actualizar_inventario(productos)
            return True, [], [], total_calculado, total_excel_boleta, None
        else:
            print("\nDiscrepancia detectada:")
            print(f"Total en factura calculado: {total_calculado:.2f}")
            print(f"Total en Excel: {total_excel_boleta:.2f}")
            for d in detalles_discrepancia:
                print(d)
            if cantidades_faltantes:
                # Restar las cantidades faltantes del DataFrame `productos`
                for codigo, faltante in cantidades_faltantes.items():
                    # Buscar el índice correspondiente al producto por su código
                    codigo = int(codigo)
                    if codigo in productos["CODIGO"].values:
                        idx = productos[productos["CODIGO"] == codigo].index[0]
                        productos.at[idx, "CANTIDAD"] -= faltante  # Restar la cantidad faltante
                
                print("Desea aceptar igualmente la orden? (Ingrese '1':Si / '2': No)")
                opcion = input()
                while True:
                    if opcion == '1' :
                        actualizar_inventario(productos)
                        break
                    elif opcion == '2' :
                        print("El pedido ha sido rechazado")
                        break
                    else :
                        print("Opcion invalida. Por favor ingrese '1':Si / '2': No)")
                        opcion = input()
            return

    except Exception as e:
        print(f"Error validando la factura: {e}")
        return False, None, None, None, None, None

# Flujo principal ajustado
def app(imagen_factura, carpeta_excel):
    texto_extraido = procesar_factura(imagen_factura)
    if texto_extraido is None:
        print("No se pudo procesar la factura.")
        return

    numero_orden = input("Por favor, ingrese el número de orden: ").strip()
    archivo_excel = os.path.join(carpeta_excel, f"{numero_orden}.xlsx")
    if not os.path.exists(archivo_excel):
        print(f"No se encontró el archivo Excel: {archivo_excel}")
        return

    productos, datos_adicionales = procesar_orden_compra(archivo_excel)
    if productos is None or datos_adicionales is None:
        print("No se pudo procesar la orden de compra.")
        return

    # Validar factura
    validar_factura_vs_excel(texto_extraido, productos, datos_adicionales)

# Ejecutar flujo con ejemplos
app("facturas/2.jpg", "ordenes_erroneas")
