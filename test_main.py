import pytest
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

class TestSaucedemo():
    def setup_method(self, method):
        self.driver = webdriver.Chrome()
        self.driver.implicitly_wait(10)

    def teardown_method(self, method):
        self.driver.quit()

    def test_login_fallo_password_incorrecta(self):
        """Valida el mensaje de error al ingresar con credenciales inválidas."""
        self.driver.get("https://www.saucedemo.com/")
        self.driver.find_element(By.ID, "user-name").send_keys("standard_user")
        time.sleep(2)

        self.driver.find_element(By.ID, "password").send_keys("wrong_password")
        time.sleep(2)

        self.driver.find_element(By.ID, "login-button").click()

        error_message = WebDriverWait(self.driver, 10).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-test='error']"))
        ).text

        assert "Epic sadface: Username and password do not match any user in this service" in error_message, "El mensaje de error no es el esperado para contraseña incorrecta."

    def test_login(self):
        """Valida el inicio de sesión con credenciales válidas."""
        self.driver.get("https://www.saucedemo.com/")
        self.driver.find_element(By.ID, "user-name").send_keys("standard_user")
        time.sleep(1)

        self.driver.find_element(By.ID, "password").send_keys("secret_sauce")
        time.sleep(1)

        self.driver.find_element(By.ID, "login-button").click()

        assert "https://www.saucedemo.com/inventory.html" in self.driver.current_url, "La URL no es la esperada después de iniciar sesión."

    def test_filtrado(self):
        """Valida el funcionamiento del filtro de productos."""
        self.test_login()
        time.sleep(1)

        self.driver.find_element(By.CLASS_NAME, "product_sort_container").click()
        time.sleep(1)

        self.driver.find_element(By.XPATH, "//option[text()='Price (high to low)']").click()
        time.sleep(1)

        
        # Obtener los precios de los productos y validarlos
        prices = []
        products = self.driver.find_elements(By.CLASS_NAME, "inventory_item_price")
        for product in products:
            price_text = product.text.replace("$", "")
            prices.append(float(price_text))

        time.sleep(2)


        # Verificar que la lista de precios esté ordenada de mayor a menor
        assert prices == sorted(prices, reverse=True), "Los productos no están ordenados por precio de mayor a menor"

    def test_ver_producto(self):
        """Valida la información de los productos."""
        self.test_filtrado()

        # Obtener los productos
        products = WebDriverWait(self.driver, 10).until(
            EC.visibility_of_all_elements_located((By.CLASS_NAME, "inventory_item"))
        )
        time.sleep(1)

        # Seleccionar los dos últimos productos (los más baratos)
        for i in range(-2, 0):
            # Reobtener la lista de productos después de cada navegación
            products = WebDriverWait(self.driver, 10).until(
                EC.visibility_of_all_elements_located((By.CLASS_NAME, "inventory_item"))
            )
            
            product_name = products[i].find_element(By.CLASS_NAME, "inventory_item_name").text
            product_price = products[i].find_element(By.CLASS_NAME, "inventory_item_price").text
            products[i].find_element(By.TAG_NAME, "a").click()

            # Validar que el nombre y el precio coinciden con la página principal
            product_details_name = WebDriverWait(self.driver, 10).until(
                EC.visibility_of_element_located((By.CLASS_NAME, "inventory_details_name"))
            ).text
            product_details_price = self.driver.find_element(By.CLASS_NAME, "inventory_details_price").text

            assert product_name == product_details_name, f"Expected {product_name}, but got {product_details_name}"
            assert product_price == product_details_price, f"Expected {product_price}, but got {product_details_price}"

            # Volver a la página principal
            self.driver.back()

    def test_agregar_productos(self):
        """Valida la funcionalidad del carrito (agregar)."""
        self.test_filtrado()
        
        # Obtener los productos y ordenarlos por precio de menor a mayor
        products = WebDriverWait(self.driver, 10).until(
            EC.visibility_of_all_elements_located((By.CLASS_NAME, "inventory_item"))
        )
        
        # Ordenar los productos por precio (de menor a mayor)
        products.sort(key=lambda product: float(product.find_element(By.CLASS_NAME, "inventory_item_price").text.replace("$", "")))
        
        # Seleccionar los dos productos más baratos
        productos_baratos = products[:2]

        for producto in productos_baratos:
            product_id = producto.find_element(By.CLASS_NAME, "btn_inventory").get_attribute("data-test").replace("add-to-cart-", "")
            add_to_cart_button = producto.find_element(By.CSS_SELECTOR, f"[data-test='add-to-cart-{product_id}']")
            add_to_cart_button.click()
            
            # Reobtener la lista de productos después de cada clic
            products = WebDriverWait(self.driver, 10).until(
                EC.visibility_of_all_elements_located((By.CLASS_NAME, "inventory_item"))
            )
            
            # Verificar que el botón cambió a "Remove"
            remove_button = producto.find_element(By.CSS_SELECTOR, f"[data-test='remove-{product_id}']")
            assert remove_button.text == "Remove", "El botón no cambió a 'Remove' después de agregar el producto"
            time.sleep(1)

        # Verificar que el contador del carrito se actualiza
        cart_badge = WebDriverWait(self.driver, 10).until(
            EC.visibility_of_element_located((By.CLASS_NAME, "shopping_cart_badge"))
        )
        assert cart_badge.text == "2", "El contador del carrito no se actualizó correctamente"

    def test_verificar_carrito(self):
        """Valida la correcta visualización del carrito."""
        self.test_agregar_productos()
        self.driver.find_element(By.CLASS_NAME, "shopping_cart_link").click()
        
        # Esperar a que los elementos del carrito sean visibles
        cart_items = WebDriverWait(self.driver, 10).until(
            EC.visibility_of_all_elements_located((By.CLASS_NAME, "cart_item"))
        )
        
        # Verificar que el carrito contiene los dos productos esperados
        assert len(cart_items) == 2, "El carrito no contiene los dos productos esperados"

        # Validar la información de cada producto en el carrito
        expected_products = [
            {"name": "Sauce Labs Onesie", "price": "$7.99"},
            {"name": "Sauce Labs Bike Light", "price": "$9.99"}
        ]

        for item in cart_items:
            product_name = item.find_element(By.CLASS_NAME, "inventory_item_name").text
            product_price = item.find_element(By.CLASS_NAME, "inventory_item_price").text
            
            # Verificar que el producto está en la lista de productos esperados
            assert any(product_name == expected["name"] and product_price == expected["price"] for expected in expected_products), f"Producto inesperado en el carrito: {product_name} - {product_price}"

    def test_eliminar_producto(self):
        """Valida la función de eliminar productos del carrito."""
        self.test_verificar_carrito()
        
        # Obtener el primer producto en el carrito
        cart_item = self.driver.find_element(By.CLASS_NAME, "cart_item")
        
        # Obtener el ID del producto
        product_id = cart_item.find_element(By.CLASS_NAME, "btn_secondary").get_attribute("data-test").replace("remove-", "")

        # Construir el selector CSS para el botón "Remove"
        remove_button_selector = f"[data-test='remove-{product_id}']"
        
        # Hacer clic en el botón "Remove"
        remove_button = cart_item.find_element(By.CSS_SELECTOR, remove_button_selector)
        remove_button.click()
        
        time.sleep(1)

    def test_proceder_compra(self):
        """Valida la redirección al formulario."""
        # self.test_agregar_productos()
        self.test_verificar_carrito()
        self.driver.find_element(By.ID, "checkout").click()
        time.sleep(1)
        assert "checkout-step-one.html" in self.driver.current_url, "No se redirigió al formulario correctamente"

    def test_mensajes_error_campos_requeridos(self):
        """Valida mensajes de error de campos requeridos."""
        self.test_proceder_compra()
        self.driver.find_element(By.ID, "continue").click()
        
        # Verificar que se muestran los mensajes de error
        error_message = self.driver.find_element(By.CSS_SELECTOR, "[data-test='error']").text
        assert "Error: First Name is required" in error_message

    def test_informacion_productos_confirmacion(self):
        """Valida información de los productos en la página de confirmación."""
        self.test_proceder_compra()
        self.driver.find_element(By.ID, "first-name").send_keys("John")
        self.driver.find_element(By.ID, "last-name").send_keys("Doe")
        self.driver.find_element(By.ID, "postal-code").send_keys("12345")
        self.driver.find_element(By.ID, "continue").click()
        
        # Obtener la información de los productos en la página de confirmación
        # y compararla con la información esperada

    def test_finalizacion_compra(self):
        """Valida la finalización de la compra."""
        self.test_informacion_productos_confirmacion()
        self.driver.find_element(By.ID, "finish").click()

        confirmation_text = WebDriverWait(self.driver, 10).until(
            EC.visibility_of_element_located((By.CLASS_NAME, "complete-header"))
        ).text

        assert "thank you for your order!" in confirmation_text.lower(), f"Expected 'thank you for your order!' but got '{confirmation_text}'"

    def test_redireccion_pagina_principal(self):
        """Valida la redirección a la página principal al completar la compra."""
        self.test_finalizacion_compra()
        self.driver.find_element(By.ID, "back-to-products").click()
        assert "inventory.html" in self.driver.current_url, "No se redirigió a la página principal correctamente"

    def test_cierre_sesion(self):
        """Valida el cierre de sesión."""
        self.test_login()  # Asegurarse de que se haya iniciado sesión
        burger_button = self.driver.find_element(By.ID, "react-burger-menu-btn")
        burger_button.click()

        logout_link = WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.ID, "logout_sidebar_link"))
        )
        logout_link.click()

        assert "https://www.saucedemo.com/" in self.driver.current_url, "La URL no es la esperada después del logout."
        assert self.driver.find_element(By.ID, "login-button").is_displayed(), "El botón de login no está visible después del logout."