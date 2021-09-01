"""Permite la conexión a SQLite.

Módulo para la conexión a base de datos SQLite desde Python.

Classes:
    DB

"""
import sqlite3


class DB(object):
    """Conexión a base de datos SQLite.

    Conexión a base de datos mediante sqlite3.

    Attributes:
        _success
        _db
        _cur

    Methods:
        _instance
        _exec
        _getData
        user_login
        user_list
        user_delete
        user_by_id
        user_insert
        user_by_dni
        user_update
        user_pic_delete
        user_pic_add
        user_pass_update
        event_insert
        event_denied
    """
    _success = None
    _db = None
    _cur = None

    @staticmethod
    def _instance():
        """Crea una conexión a la base de datos.

         Returns:
             True or False
        """
        if DB._success is None:
            with sqlite3.connect('db.db') as conn:
                DB._db = conn
                DB._cur = conn.cursor()
                DB._success = True
        return DB._success

    @staticmethod
    def _exec(sql, parameters=[]):
        """Ejecuta una consulta.

        Args:
            sql: Consulta SQL
            parameters: Arreglo de valores que corresponde a cada ? de la
            consulta.
        """
        if DB._instance():
            DB._cur.execute(sql, parameters)
            DB._db.commit()

    @staticmethod
    def _getData(sql, parameters=[]):
        """Obtiene resutados de una consulta.

        Args:
            sql: Consulta SQL
            parameters: Arreglo de valores que corresponde a cada ? de la
            consulta.
        """
        if DB._instance():
            return DB._cur.execute(sql, parameters).fetchall()
        else:
            return []

    @staticmethod
    def user_login(dni, passw):
        """Obtiene datos de usuario apartir del DNI y password.

        Args:
            dni: DNI del usuario.
            passw: Password del usuario.

        Returns:
            Arreglo con datos del usuario o arreglo vacío.

        """
        sql = 'SELECT * FROM users WHERE role = "Administrador" AND dni = ?' \
              ' AND pass = ?'
        return DB._getData(sql, [dni, passw])

    @staticmethod
    def user_list():
        """Obtiene lista de usuarios.

        Returns:
            Arreglo con datos de los usuarios o arreglo vacío.

        """
        sql = 'SELECT * FROM users WHERE id > 1 ORDER BY name'
        return DB._getData(sql)

    @staticmethod
    def user_delete(id):
        """Elimina un usuario por id.

        Args:
            id: Identificador de usuario.
        """
        DB._exec('DELETE FROM users WHERE id=?', [id])

    @staticmethod
    def user_by_id(id):
        """Obtiene un usuario por id.

        Args:
            id: Identificador de usuario.

        Returns:
            Arreglo con datos del usuario o arreglo vacío.

        """
        return DB._getData('SELECT * FROM users WHERE id=?', [id])

    @staticmethod
    def user_insert(dni, name, rol, passw):
        """Inserta un usuario.

        Args:
            dni: DNI del usuario.
            name: Nombre completo del usuario.
            rol: Rol del usuario Administrador o Usuario.
            passw: Clave del usuario.

        Returns:
            Identificador de usuario insertado.

        """
        sql = 'INSERT INTO users VALUES(NULL, ?, ?, ?, ?, 0)'
        DB._exec(sql, [dni, name, rol, passw])
        return DB._cur.lastrowid

    @staticmethod
    def user_by_dni(dni):
        """Obtiene un usuario por DNI.

        Args:
            dni: DNI de usuario.

        Returns:
            Arreglo con datos del usuario o arreglo vacío.

        """
        return DB._getData('SELECT * FROM users WHERE dni=?', [dni])

    @staticmethod
    def user_update(id, dni, name, role, passw):
        """Modifica los datos de un usuario.

        Args:
            id: Identificador de usuario.
            dni: DNI de usuario.
            name: Nombre completo.
            role: Rol de usuario Administrador o Usuario.
            passw: Clave de usuario.

        """
        sql = 'UPDATE users SET dni=?, name=?, role=?, pass=? WHERE id=?'
        DB._exec(sql, [dni, name, role, passw, id])

    @staticmethod
    def user_pic_delete(id):
        """Disminuye en 1 el número de rostros.

        Args:
            id: Identificador de usuario.

        """
        sql = 'UPDATE users SET face = face - 1 WHERE id = ?'
        DB._exec(sql, [id])

    @staticmethod
    def user_pic_add(id):
        """Incrementa en 1 el número de rostros.

        Args:
            id: Identificador de usuario.

        """
        sql = 'UPDATE users SET face = face + 1 WHERE id = ?'
        DB._exec(sql, [id])

    @staticmethod
    def user_pass_update(passw, id):
        """Cambia la clave de un usuario.

        Args:
            passw: Nueva contraseña de usuario.
            id: Identificador de usuario.

        """
        sql = 'UPDATE users SET pass = ? WHERE id = ?'
        DB._exec(sql, [passw, id])

    @staticmethod
    def event_insert(user_id, temp, detect, gauge):
        """Inserta un evento de usuario.

        Args:
            user_id: Identificador de usuario.
            temp: Temperatura.
            detect: Tiempo de identificación.
            gauge: Tiempo de toma de temperatura.

        """
        sql = "INSERT INTO events VALUES(NULL, ?, date('now','localtime'), " \
              "strftime('%H', time('now','localtime')), " \
              "strftime('%M', time('now','localtime')), ?, ?, ?)"
        DB._exec(sql, [user_id, temp, detect, gauge])

    @staticmethod
    def event_denied(with_mask=1):
        """Inserta un evento de denegación.

        Args:
            mask: Detectó mascarilla.

        """
        sql = "INSERT INTO events VALUES(NULL, NULL, " \
              "date('now','localtime'), " \
              "strftime('%H', time('now','localtime')), " \
              "strftime('%M', time('now','localtime')), NULL, NULL, ?)"
        DB._exec(sql, [with_mask])
