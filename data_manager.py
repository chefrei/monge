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
        writer.writerow(["Categoria", "Producto", "Precio"])
        for cat, items in categorias.items():
            for nombre, precio in items.items():
                writer.writerow([cat, nombre, precio])

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
                    if cat not in categorias:
                        categorias[cat] = {}
                    categorias[cat][prod] = precio
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

def cargar_historial_ventas():
    historial = []
    if os.path.exists(ARCHIVO_VENTAS):
        try:
            with open(ARCHIVO_VENTAS, mode='r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    txt = f"--- FACTURA ---\n{row['Fecha']}\nCliente: {row['Cliente']}\n----------------\n"
                    prods = row['Productos'].split(", ")
                    for p in prods:
                        txt += f"- {p}\n"
                    t_usd = row.get('Total_USD', row.get('Total', '0.0'))
                    t_vef = row.get('Total_VEF', '0.0')
                    txt += f"----------------\nTOTAL: ${t_usd} / {t_vef} Bs.\n----------------"
                    historial.append(txt)
        except Exception:
            pass
    return historial

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
    tasa_temp = data_manager.cargar_configuracion().get("tasa_dolar", 1.0) # Fallback
    total_ingreso_vef = total_ingreso_usd * tasa_temp
    
    nueva_fila = [fecha_str, total_ventas, f"{total_ingreso_usd:.2f}", f"{total_ingreso_vef:.2f}", detalle_csv]
    
    encontrado = False
    if sobreescribir:
        for i, fila in enumerate(filas):
            if i == 0: continue
            # Comparar solo la parte de la fecha (YYYY-MM-DD)
            fecha_fila = fila[0].split(" ")[0]
            if fecha_fila == fecha_buscada:
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

def generar_pdf_ticket(texto_ticket, factura_num):
    from fpdf import FPDF
    asegurar_directorios()
    pdf_path = os.path.join(DIR_FACTURAS_PDF, f"Factura_{factura_num.replace('-', '_')}.pdf")
    
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Courier", size=10)
    
    # Escribir el texto línea por línea
    lineas = texto_ticket.split('\n')
    for linea in lineas:
        pdf.cell(200, 5, txt=linea, ln=True, align='L')
    
    pdf.output(pdf_path)
    return pdf_path

def enviar_email_ticket(destinatario, pdf_path, factura_num, config):
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
