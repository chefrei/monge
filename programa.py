import tkinter as tk
from tkinter import messagebox, simpledialog, PhotoImage, ttk
import os
from datetime import datetime
from constants import *
import data_manager

# Intento de importar Pillow para mejor manejo de imágenes
try:
    from PIL import Image, ImageTk
    HAS_PILLOW = True
except ImportError:
    HAS_PILLOW = False

# --- Variables globales ---
categorias = {}
historial_facturas = []
indice_historial = -1
config = {}

# --- Funciones de Lógica ---
def actualizar_navegacion(nuevo_indice):
    global indice_historial
    if not historial_facturas:
        return
    indice_historial = nuevo_indice
    factura_label.config(text=historial_facturas[indice_historial])
    lbl_pag.config(text=f"{indice_historial + 1} / {len(historial_facturas)}")
    
    btn_ant.config(state=tk.NORMAL if indice_historial > 0 else tk.DISABLED)
    btn_sig.config(state=tk.NORMAL if indice_historial < len(historial_facturas) - 1 else tk.DISABLED)

def anterior_factura():
    if indice_historial > 0:
        actualizar_navegacion(indice_historial - 1)

def siguiente_factura():
    if indice_historial < len(historial_facturas) - 1:
        actualizar_navegacion(indice_historial + 1)

def obtener_precio(nombre):
    for cat in categorias.values():
        if nombre in cat:
            return cat[nombre]
    return 0

def agregar_producto(nombre):
    cantidad = simpledialog.askinteger("Cantidad", f"¿Cuántas {nombre}?", minvalue=1)
    if cantidad:
        subtotal = obtener_precio(nombre) * cantidad
        ticket_listbox.insert(tk.END, f"{nombre} x {cantidad} = ${subtotal:.2f}")
        actualizar_total()

def actualizar_total():
    tasa = config.get("tasa_dolar", 1.0)
    total_usd = sum([obtener_precio(item.split(" x ")[0]) * int(item.split(" x ")[1].split(" = ")[0])
                 for item in ticket_listbox.get(0, tk.END)])
    total_vef = total_usd * tasa
    total_var.set(f"${total_usd:.2f} / {total_vef:.2f} Bs.")

def eliminar_item():
    selected = ticket_listbox.curselection()
    if selected:
        ticket_listbox.delete(selected)
        actualizar_total()
    else:
        messagebox.showwarning("Atención", "Seleccione un producto para eliminar.")

def cobrar():
    items = ticket_listbox.get(0, tk.END)
    if not items:
        messagebox.showwarning("Atención", "No hay productos en el ticket.")
        return

    # Ventana modal de cobro
    ventana_cobro = tk.Toplevel(root)
    ventana_cobro.title("Finalizar Venta - Datos del Cliente")
    ventana_cobro.geometry("450x400")
    ventana_cobro.grab_set()
    
    dict_clientes = data_manager.cargar_clientes()
    lista_cedulas = list(dict_clientes.keys())
    
    tk.Label(ventana_cobro, text="DATOS DEL CLIENTE", font=("Arial", 12, "bold")).pack(pady=10)
    
    tk.Label(ventana_cobro, text="Cédula / RIF:").pack()
    cedula_var = tk.StringVar()
    cb_cedula = ttk.Combobox(ventana_cobro, textvariable=cedula_var, values=lista_cedulas, width=30)
    cb_cedula.pack(pady=5)
    
    tk.Label(ventana_cobro, text="Nombre / Razón Social:").pack()
    nombre_var = tk.StringVar()
    ent_nombre = tk.Entry(ventana_cobro, textvariable=nombre_var, width=33)
    ent_nombre.pack(pady=5)
    
    tk.Label(ventana_cobro, text="Dirección Fiscal:").pack()
    dir_var = tk.StringVar()
    ent_dir = tk.Entry(ventana_cobro, textvariable=dir_var, width=33)
    ent_dir.pack(pady=5)
    
    tk.Label(ventana_cobro, text="Correo Electrónico:").pack()
    email_var = tk.StringVar()
    ent_email = tk.Entry(ventana_cobro, textvariable=email_var, width=33)
    ent_email.pack(pady=5)
    
    def on_cedula_change(event):
        c = cedula_var.get()
        if c in dict_clientes:
            nombre_var.set(dict_clientes[c]["Nombre"])
            dir_var.set(dict_clientes[c]["Direccion"])
            email_var.set(dict_clientes[c].get("Email", ""))
            
    cb_cedula.bind("<<ComboboxSelected>>", on_cedula_change)
    cb_cedula.bind("<FocusOut>", on_cedula_change)

    total_usd = sum([obtener_precio(item.split(" x ")[0]) * int(item.split(" x ")[1].split(" = ")[0])
                 for item in items])
    tasa_actual = config.get("tasa_dolar", 1.0)
    total_vef = total_usd * tasa_actual
    
    lbl_total = tk.Label(ventana_cobro, text=f"TOTAL A PAGAR: ${total_usd:.2f} / {total_vef:.2f} Bs.", 
                         font=("Arial", 11, "bold"), fg=SUCCESS_GREEN)
    lbl_total.pack(pady=20)

    def confirmar_pago():
        cedula = cedula_var.get().strip()
        nombre = nombre_var.get().strip()
        direccion = dir_var.get().strip()
        email = email_var.get().strip()
        
        if not cedula or not nombre:
            messagebox.showerror("Error", "Cédula y Nombre son obligatorios.", parent=ventana_cobro)
            return
            
        data_manager.guardar_cliente(cedula, nombre, direccion, email)
        
        fecha_hoy = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        prods_detalle = []
        for item in items:
            n = item.split(" x ")[0]
            c = item.split(" x ")[1].split(" = ")[0]
            prods_detalle.append(f"{n}({c})")
            
        num_factura = data_manager.obtener_y_actualizar_secuencia()
        cliente_data = {"cedula": cedula, "nombre": nombre, "direccion": direccion, "email": email}
        
        data_manager.registrar_venta_csv(fecha_hoy, nombre, prods_detalle, total_usd, tasa_actual)
        ticket_texto = data_manager.generar_texto_ticket(num_factura, fecha_hoy, cliente_data, prods_detalle, total_usd, tasa_actual, config)
        
        # Generar PDF automáticamente
        pdf_path = data_manager.generar_pdf_ticket(ticket_texto, num_factura)
        
        messagebox.showinfo("Éxito", f"Venta Realizada.\nFactura: {num_factura}\nPDF guardado en data/facturas_pdf", parent=ventana_cobro)
        
        if messagebox.askyesno("Imprimir", "¿Desea imprimir el ticket físico?", parent=ventana_cobro):
            try:
                data_manager.imprimir_ticket(ticket_texto)
            except Exception as e:
                messagebox.showerror("Error de Impresión", str(e), parent=ventana_cobro)
            
        if email and messagebox.askyesno("Email", f"¿Enviar factura a {email}?", parent=ventana_cobro):
            exito, msg = data_manager.enviar_email_ticket(email, pdf_path, num_factura, config)
            if exito:
                messagebox.showinfo("Email Enviado", "La factura ha sido enviada correctamente.", parent=ventana_cobro)
            else:
                messagebox.showerror("Error Email", f"No se pudo enviar: {msg}\nVerifique configuración en settings.json", parent=ventana_cobro)
            
        historial_facturas.append(ticket_texto)
        actualizar_navegacion(len(historial_facturas)-1)
        
        ticket_listbox.delete(0, tk.END)
        actualizar_total()
        ventana_cobro.destroy()

    tk.Button(ventana_cobro, text="CONFIRMAR Y FACTURAR", bg=SUCCESS_GREEN, fg=WHITE, 
              font=("Arial", 10, "bold"), command=confirmar_pago, width=25).pack(pady=10)

def cierre_dia():
    hoy_defecto = datetime.now().strftime("%d-%m-%Y")
    fecha_input = simpledialog.askstring("Fecha de Cierre", f"Ingrese la fecha a cerrar (DD-MM-AAAA):", initialvalue=hoy_defecto)
    
    if not fecha_input: return
    
    try:
        # Validar formato y convertir a YYYY-MM-DD para la lógica interna
        fecha_obj = datetime.strptime(fecha_input, "%d-%m-%Y")
        fecha_str = fecha_obj.strftime("%Y-%m-%d")
    except ValueError:
        messagebox.showerror("Error", "Formato de fecha inválido. Use DD-MM-AAAA.")
        return

    sobreescribir = False
    if data_manager.verificar_cierre_existente(fecha_str):
        if messagebox.askyesno("Cierre Existente", f"Ya existe un cierre para el {fecha_input}.\n\n¿Desea SOBREESCRIBIRLO con los datos actuales?"):
            sobreescribir = True
        else:
            return

    t_usd, t_vef, num_ventas, conteo_fecha, ventas_detalle = data_manager.obtener_ventas_fecha(fecha_str)
    
    if num_ventas == 0:
        messagebox.showwarning("Atención", f"No se han registrado ventas para el día {fecha_input}.")
        return
    
    detalle_csv = "; ".join([f"{nombre}: {cantidad}" for nombre, cantidad in conteo_fecha.items()])
    data_manager.registrar_cierre_csv(fecha_str, num_ventas, t_usd, detalle_csv, sobreescribir=sobreescribir)
    
    # Reporte Detallado
    resumen = f"--- CIERRE DE CAJA ({fecha_input}) ---\n"
    resumen += f"Cant. Facturas: {num_ventas}\n"
    resumen += f"Total USD: ${t_usd:.2f}\n"
    resumen += f"Total VEF: {t_vef:.2f} Bs.\n"
    resumen += f"-----------------------\n"
    resumen += "RESUMEN PRODUCTOS:\n"
    for nombre, cantidad in conteo_fecha.items():
        resumen += f"- {nombre}: {cantidad}\n"
        
    messagebox.showinfo("Cierre Exitoso", resumen)
    if messagebox.askyesno("Reporte", "¿Desea ver el reporte detallado?"):
        mostrar_reporte_detallado(fecha_input, ventas_detalle)

def mostrar_reporte_detallado(fecha_display, ventas_detalle):
    ventana_det = tk.Toplevel(root)
    ventana_det.title(f"Ventas del {fecha_display}")
    ventana_det.geometry("600x650")
    
    txt_area = tk.Text(ventana_det, wrap=tk.NONE, font=("Courier", 9))
    txt_area.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    reporte = f"REPORTE DE VENTAS - {fecha_display}\n"
    reporte += "="*50 + "\n"
    for v in ventas_detalle:
        reporte += f"ID: {v['id']:<5} | HORA: {v['fecha'].split(' ')[1]} | {v['cliente'][:12]:<12}\n"
        reporte += f"USD: ${v['total_usd']:>7.2f} | VES: {v['total_vef']:>10.2f} Bs.\n"
        reporte += f"PRODUCTOS: {v['productos']}\n"
        reporte += "-"*50 + "\n"
    
    txt_area.insert(tk.END, reporte)
    txt_area.config(state=tk.DISABLED)

    def imprimir_con_error():
        try:
            data_manager.imprimir_ticket(reporte)
        except Exception as e:
            messagebox.showerror("Error de Impresión", str(e), parent=ventana_det)

    tk.Button(ventana_det, text="IMPRIMIR REPORTE", command=imprimir_con_error).pack(pady=5)

def actualizar_tasa():
    nueva_tasa = simpledialog.askfloat("Tasa Cambiaria", "Ingrese la tasa del dólar hoy (Bs.):", initialvalue=config.get("tasa_dolar", 1.0))
    if nueva_tasa:
        config["tasa_dolar"] = nueva_tasa
        with open(ARCHIVO_CONFIG, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4)
        actualizar_total()
        messagebox.showinfo("Tasa Actualizada", f"Nueva tasa: {nueva_tasa} Bs.")

def configurar_email():
    ventana_mail = tk.Toplevel(root)
    ventana_mail.title("Configuración de Correo (SMTP)")
    ventana_mail.geometry("400x450")
    
    tk.Label(ventana_mail, text="CONFIGURACIÓN DE ENVÍO", font=("Arial", 12, "bold")).pack(pady=10)
    
    campos = [
        ("Servidor SMTP (ej: smtp.gmail.com)", "smtp_server"),
        ("Puerto (ej: 587)", "smtp_port"),
        ("Usuario/Email Emisor", "smtp_user"),
        ("Contraseña de Aplicación", "smtp_password")
    ]
    
    entries = {}
    for label_text, key in campos:
        tk.Label(ventana_mail, text=label_text).pack(pady=(5,0))
        var = tk.StringVar(value=config.get(key, ""))
        ent = tk.Entry(ventana_mail, textvariable=var, width=40)
        if key == "smtp_password": ent.config(show="*")
        ent.pack(pady=5)
        entries[key] = var

    tk.Label(ventana_mail, text="Nota: Para Gmail, usa una 'Contraseña de Aplicación'.", 
             font=("Arial", 8, "italic"), fg="gray").pack(pady=5)

    def guardar_mail():
        for key, var in entries.items():
            val = var.get().strip()
            if key == "smtp_port":
                try: val = int(val)
                except: val = 587
            config[key] = val
            
        with open(ARCHIVO_CONFIG, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4)
        messagebox.showinfo("Configuración", "Datos de correo guardados con éxito.")
        ventana_mail.destroy()

    def probar_conexion():
        # Crear config temporal para la prueba
        temp_config = config.copy()
        for key, var in entries.items():
            val = var.get().strip()
            if key == "smtp_port":
                try: val = int(val)
                except: val = 587
            temp_config[key] = val
        
        # Generar un PDF ficticio para la prueba si no existe
        dummy_pdf = "data/test_factura.pdf"
        if not os.path.exists("data"): os.makedirs("data")
        with open(dummy_pdf, "w") as f: f.write("Prueba de PDF")
        
        exito, msg = data_manager.enviar_email_ticket(temp_config["smtp_user"], dummy_pdf, "PRUEBA-001", temp_config)
        if exito:
            messagebox.showinfo("Éxito", "¡Conexión exitosa! El correo de prueba fue enviado a ti mismo.", parent=ventana_mail)
        else:
            messagebox.showerror("Error", f"Fallo en la conexión:\n{msg}", parent=ventana_mail)

    btn_frame = tk.Frame(ventana_mail)
    btn_frame.pack(pady=20)
    
    tk.Button(btn_frame, text="GUARDAR", bg=ADMIN_BLUE, fg=WHITE, width=15,
              command=guardar_mail).pack(side=tk.LEFT, padx=5)
    
    tk.Button(btn_frame, text="PROBAR ENVÍO", bg=SUCCESS_GREEN, fg=WHITE, width=15,
              command=probar_conexion).pack(side=tk.LEFT, padx=5)

def consultar_ventas_dia():
    hoy_defecto = datetime.now().strftime("%d-%m-%Y")
    fecha_input = simpledialog.askstring("Consultar Día", "Fecha (DD-MM-AAAA):", initialvalue=hoy_defecto)
    if not fecha_input: return
    try:
        f_obj = datetime.strptime(fecha_input, "%d-%m-%Y")
        f_str = f_obj.strftime("%Y-%m-%d")
        _, _, num_v, _, v_det = data_manager.obtener_ventas_fecha(f_str)
        if num_v == 0:
            messagebox.showinfo("Sin ventas", "No hay ventas registradas para este día.")
        else:
            mostrar_reporte_detallado(fecha_input, v_det)
    except:
        messagebox.showerror("Error", "Fecha inválida.")

def agregar_nuevo_producto():
    ventana_prod = tk.Toplevel(root)
    ventana_prod.title("Gestionar Inventario")
    ventana_prod.geometry("400x380")
    ventana_prod.grab_set() # Hacerla modal
    
    tk.Label(ventana_prod, text="CATEGORÍA:", font=("Arial", 10, "bold")).pack(pady=(10, 0))
    cat_var = tk.StringVar()
    lista_categorias = list(categorias.keys()) + ["+ Nueva Categoría..."]
    cb_cat = ttk.Combobox(ventana_prod, textvariable=cat_var, values=lista_categorias, state="readonly", width=35)
    cb_cat.pack(pady=5)
    
    lbl_nueva_cat = tk.Label(ventana_prod, text="Nombre nueva categoría:")
    entry_nueva_cat = tk.Entry(ventana_prod, width=38)
    
    def on_cat_change(event):
        if cat_var.get() == "+ Nueva Categoría...":
            lbl_nueva_cat.pack(pady=(5, 0))
            entry_nueva_cat.pack(pady=5)
            cb_prod.config(values=["+ Nuevo Producto..."])
            prod_var.set("+ Nuevo Producto...")
            on_prod_change(None)
        else:
            lbl_nueva_cat.pack_forget()
            entry_nueva_cat.pack_forget()
            # Cargar productos de esa categoría
            prods = list(categorias[cat_var.get()].keys()) + ["+ Nuevo Producto..."]
            cb_prod.config(values=prods)
            prod_var.set("+ Nuevo Producto...")
            on_prod_change(None)
            
    cb_cat.bind("<<ComboboxSelected>>", on_cat_change)
    
    tk.Label(ventana_prod, text="PRODUCTO:", font=("Arial", 10, "bold")).pack(pady=(10, 0))
    prod_var = tk.StringVar()
    cb_prod = ttk.Combobox(ventana_prod, textvariable=prod_var, values=["+ Nuevo Producto..."], state="readonly", width=35)
    cb_prod.pack(pady=5)
    
    lbl_nuevo_prod = tk.Label(ventana_prod, text="Nombre del producto:")
    entry_nuevo_prod = tk.Entry(ventana_prod, width=38)
    
    def on_prod_change(event):
        if prod_var.get() == "+ Nuevo Producto...":
            lbl_nuevo_prod.pack(pady=(5, 0))
            entry_nuevo_prod.pack(pady=5)
            precio_var.set("0.0")
        else:
            lbl_nuevo_prod.pack_forget()
            entry_nuevo_prod.pack_forget()
            # Cargar precio actual
            precio_actual = categorias[cat_var.get()][prod_var.get()]
            precio_var.set(str(precio_actual))
            
    cb_prod.bind("<<ComboboxSelected>>", on_prod_change)
    
    tk.Label(ventana_prod, text="PRECIO ($):", font=("Arial", 10, "bold")).pack(pady=(10, 0))
    precio_var = tk.StringVar(value="0.0")
    tk.Entry(ventana_prod, textvariable=precio_var, width=15).pack(pady=5)
    
    def guardar():
        # Validar categoría
        cat_final = ""
        if cat_var.get() == "+ Nueva Categoría...":
            cat_final = entry_nueva_cat.get().strip().capitalize()
            if not cat_final:
                messagebox.showerror("Error", "Ingrese el nombre de la nueva categoría.", parent=ventana_prod)
                return
        else:
            cat_final = cat_var.get()
            if not cat_final:
                messagebox.showerror("Error", "Seleccione una categoría.", parent=ventana_prod)
                return
                
        # Validar producto
        prod_final = ""
        if prod_var.get() == "+ Nuevo Producto...":
            prod_final = entry_nuevo_prod.get().strip()
            if not prod_final:
                messagebox.showerror("Error", "Ingrese el nombre del producto.", parent=ventana_prod)
                return
        else:
            prod_final = prod_var.get()
            
        # Validar precio
        try:
            precio_final = float(precio_var.get())
        except ValueError:
            messagebox.showerror("Error", "El precio debe ser un número.", parent=ventana_prod)
            return
            
        # Guardar
        if cat_final not in categorias:
            categorias[cat_final] = {}
        categorias[cat_final][prod_final] = precio_final
        
        data_manager.guardar_inventario(categorias)
        actualizar_botones()
        messagebox.showinfo("Guardado", f"Producto '{prod_final}' guardado en '{cat_final}'.", parent=ventana_prod)
        ventana_prod.destroy()

    tk.Button(ventana_prod, text="GUARDAR CAMBIOS", bg=SUCCESS_GREEN, fg=WHITE, font=("Arial", 10, "bold"), command=guardar).pack(pady=20)
    on_prod_change(None) # Inicializar vista ocultando extras

def eliminar_producto_inventario():
    productos_lista = [f"{cat} - {p}" for cat, it in categorias.items() for p in it]
    if not productos_lista: return
    
    ventana_eliminar = tk.Toplevel(root)
    ventana_eliminar.title("Eliminar del Inventario")
    lb = tk.Listbox(ventana_eliminar, width=40, height=15)
    lb.pack(pady=5, padx=10)
    for p in productos_lista: lb.insert(tk.END, p)
        
    def confirmar():
        sel = lb.curselection()
        if not sel: return
        cat_sel, prod_sel = lb.get(sel).split(" - ")
        if messagebox.askyesno("Confirmar", f"¿Eliminar {prod_sel}?", parent=ventana_eliminar):
            del categorias[cat_sel][prod_sel]
            if not categorias[cat_sel]: del categorias[cat_sel]
            data_manager.guardar_inventario(categorias)
            actualizar_botones()
            ventana_eliminar.destroy()
            
    tk.Button(ventana_eliminar, text="ELIMINAR", bg=DANGER_RED, fg=WHITE, command=confirmar).pack(pady=10)

def actualizar_botones():
    for widget in scrollable_frame.winfo_children(): widget.destroy()
    num_cols = 3
    for c in range(num_cols): scrollable_frame.grid_columnconfigure(c, weight=1)

    row = 0
    for cat, items in categorias.items():
        tk.Label(scrollable_frame, text=cat.upper(), font=("Arial", 12, "bold"), bg=BG_COLOR, pady=10).grid(row=row, column=0, columnspan=num_cols, sticky="ew")
        row += 1
        col = 0
        for nombre in items:
            btn = tk.Button(scrollable_frame, text=f"{nombre}\n${items[nombre]:.2f}", width=18, height=2, bg=WHITE, command=lambda n=nombre: agregar_producto(n))
            btn.grid(row=row, column=col, padx=10, pady=5, sticky="nsew")
            col += 1
            if col >= num_cols:
                col = 0
                row += 1
        if col != 0: row += 1
    
    canvas.update_idletasks()
    canvas.config(scrollregion=canvas.bbox("all"))

# --- Inicialización de Interfaz ---
root = tk.Tk()
config = data_manager.cargar_configuracion()
root.title(f"POS Profesional - {config['nombre_empresa']}")
root.geometry("1400x800")
root.configure(bg=BG_COLOR)

# Header
header_frame = tk.Frame(root, bg=WHITE, height=config['logo_alto'] + 20)
header_frame.pack(fill=tk.X, padx=10, pady=5)

logo_path = os.path.join(CONFIG_DIR, config['logo_imagen'])
if os.path.exists(logo_path):
    try:
        if HAS_PILLOW:
            img = Image.open(logo_path).resize((config['logo_ancho'], config['logo_alto']), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(img)
        else:
            photo = tk.PhotoImage(file=logo_path)
        lbl = tk.Label(header_frame, image=photo, bg=WHITE)
        lbl.image = photo
        lbl.pack(side=tk.LEFT, padx=20)
    except: pass

tk.Label(header_frame, text=config['nombre_empresa'], font=("Arial", 28, "bold"), bg=WHITE, fg="#333").pack(side=tk.LEFT, padx=20)

# Zona Izquierda: Productos
frame_izq = tk.Frame(root, bg=BG_COLOR)
frame_izq.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
canvas = tk.Canvas(frame_izq, bg=BG_COLOR, highlightthickness=0)
scrollbar = tk.Scrollbar(frame_izq, orient="vertical", command=canvas.yview)
scrollable_frame = tk.Frame(canvas, bg=BG_COLOR)
scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
canvas.configure(yscrollcommand=scrollbar.set)
canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

def _on_mousewheel(event):
    move = -1*(event.delta/120) if event.delta else (1 if event.num==5 else -1)
    canvas.yview_scroll(int(move), "units")

canvas.bind_all("<MouseWheel>", _on_mousewheel)
canvas.bind_all("<Button-4>", _on_mousewheel)
canvas.bind_all("<Button-5>", _on_mousewheel)

# Zona Central: Ticket
frame_cen = tk.Frame(root, bg=WHITE, bd=2, relief=tk.SUNKEN)
frame_cen.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)
tk.Label(frame_cen, text="CUENTA ACTUAL", font=("Arial", 14, "bold"), bg=ACCENT_BLUE).pack(fill=tk.X, pady=(0, 10))
ticket_listbox = tk.Listbox(frame_cen, width=35, height=20, font=("Arial", 10))
ticket_listbox.pack(pady=5, padx=10)
total_var = tk.StringVar(value="$0.00")
tk.Label(frame_cen, text="TOTAL A PAGAR", font=("Arial", 12, "bold"), bg=WHITE).pack()
tk.Label(frame_cen, textvariable=total_var, font=("Arial", 20, "bold"), bg=WHITE, fg=SUCCESS_GREEN).pack(pady=5)
tk.Button(frame_cen, text="ELIMINAR DEL TICKET", width=25, height=2, bg=WARNING_ORANGE, fg=WHITE, font=("Arial", 10, "bold"), command=eliminar_item).pack(pady=5)
tk.Button(frame_cen, text="COBRAR AHORA", width=25, height=3, bg=SUCCESS_GREEN, fg=WHITE, font=("Arial", 12, "bold"), command=cobrar).pack(pady=10)

# Zona Derecha: Historial
frame_der = tk.Frame(root, bg="#f5f5f5", bd=2, relief=tk.GROOVE)
frame_der.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)
tk.Label(frame_der, text="HISTORIAL DE VENTAS", font=("Arial", 12, "bold"), bg="#eeeeee").pack(fill=tk.X, pady=(0, 5))
factura_label = tk.Label(frame_der, text="Ninguna venta realizada", font=("Courier", 9), bg=TICKET_YELLOW, justify=tk.LEFT, anchor="nw", relief=tk.SOLID, bd=1, width=32, height=15)
factura_label.pack(pady=5, padx=10)
frame_nav = tk.Frame(frame_der, bg="#f5f5f5")
frame_nav.pack(fill=tk.X, padx=10)
btn_ant = tk.Button(frame_nav, text="< Anterior", command=anterior_factura, state=tk.DISABLED)
btn_ant.pack(side=tk.LEFT, expand=True, padx=2)
lbl_pag = tk.Label(frame_nav, text="0 / 0", bg="#f5f5f5", font=("Arial", 10))
lbl_pag.pack(side=tk.LEFT, expand=True)
btn_sig = tk.Button(frame_nav, text="Siguiente >", command=siguiente_factura, state=tk.DISABLED)
btn_sig.pack(side=tk.LEFT, expand=True, padx=2)
tk.Label(frame_der, text="--- ADMINISTRACIÓN ---", font=("Arial", 10, "bold"), bg="#f5f5f5").pack(pady=(20, 5))
tk.Button(frame_der, text="Realizar Cierre del Día", width=25, bg=ADMIN_BLUE, fg=WHITE, command=cierre_dia).pack(pady=2)
tk.Button(frame_der, text="Consultar Ventas del Día", width=25, bg="#4db6ac", fg=WHITE, command=consultar_ventas_dia).pack(pady=2)
tk.Button(frame_der, text="Actualizar Tasa $", width=25, bg="#fb8c00", fg=WHITE, command=actualizar_tasa).pack(pady=2)
tk.Button(frame_der, text="Configurar Email", width=25, bg="#78909c", fg=WHITE, command=configurar_email).pack(pady=2)
tk.Button(frame_der, text="Añadir/Editar Producto", width=25, bg=INFO_PURPLE, fg=WHITE, command=agregar_nuevo_producto).pack(pady=2)
tk.Button(frame_der, text="Borrar del Inventario", width=25, bg=DANGER_RED, fg=WHITE, command=eliminar_producto_inventario).pack(pady=2)

def imprimir_actual():
    if not historial_facturas: return
    ticket_texto = historial_facturas[indice_historial]
    
    ventana_opc = tk.Toplevel(root)
    ventana_opc.title("Opciones de Factura")
    ventana_opc.geometry("300x200")
    
    # Extraer numero de factura del texto
    import re
    match = re.search(r"FACTURA: (F-\d+)", ticket_texto)
    factura_num = match.group(1) if match else "Desconocida"
    
    def imprimir_con_error():
        try:
            data_manager.imprimir_ticket(ticket_texto)
            ventana_opc.destroy()
        except Exception as e:
            messagebox.showerror("Error de Impresión", str(e), parent=ventana_opc)

    tk.Button(ventana_opc, text="🖨️ IMPRIMIR TICKET", width=25, command=imprimir_con_error).pack(pady=10)
    
    def guardar_y_avisar():
        path = data_manager.generar_pdf_ticket(ticket_texto, factura_num)
        messagebox.showinfo("PDF Guardado", f"Factura guardada en:\n{path}")
        ventana_opc.destroy()
        
    tk.Button(ventana_opc, text="📄 GUARDAR COMO PDF", width=25, command=guardar_y_avisar).pack(pady=10)

tk.Button(frame_der, text="OPCIONES FACTURA ACTUAL", width=25, bg=WHITE, fg="black", command=imprimir_actual).pack(pady=15)

# Carga final
categorias = data_manager.cargar_inventario()
historial_facturas = data_manager.cargar_historial_ventas()
if historial_facturas: actualizar_navegacion(len(historial_facturas)-1)
actualizar_botones()

if __name__ == "__main__":
    root.mainloop()