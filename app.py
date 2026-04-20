from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
from datetime import datetime
import os
import data_manager

app = Flask(__name__)
CORS(app)

# Ensure the static images directory exists
images_dir = os.path.join("static", "images", "products")
if not os.path.exists(images_dir):
    os.makedirs(images_dir)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/inventory', methods=['GET'])
def get_inventory():
    try:
        inventory = data_manager.cargar_inventario()
        # Convert the dictionary to a more frontend-friendly list
        categories = []
        for cat, items in inventory.items():
            products = []
            for name, data in items.items():
                price = data.get("precio", 0.0)
                img_name = data.get("imagen", "")
                
                # Fallback to name-based guess if no image is stored
                if not img_name:
                    img_name = name.lower().replace(" ", "_") + ".jpg"
                
                products.append({
                    "name": name,
                    "price": price,
                    "image": img_name
                })
            categories.append({
                "name": cat,
                "products": products
            })
        return jsonify({"success": True, "categories": categories})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/checkout', methods=['POST'])
def checkout():
    try:
        data = request.json
        cart = data.get('cart', [])
        total_usd = float(data.get('total_usd', 0))
        cliente_data = data.get('cliente', {})
        enviar_correo = data.get('enviar_correo', False)
        
        config = data_manager.cargar_configuracion()
        tasa_vef = config.get("tasa_dolar", 36.0) # Fallback Tasa si no existe
        
        if not cart:
            return jsonify({"success": False, "error": "Carrito vacío"}), 400

        fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Save or update client
        cedula = cliente_data.get('cedula', '00000000').strip()
        nombre = cliente_data.get('nombre', 'Consumidor Final').strip()
        direccion = cliente_data.get('direccion', 'Ciudad').strip()
        email = cliente_data.get('email', '').strip()
        if not cedula: cedula = '00000000'
        if not nombre: nombre = 'Consumidor Final'
        data_manager.guardar_cliente(cedula, nombre, direccion, email)

        productos_str_list = []
        for item in cart:
            productos_str_list.append(f"{item['name']}({item['quantity']})")

        # Registrar Venta en CSV
        data_manager.registrar_venta_csv(
            fecha,
            nombre,
            productos_str_list,
            total_usd,
            float(tasa_vef)
        )
        
        factura_num = data_manager.obtener_y_actualizar_secuencia()
        
        # 1. El ticket de impresion termica se genera opcionalmente con generar_texto_ticket
        # texto_ticket = data_manager.generar_texto_ticket(...)
        
        # 2. Generar hermoso PDF Nativamente
        pdf_path = data_manager.generar_pdf_ticket(
            factura_num, fecha, 
            {"cedula": cedula, "nombre": nombre, "direccion": direccion}, 
            productos_str_list, total_usd, tasa_vef, config
        )
        
        msg_email = ""
        if enviar_correo and email:
            # 3. Generar Ticket especial para Correo (Con imágenes incrustadas CID en el HTML)
            html_email = data_manager.generar_html_ticket(
                factura_num, fecha, 
                {"cedula": cedula, "nombre": nombre, "direccion": direccion}, 
                productos_str_list, total_usd, tasa_vef, config
            )
            exito, msg = data_manager.enviar_email_ticket(email, pdf_path, factura_num, config, html_body=html_email)
            msg_email = msg
            if not exito:
                msg_email = "Fallo el correo: " + msg

        return jsonify({"success": True, "factura": factura_num, "msg_email": msg_email})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/history', methods=['GET'])
def get_history():
    try:
        tipo = request.args.get('tipo', 'hoy')
        fecha = request.args.get('fecha', '')
        historial = data_manager.cargar_historial_ventas(tipo, fecha)
        return jsonify({"success": True, "history": historial})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/admin/tasa', methods=['POST'])
def update_tasa():
    try:
        data = request.json
        nueva_tasa = data.get('tasa')
        if not nueva_tasa:
            return jsonify({"success": False, "error": "Tasa no proporcionada"}), 400
            
        config = data_manager.cargar_configuracion()
        config['tasa_dolar'] = float(nueva_tasa)
        # Note: data_manager doesn't have a direct save config function easily exposed 
        # but we can write to it manually.
        import json
        from constants import ARCHIVO_CONFIG
        with open(ARCHIVO_CONFIG, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4)
            
        return jsonify({"success": True, "message": "Tasa actualizada"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/admin/cierre', methods=['POST'])
def cierre_dia():
    try:
        data = request.json
        fecha_str = data.get('fecha')
        sobreescribir = data.get('sobreescribir', False)
        
        if data_manager.verificar_cierre_existente(fecha_str) and not sobreescribir:
            return jsonify({"success": False, "prompt_overwrite": True})
            
        t_usd, t_vef, num_ventas, conteo_fecha, ventas_detalle = data_manager.obtener_ventas_fecha(fecha_str)
        if num_ventas == 0:
            return jsonify({"success": False, "error": "No hay ventas en esta fecha"})
            
        detalle_csv = "; ".join([f"{n}: {c}" for n, c in conteo_fecha.items()])
        data_manager.registrar_cierre_csv(fecha_str, num_ventas, t_usd, detalle_csv, sobreescribir=sobreescribir)
        
        return jsonify({"success": True, "num_ventas": num_ventas, "total_usd": t_usd, "total_vef": t_vef})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/admin/product', methods=['POST'])
def add_product():
    try:
        # Handle both JSON and Multipart (for file uploads)
        if request.content_type and 'multipart/form-data' in request.content_type:
            cat = request.form.get('categoria')
            nombre = request.form.get('nombre')
            precio = request.form.get('precio')
            uploaded_file = request.files.get('imagen_archivo')
        else:
            data = request.json
            cat = data.get('categoria')
            nombre = data.get('nombre')
            precio = data.get('precio')
            uploaded_file = None

        if not cat or not nombre or precio is None:
            return jsonify({"success": False, "error": "Faltan datos."}), 400
            
        # Process Image
        imagen_final = ""
        if uploaded_file and uploaded_file.filename:
            from werkzeug.utils import secure_filename
            filename = secure_filename(uploaded_file.filename)
            # Ensure static/images/products exists
            img_dir = os.path.join(app.static_folder, 'images', 'products')
            if not os.path.exists(img_dir):
                os.makedirs(img_dir)
            
            save_path = os.path.join(img_dir, filename)
            uploaded_file.save(save_path)
            imagen_final = filename

        categorias = data_manager.cargar_inventario()
        if cat not in categorias:
            categorias[cat] = {}
        
        # Guardar con la nueva estructura
        categorias[cat][nombre] = {
            "precio": float(precio),
            "imagen": imagen_final
        }
        
        data_manager.guardar_inventario(categorias)
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/client/<cedula>', methods=['GET'])
def get_client(cedula):
    clientes = data_manager.cargar_clientes()
    if cedula in clientes:
        return jsonify({"success": True, "cliente": clientes[cedula]})
    return jsonify({"success": False})

@app.route('/api/admin/email_config', methods=['GET', 'POST'])
def email_config():
    from constants import ARCHIVO_CONFIG
    import json
    if request.method == 'GET':
        config = data_manager.cargar_configuracion()
        return jsonify({
            "success": True,
            "smtp_server": config.get("smtp_server", "smtp.gmail.com"),
            "smtp_port": config.get("smtp_port", 587),
            "smtp_user": config.get("smtp_user", ""),
            "smtp_password": config.get("smtp_password", "")
        })
    else:
        try:
            data = request.json
            config = data_manager.cargar_configuracion()
            config["smtp_server"] = data.get("smtp_server")
            config["smtp_port"] = int(data.get("smtp_port", 587))
            config["smtp_user"] = data.get("smtp_user")
            config["smtp_password"] = data.get("smtp_password")
            with open(ARCHIVO_CONFIG, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4)
            return jsonify({"success": True})
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/admin/test_email', methods=['POST'])
def test_email():
    try:
        data = request.json
        config = {
            "smtp_server": data.get("smtp_server"),
            "smtp_port": int(data.get("smtp_port", 587)),
            "smtp_user": data.get("smtp_user"),
            "smtp_password": data.get("smtp_password")
        }
        
        exito, msg = data_manager.probar_email_config(config)
        return jsonify({"success": exito, "message": msg})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/admin/product', methods=['DELETE'])
def delete_product():
    try:
        data = request.json
        cat = data.get('categoria')
        nombre = data.get('nombre')
        if data_manager.eliminar_producto(cat, nombre):
            return jsonify({"success": True})
        return jsonify({"success": False, "error": "Producto no encontrado"}), 404
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/admin/sale', methods=['DELETE'])
def delete_sale():
    try:
        data = request.json
        fecha = data.get('fecha')
        if not fecha:
            return jsonify({"success": False, "error": "Falta fecha"}), 400
        if data_manager.eliminar_venta(fecha):
            return jsonify({"success": True})
        return jsonify({"success": False, "error": "Venta no encontrada"}), 404
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
