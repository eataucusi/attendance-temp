"""Principal

Classes:
    Check
    Login
    Menu
    Date
    UserPass
    UserList
    UserPics
    AddFace
    UserAdd
    UserEdit
    Board
"""
import tkinter as tk
from PIL import ImageTk, Image
from datetime import datetime
import threading
import tkinter.messagebox
import tkinter.ttk
import requests
import cv
import db
import theme


class Check(object):
    """Registra asistencia y temperatura.

    Args:
        parent: Ventana padre.

    Attributes:
        root: Ventana padre.
        window: Ventana actual.
        canvas: Lienzo para mostrar la lectura de la cámara.
        recognize: Objeto que detecta rostros en imágenes.
        label: Etiqueta que muestra información al usuario.
        label_timer: Temporizador para la etiqueta.
        label_job: Llamada a una función pasado un tiempo para la etiqueta.
        canvas_job: Llamada a una función pasado un tiempo para el lienzo.
        clock_job: Llamada a una función pasado un segundo para el reloj.
        icon: Set de íconos.

    """

    root = None
    window = None
    canvas = None
    recognize = None
    label = None
    label_timer = 15
    label_job = None
    canvas_job = None
    clock_job = None

    def __init__(self, parent):
        self.root = parent
        self.window = tk.Toplevel(parent)  # Crear ventana hija
        self.window.title('Control de acceso')
        self.window.protocol("WM_DELETE_WINDOW", self._on_press_close)
        self.window.attributes('-fullscreen', True)
        parent.withdraw()  # Ocultar ventana padre
        self.canvas = tk.Canvas(self.window, width=480, height=640)
        self.canvas.pack()  # Crear y ubicar canvas
        self.icon = theme.Icon.instance()
        self.label = tk.Label(
            self.window, text='Ubique sus ojos\nen el recuadro',
            font=('Arial', 20))  # Crear y ubicar label
        self.label.place(width=260, relx=0.5, x=-130, y=150)
        self.name = tk.Label(
            self.window, text='Cargando ...',
            font=('Arial', 20))  # Crear y ubicar label
        self.name.place(width=400, relx=0.5, x=-200, y=400)
        self._clock = tk.Label(self.window, font=('Arial', 28))
        self._clock.pack(fill=tk.X)
        self._update_clock()
        job = threading.Timer(1, self._load_recognizer)
        job.start()

    def _update_clock(self):
        """Actualizar el reloj cada segundo."""
        date = datetime.now()  # Fecha y hora actual
        self._clock.configure(text=date.strftime('%H:%M:%S\n%d/%m/%Y'))
        self.clock_job = threading.Timer(1, self._update_clock)
        self.clock_job.start()

    def _load_recognizer(self):
        """Iniciar el reconocimiento."""
        self.recognize = cv.Recognize()
        self.update_canvas()
        self.name.place_forget()
        tk.Button(self.window, text='Administrador', image=self.icon.lock,
                  compound='left', command=self._on_press_login
                  ).pack(fill=tk.X)
        tk.Button(self.window, text='Salir', compound='left',
                  image=self.icon.exit, command=self._on_press_close
                  ).pack(fill=tk.X)

    def update_canvas(self):
        """Actualizar contenido del canvas contenedor de imagen.

        El canvas muestra la imagen capturada por la cámara, puede
        detectar un rostro en la imagen.

        """
        if self.label_timer == 0:
            image = self.recognize.load(True)
            self.label.place_forget()  # Ocultar información
            self.name.place_forget()
        else:
            if self.label_job is None:
                self.label_timer -= 1
            image = self.recognize.load(False)
        image = ImageTk.PhotoImage(Image.fromarray(image))  # Array a Imagen
        self.canvas.image = image  # Evitar el recolector de basura
        self.canvas.delete('all')  # Limpiar
        self.canvas.create_image(0, 0, anchor=tk.NW, image=image)
        if self.recognize.found_nose:
            cv.Helper.play('sound/mascarilla.mp3')
            db.DB.event_denied(0)
            self.label.place(width=260, relx=0.5, x=-130, y=150)
            self.recognize.reset()
            self.label_timer = 5
            self.update_label()
            self.canvas_job = self.window.after(1000, self.update_canvas)
        elif self.recognize.found_face:
            if self.recognize.avg_temp() > 38:
                cv.Helper.play('sound/temperatura.mp3')
            else:
                cv.Helper.play('sound/correcto.mp3')
            user = db.DB.user_by_id(self.recognize.face_of)
            db.DB.event_insert(user[0][0], self.recognize.avg_temp(),
                               self.recognize.recog_time(),
                               self.recognize.gauge_time())
            self.name.configure(text=user[0][2])
            self.recognize.reset()
            self.name.place(width=400, relx=0.5, x=-200, y=400)
            self.label.place(width=260, relx=0.5, x=-130, y=150)
            self.label_timer = 5
            self.update_label()
            self.canvas_job = self.window.after(1500, self.update_canvas)
        elif self.recognize.count == 10:
            cv.Helper.play('sound/denegado.mp3')
            db.DB.event_denied()
            self.recognize.reset()
            self.label_timer = 3
            self.label.place(width=260, relx=0.5, x=-130, y=150)
            self.update_label()
            self.canvas_job = self.window.after(1000, self.update_canvas)
        else:
            self.canvas_job = self.window.after(125, self.update_canvas)

    def update_label(self):
        """Actualizar el label cada segundo.
        """
        if self.label_timer == 1:
            self.label.place_forget()
        else:
            self.label.config(text=f'Próxima captura en\n{self.label_timer}')
            # Actualizar label luego de un segundo
            self.label_job = threading.Timer(1, self.update_label)
            self.label_job.start()
        self.label_timer -= 1

    def _on_press_close(self):
        """Cerrar ventana. """
        if self.canvas_job is not None:
            self.window.after_cancel(self.canvas_job)  # Cancelar pendiente
        if self.label_job is not None:
            self.label_job.cancel()  # Cancelar pendiente
        if self.clock_job is not None:
            self.clock_job.cancel()  # Cancelar pendiente
        self.root.destroy()  # Cerrar ventanas

    def _on_press_login(self):
        """Abrir login. """
        if self.canvas_job is not None:
            self.window.after_cancel(self.canvas_job)  # Cancelar pendiente
            self.canvas_job = None
        if self.label_job is not None:
            self.label_job.cancel()  # Cancelar pendiente
            self.label_job = None
        self.name.place_forget()
        Login(self)


class Login(object):
    """Iniciar sesión.

    Args:
        parent: Objeto que invoca a este objeto.

    Attributes:
        _parent: Objeto padre.
        _window: Interfaz gráfica de inicio de sesión.

    """
    _parent = None
    _window = None

    def __init__(self, parent):
        self._parent = parent
        self._window = tk.Toplevel(parent.window)  # Crear ventana hija
        self._window.title('Acceder')
        self._window.focus_force()
        parent.window.withdraw()  # Ocultar ventana padre
        self._window.attributes('-fullscreen', True)
        self._window.protocol("WM_DELETE_WINDOW", self._on_press_close)
        self._window.rowconfigure(0, weight=1)  # Única de altura 100%
        self._window.columnconfigure(0, weight=1)  # Columna con 50% de ancho
        self._window.columnconfigure(1, weight=1)  # Columna con 50% de ancho
        left_frame = tk.Frame(self._window)
        right_frame = tk.Frame(self._window)
        left_frame.grid(row=0, column=0, sticky='nsew')  # Poner en 0, 0
        right_frame.grid(row=0, column=1, sticky='nsew')  # Poner en 0, 1
        left_frame.columnconfigure(0, weight=1)  # Ancho 100%
        right_frame.columnconfigure(0, weight=1)  # Ancho 100%
        # Posicionados a la derecha con sticky e (este)
        tk.Label(left_frame, text='Usuario').grid(
            row=0, column=0, sticky='e', padx=5, pady=10, ipady=3)
        tk.Label(left_frame, text='Contraseña').grid(
            row=1, column=0, sticky='e', padx=5, pady=10, ipady=3)
        tk.Button(left_frame, text='Atras', command=self._on_press_close,
                  compound='left', image=parent.icon.back).grid(
            row=2, column=0, padx=5, pady=10, ipadx=5, sticky='e')
        # Posicionados a la izquierda con sticky w (west)
        board = Board(self._window)
        dni_text = tk.Entry(right_frame)
        dni_text.grid(row=0, column=0, sticky='w', padx=5, pady=10, ipady=3)
        dni_text.bind('<Button-1>', board.show)
        pass_text = tk.Entry(right_frame)
        pass_text.grid(row=1, column=0, sticky='w', padx=5, pady=10, ipady=3)
        pass_text.bind('<Button-1>', board.show)
        tk.Button(right_frame, text='Acceder', command=lambda:
        self._on_press_login(dni_text.get(), pass_text.get()),
                  compound='right', image=parent.icon.next).grid(
            row=2, column=0, padx=5, pady=14, ipadx=5, sticky='w')

    def _on_press_login(self, dni, passw):
        """Al Enviar datos."""
        user = db.DB.user_login(dni, passw)
        if len(user):
            self._window.destroy()
            Menu(self._parent, user[0][0])
            del self
        else:
            tk.messagebox.showerror(
                message='Datos incorrectos', title='No pudo Acceder')

    def _on_press_close(self):
        """Al cerra la ventana."""
        self._parent.window.deiconify()  # Restaurar ventana
        self._parent.update_canvas()  # Actualizar lienzo
        self._window.destroy()
        del self


class Menu(object):
    """Menu principal.

    Args:
        parent: Objeto que invoca a este objeto.

    Attributes:
        parent: Objeto padre.
        window: Interfaz gráfica del menu.
        id: Identificador de usuario que inició sesión.

    Methods:
        _on_press_close
        _on_press_list
        _on_press_pass
        _on_press_date
        _on_press_train
        _on_press_sync
    """
    parent = None
    window = None
    id = None

    def __init__(self, parent, id):
        self.parent = parent
        self.id = id
        self.window = tk.Toplevel(parent.window)  # Crear ventana hija
        self.window.title('Menú')
        self.window.focus_force()
        parent.window.withdraw()  # Ocultar ventana padre
        self.window.attributes('-fullscreen', True)
        self.window.protocol("WM_DELETE_WINDOW", self._on_press_close)
        self.window.columnconfigure(0, weight=1)  # Ancho 100%
        tk.Button(self.window, image=parent.icon.users, text='Ver Usuarios',
                  compound='left', anchor='w', command=self._on_press_list
                  ).grid(row=0, column=0, sticky='we')
        tk.Button(self.window, image=parent.icon.lock,
                  text='Cambiar Contraseña', compound='left', anchor='w',
                  command=self._on_press_pass
                  ).grid(row=1, column=0, sticky='we')
        tk.Button(self.window, image=parent.icon.clock, text='Cambiar Hora',
                  compound='left', anchor='w', command=self._on_press_date
                  ).grid(row=2, column=0, sticky='we')
        tk.Button(self.window, image=parent.icon.train,
                  text='Entrenar y salir', compound='left', anchor='w',
                  command=self._on_press_train).grid(row=3, column=0,
                                                     sticky='we')
        tk.Button(self.window, text='Sincronizar', compound='left', anchor='w',
                  image=parent.icon.sync, command=self._on_press_sync
                  ).grid(row=4, column=0, sticky='we')
        tk.Button(self.window, text='Salir', compound='left', anchor='w',
                  image=parent.icon.exit, command=self._on_press_close
                  ).grid(row=5, column=0, sticky='we')

    def _on_press_close(self):
        """Al cerrar la ventana."""
        self.parent.window.deiconify()  # Restaurar ventana
        self.parent.update_canvas()  # Actualizar lienzo
        self.window.destroy()
        del self

    def _on_press_list(self):
        """Al presionar sobre listar usuarios."""
        UserList(self)

    def _on_press_pass(self):
        """Al presionar sobre cambiar contraseña."""
        UserPass(self)

    def _on_press_date(self):
        """Al presionar sobre cambiar fecha."""
        Date(self)

    def _on_press_train(self):
        """Al presionar sobre Entrenar."""
        title = 'Iniciar entrenamiento'
        message = 'Este proceso se debe ejecutar al insertar nuevos rostros'
        if tk.messagebox.askyesno(title, message, parent=self.window):
            for child in self.window.winfo_children():
                child.configure(state=tk.DISABLED)
            cv.Train()
            for child in self.window.winfo_children():
                child.configure(state=tk.NORMAL)
            tk.messagebox.showinfo('Ejecutado correctamente',
                                   'Debe volver a iniciar la aplicación.',
                                   parent=self.window)
            self.window.destroy()
            self.parent.root.destroy()

    def _on_press_sync(self):
        """Al presionar sobre sincronizar."""
        myurl = 'https://edisonat.com/main/sync'
        files = {'db': open('db.db', 'rb')}
        nav = 'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:47.0)' \
              'Gecko/20100101 Firefox/47.0'
        getdata = requests.post(myurl, files=files, data={'_token': '-'},
                                headers={'User-Agent': nav})
        print(getdata.text)


class Date(object):
    """Cambiar de fecha.

    Args:
        parent: Objeto que invoca a este objeto.

    Attributes:
        _icon: Set de íconos.
        _parent: Objeto padre.
        _window: Interfaz gráfica para el cambio de fecha y hora.

    Methods:
        _on_press_close
        _on_press_save
    """

    def __init__(self, parent):
        self._icon = theme.Icon.instance()
        self._parent = parent
        parent.window.withdraw()
        self._window = tk.Toplevel(parent.window, padx=10)
        self._window.title('Cambiar fecha y hora')
        self._window.focus_force()  # Foco en la ventana
        self._window.attributes('-fullscreen', True)
        self._window.protocol("WM_DELETE_WINDOW", self._on_press_close)
        date = datetime.now()
        tk.Label(self._window, text='Día', anchor='w', pady=5).pack(fill=tk.X)
        day_cbx = tk.ttk.Combobox(self._window, state='readonly',
                                  values=list(range(1, 32)))
        day_cbx.pack(fill=tk.X)
        tk.Label(self._window, text='Mes', anchor='w', pady=5).pack(fill=tk.X)
        month_cbx = tk.ttk.Combobox(self._window, state='readonly',
                                    values=list(range(1, 13)))
        month_cbx.pack(fill=tk.X)
        tk.Label(self._window, text='Año', anchor='w', pady=5).pack(fill=tk.X)
        year_cbx = tk.ttk.Combobox(
            self._window, state='readonly',
            values=list(range(date.year - 5, date.year + 5)))
        year_cbx.pack(fill=tk.X)
        tk.Label(self._window, text='Hora', anchor='w', pady=5).pack(fill=tk.X)
        hour_cbx = tk.ttk.Combobox(self._window, state='readonly',
                                   values=list(range(0, 24)))
        hour_cbx.pack(fill=tk.X)
        tk.Label(self._window, text='Minuto',
                 anchor='w', pady=5).pack(fill=tk.X)
        min_cbx = tk.ttk.Combobox(self._window, state='readonly',
                                  values=list(range(0, 60)))
        min_cbx.pack(fill=tk.X)
        tk.Label(self._window, text='Segundo',
                 anchor='w', pady=5).pack(fill=tk.X)
        sec_cbx = tk.ttk.Combobox(self._window, state='readonly',
                                  values=list(range(0, 60)))
        sec_cbx.pack(fill=tk.X)
        # Establecer valores actuales
        day_cbx.current(date.day - 1)
        month_cbx.current(date.month - 1)
        year_cbx.current(5)
        hour_cbx.current(date.hour)
        min_cbx.current(date.minute)
        sec_cbx.current(date.second)
        # Botonera
        btn_frm = tk.Frame(self._window, pady=20)
        btn_frm.pack(fill=tk.X)
        btn_frm.columnconfigure(0, weight=1)
        btn_frm.columnconfigure(1, weight=1)
        tk.Button(btn_frm, text='Volver', image=self._icon.back,
                  compound='left', command=self._on_press_close).grid(
            row=0, column=0, ipadx=10)
        tk.Button(btn_frm, text='Guardar', image=self._icon.disk,
                  compound='right', command=lambda: self._on_press_save(
                day_cbx.get(), month_cbx.get(), year_cbx.get(),
                hour_cbx.get(), min_cbx.get(), sec_cbx.get())
                  ).grid(row=0, column=1, ipadx=10)

    def _on_press_close(self):
        """Al cerrar la ventana."""
        self._parent.window.deiconify()  # Restaurar ventana
        self._window.destroy()
        del self

    def _on_press_save(self, day, month, year, hour, min, sec):
        """Al presionar guardar."""
        cmd = f'date --set "{year}-{month}-{day} {hour}:{min}:{sec}"'
        cv.Helper.set_date(cmd)
        self._on_press_close()


class UserPass(object):
    """Cambiar contraseña del administrador.

    Args:
        parent: Objeto que invoca a este objeto.

    Attributes:
        _icon: Set de íconos.
        _parent: Objeto padre.
        _window: Interfaz gráfica para el cambio de contraseña.

    Methods:
        _on_press_close
        _on_press_save
    """

    def __init__(self, parent):
        self._icon = theme.Icon.instance()
        self._parent = parent
        parent.window.withdraw()
        self._window = tk.Toplevel(parent.window, padx=10)
        self._window.title('Cambiar clave')
        self._window.focus_force()  # Foco en la ventana
        self._window.attributes('-fullscreen', True)
        self._window.protocol("WM_DELETE_WINDOW", self._on_press_close)
        tk.Label(self._window, text='Clave',
                 anchor='w', pady=5).pack(fill=tk.X)
        board = Board(self._window)
        pass_txt = tk.Entry(self._window)
        pass_txt.pack(fill=tk.X)
        pass_txt.bind('<Button-1>', board.show)
        tk.Label(self._window, text='Nueva clave',
                 anchor='w', pady=5).pack(fill=tk.X)
        pass1_txt = tk.Entry(self._window)
        pass1_txt.pack(fill=tk.X)
        pass1_txt.bind('<Button-1>', board.show)
        btn_frm = tk.Frame(self._window, pady=20)
        btn_frm.pack(fill=tk.X)
        btn_frm.columnconfigure(0, weight=1)
        btn_frm.columnconfigure(1, weight=1)
        tk.Button(btn_frm, text='Volver', image=self._icon.back,
                  compound='left', command=self._on_press_close).grid(
            row=0, column=0, ipadx=10)
        tk.Button(btn_frm, text='Guardar', image=self._icon.disk,
                  compound='right', command=lambda: self._on_press_save(
                pass_txt.get(), pass1_txt.get())).grid(row=0, column=1,
                                                       ipadx=10)

    def _on_press_close(self):
        """Al cerrar la ventana."""
        self._parent.window.deiconify()  # Restaurar ventana
        self._window.destroy()
        del self

    def _on_press_save(self, passw, passw1):
        """Al presionar en guardar."""
        user = db.DB.user_by_id(self._parent.id)
        if user[0][4] == passw:
            db.DB.user_pass_update(passw1, user[0][0])
            title = 'Operación correcta'
            message = 'Se ha guardado su nueva clave.'
            tk.messagebox.showinfo(title, message, parent=self._window)
            self._on_press_close()
        else:
            title = 'Error al cambiar clave'
            message = 'La clave actual no coincide.'
            tk.messagebox.showerror(title, message, parent=self._window)


class UserList(object):
    """Listar usuarios..

    Args:
        parent: Objeto que invoca a este objeto.

    Attributes:
        parent: Objeto padre.
        window: Interfaz gráfica para listar usuarios.
        table: Tabla para mostrar usuarios.
        _edit: Botón editar de cada usuario.
        _delete: Botón Eliminar de cada usuario.
        _icon: Set de íconos.
        _pics: Botón mostrar rostros.

    Methods:
        _on_select
        _on_press_delete
        _on_press_add
        _on_press_edit
        _on_press_pics
        _on_press_close
    """
    parent = None
    window = None
    table = None
    _edit = None
    _delete = None

    def __init__(self, parent):
        self._icon = theme.Icon.instance()
        self.parent = parent
        self.window = tk.Toplevel(parent.window)  # Crear ventana hija
        self.window.title('Lista de usuarios')
        self.window.focus_force()
        parent.window.withdraw()  # Ocultar ventana padre
        self.window.attributes('-fullscreen', True)
        self.window.protocol("WM_DELETE_WINDOW", self._on_press_close)
        self.window.columnconfigure(0, weight=1)  # Las 4 columnas
        self.window.columnconfigure(1, weight=1)
        self.window.columnconfigure(2, weight=1)
        self.window.columnconfigure(3, weight=1)
        self.window.rowconfigure(0, pad=10)  # Las 2 filas
        self.window.rowconfigure(1, weight=1)
        # Los botones de la parte superior
        tk.Button(self.window, text='Volver', compound='left',
                  image=self._icon.back, command=self._on_press_close
                  ).grid(row=0, column=0, ipadx=5)
        tk.Button(self.window, text='Nuevo', compound='left',
                  image=self._icon.user_add, command=self._on_press_add
                  ).grid(row=0, column=1, ipadx=5)
        self._pics = tk.Button(self.window, text='Rostros', compound='left',
                               state=tk.DISABLED,
                               image=self._icon.camera,
                               command=self._on_press_pics)
        self._pics.grid(row=0, column=2, ipadx=5)
        self._edit = tk.Button(self.window, text='Editar', compound='left',
                               state=tk.DISABLED,
                               image=self._icon.edit,
                               command=self._on_press_edit)
        self._edit.grid(row=0, column=3, ipadx=5)
        self._delete = tk.Button(self.window, text='Eliminar',
                                 compound='left',
                                 state=tk.DISABLED,
                                 image=self._icon.delete,
                                 command=self._on_press_delete)
        self._delete.grid(row=0, column=4, ipadx=5)
        # La tabla
        self.table = tk.ttk.Treeview(
            self.window, columns=('#1', '#2', '#3'), selectmode=tk.BROWSE)
        self.table.heading('#0', text='Apellidos y nombres')  # Encabezados
        self.table.heading('#1', text='DNI')
        self.table.heading('#2', text='Admin')
        self.table.heading('#3', text='Faces')
        self.table.column('#1', width=80, stretch=False)  # Anchos
        self.table.column('#2', width=45, stretch=False)
        self.table.column('#3', width=45, stretch=False)
        self.table.grid(row=1, column=0, columnspan=5, sticky='nsew')
        scroll = tk.ttk.Scrollbar(self.window, orient="vertical",
                                  command=self.table.yview)  # table a scroll
        scroll.grid(row=1, column=5, sticky='snew')
        self.table.configure(yscrollcommand=scroll.set)  # scroll a table
        data = db.DB.user_list()  # Consulta bd
        tk.Label(self.window, text=f'{len(data)} registros').grid(
            row=2, column=0, columnspan=4)
        for row in data:
            admin = '*' if row[3] == 'Administrador' else ''
            self.table.insert(
                '', tk.END, iid=row[0], text=row[2], values=(row[1], admin,
                                                             row[5]))
        self.table.bind('<<TreeviewSelect>>', self._on_select)

    def _on_select(self, event):
        """Al seleccionar item de la tabla."""
        self._edit.configure(state=tk.NORMAL)  # Habilitar botones
        self._delete.configure(state=tk.NORMAL)
        self._pics.configure(state=tk.NORMAL)

    def _on_press_delete(self):
        """Al presionar eliminar. """
        id = self.table.selection()  # Seleccionado
        if len(id):
            message = '¿Desea eliminar este usuario?\n' + \
                      self.table.item(id[0], 'text')
            title = 'Eliminar usuario'
            if tk.messagebox.askyesno(title, message, parent=self.window):
                self.table.delete(id[0])
                self._edit.configure(state=tk.DISABLED)  # Deshabilitar botones
                self._delete.configure(state=tk.DISABLED)
                self._pics.configure(state=tk.DISABLED)
                db.DB.user_delete(id[0])
                cv.Helper.remove_dir('data/' + str(id[0]))

    def _on_press_add(self):
        """Al presionar agregar. """
        UserAdd(self)

    def _on_press_edit(self):
        """Al presionar editar. """
        id = self.table.selection()  # Seleccionado
        if len(id):
            UserEdit(self)

    def _on_press_pics(self):
        id = self.table.selection()  # Seleccionado
        if len(id):
            UserPics(self)

    def _on_press_close(self):
        """Al cerrar la ventana. """
        self.parent.window.deiconify()  # Restaurar ventana
        self.window.destroy()
        del self


class UserPics(object):
    """Listar rostros de un usuario.

    Args:
        parent: Objeto que invoca a este objeto.

    Attributes:
        _icon: Set de íconos.
        parent: Objeto padre.
        window: Interfaz gráfica para listar rostros.

    Methods:
        update
        _on_press_delete
        _on_press_add
        _on_press_close

    """

    def __init__(self, parent):
        self._icon = theme.Icon.instance()
        self.parent = parent
        self.window = tk.Toplevel(parent.window)
        self.window.title('Lista de rostros')
        parent.window.withdraw()
        self.window.attributes('-fullscreen', True)
        self.window.protocol("WM_DELETE_WINDOW", self._on_press_close)
        self.window.focus_force()  # Foco en la ventana
        self.window.columnconfigure(0, weight=1)
        self.window.columnconfigure(1, weight=1)
        self.window.rowconfigure(0, pad=10)
        tk.Button(self.window, text='Volver', compound='left',
                  image=self._icon.back, command=self._on_press_close
                  ).grid(row=0, column=0, ipadx=10)
        tk.Button(self.window, text='Capturar', compound='right',
                  image=self._icon.camera, command=self._on_press_add
                  ).grid(row=0, column=1, ipadx=10)
        self._frame = None
        self.update()

    def update(self):
        """Actualizar la lista de rostros."""
        if self._frame is not None:
            self._frame.destroy()
        self._frame = tk.Frame(self.window)
        self._frame.grid(row=1, column=0, columnspan=2, sticky='EW')
        self._frame.columnconfigure(0, weight=1)
        self._frame.columnconfigure(1, weight=1)
        self._frame.columnconfigure(2, weight=1)
        pics = cv.Helper.get_pics(str(self.parent.table.selection()[0]))
        col = 0
        row = 0
        for pic in pics:
            image = ImageTk.PhotoImage(Image.open(pic))
            delete = tk.Button(self._frame, image=image, bg='white')
            delete.grid(row=row, column=col)
            delete.image = image
            delete.path = pic
            delete.bind('<Button-1>', self._on_press_delete)
            col += 1
            if col % 3 == 0:
                col = 0
                row += 1

    def _on_press_delete(self, event):
        """Al presionar sobre eliminar rostro."""
        title = 'Eliminar imagen'
        message = '¿Desea eliminar esta imagen?'
        event.widget.configure(bg='yellow')
        if tk.messagebox.askyesno(title, message, parent=self.window):
            cv.Helper.remove_file(event.widget.path)
            id = self.parent.table.selection()[0]
            db.DB.user_pic_delete(str(id))
            values = self.parent.table.item(id, 'values')
            self.parent.table.item(id, values=(
                values[0], values[1], int(values[2]) - 1))
            self.update()
        else:
            event.widget.configure(bg='white')

    def _on_press_add(self):
        """Al presionar sobre agregar rostro."""
        AddFace(self)

    def _on_press_close(self):
        """Al cerrar ventana. """
        self.parent.window.deiconify()
        self.window.destroy()
        del self


class AddFace(object):
    """Agregar rostros de un usuario.

    Args:
        parent: Objeto que invoca a este objeto.

    Attributes:
        _window: Interfaz gráfica para agregar rostro.
        _canvas: Lienzo para mostrar la lectura de la cámara.
        _capture: Objeto que detecta rostros en imágenes.
        _label: Etiqueta que muestra información al usuario.
        _label_timer: Temporizador para la etiqueta.
        _label_job: Llamada a un función pasado un tiempo para la etiqueta.
        _canvas_job: Llamada a un función pasado un tiempo para el lienzo.
        _icon: Set de íconos.
        _parent: Ventana padre.

    Methods:
        _update_canvas
        _update_label
        _on_press_close
    """
    _window = None
    _canvas = None
    _capture = None
    _label = None
    _label_timer = 15
    _label_job = None
    _canvas_job = None

    def __init__(self, parent):
        self._icon = theme.Icon.instance()
        self._parent = parent
        self._window = tk.Toplevel(parent.window)  # Crear ventana hija
        self._window.title('Agregar rostro')
        parent.window.withdraw()  # Ocultar ventana padre
        self._window.attributes('-fullscreen', True)
        self._window.focus_force()  # Foco en la ventana
        self._canvas = tk.Canvas(self._window, width=480, height=640)
        self._canvas.pack()  # Crear y ubicar canvas
        self._capture = cv.Capture(str(parent.parent.table.selection()[0]),
                                   parent.parent.parent.parent.recognize.cap)
        tk.Button(self._window, text='Volver', image=self._icon.back,
                  compound='left', command=self._on_press_close).pack(ipadx=10)
        self._label = tk.Label(
            self._window, text='Ubique sus ojos\nen el recuadro',
            font=('Arial', 20))  # Crear y ubicar label
        self._label.place(width=260, relx=0.5, x=-130, y=150)
        self._update_canvas()

    def _update_canvas(self):
        """Actualizar contenido del canvas contenedor de imagen.

        El canvas muestra la imagen capturada por la cámara, puede
        detectar un rostro en la imagen.

        """
        if self._label_timer == 0:
            image = self._capture.load(True)
            self._label.place_forget()  # Ocultar información
        else:
            if self._label_job is None:
                self._label_timer -= 1
            image = self._capture.load(False)
        image = ImageTk.PhotoImage(Image.fromarray(image))  # Array a Imagen
        self._canvas.image = image  # Evitar el recolector de basura
        self._canvas.delete('all')  # Limpiar
        self._canvas.create_image(0, 0, anchor=tk.NW, image=image)
        if self._capture.is_face:  # ¿Detectó un rostro?
            self._capture.is_face = False
            self._label_timer = 4
            self._label.place(width=260, relx=0.5, x=-130, y=150)
            cv.Helper.play('sound/correcto.mp3')
            id = self._parent.parent.table.selection()[0]
            db.DB.user_pic_add(str(id))
            values = self._parent.parent.table.item(id, 'values')
            self._parent.parent.table.item(id, values=(
                values[0], values[1], int(values[2]) + 1))
            self._update_label()
            # Actualizar contenido del canvas luego de un segundo.
            self._canvas_job = self._window.after(1000, self._update_canvas)
        else:
            # Actualizar contenido del canvas luego de 125 milisegundos.
            self._canvas_job = self._window.after(125, self._update_canvas)

    def _update_label(self):
        """Actualizar el label cada segundo."""
        if self._label_timer == 1:
            self._label.place_forget()
        else:
            self._label.config(text=f'Próxima captura en\n{self._label_timer}')
            # Actualizar label luego de un segundo
            self._label_job = threading.Timer(1, self._update_label)
            self._label_job.start()
        self._label_timer -= 1

    def _on_press_close(self):
        """Al cerrar ventana. """
        if self._canvas_job is not None:
            self._window.after_cancel(self._canvas_job)  # Cancelar pendiente
            self._canvas_job = None
        if self._label_job is not None:
            self._label_job.cancel()  # Cancelar pendiente
            self._label_job = None
        self._parent.window.deiconify()  # Cerrar ventanas
        self._parent.update()
        self._window.destroy()
        del self


class UserAdd(object):
    """Agregar usuario.

    Args:
        parent: Objeto que invoca a este objeto.

    Attributes:
        _parent: Objeto padre.
        _window: Interfaz gráfica para editar usuario
        _icon: Set de íconos.

    Methods:
        _on_press_save
        _on_press_close

    """
    _parent = None
    _window = None

    def __init__(self, parent):
        self._icon = theme.Icon.instance()
        self._parent = parent
        parent.window.withdraw()
        self._window = tk.Toplevel(parent.window, padx=10)
        self._window.title('Editar usuario')
        self._window.focus_force()  # Foco en la ventana
        self._window.attributes('-fullscreen', True)
        self._window.protocol("WM_DELETE_WINDOW", self._on_press_close)
        tk.Label(self._window, text='DNI', anchor='w', pady=5).pack(fill=tk.X)
        board = Board(self._window)
        dni_txt = tk.Entry(self._window)
        dni_txt.pack(fill=tk.X)
        dni_txt.bind('<Button-1>', board.show)
        tk.Label(self._window, text='Apellidos y nombres',
                 anchor='w', pady=5).pack(fill=tk.X)
        name_txt = tk.Entry(self._window)
        name_txt.pack(fill=tk.X)
        name_txt.bind('<Button-1>', board.show)
        tk.Label(self._window, text='Tipo de usuario',
                 anchor='w', pady=5).pack(fill=tk.X)
        rol_cbx = tk.ttk.Combobox(self._window,
                                  values=['Usuario', 'Administrador'],
                                  state='readonly')
        rol_cbx.pack(fill=tk.X)
        tk.Label(self._window, text='Clave',
                 anchor='w', pady=5).pack(fill=tk.X)
        pass_txt = tk.Entry(self._window)
        pass_txt.pack(fill=tk.X)
        pass_txt.bind('<Button-1>', board.show)
        btn_frm = tk.Frame(self._window, pady=20)
        btn_frm.pack(fill=tk.X)
        btn_frm.columnconfigure(0, weight=1)
        btn_frm.columnconfigure(1, weight=1)
        tk.Button(btn_frm, text='Volver', image=self._icon.back,
                  compound='left', command=self._on_press_close).grid(
            row=0, column=0, ipadx=10)
        tk.Button(btn_frm, text='Guardar', image=self._icon.disk,
                  compound='right', command=lambda: self._on_press_save(
                dni_txt.get(), name_txt.get(), rol_cbx.get(),
                pass_txt.get())).grid(row=0, column=1, ipadx=10)
        rol_cbx.current(0)

    def _on_press_save(self, dni, name, rol, passw):
        """Al presionar guardar. """
        if dni == '' or name == '' or rol == '':
            tk.messagebox.showerror('Datos incompletos',
                                    'Complete los datos requeridos.',
                                    parent=self._window)
            return
        user = db.DB.user_by_dni(dni)
        if len(user):
            tk.messagebox.showerror('El usuario ya existe',
                                    'Este DNI ya fue asignado a un usuario.',
                                    parent=self._window)
        else:
            id = db.DB.user_insert(dni, name, rol, passw)
            # Actualizar con datos obtenidos y nuevos.
            rol = '*' if rol == 'Administrador' else ''
            self._parent.table.insert(
                '', tk.END, iid=id, text=name, values=(dni, rol, 0))
            self._parent.table.see(id)
            self._parent.table.selection_set(id)
            self._on_press_close()  # Cerrar ventana

    def _on_press_close(self):
        """Al cerrar ventana. """
        self._parent.window.deiconify()
        self._window.destroy()
        del self


class UserEdit(object):
    """Editar usuario.

    Args:
        parent: Objeto que invoca a este objeto.

    Attributes:
        _parent: Objeto padre.
        _window: Interfaz gráfica para editar usuario.
        _icon: Set de íconos.

    Methods:
        _on_press_save
        _on_press_close
    """
    _parent = None
    _window = None

    def __init__(self, parent):
        id = parent.table.selection()[0]
        user = db.DB.user_by_id(id)
        if not len(user):
            return
        self._icon = theme.Icon.instance()
        self._parent = parent
        parent.window.withdraw()
        self._window = tk.Toplevel(parent.window, padx=10)
        self._window.title('Editar usuario')
        self._window.focus_force()  # Foco en la ventana
        self._window.attributes('-fullscreen', True)
        self._window.protocol("WM_DELETE_WINDOW", self._on_press_close)
        tk.Label(self._window, text='DNI', anchor='w', pady=5).pack(fill=tk.X)
        board = Board(self._window)
        dni_txt = tk.Entry(self._window)
        dni_txt.pack(fill=tk.X)
        dni_txt.bind('<Button-1>', board.show)
        tk.Label(self._window, text='Apellidos y nombres',
                 anchor='w', pady=5).pack(fill=tk.X)
        name_txt = tk.Entry(self._window)
        name_txt.pack(fill=tk.X)
        name_txt.bind('<Button-1>', board.show)
        tk.Label(self._window, text='Tipo de usuario',
                 anchor='w', pady=5).pack(fill=tk.X)
        rol_cbx = tk.ttk.Combobox(self._window,
                                  values=['Usuario', 'Administrador'],
                                  state='readonly')
        rol_cbx.pack(fill=tk.X)
        tk.Label(self._window, text='Clave',
                 anchor='w', pady=5).pack(fill=tk.X)
        pass_txt = tk.Entry(self._window)
        pass_txt.pack(fill=tk.X)
        pass_txt.bind('<Button-1>', board.show)
        btn_frm = tk.Frame(self._window, pady=20)
        btn_frm.pack(fill=tk.X)
        btn_frm.columnconfigure(0, weight=1)
        btn_frm.columnconfigure(1, weight=1)
        tk.Button(btn_frm, text='Volver', image=self._icon.back,
                  compound='left', command=self._on_press_close).grid(
            row=0, column=0, ipadx=10)
        tk.Button(btn_frm, text='Guardar', image=self._icon.disk,
                  compound='right', command=lambda: self._on_press_save(
                dni_txt.get(), name_txt.get(), rol_cbx.get(),
                pass_txt.get(), id)).grid(row=0, column=1, ipadx=10)
        dni_txt.insert(tk.END, user[0][1])
        name_txt.insert(tk.END, user[0][2])
        if user[0][3] == 'Administrador':
            rol_cbx.current(1)
        else:
            rol_cbx.current(0)
        pass_txt.insert(tk.END, user[0][4])

    def _on_press_save(self, dni, name, rol, passw, id):
        """Al presionar guardar. """
        if dni == '' or name == '' or rol == '':
            tk.messagebox.showerror('Datos incompletos',
                                    'Complete los datos requeridos.',
                                    parent=self._window)
            return
        user = db.DB.user_by_dni(dni)
        if len(user) and int(id) != int(user[0][0]):
            tk.messagebox.showerror('El usuario ya existe',
                                    'Este DNI ya fue asignado a un usuario.',
                                    parent=self._window)
        else:
            db.DB.user_update(id, dni, name, rol, passw)
            # Actualizar con datos obtenidos y nuevos.
            rol = '*' if rol == 'Administrador' else ''
            faces = self._parent.table.item(id, 'values')[2]
            self._parent.table.item(id, text=name, values=(dni, rol, faces))
            self._on_press_close()  # Cerrar ventana

    def _on_press_close(self):
        """Al cerrar ventana. """
        self._parent.window.deiconify()
        self._window.destroy()
        del self


class Board(object):
    """Teclado virtual.

    Args:
        root: Ventana raíz.

    Attributes:
        _frame: Marco del teclado.
        _entry: Cuadro de texto actual.
        _icon: Íconos.
        _display: ¿Se muestra el teclado virtual?

    Methods:
        show
        _space
        _press
        _delete
        _hide
    """
    _frame = None
    _entry = None
    _icon = None
    _display = False

    def __init__(self, root):
        self._icon = theme.Icon.instance()
        self._frame = tk.Frame(root)
        row1 = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '0']
        for i in range(0, 10):
            btn = tk.Button(
                self._frame, text=row1[i], bg='#333366', fg='#ffffff')
            btn.id = row1[i]
            btn.grid(row=0, column=i, sticky='NSEW')
            self._frame.columnconfigure(i, weight=1)
            btn.bind('<Button-1>', self._press)
        row1 = ['q', 'w', 'e', 'r', 't', 'y', 'u', 'i', 'o', 'p']
        for i in range(0, 10):
            btn = tk.Button(
                self._frame, text=row1[i], bg='#333366', fg='#ffffff')
            btn.id = row1[i]
            btn.grid(row=1, column=i, sticky='NSEW')
            btn.bind('<Button-1>', self._press)
        row1 = ['a', 's', 'd', 'f', 'g', 'h', 'j', 'k', 'l', 'ñ']
        for i in range(0, 10):
            btn = tk.Button(
                self._frame, text=row1[i], bg='#333366', fg='#ffffff')
            btn.id = row1[i]
            btn.grid(row=2, column=i, sticky='NSEW')
            btn.bind('<Button-1>', self._press)
        row1 = ['z', 'x', 'c', 'v', 'b', 'n', 'm']
        for i in range(0, 7):
            btn = tk.Button(
                self._frame, text=row1[i], bg='#333366', fg='#ffffff')
            btn.id = row1[i]
            btn.grid(row=3, column=i, sticky='NSEW')
            btn.bind('<Button-1>', self._press)
        btn = tk.Button(self._frame, image=self._icon.space,
                        command=self._space, bg='#669999')
        btn.grid(row=3, column=7, sticky='NSEW')
        btn = tk.Button(self._frame, image=self._icon.backspace,
                        command=self._delete, bg='#669999')
        btn.grid(row=3, column=8, sticky='NSEW')
        btn = tk.Button(self._frame, image=self._icon.check,
                        command=self._hide, bg='#669999')
        btn.grid(row=3, column=9, sticky='NSEW')

    def show(self, event):
        """Mostrar teclado. """
        if self._entry == event.widget:
            if self._display:
                self._hide()
                return
        self._entry = event.widget
        y = self._entry.winfo_y() + self._entry.winfo_height()
        self._frame.place(width=300, relx=0.5, x=-150, y=y)
        self._frame.lift()
        self._display = True

    def _space(self):
        """Barra espaciadora. """
        self._entry.insert(tk.INSERT, ' ')

    def _press(self, event):
        """Presionar en los botnes alfanumericos. """
        self._entry.insert(tk.INSERT, event.widget.id)

    def _delete(self):
        """Teclado retroseso. """
        position = self._entry.index(tk.INSERT)
        if position > 0:
            self._entry.delete(position - 1)

    def _hide(self, event=False):
        """Ocultar teclado. """
        text = self._entry.get().title()
        self._entry.delete(0, tk.END)
        self._entry.insert(0, text)
        self._frame.place_forget()
        self._display = False


if __name__ == '__main__':
    root = tk.Tk()
    Check(root)
    root.mainloop()
