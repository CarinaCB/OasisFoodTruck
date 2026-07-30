from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.spinner import Spinner
from kivy.uix.popup import Popup
from kivy.uix.image import Image
from kivy.uix.textinput import TextInput
from kivy.clock import Clock
from functools import partial
import sqlite3
import datetime
import os

DB_PATH = 'database/Oasis.db'
print("DB_PATH:", DB_PATH)
print("ABSOLUTO:", os.path.abspath(DB_PATH))

def init_db():
    os.makedirs('database', exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Productos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            Nombre TEXT NOT NULL,
            Precio REAL NOT NULL
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ventas_diarias (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha TEXT,
            horas TEXT,
            detalles TEXT,
            total REAL,
            pago TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS deudores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha TEXT,
            nombre TEXT,
            productos TEXT,
            total REAL
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS total_ventas (
            fecha TEXT PRIMARY KEY,
            numdeventas INTEGER,
            efectivo REAL,
            mercadopago REAL,
            total REAL
        )
    """)
    conn.commit()
    conn.close()


# ==========================================
# BARRA SUPERIOR UNIFICADA
# ==========================================
class HeaderBar(BoxLayout):
    def __init__(self, title_text, screen_manager, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'horizontal'
        self.size_hint = (1, None)
        self.height = 45
        self.padding = [10, 5]
        self.spacing = 10

        btn_back = Button(
            text="← Volver",
            size_hint=(None, None),
            size=(90, 35),
            font_size=14,
            background_normal='',
            background_color=(0.2, 0.4, 0.7, 1),
            color=(1, 1, 1, 1)
        )
        btn_back.bind(on_press=lambda x: setattr(screen_manager, 'current', 'main'))
        self.add_widget(btn_back)

        lbl_title = Label(
            text=title_text,
            font_size=18,
            bold=True,
            color=(0.95, 0.6, 0.2, 1),
            halign='center',
            valign='middle'
        )
        lbl_title.bind(size=lbl_title.setter('text_size'))
        self.add_widget(lbl_title)


# ==========================================
# PANTALLA PRINCIPAL
# ==========================================
class MainScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.cart = []
        
        layout = BoxLayout(orientation='vertical', padding=15, spacing=10)

        bg_image = Image(
            source='static/logo.oasis.jpg',
            size_hint=(1, 0.3),
            pos_hint={'center_x': 0.5}
        )
        layout.add_widget(bg_image)

        title = Label(
            text="Oasis Food Truck",
            font_size='26sp',
            color=(0.95, 0.6, 0.2, 1),
            size_hint=(1, 0.08),
            halign='center'
        )
        title.bind(size=title.setter('text_size'))
        layout.add_widget(title)

        menu_layout = GridLayout(cols=2, spacing=10, size_hint=(1, 0.6))

        botones = [
            ("Ver Productos", lambda x: setattr(self.manager, 'current', 'products'), (0.2, 0.3, 0.4, 1)),
            ("Ver Carrito", self.show_cart, (0.2, 0.4, 0.3, 1)),
            ("Ventas Diarias", lambda x: setattr(self.manager, 'current', 'daily_sales'), (0.25, 0.3, 0.4, 1)),
            ("Calculadora", lambda x: setattr(self.manager, 'current', 'calcular_sales'), (0.3, 0.3, 0.4, 1)),
            ("Total Ventas", lambda x: setattr(self.manager, 'current', 'total_ventas'), (0.35, 0.3, 0.4, 1)),
            ("Deudores", lambda x: setattr(self.manager, 'current', 'deudores'), (0.5, 0.3, 0.2, 1)),
            ("Configuración", lambda x: setattr(self.manager, 'current', 'configuracion'), (0.35, 0.35, 0.35, 1)),
            ("Gastos", lambda x: setattr(self.manager, 'current', 'gastos'), (0.4, 0.25, 0.25, 1))
        ]

        for texto, callback, color in botones:
            btn = Button(
                text=texto,
                font_size='14sp',
                background_normal='',
                background_color=color,
                color=(1, 1, 1, 1),
                size_hint_y=None,
                height=42
            )
            btn.bind(on_press=callback)
            menu_layout.add_widget(btn)

        layout.add_widget(menu_layout)
        self.add_widget(layout)

    def show_cart(self, instance):
        content = BoxLayout(orientation='vertical', spacing=10, padding=15)
        total = 0
        pago_options = ['Efectivo', 'Mercado Pago', 'En Deuda']

        if not self.cart:
            content.add_widget(Label(text="El carrito está vacío", font_size='15sp', color=(0.7, 0.7, 0.7, 1)))
        else:
            scroll_cart = ScrollView(size_hint=(1, 0.55))
            cart_list_layout = GridLayout(cols=1, spacing=5, size_hint_y=None)
            cart_list_layout.bind(minimum_height=cart_list_layout.setter('height'))

            for product_name, product_price in self.cart:
                product_box = BoxLayout(orientation='horizontal', spacing=10, size_hint_y=None, height=35)
                product_label = Label(text=f"{product_name} - ${product_price:,.2f}", font_size='14sp', size_hint_x=0.75, halign='left')
                product_label.bind(size=product_label.setter('text_size'))
                product_box.add_widget(product_label)

                remove_button = Button(text="Quitar", font_size='12sp', size_hint_x=0.25,
                                       background_color=(0.7, 0.2, 0.2, 1), background_normal='')
                remove_button.bind(on_press=lambda btn, name=product_name: self.remove_from_cart(name))
                product_box.add_widget(remove_button)

                cart_list_layout.add_widget(product_box)
                total += float(product_price)

            scroll_cart.add_widget(cart_list_layout)
            content.add_widget(scroll_cart)

            total_label = Label(text=f"Total: ${total:,.2f}", font_size='17sp', bold=True, size_hint_y=None, height=35)
            content.add_widget(total_label)

            pago_spinner = Spinner(
                text='Seleccionar método de pago',
                values=pago_options,
                size_hint=(1, None),
                height=38
            )

            def on_pago_select(instance, value):
                if value == 'En Deuda':
                    self.show_debt_popup()

            pago_spinner.bind(text=on_pago_select)
            content.add_widget(pago_spinner)

            save_button = Button(text="Guardar Compra", font_size='14sp', size_hint=(1, None), height=38, background_color=(0.2, 0.5, 0.3, 1), background_normal='')
            save_button.bind(on_press=lambda btn: (
                self.save_purchase(
                    total=total,
                    detalles=", ".join([f"{n} - ${p:,.2f}" for n, p in self.cart]),
                    pago=pago_spinner.text
                ) if pago_spinner.text != 'Seleccionar método de pago' else (
                    Popup(title="Atención", content=Label(text="Seleccione un método de pago."), size_hint=(None, None), size=(300, 150)).open()
                )
            ))
            content.add_widget(save_button)

        btn_close = Button(text="Cerrar", size_hint=(1, None), height=35, on_press=lambda x: self.cart_popup.dismiss(), background_color=(0.4, 0.4, 0.4, 1), background_normal='')
        content.add_widget(btn_close)

        self.cart_popup = Popup(title="Carrito de Compras", content=content, size_hint=(None, None), size=(380, 400))
        self.cart_popup.open()

    def remove_from_cart(self, product_name):
        for item in self.cart:
            if item[0] == product_name:
                self.cart.remove(item)
                break
        try:
            self.cart_popup.dismiss()
        except:
            pass
        self.show_cart(None)

    def show_debt_popup(self):
        debt_popup_content = BoxLayout(orientation='vertical', spacing=10, padding=15)
        debt_name_input = TextInput(hint_text="Nombre del deudor", font_size='14sp', size_hint_y=None, height=35, multiline=False)
        debt_popup_content.add_widget(debt_name_input)

        debt_popup = Popup(title="Registrar Deudor", content=debt_popup_content, size_hint=(None, None), size=(340, 180))

        def on_debt_save(instance):
            debtor_name = debt_name_input.text.strip()
            print("Nombre ingresado:", debtor_name)
            if debtor_name:
                self.save_debt_info(debtor_name)
                try:
                    self.cart_popup.dismiss()
                except:
                    pass
                debt_popup.dismiss()
            else:
                Popup(title="Error", content=Label(text="Ingrese un nombre válido."), size_hint=(None, None), size=(300, 140)).open()

        debt_save_button = Button(text="Guardar Deudor", font_size='13sp', size_hint_y=None, height=35, background_color=(0.2, 0.5, 0.3, 1), background_normal='')
        debt_save_button.bind(on_press=on_debt_save)
        debt_popup_content.add_widget(debt_save_button)

        debt_cancel_button = Button(text="Cancelar", font_size='13sp', size_hint_y=None, height=35, background_color=(0.6, 0.2, 0.2, 1), background_normal='')
        debt_cancel_button.bind(on_press=lambda btn: debt_popup.dismiss())
        debt_popup_content.add_widget(debt_cancel_button)

        debt_popup.open()

    def save_debt_info(self, debtor_name):
        print("Entró a save_debt_info")
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        fecha_actual = datetime.datetime.now().strftime('%Y-%m-%d')
        total_deuda = sum([p for n, p in self.cart])
        productos_str = ", ".join([f"{n} - ${p:,.2f}" for n, p in self.cart])

        cursor.execute("""
            INSERT INTO deudores (fecha, nombre, productos, total)
            VALUES (?, ?, ?, ?)
        """, (fecha_actual, debtor_name, productos_str, total_deuda))
        print("INSERT realizado")

        conn.commit()
        conn.close()

        self.save_purchase(
            total=total_deuda,
            detalles=f"Deudor: {debtor_name} - {productos_str}",
            pago="En Deuda"
        )

        popup_exito = Popup(title="Éxito", content=Label(text=f"Deudor guardado correctamente."), size_hint=(None, None), size=(300, 140))
        popup_exito.open()
        Clock.schedule_once(lambda dt: popup_exito.dismiss(), 1.5)

    def add_to_cart(self, product_name, product_price):
        try:
            product_price = round(float(product_price), 2)
            self.cart.append((product_name, product_price))
            
            p = Popup(title="", content=Label(text=f"✔ {product_name} agregado", font_size='13sp'), size_hint=(None, None), size=(200, 90), separator_height=0)
            p.open()
            Clock.schedule_once(lambda dt: p.dismiss(), 0.8)
        except ValueError:
            Popup(title="Error", content=Label(text="Precio no válido."), size_hint=(None, None), size=(300, 140)).open()

    def save_purchase(self, total, detalles, pago):
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        fecha_actual = datetime.datetime.now().strftime('%Y-%m-%d')
        horas = datetime.datetime.now().strftime('%H:%M:%S')
        total = round(float(total), 2)

        cursor.execute("""
            INSERT INTO ventas_diarias (fecha, horas, detalles, total, pago)
            VALUES (?, ?, ?, ?, ?)
        """, (fecha_actual, horas, detalles, total, pago))

        conn.commit()
        conn.close()

        confirmation_popup = Popup(title="Guardado", content=Label(text=f"Venta de ${total:,.2f} registrada."), size_hint=(None, None), size=(300, 140))
        confirmation_popup.open()
        Clock.schedule_once(lambda dt: confirmation_popup.dismiss(), 1.5)

        self.cart.clear()


# ==========================================
# PANTALLA PRODUCTOS (CON PANEL LATERAL)
# ==========================================
class ProductsScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.main_layout = BoxLayout(orientation='vertical')
        self.add_widget(self.main_layout)

    def on_enter(self):
        self.main_layout.clear_widgets()
        self.main_layout.add_widget(HeaderBar("Productos y Carrito", self.manager))

        content_split = BoxLayout(orientation='horizontal', spacing=10, padding=10)

        left_box = BoxLayout(orientation='vertical', size_hint_x=0.65)
        scroll_view = ScrollView()
        self.grid_layout = GridLayout(cols=1, spacing=8, size_hint_y=None, padding=5)
        self.grid_layout.bind(minimum_height=self.grid_layout.setter('height'))
        scroll_view.add_widget(self.grid_layout)
        left_box.add_widget(scroll_view)
        content_split.add_widget(left_box)

        self.right_cart_box = BoxLayout(orientation='vertical', padding=10, spacing=8, size_hint_x=0.35)
        content_split.add_widget(self.right_cart_box)

        self.main_layout.add_widget(content_split)
        self.update_product_list()
        self.update_live_cart_panel()

    def add_to_cart(self, name, price):
        main_screen = self.manager.get_screen('main')
        main_screen.add_to_cart(name, price)
        self.update_live_cart_panel()

    def remove_from_live_cart(self, name):
        main_screen = self.manager.get_screen('main')
        for item in main_screen.cart:
            if item[0] == name:
                main_screen.cart.remove(item)
                break
        self.update_live_cart_panel()

    def update_live_cart_panel(self):
        self.right_cart_box.clear_widgets()
        self.right_cart_box.add_widget(Label(text="[b]Carrito Actual[/b]", markup=True, font_size='15sp', size_hint_y=None, height=30, color=(0.95, 0.6, 0.2, 1)))

        main_screen = self.manager.get_screen('main')
        scroll_cart = ScrollView(size_hint=(1, 0.7))
        cart_grid = GridLayout(cols=1, spacing=5, size_hint_y=None)
        cart_grid.bind(minimum_height=cart_grid.setter('height'))

        total = 0
        if not main_screen.cart:
            cart_grid.add_widget(Label(text="Vacío", font_size='13sp', color=(0.5, 0.5, 0.5, 1)))
        else:
            for name, price in main_screen.cart:
                row = BoxLayout(size_hint_y=None, height=30, spacing=5)
                row.add_widget(Label(text=f"{name}", font_size='12sp', halign='left', size_hint_x=0.6))
                row.add_widget(Label(text=f"${price:,.0f}", font_size='12sp', halign='right', size_hint_x=0.4))
                
                btn_del = Button(text="X", size_hint=(None, None), size=(25, 25), background_color=(0.7, 0.2, 0.2, 1), background_normal='', font_size='10sp')
                btn_del.bind(on_press=lambda x, n=name: self.remove_from_live_cart(n))
                row.add_widget(btn_del)
                
                cart_grid.add_widget(row)
                total += price

        scroll_cart.add_widget(cart_grid)
        self.right_cart_box.add_widget(scroll_cart)

        self.right_cart_box.add_widget(Label(text=f"Total: ${total:,.2f}", font_size='14sp', bold=True, size_hint_y=None, height=30))
        
        btn_go_cart = Button(text="Ver / Pagar", font_size='13sp', size_hint_y=None, height=38, background_color=(0.2, 0.5, 0.3, 1), background_normal='')
        btn_go_cart.bind(on_press=lambda x: main_screen.show_cart(None))
        self.right_cart_box.add_widget(btn_go_cart)

    def update_product_list(self):
        self.grid_layout.clear_widgets()
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT Nombre, Precio FROM Productos")
        products = cursor.fetchall()
        conn.close()

        if not products:
            self.grid_layout.add_widget(Label(text="No hay productos cargados.", font_size='14sp', color=(0.6, 0.6, 0.6, 1)))
            return

        for name, price in products:
            product_card = BoxLayout(orientation='horizontal', size_hint_y=None, height=45, spacing=10, padding=5)

            text_label = Label(text=f"{name} - ${price:,.2f}", font_size='14sp', size_hint_x=0.7, halign='left', valign='middle')
            text_label.bind(size=text_label.setter('text_size'))
            product_card.add_widget(text_label)

            add_button = Button(
                text="Añadir",
                background_normal='',
                background_color=(0.2, 0.5, 0.3, 1),
                size_hint_x=0.3,
                font_size='13sp'
            )
            add_button.bind(on_press=lambda btn, n=name, p=price: self.add_to_cart(n, p))
            product_card.add_widget(add_button)

            self.grid_layout.add_widget(product_card)


# ==========================================
# VENTAS DIARIAS (CON FORMATO Y ANCHOS AJUSTADOS)
# ==========================================
class DailySalesScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.layout = BoxLayout(orientation='vertical')
        self.add_widget(self.layout)

    def on_enter(self):
        self.load_sales()

    def load_sales(self):
        self.layout.clear_widgets()
        self.layout.add_widget(HeaderBar("Ventas Diarias", self.manager))
        
        content = BoxLayout(orientation='vertical', padding=15, spacing=10)
        
        top_buttons_layout = BoxLayout(size_hint=(1, None), height=38, spacing=10)
        btn_close_day = Button(text="Cerrar Día", font_size='13sp', background_color=(0.2, 0.5, 0.3, 1), background_normal='')
        btn_close_day.bind(on_press=self.cerrar_dia)
        btn_revertir_cierre = Button(text="Revertir Cierre", font_size='13sp', background_color=(0.6, 0.3, 0.3, 1), background_normal='')
        btn_revertir_cierre.bind(on_press=self.revertir_cierre)
        
        top_buttons_layout.add_widget(btn_close_day)
        top_buttons_layout.add_widget(btn_revertir_cierre)
        content.add_widget(top_buttons_layout)

        scroll_view = ScrollView()
        # Usamos anchos fijos y proporcionales para evitar superposición
        self.grid = GridLayout(cols=6, spacing=6, padding=[0, 5], size_hint_y=None, size_hint_x=1)
        self.grid.bind(minimum_height=self.grid.setter('height'))
        scroll_view.add_widget(self.grid)
        content.add_widget(scroll_view)

        self.layout.add_widget(content)

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT id, fecha, horas, detalles, total, pago FROM ventas_diarias WHERE fecha IS NOT NULL AND fecha != ''")
        ventas = cursor.fetchall()
        conn.close()

        if not ventas:
            self.grid.cols = 1
            self.grid.add_widget(Label(text="No hay ventas registradas hoy.", font_size='14sp', size_hint_y=None, height=40))
        else:
            self.grid.cols = 6
            headers = [("N°", 0.08), ("Fecha", 0.15), ("Hora", 0.12), ("Detalles", 0.40), ("Total", 0.15), ("Acción", 0.10)]
            
            for h_text, h_width in headers:
                self.grid.add_widget(Label(text=h_text, font_size='13sp', bold=True, size_hint_x=h_width, size_hint_y=None, height=35))

            for venta in ventas:
                id, fecha, horas, detalles, total, pago = venta
                
                # Fila con tamaño dinámico y text_size adaptado para evitar superposición
                lbl_id = Label(text=str(id), font_size='12sp', size_hint_x=0.08, size_hint_y=None, height=45)
                lbl_fec = Label(text=str(fecha), font_size='12sp', size_hint_x=0.15, size_hint_y=None, height=45)
                lbl_hor = Label(text=str(horas), font_size='12sp', size_hint_x=0.12, size_hint_y=None, height=45)
                
                lbl_det = Label(text=str(detalles), font_size='11sp', size_hint_x=0.40, size_hint_y=None, height=45, halign='left', valign='middle')
                lbl_det.bind(size=lbl_det.setter('text_size'))
                
                lbl_tot = Label(text=f"${float(total):,.2f}", font_size='12sp', size_hint_x=0.15, size_hint_y=None, height=45)

                delete_button = Button(text="Eliminar", size_hint=(None, None), size=(65, 30), background_color=(0.7, 0.2, 0.2, 1), background_normal='', font_size='11sp')
                delete_button.bind(on_press=partial(self.delete_sale, id_venta=id))

                self.grid.add_widget(lbl_id)
                self.grid.add_widget(lbl_fec)
                self.grid.add_widget(lbl_hor)
                self.grid.add_widget(lbl_det)
                self.grid.add_widget(lbl_tot)
                self.grid.add_widget(delete_button)

    def delete_sale(self, button_instance, id_venta):
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM ventas_diarias WHERE id = ?', (int(id_venta),))
        conn.commit()
        conn.close()
        self.load_sales()

    def cerrar_dia(self, *args):
        Popup(title="Cierre", content=Label(text="Día cerrado correctamente."), size_hint=(None, None), size=(300, 140)).open()

    def revertir_cierre(self, *args):
        Popup(title="Reversión", content=Label(text="Acción lista."), size_hint=(None, None), size=(300, 140)).open()


# ==========================================
# CALCULADORA
# ==========================================
class CalculadoraScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.layout = BoxLayout(orientation='vertical')
        self.add_widget(self.layout)

    def on_enter(self):
        self.layout.clear_widgets()
        self.layout.add_widget(HeaderBar("Calculadora", self.manager))
        
        content = BoxLayout(orientation='vertical', padding=20, spacing=15)
        self.calc_input = TextInput(text='', font_size='22sp', readonly=True, size_hint=(1, None), height=50, halign='right')
        content.add_widget(self.calc_input)

        buttons = [
            ('7', '8', '9', '/'),
            ('4', '5', '6', '*'),
            ('1', '2', '3', '-'),
            ('C', '0', '=', '+')
        ]

        for row in buttons:
            r_layout = BoxLayout(spacing=5, size_hint_y=None, height=45)
            for char in row:
                btn = Button(text=char, font_size='16sp', background_color=(0.3, 0.3, 0.3, 1), background_normal='')
                btn.bind(on_press=self.on_button_press)
                r_layout.add_widget(btn)
            content.add_widget(r_layout)

        self.layout.add_widget(content)

    def on_button_press(self, instance):
        text = instance.text
        if text == 'C':
            self.calc_input.text = ''
        elif text == '=':
            try:
                self.calc_input.text = str(eval(self.calc_input.text))
            except:
                self.calc_input.text = 'Error'
        else:
            self.calc_input.text += text


# ==========================================
# TOTAL VENTAS
# ==========================================
class TotalSalesScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.layout = BoxLayout(orientation='vertical')
        self.add_widget(self.layout)

    def on_enter(self):
        self.layout.clear_widgets()
        self.layout.add_widget(HeaderBar("Total Ventas", self.manager))
        
        content = BoxLayout(orientation='vertical', padding=15, spacing=10)
        scroll = ScrollView()
        self.grid = GridLayout(cols=5, spacing=5, size_hint_y=None)
        self.grid.bind(minimum_height=self.grid.setter('height'))
        scroll.add_widget(self.grid)
        content.add_widget(scroll)
        self.layout.add_widget(content)
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT fecha, numdeventas, efectivo, mercadopago, total FROM total_ventas")
        rows = cursor.fetchall()
        conn.close()

        headers = ["Fecha", "N° Ventas", "Efectivo", "Mercado Pago", "Total"]
        for h in headers:
            self.grid.add_widget(Label(text=h, font_size='13sp', bold=True, size_hint_y=None, height=35))

        if not rows:
            self.grid.cols = 1
            self.grid.add_widget(Label(text="No hay cierres registrados.", font_size='13sp', size_hint_y=None, height=40))
        else:
            self.grid.cols = 5
            for r in rows:
                for col in r:
                    self.grid.add_widget(Label(text=str(col), font_size='12sp', size_hint_y=None, height=40))


# ==========================================
# DEUDORES
# ==========================================
class DeudoresScreen(Screen):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.layout = BoxLayout(orientation='vertical')
        self.add_widget(self.layout)

    def on_enter(self):
        self.load_deudores()

    def load_deudores(self):
        self.layout.clear_widgets()
        self.layout.add_widget(HeaderBar("Deudores", self.manager))

        content = BoxLayout(
            orientation='vertical',
            padding=15,
            spacing=10
        )

        scroll = ScrollView()

        contenedor = GridLayout(
            cols=1,
            spacing=5,
            size_hint_y=None
        )
        contenedor.bind(minimum_height=contenedor.setter('height'))

        scroll.add_widget(contenedor)
        content.add_widget(scroll)
        self.layout.add_widget(content)

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, fecha, nombre, productos, total
            FROM deudores
            WHERE estado='Pendiente'
            ORDER BY id DESC
        """)

        deudores = cursor.fetchall()
        conn.close()

        if not deudores:
            contenedor.add_widget(
                Label(
                    text="No hay deudores registrados.",
                    font_size='14sp',
                    size_hint_y=None,
                    height=40
                )
            )
            return

    # ===========================
    # CABECERA
    # ===========================

        header = BoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=35,
            spacing=5
        )

        header.add_widget(Label(text="N°", bold=True, size_hint_x=0.08))
        header.add_widget(Label(text="Fecha", bold=True, size_hint_x=0.15))
        header.add_widget(Label(text="Nombre", bold=True, size_hint_x=0.18))
        header.add_widget(Label(text="Productos", bold=True, size_hint_x=0.32))
        header.add_widget(Label(text="Total", bold=True, size_hint_x=0.12))
        header.add_widget(Label(text="Acción", bold=True, size_hint_x=0.15))

        contenedor.add_widget(header)

    # ===========================
    # FILAS
    # ===========================

        for deuda in deudores:

            deuda_id, fecha, nombre, productos, total = deuda

            fila = BoxLayout(
                orientation='horizontal',
                size_hint_y=None,
                height=45,
                spacing=5
            )

            fila.add_widget(
                Label(
                    text=str(deuda_id),
                    size_hint_x=0.08
                )
            )

            fila.add_widget(
                Label(
                    text=fecha,
                    size_hint_x=0.15
                )
            )

            fila.add_widget(
                Label(
                    text=nombre,
                    size_hint_x=0.18
                ) 
            )

            lbl = Label(
                text=productos,
                size_hint_x=0.32,
                halign='left',
                valign='middle'
            )

            lbl.bind(size=lbl.setter("text_size"))

            fila.add_widget(lbl)

            fila.add_widget(
                Label(
                    text=f"${float(total):,.2f}",
                    size_hint_x=0.12
                )
            )

            btn = Button(
                text="Pagó",
                size_hint_x=0.15,
                background_normal="",
                background_color=(0.2, 0.6, 0.2, 1)
            )

            btn.bind(
                on_press=lambda x, did=deuda_id: self.pagar_deuda(did)
            )

            fila.add_widget(btn)

            contenedor.add_widget(fila)

    def pagar_deuda(self, deuda_id):
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE deudores
            SET estado='Pagado'
            WHERE id=?
        """, (deuda_id,))

        conn.commit()
        conn.close()

        self.load_deudores()


# ==========================================
# GASTOS
# ==========================================
class GastosScreen(Screen):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.layout = BoxLayout(orientation="vertical")
        self.add_widget(self.layout)

    def on_enter(self):
        self.load_gastos_ui()

    def load_gastos_ui(self):

        self.layout.clear_widgets()

        self.layout.add_widget(HeaderBar("Gastos", self.manager))

        content = BoxLayout(
            orientation="vertical",
            padding=20,
            spacing=10
        )

        titulo = Label(
            text="Administración de Gastos",
            font_size="18sp",
            bold=True,
            size_hint=(1, None),
            height=40,
            color=(0.95, 0.6, 0.2, 1)
        )
        content.add_widget(titulo)

        subtitulo = Label(
            text="Registrar, editar y eliminar gastos operativos.",
            font_size="14sp",
            color=(0.7, 0.7, 0.7, 1),
            size_hint=(1, None),
            height=30
        )
        content.add_widget(subtitulo)

        btn_add = Button(
            text="+ Agregar Gasto",
            size_hint=(1, None),
            height=45,
            background_normal="",
            background_color=(0.2, 0.6, 0.3, 1)
        )
        btn_add.bind(on_press=self.show_add_gasto_popup)
        content.add_widget(btn_add)

        # Encabezados
        header = GridLayout(
            cols=4,
            size_hint=(1, None),
            height=35,
            spacing=10
        )

        header.add_widget(Label(
            text="[b]Fecha[/b]",
            markup=True
        ))

        header.add_widget(Label(
            text="[b]Detalle[/b]",
            markup=True
        ))

        header.add_widget(Label(
            text="[b]Monto[/b]",
            markup=True
        ))

        header.add_widget(Label(
            text="[b]Acciones[/b]",
            markup=True
        ))

        content.add_widget(header)

        scroll = ScrollView()

        self.gastos_grid = GridLayout(
            cols=1,
            spacing=8,
            size_hint_y=None,
            padding=5
        )

        self.gastos_grid.bind(
            minimum_height=self.gastos_grid.setter("height")
        )

        scroll.add_widget(self.gastos_grid)
        content.add_widget(scroll)

        self.lbl_total = Label(
            text="Total Gastos: $0.00",
            font_size="16sp",
            bold=True,
            size_hint=(1, None),
            height=40,
            color=(1, 0.8, 0.2, 1)
        )

        content.add_widget(self.lbl_total)

        self.layout.add_widget(content)

        self.refresh_gastos()

    # ==========================================
    # RECARGAR LISTA
    # ==========================================
    def refresh_gastos(self):

        self.gastos_grid.clear_widgets()

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, fecha, detalle, total
            FROM gastos
            ORDER BY id DESC
        """)

        gastos = cursor.fetchall()

        total_general = 0

        if not gastos:

            self.gastos_grid.add_widget(
                Label(
                    text="No hay gastos registrados.",
                    size_hint_y=None,
                    height=40
                )
            )

            self.lbl_total.text = "Total Gastos: $0.00"

            conn.close()
            return

        for gasto in gastos:

            gasto_id, fecha, detalle, total = gasto

            total_general += total

            fila = GridLayout(
                cols=4,
                size_hint_y=None,
                height=45,
                spacing=10
            )

            fila.add_widget(
                Label(
                    text=fecha
                )
            )

            fila.add_widget(
                Label(
                    text=detalle
                )
            )

            fila.add_widget(
                Label(
                    text=f"${total:,.2f}"
                )
            )

            acciones = BoxLayout(
                spacing=5
            )

            btn_edit = Button(
                text="Editar",
                background_normal="",
                background_color=(0.25, 0.45, 0.85, 1)
            )

            btn_edit.bind(
                on_press=lambda x,
                gid=gasto_id,
                f=fecha,
                d=detalle,
                t=total:
                self.show_edit_gasto_popup(
                    gid,
                    f,
                    d,
                    t
                )
            )

            acciones.add_widget(btn_edit)

            btn_delete = Button(
                text="Eliminar",
                background_normal="",
                background_color=(0.8, 0.2, 0.2, 1)
            )

            btn_delete.bind(
                on_press=lambda x,
                gid=gasto_id:
                self.delete_gasto(gid)
            )

            acciones.add_widget(btn_delete)

            fila.add_widget(acciones)

            self.gastos_grid.add_widget(fila)

        self.lbl_total.text = f"Total Gastos: ${total_general:,.2f}"

        conn.close()
        # ==========================================
    # POPUP AGREGAR
    # ==========================================
    def show_add_gasto_popup(self, instance):

        layout = BoxLayout(
            orientation="vertical",
            spacing=10,
            padding=15
        )

        fecha = TextInput(
            text=datetime.datetime.now().strftime("%d/%m/%Y"),
            multiline=False
        )

        detalle = TextInput(
            hint_text="Detalle del gasto",
            multiline=False
        )

        total = TextInput(
            hint_text="Monto",
            multiline=False,
            input_filter="float"
        )

        layout.add_widget(Label(text="Fecha"))
        layout.add_widget(fecha)

        layout.add_widget(Label(text="Detalle"))
        layout.add_widget(detalle)

        layout.add_widget(Label(text="Monto"))
        layout.add_widget(total)

        botones = BoxLayout(
            size_hint_y=None,
            height=45,
            spacing=10
        )

        popup = Popup(
            title="Agregar Gasto",
            content=layout,
            size_hint=(0.75, 0.65)
        )

        btn_guardar = Button(text="Guardar")
        btn_cancelar = Button(text="Cancelar")

        botones.add_widget(btn_guardar)
        botones.add_widget(btn_cancelar)

        layout.add_widget(botones)

        btn_guardar.bind(
            on_press=lambda x: self.save_gasto(
                popup,
                fecha.text,
                detalle.text,
                total.text
            )
        )

        btn_cancelar.bind(on_press=popup.dismiss)

        popup.open()

    # ==========================================
    # GUARDAR
    # ==========================================
    def save_gasto(self, popup, fecha, detalle, total):

        if detalle.strip() == "" or total.strip() == "":
            return

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO gastos
            (fecha, detalle, total)
            VALUES (?, ?, ?)
        """, (
            fecha,
            detalle,
            float(total)
        ))

        conn.commit()
        conn.close()

        popup.dismiss()

        self.refresh_gastos()

    # ==========================================
    # POPUP EDITAR
    # ==========================================
    def show_edit_gasto_popup(self, gasto_id, fecha_actual, detalle_actual, total_actual):

        layout = BoxLayout(
            orientation="vertical",
            spacing=10,
            padding=15
        )

        fecha = TextInput(
            text=fecha_actual,
            multiline=False
        )

        detalle = TextInput(
            text=detalle_actual,
            multiline=False
        )

        total = TextInput(
            text=str(total_actual),
            multiline=False,
            input_filter="float"
        )

        layout.add_widget(Label(text="Fecha"))
        layout.add_widget(fecha)

        layout.add_widget(Label(text="Detalle"))
        layout.add_widget(detalle)

        layout.add_widget(Label(text="Monto"))
        layout.add_widget(total)

        botones = BoxLayout(
            size_hint_y=None,
            height=45,
            spacing=10
        )

        popup = Popup(
            title="Editar Gasto",
            content=layout,
            size_hint=(0.75, 0.65)
        )

        btn_guardar = Button(text="Guardar")
        btn_cancelar = Button(text="Cancelar")

        botones.add_widget(btn_guardar)
        botones.add_widget(btn_cancelar)

        layout.add_widget(botones)

        btn_guardar.bind(
            on_press=lambda x: self.update_gasto(
                popup,
                gasto_id,
                fecha.text,
                detalle.text,
                total.text
            )
        )

        btn_cancelar.bind(on_press=popup.dismiss)

        popup.open()

    # ==========================================
    # ACTUALIZAR
    # ==========================================
    def update_gasto(self, popup, gasto_id, fecha, detalle, total):

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE gastos
            SET fecha=?,
                detalle=?,
                total=?
            WHERE id=?
        """, (
            fecha,
            detalle,
            float(total),
            gasto_id
        ))

        conn.commit()
        conn.close()

        popup.dismiss()

        self.refresh_gastos()

    # ==========================================
    # ELIMINAR
    # ==========================================
    def delete_gasto(self, gasto_id):

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute("""
            DELETE FROM gastos
            WHERE id=?
        """, (
            gasto_id,
        ))

        conn.commit()
        conn.close()

        self.refresh_gastos()




# ==========================================
# CONFIGURACIÓN
# ==========================================
class ConfigScreen(Screen):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.layout = BoxLayout(orientation="vertical")
        self.add_widget(self.layout)

    def on_enter(self):
        self.load_config_ui()

    def load_config_ui(self):

        self.layout.clear_widgets()

        self.layout.add_widget(
            HeaderBar("Configuración", self.manager)
        )

        content = BoxLayout(
            orientation="vertical",
            padding=20,
            spacing=15
        )

        titulo = Label(
            text="Administración de Productos",
            font_size="20sp",
            bold=True,
            color=(0.95, 0.6, 0.2, 1),
            size_hint_y=None,
            height=35
        )

        subtitulo = Label(
            text="Agregar, editar y eliminar productos del menú.",
            font_size="14sp",
            color=(0.65,0.65,0.65,1),
            size_hint_y=None,
            height=25
        )

        content.add_widget(titulo)
        content.add_widget(subtitulo)

        btn_add = Button(
            text="+ Agregar Producto",
            size_hint=(1,None),
            height=45,
            font_size="15sp",
            background_normal="",
            background_color=(0.18,0.60,0.30,1)
        )

        btn_add.bind(on_press=self.show_add_product_popup)

        content.add_widget(btn_add)

        encabezado = BoxLayout(
            size_hint_y=None,
            height=35,
            spacing=10
        )

        encabezado.add_widget(Label(
            text="Producto",
            bold=True,
            halign="left"
        ))

        encabezado.add_widget(Label(
            text="Precio",
            bold=True,
            size_hint_x=.30
        ))

        encabezado.add_widget(Label(
            text="Acciones",
            bold=True,
            size_hint_x=.45
        ))

        content.add_widget(encabezado)

        scroll = ScrollView()

        self.prod_grid = GridLayout(
            cols=1,
            spacing=8,
            padding=5,
            size_hint_y=None
        )

        self.prod_grid.bind(
            minimum_height=self.prod_grid.setter("height")
        )

        scroll.add_widget(self.prod_grid)

        content.add_widget(scroll)

        self.layout.add_widget(content)

        self.refresh_product_management_list()

    # -------------------------------------------------

    def refresh_product_management_list(self):

        self.prod_grid.clear_widgets()

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, Nombre, Precio
            FROM Productos
            ORDER BY Nombre
        """)

        productos = cursor.fetchall()

        conn.close()

        if len(productos) == 0:

            self.prod_grid.add_widget(

                Label(
                    text="No existen productos cargados.",
                    size_hint_y=None,
                    height=45,
                    color=(0.6,0.6,0.6,1)
                )

            )

            return

        for pid, nombre, precio in productos:

            fila = BoxLayout(
                orientation="horizontal",
                spacing=10,
                size_hint_y=None,
                height=45
            )

            lbl_nombre = Label(
                text=nombre,
                halign="left",
                valign="middle"
            )

            lbl_nombre.bind(
                size=lbl_nombre.setter("text_size")
            )

            fila.add_widget(lbl_nombre)

            fila.add_widget(

                Label(
                    text=f"${precio:,.2f}",
                    size_hint_x=.30
                )

            )

            acciones = BoxLayout(
                spacing=5,
                size_hint_x=.45
            )

            btn_edit = Button(
                text="Editar",
                background_normal="",
                background_color=(0.22,0.45,0.85,1)
            )

            btn_edit.bind(

                on_press=lambda x,
                idp=pid,
                nom=nombre,
                pre=precio:
                self.show_edit_product_popup(
                    idp,
                    nom,
                    pre
                )

            )

            acciones.add_widget(btn_edit)

            btn_delete = Button(
                text="Eliminar",
                background_normal="",
                background_color=(0.75,0.20,0.20,1)
            )

            btn_delete.bind(

                on_press=lambda x,
                idp=pid:
                self.delete_product(idp)

            )

            acciones.add_widget(btn_delete)

            fila.add_widget(acciones)

            self.prod_grid.add_widget(fila)

    # -------------------------------------------------

    def show_add_product_popup(self, instance):

        layout = BoxLayout(
            orientation="vertical",
            spacing=10,
            padding=15
        )

        txt_nombre = TextInput(
            hint_text="Nombre del producto",
            multiline=False
        )

        txt_precio = TextInput(
            hint_text="Precio",
            multiline=False,
            input_filter="float"
        )

        layout.add_widget(txt_nombre)
        layout.add_widget(txt_precio)

        botones = BoxLayout(
            spacing=10,
            size_hint_y=None,
            height=40
        )

        btn_guardar = Button(
            text="Guardar",
            background_normal="",
            background_color=(0.18,0.60,0.30,1)
        )

        btn_cancelar = Button(
            text="Cancelar",
            background_normal="",
            background_color=(0.60,0.20,0.20,1)
        )

        botones.add_widget(btn_guardar)
        botones.add_widget(btn_cancelar)

        layout.add_widget(botones)

        popup = Popup(
            title="Agregar Producto",
            content=layout,
            size_hint=(None,None),
            size=(400,240)
        )

        btn_cancelar.bind(
            on_press=lambda x: popup.dismiss()
        )

        btn_guardar.bind(
            on_press=lambda x:
            self.save_product(
                popup,
                txt_nombre.text,
                txt_precio.text
            )
        )

        popup.open()


        # -------------------------------------------------
    # GUARDAR PRODUCTO
    # -------------------------------------------------

    def save_product(self, popup, nombre, precio):

        nombre = nombre.strip()

        if nombre == "":
            Popup(
                title="Error",
                content=Label(text="Ingrese un nombre."),
                size_hint=(None,None),
                size=(300,150)
            ).open()
            return

        try:
            precio = float(precio)
        except:
            Popup(
                title="Error",
                content=Label(text="Precio inválido."),
                size_hint=(None,None),
                size=(300,150)
            ).open()
            return

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO Productos
            (Nombre, Precio)
            VALUES (?,?)
        """,(nombre,precio))

        conn.commit()
        conn.close()

        popup.dismiss()

        self.refresh_product_management_list()

    # -------------------------------------------------
    # EDITAR
    # -------------------------------------------------

    def show_edit_product_popup(self, pid, nombre, precio):

        layout = BoxLayout(
            orientation="vertical",
            spacing=10,
            padding=15
        )

        txt_nombre = TextInput(
            text=str(nombre),
            multiline=False
        )

        txt_precio = TextInput(
            text=str(precio),
            multiline=False,
            input_filter="float"
        )

        layout.add_widget(txt_nombre)
        layout.add_widget(txt_precio)

        botones = BoxLayout(
            spacing=10,
            size_hint_y=None,
            height=40
        )

        btn_guardar = Button(
            text="Guardar Cambios",
            background_normal="",
            background_color=(0.20,0.45,0.80,1)
        )

        btn_cancelar = Button(
            text="Cancelar",
            background_normal="",
            background_color=(0.60,0.20,0.20,1)
        )

        botones.add_widget(btn_guardar)
        botones.add_widget(btn_cancelar)

        layout.add_widget(botones)

        popup = Popup(
            title="Editar Producto",
            content=layout,
            size_hint=(None,None),
            size=(420,250)
        )

        btn_cancelar.bind(
            on_press=lambda x: popup.dismiss()
        )

        btn_guardar.bind(
            on_press=lambda x:
            self.update_product(
                popup,
                pid,
                txt_nombre.text,
                txt_precio.text
            )
        )

        popup.open()

    # -------------------------------------------------
    # ACTUALIZAR
    # -------------------------------------------------

    def update_product(self, popup, pid, nombre, precio):

        nombre = nombre.strip()

        if nombre == "":
            Popup(
                title="Error",
                content=Label(text="Ingrese un nombre."),
                size_hint=(None,None),
                size=(300,150)
            ).open()
            return

        try:
            precio = float(precio)
        except:
            Popup(
                title="Error",
                content=Label(text="Precio inválido."),
                size_hint=(None,None),
                size=(300,150)
            ).open()
            return

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE Productos
            SET Nombre=?,
                Precio=?
            WHERE id=?
        """,(nombre,precio,pid))

        conn.commit()
        conn.close()

        popup.dismiss()

        self.refresh_product_management_list()

    # -------------------------------------------------
    # ELIMINAR
    # -------------------------------------------------

    def delete_product(self, pid):

        contenido = BoxLayout(
            orientation="vertical",
            spacing=15,
            padding=15
        )

        contenido.add_widget(

            Label(
                text="¿Desea eliminar este producto?"
            )

        )

        botones = BoxLayout(
            spacing=10,
            size_hint_y=None,
            height=40
        )

        btn_si = Button(
            text="Eliminar",
            background_normal="",
            background_color=(0.75,0.20,0.20,1)
        )

        btn_no = Button(
            text="Cancelar",
            background_normal="",
            background_color=(0.35,0.35,0.35,1)
        )

        botones.add_widget(btn_si)
        botones.add_widget(btn_no)

        contenido.add_widget(botones)

        popup = Popup(
            title="Confirmación",
            content=contenido,
            size_hint=(None,None),
            size=(340,180)
        )

        btn_no.bind(
            on_press=lambda x: popup.dismiss()
        )

        def confirmar(instance):

            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()

            cursor.execute(
                "DELETE FROM Productos WHERE id=?",
                (pid,)
            )

            conn.commit()
            conn.close()

            popup.dismiss()

            self.refresh_product_management_list()

        btn_si.bind(on_press=confirmar)

        popup.open()


# ==========================================
# APLICACIÓN PRINCIPAL
# ==========================================
class OasisFoodTruckApp(App):
    def build(self):
        init_db()
        sm = ScreenManager()
        sm.add_widget(MainScreen(name='main'))
        sm.add_widget(ProductsScreen(name='products'))
        sm.add_widget(DailySalesScreen(name='daily_sales'))
        sm.add_widget(CalculadoraScreen(name='calcular_sales'))
        sm.add_widget(TotalSalesScreen(name='total_ventas'))
        sm.add_widget(DeudoresScreen(name='deudores'))
        sm.add_widget(ConfigScreen(name='configuracion'))
        sm.add_widget(GastosScreen(name='gastos'))
        return sm

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

cursor.execute("PRAGMA table_info(Productos)")
print(cursor.fetchall())

conn.close()

if __name__ == '__main__':
    OasisFoodTruckApp().run()