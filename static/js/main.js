let allCategories = [];
let cart = {};

// Fetch data on load
document.addEventListener('DOMContentLoaded', () => {
    fetchInventory();
    
    document.getElementById('searchInput').addEventListener('input', (e) => {
        filterProducts(e.target.value);
    });
    
    document.getElementById('checkoutBtn').addEventListener('click', openCheckoutModal);
    
    // Global ESC handler for static modals
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            const staticModals = document.querySelectorAll('.modal');
            staticModals.forEach(m => {
                if (m.style.display === 'flex' && m.id !== 'dialogModal') {
                    m.style.display = 'none';
                }
            });
        }
    });
});

async function fetchInventory() {
    try {
        const response = await fetch('/api/inventory');
        const data = await response.json();
        if (data.success) {
            allCategories = data.categories;
            renderCategories();
            renderProducts();
        } else {
            console.error('Failed to load inventory:', data.error);
        }
    } catch (e) {
        console.error('Error fetching inventory:', e);
    }
}

function renderCategories() {
    const container = document.getElementById('categoryContainer');
    container.innerHTML = '';
    
    const btnTodos = document.createElement('button');
    btnTodos.className = activeCategory === null ? 'category-btn active' : 'category-btn';
    btnTodos.innerText = 'TODOS';
    btnTodos.onclick = () => filterByCategory(null);
    container.appendChild(btnTodos);
    
    // Can map to fixed colors if needed or all green per mockup
    allCategories.forEach((cat, index) => {
        const btn = document.createElement('button');
        btn.className = activeCategory === cat.name ? 'category-btn active' : 'category-btn';
        btn.innerText = cat.name.toUpperCase();
        btn.onclick = () => filterByCategory(cat.name);
        container.appendChild(btn);
    });
}

let activeCategory = null;

function filterByCategory(catName) {
    if (activeCategory === catName) {
        activeCategory = null; // Toggle off
    } else {
        activeCategory = catName;
    }
    renderCategories();
    renderProducts();
}

function filterProducts(searchTerm) {
    renderProducts(searchTerm.toLowerCase());
}

function renderProducts(searchFilter = '') {
    const container = document.getElementById('productGrid');
    container.innerHTML = '';
    
    allCategories.forEach(cat => {
        if (activeCategory && cat.name !== activeCategory) return;
        
        cat.products.forEach(prod => {
            if (searchFilter && !prod.name.toLowerCase().includes(searchFilter)) return;
            
            const card = document.createElement('div');
            card.className = 'product-card';
            card.onclick = () => addToCart(prod);
            
            const imgSrc = `/static/images/products/${prod.image}`;
            
            card.innerHTML = `
                <img src="${imgSrc}" onerror="this.onerror=null; this.src='https://placehold.co/400x300?text=No+Image'" class="product-img" alt="${prod.name}">
                <div class="product-info-overlay">
                    <div class="product-details">
                        <div class="product-name">${prod.name}</div>
                    </div>
                    <div class="price-badge">$${parseFloat(prod.price).toFixed(2)}</div>
                </div>
            `;
            container.appendChild(card);
        });
    });
}

function addToCart(product) {
    if (cart[product.name]) {
        cart[product.name].quantity += 1;
    } else {
        cart[product.name] = { ...product, quantity: 1 };
    }
    updateCartUI();
}

function updateCartUI() {
    const container = document.getElementById('cartItems');
    container.innerHTML = '';
    
    let total = 0;
    Object.values(cart).forEach(item => {
        const itemTotal = item.price * item.quantity;
        total += itemTotal;
        
        const el = document.createElement('div');
        el.className = 'cart-item';
        el.innerHTML = `
            <div class="cart-item-info">
                <span class="cart-item-name">${item.name} (x${item.quantity})</span>
            </div>
            <div class="cart-item-price">$${itemTotal.toFixed(2)}</div>
        `;
        // Allow removing item on click
        el.onclick = () => {
             cart[item.name].quantity -= 1;
             if(cart[item.name].quantity === 0) delete cart[item.name];
             updateCartUI();
        };
        el.style.cursor = "pointer";
        container.appendChild(el);
    });
    
    document.getElementById('totalPrice').innerText = `$${total.toFixed(2)}`;
    return total;
}

async function processCheckout() {
    const items = Object.values(cart);
    if (items.length === 0) {
        await customDialog({message: "El carrito está vacío."});
        return;
    }
    
    const total_usd = updateCartUI(); // Get latest total
    
    const cedula = document.getElementById('clientCedula').value.trim();
    const nombre = document.getElementById('clientNombre').value.trim();
    const direccion = document.getElementById('clientDireccion').value.trim();
    const email = document.getElementById('clientEmail').value.trim();
    const sendEmailCheckbox = document.getElementById('sendEmailCheckbox').checked;

    const payload = {
        cart: items,
        total_usd: total_usd,
        cliente: { cedula, nombre, direccion, email },
        enviar_correo: sendEmailCheckbox
    };
    
    try {
        const res = await fetch('/api/checkout', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(payload)
        });
        
        const data = await res.json();
        if (data.success) {
            let msg = `Venta procesada exitosamente.\nFactura: ${data.factura}`;
            if (data.msg_email) {
                msg += `\nEstado del Correo: ${data.msg_email}`;
            }
            await customDialog({message: msg});
            cart = {};
            closeCheckoutModal();
            updateCartUI();
        } else {
            await customDialog({message: 'Error al procesar: ' + data.error});
        }
    } catch (e) {
        console.error(e);
        await customDialog({message: 'Error de conexión.'});
    }
}

// ---- NUEVAS FUNCIONALIDADES ------

function switchTab(tabId) {
    document.getElementById('posContainer').style.display = 'none';
    document.getElementById('historyContainer').style.display = 'none';
    document.getElementById('adminContainer').style.display = 'none';
    
    document.getElementById('navVentas').classList.remove('active');
    document.getElementById('navHistorial').classList.remove('active');
    document.getElementById('navAdmin').classList.remove('active');
    
    if (tabId === 'ventas') {
        document.getElementById('posContainer').style.display = 'flex';
        document.getElementById('navVentas').classList.add('active');
    } else if (tabId === 'historial') {
        document.getElementById('historyContainer').style.display = 'block';
        document.getElementById('navHistorial').classList.add('active');
        fetchHistory();
    } else if (tabId === 'admin') {
        document.getElementById('adminContainer').style.display = 'block';
        document.getElementById('navAdmin').classList.add('active');
    }
}

async function fetchHistory() {
    try {
        const filter = document.getElementById('historyFilter').value;
        const dateFilter = document.getElementById('historyDate') ? document.getElementById('historyDate').value : '';
        const res = await fetch(`/api/history?tipo=${filter}&fecha=${dateFilter}`);
        const data = await res.json();
        if (data.success) {
            const container = document.getElementById('historyList');
            container.innerHTML = '';
            if (data.history.length === 0) {
                container.innerHTML = '<div class="history-item">No hay ventas registradas.</div>';
                return;
            }
            // Mostrar desde el último al primero
            data.history.reverse().forEach(item => {
                const el = document.createElement('div');
                el.className = 'history-item';
                el.style.position = 'relative';
                el.innerText = item.texto;
                
                // Botón de eliminar venta (solo si es tipo hoy o detalla y no es un encabezado de cierre)
                if (filter === 'hoy') {
                    const delBtn = document.createElement('button');
                    delBtn.innerHTML = '🗑️';
                    delBtn.style.position = 'absolute';
                    delBtn.style.top = '10px';
                    delBtn.style.right = '10px';
                    delBtn.style.background = 'transparent';
                    delBtn.style.border = 'none';
                    delBtn.style.cursor = 'pointer';
                    delBtn.title = "Eliminar Venta";
                    delBtn.onclick = () => deleteSale(item.fecha);
                    el.appendChild(delBtn);
                }
                
                container.appendChild(el);
            });
        }
    } catch(e) {
        console.error("Error cargando historial", e);
    }
}

async function deleteSale(fecha) {
    const confirm = await customDialog({
        title: "Confirmar Eliminación", 
        message: `¿Estás seguro de que deseas eliminar la venta del ${fecha}?\n\nEsta acción no se puede deshacer y solo es posible ANTES del cierre de caja.`,
        type: "confirm"
    });
    
    if (!confirm) return;
    
    try {
        const res = await fetch('/api/admin/sale', {
            method: 'DELETE',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ fecha: fecha })
        });
        const data = await res.json();
        if (data.success) {
            await customDialog({message: "Venta eliminada correctamente."});
            fetchHistory();
        } else {
            await customDialog({message: "Error: " + data.error});
        }
    } catch(e) {
        await customDialog({message: "Error al conectar con el servidor."});
    }
}

async function adminTasa() {
    const nueva = await customDialog({title: "Actualizar Tasa", message: "Ingrese la nueva tasa de conversión ($ a Bs.):", type: "prompt"});
    if (!nueva) return;
    
    try {
        const res = await fetch('/api/admin/tasa', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({tasa: nueva})
        });
        const data = await res.json();
        if (data.success) await customDialog({message: "Tasa actualizada con éxito."});
        else await customDialog({message: "Error: " + data.error});
    } catch(e) {
        await customDialog({message: "Error de conexión"});
    }
}

async function adminCierre() {
    // Calculamos el "hoy" local para evitar problemas con la zona horaria (UTC vs Local)
    const tzOffset = (new Date()).getTimezoneOffset() * 60000;
    const localToday = (new Date(Date.now() - tzOffset)).toISOString().split('T')[0];
    
    const fecha = await customDialog({title: "Cierre de Caja", message: "Ingrese la fecha para el cierre de caja (YYYY-MM-DD):", type: "prompt", defaultValue: localToday});
    if (!fecha) return;
    
    const realizar = async (sobreescribir = false) => {
        try {
            const res = await fetch('/api/admin/cierre', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({fecha: fecha, sobreescribir: sobreescribir})
            });
            const data = await res.json();
            
            if (data.prompt_overwrite) {
                const conf = await customDialog({title: "Confirmar", message: "Ya existe un cierre para esta fecha. ¿Desea SOBREESCRIBIRLO?", type: "confirm"});
                if(conf) {
                    realizar(true);
                }
            } else if (data.success) {
                await customDialog({title: "Cierre Exitoso", message: `Facturas: ${data.num_ventas}\nTotal USD: $${data.total_usd.toFixed(2)}`});
            } else {
                await customDialog({message: "Error: " + data.error});
            }
        } catch(e) {
            await customDialog({message: "Error de conexión"});
        }
    };
    
    realizar(false);
}

// ---- PRODUCT MANAGEMENT MODAL ----
function openProductModal() {
    const modal = document.getElementById('productModal');
    const datalist = document.getElementById('catOptions');
    datalist.innerHTML = '';
    
    // Fill the datalist with existing categories
    allCategories.forEach(cat => {
        const option = document.createElement('option');
        option.value = cat.name;
        datalist.appendChild(option);
    });
    
    // Clear inputs and options
    document.getElementById('prodCategory').value = '';
    document.getElementById('prodName').value = '';
    document.getElementById('prodPrice').value = '';
    document.getElementById('prodImage').value = '';
    document.getElementById('prodOptions').innerHTML = '';
    document.getElementById('deleteProdBtn').style.display = 'none';
    
    modal.style.display = 'flex';
}

function updateProductOptions() {
    const catName = document.getElementById('prodCategory').value.trim();
    const datalist = document.getElementById('prodOptions');
    datalist.innerHTML = '';
    
    const category = allCategories.find(c => c.name === catName);
    if (category) {
        category.products.forEach(p => {
            const option = document.createElement('option');
            option.value = p.name;
            datalist.appendChild(option);
        });
    }
}

function checkProductAutoFill() {
    const catName = document.getElementById('prodCategory').value.trim();
    const prodName = document.getElementById('prodName').value.trim();
    const priceInput = document.getElementById('prodPrice');
    
    const category = allCategories.find(c => c.name === catName);
    if (category) {
        const product = category.products.find(p => p.name === prodName);
        if (product) {
            priceInput.value = product.price;
            document.getElementById('deleteProdBtn').style.display = 'block';
        } else {
            document.getElementById('deleteProdBtn').style.display = 'none';
        }
    } else {
        document.getElementById('deleteProdBtn').style.display = 'none';
    }
}

async function deleteProduct() {
    const cat = document.getElementById('prodCategory').value.trim();
    const name = document.getElementById('prodName').value.trim();
    
    if (!cat || !name) return;
    
    const confirm = await customDialog({
        title: "Eliminar Producto",
        message: `¿Seguro que quieres eliminar ${name} de la categoría ${cat}?`,
        type: "confirm"
    });
    
    if (!confirm) return;
    
    try {
        const res = await fetch('/api/admin/product', {
            method: 'DELETE',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ categoria: cat, nombre: name })
        });
        const data = await res.json();
        if (data.success) {
            await customDialog({message: "Producto eliminado."});
            closeProductModal();
            fetchInventory();
        } else {
            await customDialog({message: "Error: " + data.error});
        }
    } catch(e) {
        await customDialog({message: "Error de conexión."});
    }
}

function closeProductModal() {
    document.getElementById('productModal').style.display = 'none';
}

async function saveProduct() {
    const cat = document.getElementById('prodCategory').value.trim();
    const name = document.getElementById('prodName').value.trim();
    const priceStr = document.getElementById('prodPrice').value.trim();
    
    if (!cat || !name || !priceStr) {
        await customDialog({message: "Por favor, llena todos los campos."});
        return;
    }
    
    const price = parseFloat(priceStr);
    if (isNaN(price)) {
        await customDialog({message: "Precio inválido."});
        return;
    }
    
    const btn = document.getElementById('saveProdBtn');
    const originalText = btn.innerText;
    btn.innerText = "GUARDANDO...";
    btn.disabled = true;

    try {
        const formData = new FormData();
        formData.append('categoria', cat);
        formData.append('nombre', name);
        formData.append('precio', price);
        
        const fileInput = document.getElementById('prodImage');
        if (fileInput.files.length > 0) {
            formData.append('imagen_archivo', fileInput.files[0]);
        }
        
        const res = await fetch('/api/admin/product', {
            method: 'POST',
            body: formData
        });
        
        const data = await res.json();
        if (data.success) {
            await customDialog({message: "Producto guardado exitosamente."});
            closeProductModal();
            fetchInventory(); // Reload inventory
        } else {
            await customDialog({message: "Error: " + data.error});
        }
    } catch(e) {
        console.error(e);
        await customDialog({message: "Error de conexión al guardar producto."});
    } finally {
        btn.innerText = originalText;
        btn.disabled = false;
    }
}

// ---- CLIENT CHECKOUT MODAL ----
function openCheckoutModal() {
    const items = Object.values(cart);
    if (items.length === 0) {
        customDialog({message: "El carrito está vacío."});
        return;
    }
    document.getElementById('clientCedula').value = '';
    document.getElementById('clientNombre').value = '';
    document.getElementById('clientDireccion').value = '';
    document.getElementById('clientEmail').value = '';
    document.getElementById('sendEmailCheckbox').checked = true;
    
    document.getElementById('checkoutModal').style.display = 'flex';
}

function closeCheckoutModal() {
    document.getElementById('checkoutModal').style.display = 'none';
}

async function fetchClientData() {
    const cedula = document.getElementById('clientCedula').value.trim();
    if (!cedula) return;
    try {
        const res = await fetch('/api/client/' + cedula);
        const data = await res.json();
        if (data.success) {
            document.getElementById('clientNombre').value = data.cliente.Nombre || '';
            document.getElementById('clientDireccion').value = data.cliente.Direccion || '';
            document.getElementById('clientEmail').value = data.cliente.Email || '';
        }
    } catch(e) {
        console.error("Error fetching client");
    }
}

// ---- EMAIL CONFIG MODAL ----
async function openEmailConfigModal() {
    try {
        const res = await fetch('/api/admin/email_config');
        const data = await res.json();
        if (data.success) {
            document.getElementById('smtpServer').value = data.smtp_server || '';
            document.getElementById('smtpPort').value = data.smtp_port || '';
            document.getElementById('smtpUser').value = data.smtp_user || '';
            document.getElementById('smtpPass').value = data.smtp_password || '';
            document.getElementById('emailConfigModal').style.display = 'flex';
        }
    } catch (e) {
        customDialog({message: "Error fetching email config."});
    }
}

function closeEmailConfigModal() {
    document.getElementById('emailConfigModal').style.display = 'none';
}

async function saveEmailConfig() {
    const server = document.getElementById('smtpServer').value.trim();
    const port = document.getElementById('smtpPort').value.trim();
    const user = document.getElementById('smtpUser').value.trim();
    const pass = document.getElementById('smtpPass').value.trim();
    
    try {
        const res = await fetch('/api/admin/email_config', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                smtp_server: server,
                smtp_port: parseInt(port) || 587,
                smtp_user: user,
                smtp_password: pass
            })
        });
        const data = await res.json();
        if (data.success) {
            await customDialog({message: "Configuración guardada."});
            closeEmailConfigModal();
        } else {
            customDialog({message: "Error saving config."});
        }
    } catch (e) {
        customDialog({message: "Error connecting to server."});
    }
}

async function testEmailConfig() {
    const server = document.getElementById('smtpServer').value.trim();
    const port = document.getElementById('smtpPort').value.trim();
    const user = document.getElementById('smtpUser').value.trim();
    const pass = document.getElementById('smtpPass').value.trim();
    
    if (!server || !user || !pass) {
        await customDialog({message: "Por favor, completa los campos de Servidor, Usuario y Contraseña para probar."});
        return;
    }

    const testBtn = event.target;
    const originalText = testBtn.innerText;
    testBtn.innerText = "PROBANDO...";
    testBtn.disabled = true;

    try {
        const res = await fetch('/api/admin/test_email', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                smtp_server: server,
                smtp_port: parseInt(port) || 587,
                smtp_user: user,
                smtp_password: pass
            })
        });
        const data = await res.json();
        if (data.success) {
            await customDialog({title: "Éxito", message: data.message});
        } else {
            await customDialog({title: "Error de Prueba", message: data.message || data.error});
        }
    } catch (e) {
        await customDialog({message: "Error al conectar con el servidor para la prueba."});
    } finally {
        testBtn.innerText = originalText;
        testBtn.disabled = false;
    }
}

// ---- CUSTOM DIALOG SYSTEM ----
function customDialog({ title = "Aviso", message = "", type = "alert", defaultValue = "" }) {
    return new Promise((resolve) => {
        const modal = document.getElementById('dialogModal');
        const titleEl = document.getElementById('dialogTitle');
        const msgEl = document.getElementById('dialogMessage');
        const inputContainer = document.getElementById('dialogInputContainer');
        const inputEl = document.getElementById('dialogInput');
        const cancelBtn = document.getElementById('dialogCancelBtn');
        const confirmBtn = document.getElementById('dialogConfirmBtn');
        
        titleEl.innerText = title;
        msgEl.innerText = message;
        
        const keydownHandler = (e) => {
            if (e.key === 'Escape') {
                if (type === "alert") cleanupAndResolve(true);
                else if (type === "confirm") cleanupAndResolve(false);
                else if (type === "prompt") cleanupAndResolve(null);
            } else if (e.key === 'Enter' && type === "prompt") {
                cleanupAndResolve(inputEl.value);
            }
        };

        const cleanupAndResolve = (val) => {
            document.removeEventListener('keydown', keydownHandler);
            modal.style.display = 'none';
            resolve(val);
        };
        
        document.addEventListener('keydown', keydownHandler);
        
        if (type === "alert") {
            inputContainer.style.display = 'none';
            cancelBtn.style.display = 'none';
            
            confirmBtn.onclick = () => cleanupAndResolve(true);
        } else if (type === "confirm") {
            inputContainer.style.display = 'none';
            cancelBtn.style.display = 'block';
            
            cancelBtn.onclick = () => cleanupAndResolve(false);
            confirmBtn.onclick = () => cleanupAndResolve(true);
        } else if (type === "prompt") {
            inputContainer.style.display = 'block';
            cancelBtn.style.display = 'block';
            inputEl.value = defaultValue;
            
            cancelBtn.onclick = () => cleanupAndResolve(null);
            confirmBtn.onclick = () => cleanupAndResolve(inputEl.value);
        }
        
        modal.style.display = 'flex';
        if (type === "prompt") {
            inputEl.focus();
        }
    });
}
