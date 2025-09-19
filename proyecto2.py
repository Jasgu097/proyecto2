import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import hashlib
from collections import defaultdict
from datetime import datetime


class HashTable:
    """Implementacion de tabla hash con encadenamiento"""

    def __init__(self, size=100):
        self.size = size
        self.table = [[] for _ in range(size)]
        self.count = 0

    def _hash(self, key):
        """Funcion hash usando metodo de division"""
        return hash(key) % self.size

    def insert(self, key, value):
        """Insertar elemento en la tabla hash"""
        index = self._hash(key)
        bucket = self.table[index]

        # Verificar si la clave ya existe
        for i, (k, v) in enumerate(bucket):
            if k == key:
                bucket[i] = (key, value)  # Actualizar valor existente
                return

        # Insertar nuevo elemento
        bucket.append((key, value))
        self.count += 1

    def get(self, key):
        """Obtener elemento de la tabla hash"""
        index = self._hash(key)
        bucket = self.table[index]

        for k, v in bucket:
            if k == key:
                return v
        return None

    def delete(self, key):
        """Eliminar elemento de la tabla hash"""
        index = self._hash(key)
        bucket = self.table[index]

        for i, (k, v) in enumerate(bucket):
            if k == key:
                del bucket[i]
                self.count -= 1
                return True
        return False

    def exists(self, key):
        """Verificar si una clave existe en la tabla"""
        return self.get(key) is not None

    def get_all_values(self):
        """Obtener todos los valores de la tabla"""
        values = []
        for bucket in self.table:
            for k, v in bucket:
                values.append(v)
        return values


class Articulo:
    """Clase para representar un artículo cientifico"""

    def __init__(self, hash_id, titulo, autores, año, archivo_nombre):
        self.hash_id = hash_id
        self.titulo = titulo
        self.autores = autores
        self.año = año
        self.archivo_nombre = archivo_nombre

    def __str__(self):
        return f"Título: {self.titulo}\nAutores: {self.autores}\nAño: {self.año}\nHash: {self.hash_id}"


class GestorArticulos:
    """Gestor principal de articulos cientificos"""

    def __init__(self):
        self.tabla_hash = HashTable(200)  # Tabla hash principal
        self.indice_autores = defaultdict(list)  # Indice secundario por autor
        self.indice_años = defaultdict(list)  # Indice secundario por año
        self.db_file = "articulos_db.txt"
        self.articulos_dir = "articulos"

        # Crear directorio de articulos si no existe
        if not os.path.exists(self.articulos_dir):
            os.makedirs(self.articulos_dir)

        self.cargar_base_datos()

    def calcular_hash_fnv1(self, contenido):
        """Implementacion del algoritmo FNV-1 para generar hash"""
        FNV_PRIME = 16777619
        FNV_OFFSET_BASIS = 2166136261

        hash_value = FNV_OFFSET_BASIS
        for byte in contenido.encode('utf-8'):
            hash_value = (hash_value * FNV_PRIME) % (2 ** 32)
            hash_value = hash_value ^ byte

        return str(hash_value)

    def cargar_base_datos(self):
        """Cargar articulos desde el archivo de base de datos"""
        if not os.path.exists(self.db_file):
            return

        try:
            with open(self.db_file, 'r', encoding='utf-8') as file:
                for linea in file:
                    if linea.strip():
                        partes = linea.strip().split('|')
                        if len(partes) == 5:
                            hash_id, titulo, autores, año, archivo_nombre = partes
                            articulo = Articulo(hash_id, titulo, autores, int(año), archivo_nombre)

                            # Insertar en tabla hash principal
                            self.tabla_hash.insert(hash_id, articulo)

                            # Actualizar indices secundarios
                            self.indice_autores[autores.lower()].append(articulo)
                            self.indice_años[int(año)].append(articulo)
        except Exception as e:
            print(f"Error al cargar base de datos: {e}")

    def guardar_base_datos(self):
        """Guardar articulos en el archivo de base de datos"""
        try:
            with open(self.db_file, 'w', encoding='utf-8') as file:
                articulos = self.tabla_hash.get_all_values()
                for articulo in articulos:
                    linea = f"{articulo.hash_id}|{articulo.titulo}|{articulo.autores}|{articulo.año}|{articulo.archivo_nombre}\n"
                    file.write(linea)
        except Exception as e:
            print(f"Error al guardar base de datos: {e}")

    def agregar_articulo(self, titulo, autores, año, ruta_archivo):
        """Agregar nuevo articulo al sistema"""
        try:
            # Leer contenido del archivo
            with open(ruta_archivo, 'r', encoding='utf-8') as file:
                contenido = file.read()

            # Calcular hash del contenido
            hash_id = self.calcular_hash_fnv1(contenido)

            # Verificar duplicados
            if self.tabla_hash.exists(hash_id):
                return False, "El articulo ya existe en el sistema"

            # Crear nombre de archivo basado en hash
            archivo_nombre = f"{hash_id}.txt"
            ruta_destino = os.path.join(self.articulos_dir, archivo_nombre)

            # Copiar archivo con nuevo nombre
            with open(ruta_destino, 'w', encoding='utf-8') as file:
                file.write(contenido)

            # Crear objeto artículo
            articulo = Articulo(hash_id, titulo, autores, año, archivo_nombre)

            # Insertar en tabla hash principal
            self.tabla_hash.insert(hash_id, articulo)

            # Actualizar indices secundarios
            self.indice_autores[autores.lower()].append(articulo)
            self.indice_años[año].append(articulo)

            # Guardar en base de datos
            self.guardar_base_datos()

            return True, "Artículo agregado exitosamente"

        except Exception as e:
            return False, f"Error al agregar artículo: {e}"

    def modificar_articulo(self, hash_id, nuevo_autor=None, nuevo_año=None):
        """Modificar datos de un articulo existente"""
        articulo = self.tabla_hash.get(hash_id)
        if not articulo:
            return False, "Artículo no encontrado"

        try:
            # Remover de indices antiguos
            if articulo.autores.lower() in self.indice_autores:
                self.indice_autores[articulo.autores.lower()].remove(articulo)
            if articulo.año in self.indice_años:
                self.indice_años[articulo.año].remove(articulo)

            # Actualizar datos
            if nuevo_autor:
                articulo.autores = nuevo_autor
            if nuevo_año:
                articulo.año = nuevo_año

            # Agregar a nuevos indices
            self.indice_autores[articulo.autores.lower()].append(articulo)
            self.indice_años[articulo.año].append(articulo)

            # Guardar cambios
            self.guardar_base_datos()

            return True, "Articulo modificado exitosamente"

        except Exception as e:
            return False, f"Error al modificar articulo: {e}"

    def eliminar_articulo(self, hash_id):
        """Eliminar un artículo del sistema"""
        articulo = self.tabla_hash.get(hash_id)
        if not articulo:
            return False, "Articulo no encontrado"

        try:
            # Eliminar archivo físico
            ruta_archivo = os.path.join(self.articulos_dir, articulo.archivo_nombre)
            if os.path.exists(ruta_archivo):
                os.remove(ruta_archivo)

            # Remover de indices
            if articulo.autores.lower() in self.indice_autores:
                self.indice_autores[articulo.autores.lower()].remove(articulo)
            if articulo.año in self.indice_años:
                self.indice_años[articulo.año].remove(articulo)

            # Eliminar de tabla hash principal
            self.tabla_hash.delete(hash_id)

            # Guardar cambios
            self.guardar_base_datos()

            return True, "Artículo eliminado exitosamente"

        except Exception as e:
            return False, f"Error al eliminar artículo: {e}"

    def buscar_por_autor(self, autor):
        """Buscar articulos por autor"""
        return sorted(self.indice_autores.get(autor.lower(), []),
                      key=lambda x: x.titulo.lower())

    def buscar_por_año(self, año):
        """Buscar articulos por año"""
        return sorted(self.indice_años.get(año, []),
                      key=lambda x: x.titulo.lower())

    def listar_por_titulo(self):
        """Listar todos los articulos ordenados por titulo"""
        articulos = self.tabla_hash.get_all_values()
        return sorted(articulos, key=lambda x: x.titulo.lower())

    def listar_por_autor(self):
        """Listar todos los articulos ordenados por autor"""
        articulos = self.tabla_hash.get_all_values()
        return sorted(articulos, key=lambda x: x.autores.lower())


class InterfazGrafica:
    """Interfaz grafica principal usando Tkinter"""

    def __init__(self):
        self.gestor = GestorArticulos()
        self.root = tk.Tk()
        self.root.title("Gestor de Artículos Científicos")
        self.root.geometry("800x600")

        self.setup_ui()

    def setup_ui(self):
        """Configurar la interfaz de usuario"""
        # Notebook para pestañas
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Pestaña para agregar articulos
        self.frame_agregar = ttk.Frame(notebook)
        notebook.add(self.frame_agregar, text="Agregar Artículo")
        self.setup_agregar_tab()

        # Pestaña para buscar articulos
        self.frame_buscar = ttk.Frame(notebook)
        notebook.add(self.frame_buscar, text="Buscar Artículos")
        self.setup_buscar_tab()

        # Pestaña para gestionar articulos
        self.frame_gestionar = ttk.Frame(notebook)
        notebook.add(self.frame_gestionar, text="Gestionar Artículos")
        self.setup_gestionar_tab()

    def setup_agregar_tab(self):
        """Configurar pestaña para agregar articulos"""
        # Frame principal
        main_frame = ttk.Frame(self.frame_agregar)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # Campos de entrada
        ttk.Label(main_frame, text="Título:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.entry_titulo = ttk.Entry(main_frame, width=50)
        self.entry_titulo.grid(row=0, column=1, pady=5, padx=(10, 0))

        ttk.Label(main_frame, text="Autores:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.entry_autores = ttk.Entry(main_frame, width=50)
        self.entry_autores.grid(row=1, column=1, pady=5, padx=(10, 0))

        ttk.Label(main_frame, text="Año:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.entry_año = ttk.Entry(main_frame, width=20)
        self.entry_año.grid(row=2, column=1, sticky=tk.W, pady=5, padx=(10, 0))

        # Seleccion de archivo
        ttk.Label(main_frame, text="Archivo:").grid(row=3, column=0, sticky=tk.W, pady=5)
        archivo_frame = ttk.Frame(main_frame)
        archivo_frame.grid(row=3, column=1, sticky=tk.W, pady=5, padx=(10, 0))

        self.label_archivo = ttk.Label(archivo_frame, text="Ningún archivo seleccionado")
        self.label_archivo.pack(side=tk.LEFT)

        ttk.Button(archivo_frame, text="Seleccionar Archivo",
                   command=self.seleccionar_archivo).pack(side=tk.LEFT, padx=(10, 0))

        # Boton agregar
        ttk.Button(main_frame, text="Agregar Artículo",
                   command=self.agregar_articulo).grid(row=4, column=1, pady=20, sticky=tk.W, padx=(10, 0))

        self.archivo_seleccionado = None

    def setup_buscar_tab(self):
        """Configurar pestaña para buscar articulos"""
        main_frame = ttk.Frame(self.frame_buscar)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # Opciones de busqueda
        search_frame = ttk.LabelFrame(main_frame, text="Opciones de Búsqueda")
        search_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Button(search_frame, text="Listar por Título",
                   command=self.listar_por_titulo).pack(side=tk.LEFT, padx=5, pady=5)
        ttk.Button(search_frame, text="Listar por Autor",
                   command=self.listar_por_autor).pack(side=tk.LEFT, padx=5, pady=5)

        # Busqueda especifica
        busqueda_frame = ttk.LabelFrame(main_frame, text="Búsqueda Específica")
        busqueda_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(busqueda_frame, text="Buscar por Autor:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.entry_buscar_autor = ttk.Entry(busqueda_frame, width=30)
        self.entry_buscar_autor.grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(busqueda_frame, text="Buscar",
                   command=self.buscar_por_autor).grid(row=0, column=2, padx=5, pady=5)

        ttk.Label(busqueda_frame, text="Buscar por Año:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.entry_buscar_año = ttk.Entry(busqueda_frame, width=30)
        self.entry_buscar_año.grid(row=1, column=1, padx=5, pady=5)
        ttk.Button(busqueda_frame, text="Buscar",
                   command=self.buscar_por_año).grid(row=1, column=2, padx=5, pady=5)

        # Lista de resultados
        self.tree_resultados = ttk.Treeview(main_frame,
                                            columns=("titulo", "autores", "año", "hash"),
                                            show="headings")
        self.tree_resultados.heading("titulo", text="Título")
        self.tree_resultados.heading("autores", text="Autores")
        self.tree_resultados.heading("año", text="Año")
        self.tree_resultados.heading("hash", text="Hash ID")

        self.tree_resultados.pack(fill=tk.BOTH, expand=True)

        # Scrollbar para la lista
        scrollbar = ttk.Scrollbar(main_frame, orient=tk.VERTICAL, command=self.tree_resultados.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree_resultados.configure(yscrollcommand=scrollbar.set)

    def setup_gestionar_tab(self):
        """Configurar pestaña para gestionar articulos"""
        main_frame = ttk.Frame(self.frame_gestionar)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # Seleccion de articulo
        select_frame = ttk.LabelFrame(main_frame, text="Seleccionar Artículo")
        select_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(select_frame, text="Hash ID:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.entry_hash_gestionar = ttk.Entry(select_frame, width=40)
        self.entry_hash_gestionar.grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(select_frame, text="Cargar",
                   command=self.cargar_articulo).grid(row=0, column=2, padx=5, pady=5)

        # Modificacion
        modify_frame = ttk.LabelFrame(main_frame, text="Modificar Artículo")
        modify_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(modify_frame, text="Nuevo Autor:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.entry_nuevo_autor = ttk.Entry(modify_frame, width=40)
        self.entry_nuevo_autor.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(modify_frame, text="Nuevo Año:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.entry_nuevo_año = ttk.Entry(modify_frame, width=20)
        self.entry_nuevo_año.grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)

        ttk.Button(modify_frame, text="Modificar",
                   command=self.modificar_articulo).grid(row=2, column=1, sticky=tk.W, pady=10, padx=5)

        # Eliminacion
        delete_frame = ttk.LabelFrame(main_frame, text="Eliminar Artículo")
        delete_frame.pack(fill=tk.X)

        ttk.Button(delete_frame, text="Eliminar Artículo",
                   command=self.eliminar_articulo).pack(padx=5, pady=10)

    def seleccionar_archivo(self):
        """Seleccionar archivo de texto"""
        filename = filedialog.askopenfilename(
            title="Seleccionar archivo de artículo",
            filetypes=[("Archivos de texto", ".txt"), ("Todos los archivos", ".*")]
        )
        if filename:
            self.archivo_seleccionado = filename
            self.label_archivo.config(text=os.path.basename(filename))

    def agregar_articulo(self):
        """Agregar nuevo articulo"""
        titulo = self.entry_titulo.get().strip()
        autores = self.entry_autores.get().strip()
        año_str = self.entry_año.get().strip()

        if not all([titulo, autores, año_str, self.archivo_seleccionado]):
            messagebox.showerror("Error", "Todos los campos son obligatorios")
            return

        try:
            año = int(año_str)
        except ValueError:
            messagebox.showerror("Error", "El año debe ser un número válido")
            return

        exito, mensaje = self.gestor.agregar_articulo(titulo, autores, año, self.archivo_seleccionado)

        if exito:
            messagebox.showinfo("Éxito", mensaje)
            # Limpiar campos
            self.entry_titulo.delete(0, tk.END)
            self.entry_autores.delete(0, tk.END)
            self.entry_año.delete(0, tk.END)
            self.label_archivo.config(text="Ningún archivo seleccionado")
            self.archivo_seleccionado = None
        else:
            messagebox.showerror("Error", mensaje)

    def listar_por_titulo(self):
        """Listar artículos por titulo"""
        self.tree_resultados.delete(*self.tree_resultados.get_children())
        articulos = self.gestor.listar_por_titulo()
        for articulo in articulos:
            self.tree_resultados.insert("", tk.END, values=(
                articulo.titulo, articulo.autores, articulo.año, articulo.hash_id
            ))

    def listar_por_autor(self):
        """Listar articulos por autor"""
        self.tree_resultados.delete(*self.tree_resultados.get_children())
        articulos = self.gestor.listar_por_autor()
        for articulo in articulos:
            self.tree_resultados.insert("", tk.END, values=(
                articulo.titulo, articulo.autores, articulo.año, articulo.hash_id
            ))

    def buscar_por_autor(self):
        """Buscar articulos por autor"""
        autor = self.entry_buscar_autor.get().strip()
        if not autor:
            messagebox.showerror("Error", "Ingrese un autor para buscar")
            return

        self.tree_resultados.delete(*self.tree_resultados.get_children())
        articulos = self.gestor.buscar_por_autor(autor)
        for articulo in articulos:
            self.tree_resultados.insert("", tk.END, values=(
                articulo.titulo, articulo.autores, articulo.año, articulo.hash_id
            ))

        if not articulos:
            messagebox.showinfo("Resultado", f"No se encontraron artículos del autor: {autor}")

    def buscar_por_año(self):
        """Buscar articulos por año"""
        año_str = self.entry_buscar_año.get().strip()
        if not año_str:
            messagebox.showerror("Error", "Ingrese un año para buscar")
            return

        try:
            año = int(año_str)
        except ValueError:
            messagebox.showerror("Error", "El año debe ser un número válido")
            return

        self.tree_resultados.delete(*self.tree_resultados.get_children())
        articulos = self.gestor.buscar_por_año(año)
        for articulo in articulos:
            self.tree_resultados.insert("", tk.END, values=(
                articulo.titulo, articulo.autores, articulo.año, articulo.hash_id
            ))

        if not articulos:
            messagebox.showinfo("Resultado", f"No se encontraron artículos del año: {año}")

    def cargar_articulo(self):
        """Cargar datos de un articulo para modificacion"""
        hash_id = self.entry_hash_gestionar.get().strip()
        if not hash_id:
            messagebox.showerror("Error", "Ingrese un Hash ID")
            return

        articulo = self.gestor.tabla_hash.get(hash_id)
        if articulo:
            self.entry_nuevo_autor.delete(0, tk.END)
            self.entry_nuevo_autor.insert(0, articulo.autores)
            self.entry_nuevo_año.delete(0, tk.END)
            self.entry_nuevo_año.insert(0, str(articulo.año))
            messagebox.showinfo("Éxito", f"Artículo cargado: {articulo.titulo}")
        else:
            messagebox.showerror("Error", "Artículo no encontrado")

    def modificar_articulo(self):
        """Modificar un articulo existente"""
        hash_id = self.entry_hash_gestionar.get().strip()
        nuevo_autor = self.entry_nuevo_autor.get().strip()
        nuevo_año_str = self.entry_nuevo_año.get().strip()

        if not hash_id:
            messagebox.showerror("Error", "Ingrese un Hash ID")
            return

        nuevo_año = None
        if nuevo_año_str:
            try:
                nuevo_año = int(nuevo_año_str)
            except ValueError:
                messagebox.showerror("Error", "El año debe ser un número válido")
                return

        exito, mensaje = self.gestor.modificar_articulo(
            hash_id, nuevo_autor if nuevo_autor else None, nuevo_año
        )

        if exito:
            messagebox.showinfo("Éxito", mensaje)
        else:
            messagebox.showerror("Error", mensaje)

    def eliminar_articulo(self):
        """Eliminar un articulo"""
        hash_id = self.entry_hash_gestionar.get().strip()
        if not hash_id:
            messagebox.showerror("Error", "Ingrese un Hash ID")
            return

        if messagebox.askyesno("Confirmar", "¿Está seguro de que desea eliminar este artículo?"):
            exito, mensaje = self.gestor.eliminar_articulo(hash_id)

            if exito:
                messagebox.showinfo("Éxito", mensaje)
                # Limpiar campos
                self.entry_hash_gestionar.delete(0, tk.END)
                self.entry_nuevo_autor.delete(0, tk.END)
                self.entry_nuevo_año.delete(0, tk.END)
            else:
                messagebox.showerror("Error", mensaje)

    def run(self):
        """Ejecutar la interfaz grafica"""
        self.root.mainloop()


# Funcion principal
if __name__ == "__main__":
    app = InterfazGrafica()
    app.run()
