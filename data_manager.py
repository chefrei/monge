import csv
import os
import json
from datetime import datetime
from constants import *

def asegurar_directorios():
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
    if not os.path.exists(CONFIG_DIR):
        os.makedirs(CONFIG_DIR)
    if not os.path.exists(DIR_FACTURAS_PDF):
        os.makedirs(DIR_FACTURAS_PDF)

def cargar_configuracion():
    config = {
        "nombre_empresa": "Cachapas y Parrilla",
        "razon_social": "Nombre Fiscal C.A.",
        "rif": "J-00000000-0",
        "direccion": "Dirección de la empresa",
        "telefono": "0000-0000000",
        "logo_imagen": "logo.png",
        "logo_ancho": 150,
        "logo_alto": 100
    }
    if os.path.exists(ARCHIVO_CONFIG):
        try:
            with open(ARCHIVO_CONFIG, 'r', encoding='utf-8') as f:
                config.update(json.load(f))
        except Exception:
            pass
    return config

def guardar_inventario(categorias):
    asegurar_directorios()
    with open(ARCHIVO_INVENTARIO, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["Categoria", "Producto", "Precio", "Imagen"])
        for cat, items in categorias.items():
            for nombre, data in items.items():
                if isinstance(data, dict):
                    precio = data.get("precio", 0.0)
                    imagen = data.get("imagen", "")
                else:
                    precio = data
                    imagen = ""
                writer.writerow([cat, nombre, precio, imagen])

def cargar_inventario():
    categorias = {}
    if os.path.exists(ARCHIVO_INVENTARIO):
        try:
            with open(ARCHIVO_INVENTARIO, mode='r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    cat = row["Categoria"]
                    prod = row["Producto"]
                    precio = float(row["Precio"])
                    imagen = row.get("Imagen", "")
                    if cat not in categorias:
                        categorias[cat] = {}
                    categorias[cat][prod] = {"precio": precio, "imagen": imagen}
        except Exception:
            pass
    
    if not categorias:
        categorias = DEFAULT_CATEGORIAS
    
    return categorias

def cargar_clientes():
    clientes = {}
    if os.path.exists(ARCHIVO_CLIENTES):
        try:
            with open(ARCHIVO_CLIENTES, mode='r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    cedula = row["Cedula"]
                    clientes[cedula] = {
                        "Nombre": row["Nombre"],
                        "Direccion": row["Direccion"],
                        "Email": row.get("Email", "")
                    }
        except Exception:
            pass
    return clientes

def guardar_cliente(cedula, nombre, direccion, email=""):
    asegurar_directorios()
    clientes = cargar_clientes()
    clientes[cedula] = {"Nombre": nombre, "Direccion": direccion, "Email": email}
    
    with open(ARCHIVO_CLIENTES, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["Cedula", "Nombre", "Direccion", "Email"])
        for c, data in clientes.items():
            writer.writerow([c, data["Nombre"], data["Direccion"], data.get("Email", "")])

def cargar_historial_ventas(tipo="hoy", fecha_str=None):
    historial = []
    
    if tipo == "hoy":
        import datetime
        if not fecha_str:
            fecha_str = datetime.datetime.now().strftime("%Y-%m-%d")
            
        if os.path.exists(ARCHIVO_VENTAS):
            try:
                with open(ARCHIVO_VENTAS, mode='r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        if row.get('Fecha', '').startswith(fecha_str):
                            txt = f"--- VENTA ---\n{row['Fecha']}\nCliente: {row['Cliente']}\n----------------\n"
                            prods = row['Productos'].split(", ")
                            for p in prods:
                                txt += f"  {p}\n"
                            t_usd = row.get('Total_USD', row.get('Total', '0.0'))
                            t_vef = row.get('Total_VEF', '0.0')
                            txt += f"----------------\nTOTAL: ${t_usd} / {t_vef} Bs.\n----------------"
                            historial.append({
                                "fecha": row['Fecha'],
                                "texto": txt
                            })
            except Exception: pass

    elif tipo in ["cierres_resumen", "cierres_detallado"]:
        if os.path.exists(ARCHIVO_CIERRES):
            try:
                with open(ARCHIVO_CIERRES, mode='r', encoding='utf-8') as f:
                    reader = csv.reader(f)
                    filas = list(reader)
                    for i, row in enumerate(filas):
                        if i == 0: continue # Saltar encabezado
                        if not row: continue
                        
                        if len(row) >= 5:
                            fecha_cierre, num_v, t_usd, t_vef, detalle = row[0], row[1], row[2], row[3], row[4]
                        else:
                            fecha_cierre, num_v, t_usd = row[0], row[1], row[2]
                            t_vef = "0.0"
                            detalle = row[3] if len(row) > 3 else ""
                            
                        if fecha_str and not fecha_cierre.startswith(fecha_str):
                            continue
                            
                        txt = f"=== CIERRE DE CAJA ===\nFecha: {fecha_cierre}\nFacturas Emitidas: {num_v}\nTotal Recaudado: ${t_usd} / {t_vef} Bs.\n"
                        if tipo == "cierres_detallado" and detalle:
                            txt += f"------------------------\nDetalles de Ventas:\n"
                            for item in detalle.split('; '):
                                txt += f"  - {item}\n"
                        txt += "======================"
                        historial.append({
                            "fecha": fecha_cierre,
                            "texto": txt
                        })
            except Exception: pass
            
    return historial

def eliminar_producto(cat, nombre):
    categorias = cargar_inventario()
    if cat in categorias and nombre in categorias[cat]:
        del categorias[cat][nombre]
        if not categorias[cat]:
            del categorias[cat]
        guardar_inventario(categorias)
        return True
    return False

def eliminar_venta(fecha_completa):
    # Validar si ya hay cierre para ese día
    solo_fecha = fecha_completa.split(' ')[0]
    if verificar_cierre_existente(solo_fecha):
        raise Exception("No se puede eliminar una venta de un día ya cerrado.")
        
    if not os.path.exists(ARCHIVO_VENTAS):
        return False
        
    filas_nuevas = []
    encontrado = False
    with open(ARCHIVO_VENTAS, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        for row in reader:
            if row['Fecha'] == fecha_completa:
                encontrado = True
                continue
            filas_nuevas.append(row)
            
    if encontrado:
        with open(ARCHIVO_VENTAS, mode='w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(filas_nuevas)
        return True
    return False

def registrar_venta_csv(fecha, cliente, productos_str, total_usd, tasa_vef):
    asegurar_directorios()
    existe_archivo = os.path.isfile(ARCHIVO_VENTAS)
    
    # Asegurar que el archivo termine con un salto de línea antes de añadir
    if existe_archivo and os.path.getsize(ARCHIVO_VENTAS) > 0:
        with open(ARCHIVO_VENTAS, 'rb+') as f:
            f.seek(-1, os.SEEK_END)
            if f.read(1) != b'\n':
                f.write(b'\n')

    total_vef = total_usd * tasa_vef
    
    # Conseguir el ID (usamos el número de factura como base para el ID)
    # Por ahora simplemente contamos líneas o usamos el número de factura
    # Pero para no complicar, usaremos un "ID" que sea el número de factura actual
    sequence_data = {}
    if os.path.exists(ARCHIVO_SECUENCIA):
        with open(ARCHIVO_SECUENCIA, 'r') as s:
            sequence_data = json.load(s)
    id_venta = sequence_data.get("ultima_factura", 0)

    with open(ARCHIVO_VENTAS, mode='a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        if not existe_archivo:
            writer.writerow(["Fecha", "Cliente", "Productos", "Total_USD", "Tasa_VEF", "Total_VEF", "ID"])
        writer.writerow([fecha, cliente, prods_to_string(productos_str), f"{total_usd:.2f}", f"{tasa_vef:.2f}", f"{total_vef:.2f}", id_venta])

def prods_to_string(productos_list):
    # Auxiliar para formatear la lista de productos para el CSV
    return ", ".join(productos_list)

def registrar_cierre_csv(fecha_str, total_ventas, total_ingreso, detalle_csv, sobreescribir=False):
    asegurar_directorios()
    existe_archivo = os.path.isfile(ARCHIVO_CIERRES)
    
    filas = []
    encabezado = ["Fecha Cierre", "Total Ventas", "Ventas Acumuladas", "Detalle Productos"]
    
    if existe_archivo:
        try:
            with open(ARCHIVO_CIERRES, mode='r', encoding='utf-8') as f:
                reader = csv.reader(f)
                filas = list(reader)
        except Exception:
            pass

    # Si no hay filas o el encabezado es distinto, inicializar
    if not filas:
        filas = [encabezado]

    # Dualidad de Ingresos
    total_ingreso_usd = total_ingreso
    tasa_temp = cargar_configuracion().get("tasa_dolar", 1.0) # Fallback
    total_ingreso_vef = total_ingreso_usd * tasa_temp
    
    nueva_fila = [fecha_str, total_ventas, f"{total_ingreso_usd:.2f}", f"{total_ingreso_vef:.2f}", detalle_csv]
    
    encontrado = False
    if sobreescribir:
        for i, fila in enumerate(filas):
            if i == 0: continue
            # Comparar solo la parte de la fecha (YYYY-MM-DD)
            fecha_fila = fila[0].split(" ")[0]
            if fecha_fila == fecha_str:
                filas[i] = nueva_fila
                encontrado = True
                break
    
    if not encontrado:
        filas.append(nueva_fila)

    with open(ARCHIVO_CIERRES, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerows(filas)

def verificar_cierre_existente(fecha_str):
    if not os.path.exists(ARCHIVO_CIERRES):
        return False
    try:
        with open(ARCHIVO_CIERRES, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                fecha_fila = row["Fecha Cierre"].split(" ")[0]
                if fecha_fila == fecha_str:
                    return True
    except Exception:
        pass
    return False

def obtener_ventas_fecha(fecha_str):
    total_recaudado_usd = 0.0
    total_recaudado_vef = 0.0
    num_ventas = 0
    conteo_fecha = {}
    ventas_detalle = []
    
    if os.path.exists(ARCHIVO_VENTAS):
        try:
            with open(ARCHIVO_VENTAS, mode='r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    fecha_venta = row["Fecha"].split(" ")[0]
                    if fecha_venta == fecha_str:
                        m_usd = float(row.get("Total_USD", row.get("Total", "0.0")))
                        m_vef = float(row.get("Total_VEF", "0.0"))
                        total_recaudado_usd += m_usd
                        total_recaudado_vef += m_vef
                        num_ventas += 1
                        
                        ventas_detalle.append({
                            "fecha": row["Fecha"],
                            "cliente": row["Cliente"],
                            "productos": row["Productos"],
                            "total_usd": m_usd,
                            "total_vef": m_vef,
                            "id": row.get("ID", "0")
                        })
                        
                        prods = row["Productos"].split(", ")
                        for p in prods:
                            if "(" in p and ")" in p:
                                nombre = p.split("(")[0]
                                cant = int(p.split("(")[1].replace(")", ""))
                                conteo_fecha[nombre] = conteo_fecha.get(nombre, 0) + cant
        except Exception as e:
            print(f"Error procesando ventas de la fecha {fecha_str}: {e}")
            
    return total_recaudado_usd, total_recaudado_vef, num_ventas, conteo_fecha, ventas_detalle

def obtener_y_actualizar_secuencia():
    secuencia = 1
    if os.path.exists(ARCHIVO_SECUENCIA):
        try:
            with open(ARCHIVO_SECUENCIA, 'r') as f:
                data = json.load(f)
                secuencia = data.get("ultima_factura", 0) + 1
        except: pass
    
    with open(ARCHIVO_SECUENCIA, 'w') as f:
        json.dump({"ultima_factura": secuencia}, f)
    
    return f"F-{secuencia:05d}"

def generar_texto_ticket(factura_num, fecha, cliente_data, productos_detalle, total_usd, tasa_vef, config):
    total_vef = total_usd * tasa_vef
    txt = f"{config['nombre_empresa']}\n"
    txt += f"{config['razon_social']}\n"
    txt += f"RIF: {config['rif']}\n"
    txt += f"{config['direccion']}\n"
    txt += f"Tel: {config['telefono']}\n"
    txt += "--------------------------------\n"
    txt += f"FACTURA: {factura_num}\n"
    txt += f"FECHA  : {fecha}\n"
    txt += f"CLIENTE: {cliente_data['nombre']}\n"
    txt += f"CI/RIF : {cliente_data['cedula']}\n"
    txt += f"DIR    : {cliente_data['direccion'][:30]}\n"
    txt += "--------------------------------\n"
    for p in productos_detalle:
        txt += f"- {p}\n"
    txt += "--------------------------------\n"
    txt += f"TOTAL USD: ${total_usd:.2f}\n"
    txt += f"TASA VEF : {tasa_vef:.2f}\n"
    txt += f"TOTAL BS : {total_vef:.2f} Bs.\n"
    txt += "--------------------------------\n"
    txt += "¡Gracias por su compra!\n"
    return txt

def generar_html_ticket(factura_num, fecha, cliente_data, productos_detalle, total_usd, tasa_vef, config):
    total_vef = total_usd * tasa_vef
    nombre_empresa = config.get('nombre_empresa', 'Cachapéate')
    razon_social = config.get('razon_social', '')
    rif = config.get('rif', '')
    direccion = config.get('direccion', '')
    telefono = config.get('telefono', '')
    
    logo_html = f'<td width="30%" align="right"><img src="cid:cachapelogo" width="120"></td>'

    html = f"""
    <div style="font-family: helvetica, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; background-color: #fcfcfc;">
        <table width="100%">
            <tr>
                <td width="70%" align="left">
                    <h1><font color="#1A8F5A">{nombre_empresa}</font></h1>
                    <font size="3" color="#555555">
                        {razon_social}<br>
                        RIF: {rif} | Tel: {telefono}<br>
                        {direccion}
                    </font>
                </td>
                {logo_html}
            </tr>
        </table>
        <hr color="#1A8F5A" style="border-top: 2px solid #1A8F5A;">
        <table width="100%">
            <tr>
                <td width="50%">
                    <font size="3">
                    <b>FACTURA:</b> <font color="#1A8F5A">{factura_num}</font><br>
                    <b>FECHA:</b> {fecha}
                    </font>
                </td>
                <td width="50%" align="right">
                    <font size="3">
                    <b>CLIENTE:</b> {cliente_data.get('nombre', '')}<br>
                    <b>CI/RIF:</b> {cliente_data.get('cedula', '')}<br>
                    <b>DIR:</b> {cliente_data.get('direccion', '')[:40]}
                    </font>
                </td>
            </tr>
        </table>
        <br>
        <table width="100%" border="0" cellpadding="5">
            <thead>
                <tr bgcolor="#1A8F5A">
                    <th width="70%" align="left"><font color="#ffffff"><b>Producto</b></font></th>
                    <th width="30%" align="right"><font color="#ffffff"><b>Cant.</b></font></th>
                </tr>
            </thead>
            <tbody>
    """
    
    for i, p in enumerate(productos_detalle):
        bg = "#ffffff" if i % 2 == 0 else "#f1f6f3"
        nombre_prod = p.split('(')[0] if '(' in p else p
        cant_prod = p.split('(')[1].replace(')', '') if '(' in p else '-'
        html += f"""
                <tr bgcolor="{bg}">
                    <td align="left"><font color="#333333">{nombre_prod}</font></td>
                    <td align="right"><font color="#333333">{cant_prod}</font></td>
                </tr>
        """
        
    html += f"""
            </tbody>
        </table>
        <br>
        <table width="100%">
            <tr>
                <td width="50%"></td>
                <td width="50%" align="right">
                    <hr color="#1A8F5A">
                    <font size="4">
                    <b>TOTAL USD:</b> <font color="#1A8F5A">${total_usd:.2f}</font><br>
                    <b>TASA VEF:</b> {tasa_vef:.2f}<br>
                    <b>TOTAL BS:</b> {total_vef:.2f} Bs.
                    </font>
                </td>
            </tr>
        </table>
        <br><br>
        <p align="center"><font color="#1A8F5A" size="5"><b>¡Gracias por su compra!</b></font></p>
    </div>
    """
    return html

def imprimir_ticket(texto_ticket):
    import subprocess
    temp_file = "ticket_temp.txt"
    try:
        with open(temp_file, "w", encoding="utf-8") as f:
            f.write(texto_ticket)
        
        if os.name == 'nt':
            os.startfile(temp_file, "print")
        else:
            # En Linux, intentamos con 'lp'
            res = subprocess.run(["lp", temp_file], capture_output=True, text=True)
            if res.returncode != 0:
                error_msg = res.stderr.lower()
                if "no default destination" in error_msg:
                    raise Exception("No hay una impresora configurada como predeterminada en Linux.\nUse 'lpadmin' o la configuración de su sistema para añadir una.")
                else:
                    raise Exception(res.stderr)
            print(f"Ticket enviado a la cola de impresión de Linux (lp {temp_file})")
    except Exception as e:
        print(f"Error al imprimir: {e}")
        # Re-lanzamos para que la UI pueda atraparlo si es necesario, 
        # o simplemente lo dejamos en consola como estaba.
        raise e

def generar_pdf_ticket(factura_num, fecha, cliente_data, productos_detalle, total_usd, tasa_vef, config):
    from fpdf import FPDF
    asegurar_directorios()
    pdf_path = os.path.join(DIR_FACTURAS_PDF, f"Factura_{factura_num.replace('-', '_')}.pdf")
    
    class PDF(FPDF):
        def footer(self):
            self.set_y(-15)
            self.set_font("helvetica", "I", 8)
            self.set_text_color(26, 143, 90)
            self.cell(0, 10, align="C", txt="¡Gracias por su compra en Cachapéate!")

    pdf = PDF()
    pdf.add_page()
    
    # Colores
    color_green = (26, 143, 90)
    color_dark = (51, 51, 51)
    color_gray = (85, 85, 85)
    
    # 1. Top Section (Company & Logo)
    nombre_empresa = config.get('nombre_empresa', 'Cachapéate')
    razon_social = config.get('razon_social', '')
    rif = config.get('rif', '')
    direccion = config.get('direccion', '')
    telefono = config.get('telefono', '')
    
    pdf.set_font("helvetica", "B", 20)
    pdf.set_text_color(*color_green)
    pdf.cell(120, 10, txt=nombre_empresa, ln=1)
    
    pdf.set_font("helvetica", "", 10)
    pdf.set_text_color(*color_gray)
    pdf.cell(120, 5, txt=razon_social, ln=1)
    pdf.cell(120, 5, txt=f"RIF: {rif} | Tel: {telefono}", ln=1)
    pdf.cell(120, 5, txt=direccion[:60], ln=1)
    
    # 2. Logo (Superior Derecha)
    logo_ruta = os.path.join("static", "images", "products", "cachapeate_logo.png")
    if os.path.exists(logo_ruta):
        # Position logo at right (x=150) and force Y downward to clear it
        pdf.image(logo_ruta, x=150, y=10, w=40)
    
    # Assure we are painting the line below the logo's height (y=55)
    if pdf.get_y() < 55:
        pdf.set_y(55)
    
    pdf.set_draw_color(*color_green)
    pdf.set_line_width(0.5)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(5)
    
    # 3. Invoice details
    pdf.set_font("helvetica", "B", 10)
    pdf.set_text_color(*color_dark)
    pdf.cell(90, 5, txt="FACTURA:", align="L")
    pdf.cell(100, 5, txt="CLIENTE:", align="R", ln=1)
    
    pdf.set_font("helvetica", "", 10)
    pdf.set_text_color(*color_gray)
    pdf.cell(90, 5, txt=factura_num, align="L")
    pdf.cell(100, 5, txt=cliente_data.get('nombre', '')[:40], align="R", ln=1)
    
    pdf.set_font("helvetica", "B", 10)
    pdf.set_text_color(*color_dark)
    pdf.cell(90, 5, txt="FECHA:", align="L")
    pdf.set_font("helvetica", "", 10)
    pdf.set_text_color(*color_gray)
    pdf.cell(100, 5, txt=f"CI/RIF: {cliente_data.get('cedula', '')}", align="R", ln=1)
    
    pdf.cell(90, 5, txt=fecha, align="L")
    pdf.cell(100, 5, txt=f"DIR: {cliente_data.get('direccion', '')[:40]}", align="R", ln=1)
    
    pdf.ln(10)
    
    # 4. Table Header
    pdf.set_font("helvetica", "B", 11)
    pdf.set_fill_color(*color_green)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(140, 8, txt=" Producto", border=0, fill=True, align="L")
    pdf.cell(50, 8, txt="Cant.", border=0, fill=True, align="R", ln=1)
    
    # 5. Table Body
    pdf.set_font("helvetica", "", 10)
    for i, p in enumerate(productos_detalle):
        if i % 2 == 0:
            pdf.set_fill_color(255, 255, 255)
        else:
            pdf.set_fill_color(241, 246, 243)
        pdf.set_text_color(*color_dark)
        nombre_prod = p.split('(')[0] if '(' in p else p
        cant_prod = p.split('(')[1].replace(')', '') if '(' in p else '-'
        pdf.cell(140, 8, txt=f" {nombre_prod}", border=0, fill=True, align="L")
        pdf.cell(50, 8, txt=f"{cant_prod} ", border=0, fill=True, align="R", ln=1)
        
    pdf.ln(10)
    
    # 6. Totals
    # Draw horizontal line above totals
    pdf.set_draw_color(*color_green)
    pdf.line(100, pdf.get_y(), 190, pdf.get_y())
    pdf.ln(2)
    
    total_vef = total_usd * tasa_vef
    pdf.set_font("helvetica", "B", 12)
    pdf.cell(100, 6, txt="", align="L")
    pdf.set_text_color(*color_dark)
    pdf.cell(40, 6, txt="TOTAL USD:", align="R")
    pdf.set_text_color(*color_green)
    pdf.cell(50, 6, txt=f"${total_usd:.2f}", align="R", ln=1)
    
    pdf.set_font("helvetica", "", 10)
    pdf.cell(100, 6, txt="", align="L")
    pdf.set_text_color(*color_dark)
    pdf.cell(40, 6, txt="TASA VEF:", align="R")
    pdf.cell(50, 6, txt=f"{tasa_vef:.2f}", align="R", ln=1)
    
    pdf.cell(100, 6, txt="", align="L")
    pdf.cell(40, 6, txt="TOTAL BS:", align="R")
    pdf.cell(50, 6, txt=f"{total_vef:.2f} Bs.", align="R", ln=1)

    pdf.output(pdf_path)
    return pdf_path

def enviar_email_ticket(destinatario, pdf_path, factura_num, config, html_body=None):
    import smtplib
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText
    from email.mime.base import MIMEBase
    from email import encoders

    server = config.get("smtp_server")
    port = config.get("smtp_port", 587)
    user = config.get("smtp_user")
    pwd = config.get("smtp_password")

    if not all([server, user, pwd]):
        return False, "Configuración de correo incompleta en settings.json"

    try:
        msg = MIMEMultipart()
        msg['From'] = user
        msg['To'] = destinatario
        msg['Subject'] = f"Factura Digital {factura_num} - {config['nombre_empresa']}"

        if html_body:
            cuerpo = html_body
            msg.attach(MIMEText(cuerpo, 'html'))
            
            # Attach inline logo so it displays cleanly in Gmail/Outlook
            from email.mime.image import MIMEImage
            logo_path = os.path.join("static", "images", "products", "cachapeate_logo.png")
            if os.path.exists(logo_path):
                with open(logo_path, 'rb') as img_file:
                    msg_img = MIMEImage(img_file.read())
                    msg_img.add_header('Content-ID', '<cachapelogo>')
                    msg_img.add_header('Content-Disposition', 'inline')
                    msg.attach(msg_img)
        else:
            cuerpo = f"""
            <html>
            <body>
                <h3>Gracias por su compra en {config['nombre_empresa']}</h3>
                <p>Adjunto encontrará su factura digital número <b>{factura_num}</b>.</p>
                <p>Saludos cordiales,<br>El equipo de {config['nombre_empresa']}</p>
            </body>
            </html>
            """
            msg.attach(MIMEText(cuerpo, 'html'))

        # Adjuntar PDF
        with open(pdf_path, "rb") as attachment:
            part = MIMEBase("application", "octet-stream")
            part.set_payload(attachment.read())
            encoders.encode_base64(part)
            part.add_header("Content-Disposition", f"attachment; filename= {os.path.basename(pdf_path)}")
            msg.attach(part)

        # Enviar
        with smtplib.SMTP(server, port, timeout=10) as server_conn:
            server_conn.starttls()
            server_conn.login(user, pwd)
            server_conn.send_message(msg)
        
        return True, "Enviado con éxito"
    except smtplib.SMTPConnectError:
        return False, "Error de conexión con el servidor SMTP. Verifique servidor y puerto."
    except smtplib.SMTPAuthenticationError:
        return False, "Error de autenticación. Verifique su Correo y Contraseña de Aplicación."
    except Exception as e:
        err_str = str(e)
        if "name resolution" in err_str.lower():
            return False, "Error de DNS: No se pudo encontrar el servidor smtp.gmail.com.\nVerifique su conexión a internet o DNS."
        return False, err_str
