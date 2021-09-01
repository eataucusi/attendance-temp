"""Provee un conjunto de íconos para la aplicación.

Los íconos provienen de fontello.com.

Classes:

    Icon

"""
import tkinter as tk


class Icon(object):
    """Lee imágenes para ser utilizados en el entorno gráfico.

    En cada atributo se va precargando imágenes.

    Attributes:
        _instance

    Methods:
        instance

    """
    _instance = None

    def __init__(self):
        """Leer las imágenes sólo si no se ha instanciado."""
        if Icon._instance is None:
            self.lock = tk.PhotoImage(file='icons/lock.png')
            self.exit = tk.PhotoImage(file='icons/exit.png')
            self.back = tk.PhotoImage(file='icons/back.png')
            self.next = tk.PhotoImage(file='icons/next.png')
            self.users = tk.PhotoImage(file='icons/users.png')
            self.user_add = tk.PhotoImage(file='icons/add_user.png')
            self.clock = tk.PhotoImage(file='icons/clock.png')
            self.train = tk.PhotoImage(file='icons/train.png')
            self.search = tk.PhotoImage(file='icons/search.png')
            self.edit = tk.PhotoImage(file='icons/edit.png')
            self.delete = tk.PhotoImage(file='icons/delete.png')
            self.disk = tk.PhotoImage(file='icons/disk.png')
            self.camera = tk.PhotoImage(file='icons/camera.png')
            self.backspace = tk.PhotoImage(file='icons/backspace.png')
            self.check = tk.PhotoImage(file='icons/check.png')
            self.space = tk.PhotoImage(file='icons/space.png')
            self.sync = tk.PhotoImage(file='icons/sync.png')
            Icon._instance = self

    @staticmethod
    def instance():
        """Crea una instancia única de la clase.

        Returns:
            Instancia única de la clase.

        """
        if Icon._instance is None:
            Icon()
        return Icon._instance
