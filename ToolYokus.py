import os
import sys
import shutil
import tkinter as tk
from tkinter import messagebox, scrolledtext, ttk
import threading
import time
import subprocess
import webbrowser
from datetime import datetime
import platform
import json
import ctypes
import urllib.request
import tempfile
import struct
import psutil

class ToolByYokus:
    def __init__(self, root):
        self.root = root
        self.root.title("Tool by Yokus")
        self.root.geometry("1000x750")
        self.root.resizable(False, False)
        
        # Версия программы
        self.version = "1.0.0"
        self.github_repo = "Yokus-pyth/ToolYokus"
        
        # Флаг запуска от администратора
        self.is_admin = False
        
        # Определяем разрядность системы
        self.is_64bit = self.is_windows_64bit()
        
        # Получаем путь к папке программы
        if getattr(sys, 'frozen', False):
            self.program_path = os.path.dirname(sys.executable)
        else:
            self.program_path = os.path.dirname(os.path.abspath(__file__))
        
        # Папка для логов (рядом с программой)
        self.logs_folder = os.path.join(self.program_path, "Logs")
        if not os.path.exists(self.logs_folder):
            try:
                os.makedirs(self.logs_folder)
            except:
                self.logs_folder = os.path.join(tempfile.gettempdir(), "ToolByYokus_Logs")
                if not os.path.exists(self.logs_folder):
                    os.makedirs(self.logs_folder)
        
        # Папка для временных установщиков (рядом с программой)
        self.installers_folder = os.path.join(self.program_path, "Installers")
        if not os.path.exists(self.installers_folder):
            try:
                os.makedirs(self.installers_folder)
            except:
                self.installers_folder = os.path.join(tempfile.gettempdir(), "ToolByYokus_Installers")
                if not os.path.exists(self.installers_folder):
                    os.makedirs(self.installers_folder)
        
        # Переменные для темы
        self.dark_theme = False
        self.pinned = False
        
        # Пути для очистки
        self.temp_path = os.environ.get('TEMP') or os.environ.get('TMP') or os.path.join(os.environ['USERPROFILE'], 'AppData', 'Local', 'Temp')
        
        username = os.environ.get('USERNAME')
        self.dx_cache_path = f"C:\\Users\\{username}\\AppData\\Local\\NVIDIA\\DXCache"
        self.opengl_cache_path = f"C:\\Users\\{username}\\AppData\\Local\\NVIDIA\\GLCache"
        self.prefetch_path = "C:\\Windows\\Prefetch"
        
        # Словарь для хранения размеров папок
        self.sizes = {
            'temp': 0, 
            'dxcache': 0, 
            'opengl': 0, 
            'recycle': 0,
            'prefetch': 0,
            'ram': 0
        }
        
        # Переменные для чекбоксов
        self.temp_var = tk.BooleanVar()
        self.dx_var = tk.BooleanVar()
        self.opengl_var = tk.BooleanVar()
        self.recycle_var = tk.BooleanVar()
        self.prefetch_var = tk.BooleanVar()
        self.ram_var = tk.BooleanVar()
        
        # Переменные для чекбоксов установки софта
        self.software_vars = {}
        
        # Результаты очистки
        self.deleted_stats = {
            'temp': {'files': 0, 'size': 0, 'failed': []},
            'dxcache': {'files': 0, 'size': 0, 'failed': []},
            'opengl': {'files': 0, 'size': 0, 'failed': []},
            'recycle': {'files': 0, 'size': 0, 'failed': []},
            'prefetch': {'files': 0, 'size': 0, 'failed': []},
            'ram': {'files': 0, 'size': 0, 'failed': []}
        }
        
        self.load_settings()
        self.setup_ui()
        self.apply_theme()
        
        # Привязываем колесо мыши
        self.bind_mousewheel()
        
        # Проверка прав администратора
        self.root.after(100, self.check_admin_rights)
        
        # Логируем пути
        self.log(f"📁 Папка программы: {self.program_path}")
        self.log(f"📁 Папка логов: {self.logs_folder}")
        self.log(f"📁 Папка установщиков: {self.installers_folder}")
    
    def bind_mousewheel(self):
        """Привязка колеса мыши для прокрутки"""
        def on_mousewheel(event):
            # Прокрутка лога
            if hasattr(self, 'log_text') and self.log_text.winfo_exists():
                self.log_text.yview_scroll(int(-1*(event.delta/120)), "units")
            # Прокрутка Canvas на вкладке Софт
            if hasattr(self, 'soft_canvas') and self.soft_canvas.winfo_exists():
                self.soft_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        self.root.bind_all("<MouseWheel>", on_mousewheel)
    
    def is_windows_64bit(self):
        """Определяет разрядность Windows"""
        try:
            return struct.calcsize("P") * 8 == 64
        except:
            return platform.machine().endswith('64')
    
    def check_admin_rights(self):
        """Проверка прав администратора с автоматическим перезапуском"""
        try:
            self.is_admin = ctypes.windll.shell32.IsUserAnAdmin()
            if not self.is_admin:
                result = messagebox.askyesno(
                    "Права администратора",
                    "Для корректной работы некоторых функций (очистка Prefetch и др.) требуются права администратора.\n\n"
                    "Разрешить программе автоматически перезапуститься с правами администратора?\n\n"
                    "(Программа закроется и откроется заново)"
                )
                if result:
                    # Перезапускаем с правами и завершаем текущий процесс
                    ctypes.windll.shell32.ShellExecuteW(
                        None, "runas", sys.executable, " ".join(sys.argv), None, 1
                    )
                    self.root.quit()
                    sys.exit(0)
                else:
                    messagebox.showwarning(
                        "Внимание",
                        "Программа запущена без прав администратора.\n\n"
                        "Функции очистки Prefetch и некоторые другие могут не работать."
                    )
                    self.log("⚠️ Программа запущена без прав администратора.")
            else:
                self.log("✅ Программа запущена с правами администратора.")
        except Exception as e:
            self.log(f"⚠️ Не удалось проверить права администратора: {e}")
    
    def setup_ui(self):
        """Настройка интерфейса"""
        # Создаем основной фрейм с двумя колонками
        main_paned = tk.PanedWindow(self.root, orient=tk.HORIZONTAL, sashrelief=tk.RAISED, sashwidth=5)
        main_paned.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Левая панель с вкладками
        left_frame = tk.Frame(main_paned)
        main_paned.add(left_frame, width=800)
        
        # Правая панель с автором
        right_frame = tk.Frame(main_paned, width=180, relief=tk.RAISED, bd=1)
        main_paned.add(right_frame, width=180)
        
        # Настройка правой панели
        right_frame.pack_propagate(False)
        
        tk.Label(right_frame, text="👤 АВТОР", font=("Arial", 14, "bold"), fg="#9b59b6").pack(pady=(20, 10))
        
        author_frame = tk.Frame(right_frame, relief=tk.GROOVE, bd=2)
        author_frame.pack(padx=10, pady=10, fill=tk.X)
        
        tk.Label(author_frame, text="📱", font=("Arial", 48)).pack(pady=10)
        tk.Label(author_frame, text="Yokus", font=("Arial", 12, "bold")).pack()
        tk.Label(author_frame, text="Разработчик", font=("Arial", 9), fg="gray").pack()
        
        # Ссылка на Telegram
        tg_link = tk.Label(
            right_frame,
            text="📩 Telegram\n@Yokus1999",
            font=("Arial", 10),
            fg="#0088cc",
            cursor="hand2",
            justify=tk.CENTER
        )
        tg_link.pack(pady=10)
        tg_link.bind("<Button-1>", lambda e: webbrowser.open("https://t.me/Yokus1999"))
        
        # Кнопка проверки обновлений в правой панели
        update_icon = tk.Label(
            right_frame,
            text="🔄",
            font=("Arial", 20),
            fg="#4CAF50",
            cursor="hand2"
        )
        update_icon.pack(pady=5)
        update_icon.bind("<Button-1>", lambda e: self.check_for_updates())
        
        update_text = tk.Label(
            right_frame,
            text="Проверить обновления",
            font=("Arial", 9),
            fg="#4CAF50",
            cursor="hand2"
        )
        update_text.pack()
        update_text.bind("<Button-1>", lambda e: self.check_for_updates())
        
        tk.Label(right_frame, text=f"Версия: {self.version}", font=("Arial", 8), fg="gray").pack(side=tk.BOTTOM, pady=10)
        
        # Настройка вкладок в левой панели
        self.notebook = ttk.Notebook(left_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        style = ttk.Style()
        style.configure("TNotebook.Tab", padding=[10, 5], font=("Arial", 10))
        
        # Создаем вкладки
        self.tab_clean = ttk.Frame(self.notebook)
        self.tab_soft = ttk.Frame(self.notebook)
        self.tab_auto = ttk.Frame(self.notebook)
        self.tab_dev = ttk.Frame(self.notebook)
        
        self.notebook.add(self.tab_clean, text="🧹 Очистка")
        self.notebook.add(self.tab_soft, text="📦 Софт")
        self.notebook.add(self.tab_auto, text="⚙️ Автоматизация")
        self.notebook.add(self.tab_dev, text="🚧 В разработке")
        
        self.setup_clean_tab()
        self.setup_soft_tab()
        self.setup_auto_tab()
        self.setup_dev_tab()
        self.setup_bottom_bar()
    
    def setup_bottom_bar(self):
        """Нижняя панель"""
        bottom_frame = tk.Frame(self.root, height=40, relief=tk.RAISED, bd=1)
        bottom_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=5)
        
        # Кнопка переключения темы
        self.theme_btn = tk.Button(
            bottom_frame,
            text="🌙 Темная тема",
            command=self.toggle_theme,
            font=("Arial", 9),
            cursor="hand2"
        )
        self.theme_btn.pack(side=tk.LEFT, padx=5)
        
        # Кнопка закрепления
        self.pin_btn = tk.Button(
            bottom_frame,
            text="📌 Закрепить",
            command=self.toggle_pin,
            font=("Arial", 9),
            cursor="hand2"
        )
        self.pin_btn.pack(side=tk.LEFT, padx=5)
        
        # Кнопка открытия папки с логами
        logs_btn = tk.Button(
            bottom_frame,
            text="📁 Открыть логи",
            command=self.open_logs_folder,
            font=("Arial", 9),
            cursor="hand2"
        )
        logs_btn.pack(side=tk.RIGHT, padx=5)
    
    def open_logs_folder(self):
        """Открывает папку с логами"""
        if os.path.exists(self.logs_folder):
            os.startfile(self.logs_folder)
        else:
            messagebox.showwarning("Ошибка", f"Папка с логами не найдена:\n{self.logs_folder}")
    
    def create_tooltip(self, widget, text):
        """Создание подсказки при наведении"""
        def show_tooltip(event):
            tooltip = tk.Toplevel()
            tooltip.wm_overrideredirect(True)
            tooltip.wm_geometry(f"+{event.x_root+10}+{event.y_root+10}")
            label = tk.Label(tooltip, text=text, background="#ffffe0", relief="solid", borderwidth=1, font=("Arial", 9))
            label.pack()
            widget.tooltip = tooltip
        
        def hide_tooltip(event):
            if hasattr(widget, 'tooltip'):
                widget.tooltip.destroy()
                del widget.tooltip
        
        widget.bind("<Enter>", show_tooltip)
        widget.bind("<Leave>", hide_tooltip)
    
    def setup_clean_tab(self):
        """Вкладка Очистка"""
        main_frame = tk.Frame(self.tab_clean, padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        title_label = tk.Label(main_frame, text="Tool by Yokus", font=("Arial", 24, "bold"), fg="#9b59b6")
        title_label.pack(pady=(0, 5))
        
        subtitle_label = tk.Label(main_frame, text="Многофункциональный инструмент для оптимизации системы", font=("Arial", 10))
        subtitle_label.pack(pady=(0, 20))
        
        checkbox_frame = tk.LabelFrame(main_frame, text="Выберите что очистить", font=("Arial", 12, "bold"), padx=15, pady=15)
        checkbox_frame.pack(fill=tk.X, pady=(0, 15))
        
        def add_checkbox(frame, text, variable, tooltip_text):
            cb_frame = tk.Frame(frame)
            cb_frame.pack(fill=tk.X, pady=5)
            
            cb = tk.Checkbutton(cb_frame, text=text, variable=variable, font=("Arial", 11), anchor='w')
            cb.pack(side=tk.LEFT)
            
            hint_label = tk.Label(cb_frame, text="?", font=("Arial", 9, "bold"), fg="blue", cursor="question_arrow")
            hint_label.pack(side=tk.LEFT, padx=(5, 0))
            self.create_tooltip(hint_label, tooltip_text)
            
            return cb
        
        add_checkbox(checkbox_frame, "Очистить Temp", self.temp_var, 
                    "Удаляет временные файлы системы и программ. Безопасно для системы.")
        
        add_checkbox(checkbox_frame, "Очистить DXCache (NVIDIA DirectX кэш)", self.dx_var,
                    "Удаляет кэш шейдеров NVIDIA DirectX. Может улучшить производительность в играх.")
        
        add_checkbox(checkbox_frame, "Очистить OpenGL Cache (NVIDIA GLCache)", self.opengl_var,
                    "Удаляет кэш OpenGL NVIDIA. Безопасно для удаления.")
        
        add_checkbox(checkbox_frame, "Очистить Prefetch", self.prefetch_var,
                    "Удаляет данные о запущенных программах. Windows восстановит их при следующем запуске.")
        
        add_checkbox(checkbox_frame, "Очистить RAM (оперативную память)", self.ram_var,
                    "Освобождает неиспользуемую оперативную память. Может ускорить работу системы.")
        
        add_checkbox(checkbox_frame, "Очистить корзину", self.recycle_var,
                    "Очищает корзину Windows. Выполняется в самом конце.")
        
        self.select_all_btn = tk.Button(checkbox_frame, text="✓ Выбрать все", command=self.select_all, font=("Arial", 10), cursor="hand2")
        self.select_all_btn.pack(pady=(10, 0))
        
        btn_frame = tk.Frame(main_frame)
        btn_frame.pack(pady=10)
        
        self.analyze_btn = tk.Button(btn_frame, text="🔍 Анализировать", command=self.analyze_all, width=15, height=2, font=("Arial", 10, "bold"), cursor="hand2")
        self.analyze_btn.pack(side=tk.LEFT, padx=5)
        
        self.clean_btn = tk.Button(btn_frame, text="🧹 Очистить", command=self.start_cleanup, width=15, height=2, font=("Arial", 10, "bold"), state=tk.DISABLED, cursor="hand2")
        self.clean_btn.pack(side=tk.LEFT, padx=5)
        
        progress_frame = tk.Frame(main_frame)
        progress_frame.pack(fill=tk.X, pady=(10, 5))
        
        self.progress_label = tk.Label(progress_frame, text="Готов к работе", font=("Arial", 9))
        self.progress_label.pack()
        
        self.progress_bar = ttk.Progressbar(progress_frame, orient=tk.HORIZONTAL, length=400, mode='determinate')
        self.progress_bar.pack(fill=tk.X, pady=(5, 0))
        
        log_label = tk.Label(main_frame, text="Лог операций:", font=("Arial", 10, "bold"))
        log_label.pack(anchor='w')
        
        self.log_text = scrolledtext.ScrolledText(main_frame, height=18, width=80, font=("Consolas", 9))
        self.log_text.pack(fill=tk.BOTH, expand=True, pady=(5, 0))
    
    def setup_soft_tab(self):
        """Вкладка Софт с выпадающими категориями"""
        self.soft_canvas = tk.Canvas(self.tab_soft)
        scrollbar = ttk.Scrollbar(self.tab_soft, orient="vertical", command=self.soft_canvas.yview)
        scrollable_frame = tk.Frame(self.soft_canvas)
        
        scrollable_frame.bind("<Configure>", lambda e: self.soft_canvas.configure(scrollregion=self.soft_canvas.bbox("all")))
        self.soft_canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        self.soft_canvas.configure(yscrollcommand=scrollbar.set)
        
        self.soft_canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        title_label = tk.Label(scrollable_frame, text="Tool by Yokus", font=("Arial", 24, "bold"), fg="#9b59b6")
        title_label.grid(row=0, column=0, columnspan=2, pady=(10, 5))
        
        subtitle_label = tk.Label(scrollable_frame, text="Установка программ с автоматическим определением разрядности", font=("Arial", 10))
        subtitle_label.grid(row=1, column=0, columnspan=2, pady=(0, 20))
        
        arch_text = "64-битная система" if self.is_64bit else "32-битная система"
        arch_label = tk.Label(scrollable_frame, text=f"🔧 Обнаружена: {arch_text}", font=("Arial", 10, "bold"), fg="#4CAF50")
        arch_label.grid(row=2, column=0, columnspan=2, pady=(0, 15))
        
        btn_frame = tk.Frame(scrollable_frame)
        btn_frame.grid(row=3, column=0, columnspan=2, pady=(0, 20))
        
        install_btn = tk.Button(
            btn_frame,
            text="🚀 Установить выбранные программы",
            command=self.install_selected_software,
            font=("Arial", 11, "bold"),
            bg="#4CAF50",
            fg="white",
            cursor="hand2",
            padx=15,
            pady=5
        )
        install_btn.pack(side=tk.LEFT, padx=5)
        
        musthave_btn = tk.Button(
            btn_frame,
            text="⭐ MUST HAVE",
            command=self.install_musthave,
            font=("Arial", 11, "bold"),
            bg="#FF9800",
            fg="white",
            cursor="hand2",
            padx=15,
            pady=5
        )
        musthave_btn.pack(side=tk.LEFT, padx=5)
        
        nvidia_btn = tk.Button(
            btn_frame,
            text="🎮 Драйвер на видеокарту",
            command=lambda: webbrowser.open("https://www.nvidia.com/Download/Find.aspx"),
            font=("Arial", 10),
            bg="#76B900",
            fg="white",
            cursor="hand2",
            padx=10,
            pady=5
        )
        nvidia_btn.pack(side=tk.LEFT, padx=5)
        
        categories = {
            "🌐 Браузеры": [
                ("Google Chrome", "https://www.google.com/chrome/?standalone=1&platform=win" + ("64" if self.is_64bit else ""), "/silent /install"),
                ("Opera", "https://www.opera.com/download/get/?partner=www&opsys=Windows&bit=" + ("64" if self.is_64bit else "32"), "/silent"),
                ("Yandex", "https://browser.yandex.ru/download/?full=1&bit=" + ("64" if self.is_64bit else "32"), "/S"),
                ("Firefox", "https://download.mozilla.org/?product=firefox-latest&os=win" + ("64" if self.is_64bit else ""), "/S")
            ],
            "🎮 Платформы для игр": [
                ("Steam", "https://cdn.cloudflare.steamstatic.com/client/installer/SteamSetup.exe", "/S"),
                ("Epic Games", "https://launcher-public-service-prod06.ol.epicgames.com/launcher/api/installer/download/EpicGamesLauncherInstaller.msi", "/quiet /norestart"),
                ("Rockstar Launcher", "https://gamedownloads.rockstargames.com/public/installer/RockstarGamesLauncher.exe", "/S"),
                ("Origin", "https://download.dm.origin.com/origin/live/OriginSetup.exe", "/silent"),
                ("Battle.net", "https://www.battle.net/download/getInstaller?os=win&installer=Battle.net-Setup.exe", "/S")
            ],
            "💬 Общение": [
                ("TeamSpeak", "https://files.teamspeak-services.com/releases/client/3.6.2/TeamSpeak3-Client-win" + ("64" if self.is_64bit else "32") + "-3.6.2.exe", "/S"),
                ("Discord", "https://discord.com/api/download?platform=win", "/S"),
                ("Telegram Desktop", "https://telegram.org/dl/desktop/win" + ("64" if self.is_64bit else ""), "/S")
            ],
            "🛠️ Другое": [
                ("zapret-discord-youtube", "https://github.com/Flowseal/zapret-discord-youtube/releases/latest", "url"),
                ("WinRAR", "https://www.win-rar.com/fileadmin/winrar-versions/winrar/winrar-x" + ("64" if self.is_64bit else "32") + "-701.exe", "/S"),
                ("7-Zip", "https://www.7-zip.org/a/7z" + ("2409-x64" if self.is_64bit else "2409") + ".exe", "/S"),
                ("Visual C++ Redistributable", "https://aka.ms/vs/17/release/vc_redist.x" + ("64" if self.is_64bit else "86") + ".exe", "/quiet /norestart"),
                (".NET Desktop Runtime", "https://dotnet.microsoft.com/en-us/download/dotnet/thank-you/runtime-desktop-8.0.14-windows-x" + ("64" if self.is_64bit else "86") + "-installer", "/quiet /norestart"),
                ("qBittorrent", "https://downloads.sourceforge.net/project/qbittorrent/qbittorrent-win32/qbittorrent-5.0.3/qbittorrent_5.0.3_x" + ("64" if self.is_64bit else "32") + "_setup.exe", "/S"),
                ("VLC", "https://get.videolan.org/vlc/3.0.21/win" + ("64" if self.is_64bit else "32") + "/vlc-3.0.21-win" + ("64" if self.is_64bit else "32") + ".exe", "/S")
            ]
        }
        
        row = 4
        
        for category, programs in categories.items():
            category_frame = tk.Frame(scrollable_frame)
            category_frame.grid(row=row, column=0, columnspan=2, sticky="ew", pady=(10, 0))
            
            var_visible = tk.BooleanVar(value=False)
            
            header_btn = tk.Button(
                category_frame,
                text=f"▶ {category}",
                font=("Arial", 12, "bold"),
                fg="#9b59b6",
                bd=0,
                bg="#f0f0f0",
                anchor='w',
                cursor="hand2"
            )
            header_btn.pack(fill=tk.X)
            
            programs_frame = tk.Frame(scrollable_frame)
            programs_frame.grid(row=row+1, column=0, columnspan=2, sticky="ew")
            programs_frame.grid_remove()
            
            def toggle_category(frame, btn, visible_var, progs_frame):
                def toggle():
                    if visible_var.get():
                        progs_frame.grid_remove()
                        btn.config(text=f"▶ {frame}")
                        visible_var.set(False)
                    else:
                        progs_frame.grid()
                        btn.config(text=f"▼ {frame}")
                        visible_var.set(True)
                return toggle
            
            header_btn.config(command=toggle_category(category, header_btn, var_visible, programs_frame))
            
            for prog_name, url, silent_arg in programs:
                prog_frame = tk.Frame(programs_frame)
                prog_frame.pack(fill=tk.X, pady=2, padx=(20, 0))
                
                var = tk.BooleanVar()
                self.software_vars[prog_name] = {"var": var, "url": url, "silent": silent_arg}
                
                cb = tk.Checkbutton(
                    prog_frame,
                    text=prog_name,
                    variable=var,
                    font=("Arial", 10),
                    anchor='w'
                )
                cb.pack(side=tk.LEFT)
                
                if prog_name == "zapret-discord-youtube":
                    link = tk.Label(prog_frame, text="🔗", fg="#0088cc", cursor="hand2", font=("Arial", 9))
                    link.pack(side=tk.LEFT, padx=(5, 0))
                    link.bind("<Button-1>", lambda e, u=url: webbrowser.open(u))
            
            row += 2
    
    def setup_auto_tab(self):
        """Вкладка Автоматизация - заглушка"""
        frame = tk.Frame(self.tab_auto)
        frame.pack(fill=tk.BOTH, expand=True)
        
        center_frame = tk.Frame(frame)
        center_frame.pack(expand=True)
        
        tk.Label(center_frame, text="🚧 В РАЗРАБОТКЕ 🚧", font=("Arial", 24, "bold"), fg="#9b59b6").pack(pady=20)
        tk.Label(center_frame, text="Функции будут добавлены в следующих версиях", font=("Arial", 12), fg="gray").pack()
    
    def setup_dev_tab(self):
        """Вкладка В разработке - заглушка"""
        frame = tk.Frame(self.tab_dev)
        frame.pack(fill=tk.BOTH, expand=True)
        
        center_frame = tk.Frame(frame)
        center_frame.pack(expand=True)
        
        tk.Label(center_frame, text="🚧 В РАЗРАБОТКЕ 🚧", font=("Arial", 24, "bold"), fg="#9b59b6").pack(pady=20)
        tk.Label(center_frame, text="Функции будут добавлены в следующих версиях", font=("Arial", 12), fg="gray").pack()
    
    def apply_theme(self):
        """Применение темы"""
        self.theme_btn.config(text="🌙 Темная тема (в разработке)")
        self.theme_btn.config(state=tk.DISABLED)
    
    def toggle_theme(self):
        messagebox.showinfo("В разработке", "Темная тема будет добавлена в следующей версии!")
    
    def toggle_pin(self):
        self.pinned = not self.pinned
        self.root.attributes('-topmost', self.pinned)
        self.pin_btn.config(text="📍 Закреплено" if self.pinned else "📌 Закрепить")
    
    def load_settings(self):
        settings_file = os.path.join(self.program_path, "settings.json")
        try:
            if os.path.exists(settings_file):
                with open(settings_file, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                    self.temp_var.set(settings.get('temp', False))
                    self.dx_var.set(settings.get('dx', False))
                    self.opengl_var.set(settings.get('opengl', False))
                    self.recycle_var.set(settings.get('recycle', False))
                    self.prefetch_var.set(settings.get('prefetch', False))
                    self.ram_var.set(settings.get('ram', False))
        except:
            pass
    
    def save_settings(self):
        settings_file = os.path.join(self.program_path, "settings.json")
        settings = {
            'temp': self.temp_var.get(),
            'dx': self.dx_var.get(),
            'opengl': self.opengl_var.get(),
            'recycle': self.recycle_var.get(),
            'prefetch': self.prefetch_var.get(),
            'ram': self.ram_var.get()
        }
        try:
            with open(settings_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=4, ensure_ascii=False)
        except:
            pass
    
    def check_for_updates(self):
        """Проверка обновлений на GitHub с fallback-методом"""
        self.log("🔄 Проверка обновлений...")
        
        def check_thread():
            try:
                # Пробуем получить последний релиз
                url_latest = f"https://api.github.com/repos/{self.github_repo}/releases/latest"
                req = urllib.request.Request(url_latest, headers={'User-Agent': 'ToolByYokus'})
                
                try:
                    response = urllib.request.urlopen(req, timeout=10)
                    data = json.loads(response.read().decode())
                    latest_version = data['tag_name'].lstrip('v')
                    download_url = data['html_url']
                    
                    if latest_version > self.version:
                        self.root.after(0, lambda: self.prompt_update(latest_version, download_url))
                    else:
                        self.root.after(0, lambda: messagebox.showinfo("Обновления", "У тебя актуальная версия братан, зачилься!"))
                        self.log("✅ У тебя актуальная версия братан, зачилься!")
                        return
                        
                except urllib.error.HTTPError as e:
                    if e.code == 404:
                        # Если /latest не работает, пробуем получить список всех релизов
                        self.log("⏳ API GitHub еще не обновился, пробую альтернативный способ...")
                        url_all = f"https://api.github.com/repos/{self.github_repo}/releases"
                        req_all = urllib.request.Request(url_all, headers={'User-Agent': 'ToolByYokus'})
                        response_all = urllib.request.urlopen(req_all, timeout=10)
                        releases = json.loads(response_all.read().decode())
                        
                        if releases:
                            # Берем первый релиз (самый новый)
                            latest = releases[0]
                            latest_version = latest['tag_name'].lstrip('v')
                            download_url = latest['html_url']
                            
                            if latest_version > self.version:
                                self.root.after(0, lambda: self.prompt_update(latest_version, download_url))
                            else:
                                self.root.after(0, lambda: messagebox.showinfo("Обновления", "У тебя актуальная версия братан, зачилься!"))
                                self.log("✅ У тебя актуальная версия братан, зачилься!")
                            return
                        else:
                            raise Exception("Релизы не найдены")
                    else:
                        raise e
                        
            except Exception as e:
                # Если все способы не сработали, предлагаем открыть страницу релизов вручную
                error_msg = str(e)
                self.log(f"⚠️ Не удалось проверить обновления: {error_msg}")
                
                result = messagebox.askyesno(
                    "Проверка обновлений",
                    f"Не удалось автоматически проверить обновления.\n\n"
                    f"Ошибка: {error_msg}\n\n"
                    f"Хотите открыть страницу релизов в браузере?\n\n"
                    f"https://github.com/{self.github_repo}/releases"
                )
                if result:
                    webbrowser.open(f"https://github.com/{self.github_repo}/releases")
        
        thread = threading.Thread(target=check_thread)
        thread.daemon = True
        thread.start()
    
    def prompt_update(self, latest_version, download_url):
        result = messagebox.askyesno(
            "Доступно обновление",
            f"Доступна новая версия {latest_version}!\n\nТекущая версия: {self.version}\n\nХотите перейти на страницу загрузки?"
        )
        if result:
            webbrowser.open(download_url)
    
    def log(self, message, error=False):
        if hasattr(self, 'log_text'):
            self.log_text.insert(tk.END, f"{message}\n")
            self.log_text.see(tk.END)
            self.root.update()
    
    def select_all(self):
        self.temp_var.set(True)
        self.dx_var.set(True)
        self.opengl_var.set(True)
        self.recycle_var.set(True)
        self.prefetch_var.set(True)
        self.ram_var.set(True)
        if not hasattr(self, '_select_all_logged'):
            self.log("✓ Выбраны все пункты для очистки")
            self._select_all_logged = True
            self.root.after(1000, lambda: setattr(self, '_select_all_logged', False))
    
    def install_musthave(self):
        """Установка MUST HAVE программ"""
        must_have_list = [
            "Google Chrome", "7-Zip", "Discord", "VLC", 
            "Steam", "qBittorrent", "Visual C++ Redistributable", ".NET Desktop Runtime"
        ]
        
        programs_to_install = []
        for prog in must_have_list:
            if prog in self.software_vars:
                programs_to_install.append(prog)
                self.software_vars[prog]["var"].set(True)
        
        if not programs_to_install:
            messagebox.showwarning("Ошибка", "Не удалось найти программы для установки!")
            return
        
        result = messagebox.askyesno(
            "MUST HAVE установка",
            f"Будут установлены следующие программы:\n\n" + "\n".join(f"• {p}" for p in programs_to_install) + 
            f"\n\nВсего: {len(programs_to_install)} программ\n\nПродолжить?"
        )
        
        if result:
            self.install_selected_software()
    
    def show_progress_window(self, title, max_value):
        """Показывает окно прогресса"""
        progress_window = tk.Toplevel(self.root)
        progress_window.title(title)
        progress_window.geometry("400x150")
        progress_window.resizable(False, False)
        progress_window.transient(self.root)
        progress_window.grab_set()
        
        progress_window.update_idletasks()
        x = (progress_window.winfo_screenwidth() // 2) - (400 // 2)
        y = (progress_window.winfo_screenheight() // 2) - (150 // 2)
        progress_window.geometry(f"+{x}+{y}")
        
        tk.Label(progress_window, text=title, font=("Arial", 12, "bold")).pack(pady=10)
        
        progress_bar = ttk.Progressbar(progress_window, orient=tk.HORIZONTAL, length=350, mode='determinate', maximum=max_value)
        progress_bar.pack(pady=10)
        
        status_label = tk.Label(progress_window, text="Подготовка...", font=("Arial", 9))
        status_label.pack(pady=5)
        
        return progress_window, progress_bar, status_label
    
    def install_selected_software(self):
        """Установка выбранных программ с сохранением установщиков в папку программы"""
        selected = [name for name, data in self.software_vars.items() if data["var"].get()]
        
        if not selected:
            messagebox.showwarning("Нет выбора", "Не выбрано ни одной программы для установки!")
            return
        
        result = messagebox.askyesno(
            "Подтверждение установки",
            f"Будет установлено {len(selected)} программ.\n\n"
            f"Установщики будут сохранены в папку:\n{self.installers_folder}\n\n"
            f"После установки они будут автоматически удалены.\n\n"
            f"Продолжить?"
        )
        
        if result:
            progress_win, progress_bar, status_label = self.show_progress_window("Установка программ", len(selected))
            
            def install_thread():
                installed = []
                failed = []
                downloaded_files = []
                
                for i, prog_name in enumerate(selected):
                    status_label.config(text=f"Установка: {prog_name}")
                    progress_bar['value'] = i
                    progress_win.update()
                    
                    data = self.software_vars[prog_name]
                    url = data["url"]
                    silent_arg = data["silent"]
                    
                    try:
                        if silent_arg == "url":
                            webbrowser.open(url)
                            installed.append(prog_name)
                            continue
                        
                        safe_name = prog_name.replace(' ', '_').replace('.', '_')
                        if url.endswith('.msi'):
                            filename = os.path.join(self.installers_folder, f"{safe_name}.msi")
                        else:
                            filename = os.path.join(self.installers_folder, f"{safe_name}.exe")
                        
                        status_label.config(text=f"Скачивание: {prog_name}")
                        self.log(f"   ⬇️ Скачивание {prog_name} в {self.installers_folder}")
                        urllib.request.urlretrieve(url, filename)
                        downloaded_files.append(filename)
                        
                        status_label.config(text=f"Установка: {prog_name}")
                        self.log(f"   🔧 Установка {prog_name}")
                        
                        if filename.endswith('.msi'):
                            cmd = f'msiexec /i "{filename}" {silent_arg}'
                        else:
                            cmd = f'"{filename}" {silent_arg}'
                        
                        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                        
                        if result.returncode == 0 or result.returncode == 3010:
                            installed.append(prog_name)
                            self.log(f"   ✅ {prog_name} установлен")
                        else:
                            failed.append(prog_name)
                            self.log(f"   ❌ Ошибка установки {prog_name} (код: {result.returncode})")
                            
                    except Exception as e:
                        failed.append(prog_name)
                        self.log(f"   ❌ Ошибка: {prog_name} - {str(e)}")
                
                # Очищаем папку Installers (удаляем только содержимое, оставляя папку)
                status_label.config(text="Удаление временных файлов...")
                progress_win.update()
                
                if os.path.exists(self.installers_folder):
                    for file in os.listdir(self.installers_folder):
                        file_path = os.path.join(self.installers_folder, file)
                        try:
                            if os.path.isfile(file_path):
                                os.remove(file_path)
                                self.log(f"   🗑️ Удален установщик: {file}")
                        except:
                            pass
                    self.log("   ✅ Папка Installers очищена")
                
                progress_bar['value'] = len(selected)
                status_label.config(text="Установка завершена!")
                progress_win.update()
                
                result_text = f"Установка завершена!\n\n✅ Успешно: {len(installed)}\n❌ Ошибок: {len(failed)}"
                if installed:
                    result_text += f"\n\nУстановлено:\n" + "\n".join(f"  • {p}" for p in installed)
                if failed:
                    result_text += f"\n\nНе удалось:\n" + "\n".join(f"  • {p}" for p in failed)
                
                messagebox.showinfo("Результат установки", result_text)
                progress_win.destroy()
            
            thread = threading.Thread(target=install_thread)
            thread.daemon = True
            thread.start()
    
    def format_size(self, size_bytes):
        if size_bytes < 1024:
            return f"{size_bytes} Б"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.2f} КБ"
        elif size_bytes < 1024 * 1024 * 1024:
            return f"{size_bytes / (1024 * 1024):.2f} МБ"
        else:
            return f"{size_bytes / (1024 * 1024 * 1024):.2f} ГБ"
    
    def get_folder_size(self, folder_path):
        total = 0
        if not os.path.exists(folder_path):
            return 0
        try:
            for root, dirs, files in os.walk(folder_path):
                for file in files:
                    try:
                        file_path = os.path.join(root, file)
                        total += os.path.getsize(file_path)
                    except:
                        continue
        except:
            pass
        return total
    
    def get_recycle_bin_size(self):
        try:
            cmd = 'powershell -command "$size = 0; Get-ChildItem \'C:\\$Recycle.Bin\' -Recurse -ErrorAction SilentlyContinue | ForEach-Object { $size += $_.Length }; Write-Output $size"'
            result = subprocess.run(cmd, capture_output=True, text=True, shell=True)
            if result.stdout.strip():
                return int(result.stdout.strip())
        except:
            pass
        return 0
    
    def empty_recycle_bin(self):
        try:
            cmd = 'powershell -command "Clear-RecycleBin -Force"'
            subprocess.run(cmd, capture_output=True, text=True, shell=True)
            return True
        except:
            try:
                os.system('cmd /c "rd /s /q C:\\$Recycle.Bin"')
                return True
            except:
                return False
    
    def clear_ram_cache(self):
        """Очистка RAM (оперативной памяти)"""
        try:
            memory_before = psutil.virtual_memory()
            used_before = memory_before.used
            
            import gc
            gc.collect()
            
            memory_after = psutil.virtual_memory()
            freed = used_before - memory_after.used
            
            return freed if freed > 0 else 0
        except Exception as e:
            self.log(f"   ⚠️ Ошибка очистки RAM: {e}")
            return 0
    
    def analyze_all(self):
        self.analyze_btn.config(state=tk.DISABLED)
        self.clean_btn.config(state=tk.DISABLED)
        self.log_text.delete(1.0, tk.END)
        self.log("🔍 Начинаю анализ выбранных папок...")
        self.log("=" * 60)
        
        thread = threading.Thread(target=self._analyze_thread)
        thread.daemon = True
        thread.start()
    
    def _analyze_thread(self):
        try:
            total_size = 0
            
            if self.temp_var.get():
                self.log("📁 Анализ папки Temp...")
                size = self.get_folder_size(self.temp_path)
                self.sizes['temp'] = size
                total_size += size
                self.log(f"   Temp: {self.format_size(size)}")
            
            if self.dx_var.get():
                self.log("📁 Анализ папки DXCache...")
                size = self.get_folder_size(self.dx_cache_path)
                self.sizes['dxcache'] = size
                total_size += size
                if os.path.exists(self.dx_cache_path):
                    self.log(f"   DXCache: {self.format_size(size)}")
                else:
                    self.log(f"   DXCache: папка не найдена")
            
            if self.opengl_var.get():
                self.log("📁 Анализ папки OpenGL Cache...")
                size = self.get_folder_size(self.opengl_cache_path)
                self.sizes['opengl'] = size
                total_size += size
                if os.path.exists(self.opengl_cache_path):
                    self.log(f"   OpenGL Cache: {self.format_size(size)}")
                else:
                    self.log(f"   OpenGL Cache: папка не найдена")
            
            if self.prefetch_var.get():
                self.log("📁 Анализ папки Prefetch...")
                size = self.get_folder_size(self.prefetch_path)
                self.sizes['prefetch'] = size
                total_size += size
                self.log(f"   Prefetch: {self.format_size(size)}")
            
            if self.ram_var.get():
                self.log("💾 Анализ RAM...")
                memory = psutil.virtual_memory()
                self.sizes['ram'] = memory.available
                total_size += memory.available
                self.log(f"   Доступно RAM для очистки: {self.format_size(memory.available)}")
            
            if self.recycle_var.get():
                self.log("📁 Анализ корзины...")
                size = self.get_recycle_bin_size()
                self.sizes['recycle'] = size
                total_size += size
                self.log(f"   Корзина: {self.format_size(size)}")
            
            self.log("=" * 60)
            self.log(f"📊 Общий размер к удалению/очистке: {self.format_size(total_size)}")
            self.log("")
            
            if total_size > 0:
                self.log("✅ Анализ завершен. Можно приступать к очистке.")
                self.clean_btn.config(state=tk.NORMAL)
            else:
                self.log("✨ Нет файлов для удаления!")
                self.clean_btn.config(state=tk.DISABLED)
                
        except Exception as e:
            self.log(f"❌ Ошибка при анализе: {str(e)}")
        finally:
            self.analyze_btn.config(state=tk.NORMAL)
    
    def start_cleanup(self):
        total_size = 0
        if self.temp_var.get():
            total_size += self.sizes['temp']
        if self.dx_var.get():
            total_size += self.sizes['dxcache']
        if self.opengl_var.get():
            total_size += self.sizes['opengl']
        if self.prefetch_var.get():
            total_size += self.sizes['prefetch']
        if self.ram_var.get():
            total_size += self.sizes['ram']
        if self.recycle_var.get():
            total_size += self.sizes['recycle']
        
        confirm_window = tk.Toplevel(self.root)
        confirm_window.title("Подтверждение очистки")
        confirm_window.geometry("400x280")
        confirm_window.resizable(False, False)
        confirm_window.transient(self.root)
        confirm_window.grab_set()
        
        confirm_window.update_idletasks()
        x = (confirm_window.winfo_screenwidth() // 2) - (400 // 2)
        y = (confirm_window.winfo_screenheight() // 2) - (280 // 2)
        confirm_window.geometry(f"+{x}+{y}")
        
        tk.Label(confirm_window, text="⚠️ ПОДТВЕРЖДЕНИЕ ОЧИСТКИ", font=("Arial", 14, "bold"), fg="red").pack(pady=(20, 10))
        tk.Label(confirm_window, text=f"Будет удалено/очищено: {self.format_size(total_size)}", font=("Arial", 12)).pack(pady=5)
        
        if not self.is_admin:
            tk.Label(confirm_window, text="⚠️ Некоторые функции требуют прав администратора", font=("Arial", 9), fg="orange").pack(pady=5)
        
        self.remaining_time = 5
        timer_label = tk.Label(confirm_window, text=f"Автоматическое подтверждение через {self.remaining_time} сек...", font=("Arial", 10), fg="gray")
        timer_label.pack(pady=10)
        
        def update_timer():
            if self.remaining_time > 0:
                self.remaining_time -= 1
                timer_label.config(text=f"Автоматическое подтверждение через {self.remaining_time} сек...")
                confirm_window.after(1000, update_timer)
            else:
                confirm_window.destroy()
                self.execute_cleanup()
        
        btn_frame = tk.Frame(confirm_window)
        btn_frame.pack(pady=20)
        
        def on_yes():
            confirm_window.destroy()
            self.execute_cleanup()
        
        def on_no():
            confirm_window.destroy()
            self.log("❌ Очистка отменена пользователем")
        
        yes_btn = tk.Button(btn_frame, text="✅ ДА, ОЧИСТИТЬ", command=on_yes, bg="#4CAF50", fg="white", font=("Arial", 10, "bold"), width=15, cursor="hand2")
        yes_btn.pack(side=tk.LEFT, padx=5)
        
        no_btn = tk.Button(btn_frame, text="❌ НЕТ, ОТМЕНИТЬ", command=on_no, bg="#f44336", fg="white", font=("Arial", 10, "bold"), width=15, cursor="hand2")
        no_btn.pack(side=tk.LEFT, padx=5)
        
        update_timer()
    
    def execute_cleanup(self):
        self.analyze_btn.config(state=tk.DISABLED)
        self.clean_btn.config(state=tk.DISABLED)
        self.progress_bar['value'] = 0
        self.log("")
        self.log("=" * 60)
        self.log("🧹 НАЧАЛО ОЧИСТКИ")
        self.log("=" * 60)
        
        thread = threading.Thread(target=self._cleanup_thread)
        thread.daemon = True
        thread.start()
    
    def _cleanup_thread(self):
        try:
            total_items = 0
            if self.temp_var.get():
                total_items += 1
            if self.dx_var.get():
                total_items += 1
            if self.opengl_var.get():
                total_items += 1
            if self.prefetch_var.get():
                total_items += 1
            if self.ram_var.get():
                total_items += 1
            if self.recycle_var.get():
                total_items += 1
            
            current_item = 0
            deleted_files_total = 0
            freed_space_total = 0
            all_failed_files = []
            
            if self.temp_var.get():
                current_item += 1
                self.progress_label.config(text="Очистка Temp...")
                self.progress_bar['value'] = (current_item / total_items) * 100
                self.log("")
                self.log("📁 Очистка папки Temp...")
                
                deleted_files, freed_space, failed = self.clean_folder_with_log(self.temp_path)
                deleted_files_total += deleted_files
                freed_space_total += freed_space
                all_failed_files.extend(failed)
                self.log(f"   ✅ Удалено файлов: {deleted_files}, освобождено: {self.format_size(freed_space)}")
            
            if self.dx_var.get():
                current_item += 1
                self.progress_label.config(text="Очистка DXCache...")
                self.progress_bar['value'] = (current_item / total_items) * 100
                self.log("")
                self.log("📁 Очистка папки DXCache...")
                
                if os.path.exists(self.dx_cache_path):
                    deleted_files, freed_space, failed = self.clean_folder_with_log(self.dx_cache_path)
                    deleted_files_total += deleted_files
                    freed_space_total += freed_space
                    all_failed_files.extend(failed)
                    self.log(f"   ✅ Удалено файлов: {deleted_files}, освобождено: {self.format_size(freed_space)}")
                else:
                    self.log("   ⚠️ Папка DXCache не найдена")
            
            if self.opengl_var.get():
                current_item += 1
                self.progress_label.config(text="Очистка OpenGL Cache...")
                self.progress_bar['value'] = (current_item / total_items) * 100
                self.log("")
                self.log("📁 Очистка папки OpenGL Cache...")
                
                if os.path.exists(self.opengl_cache_path):
                    deleted_files, freed_space, failed = self.clean_folder_with_log(self.opengl_cache_path)
                    deleted_files_total += deleted_files
                    freed_space_total += freed_space
                    all_failed_files.extend(failed)
                    self.log(f"   ✅ Удалено файлов: {deleted_files}, освобождено: {self.format_size(freed_space)}")
                else:
                    self.log("   ⚠️ Папка OpenGL Cache не найдена")
            
            if self.prefetch_var.get():
                current_item += 1
                self.progress_label.config(text="Очистка Prefetch...")
                self.progress_bar['value'] = (current_item / total_items) * 100
                self.log("")
                self.log("📁 Очистка папки Prefetch...")
                
                if os.path.exists(self.prefetch_path) and self.is_admin:
                    deleted_files, freed_space, failed = self.clean_folder_with_log(self.prefetch_path)
                    deleted_files_total += deleted_files
                    freed_space_total += freed_space
                    all_failed_files.extend(failed)
                    self.log(f"   ✅ Удалено файлов: {deleted_files}, освобождено: {self.format_size(freed_space)}")
                elif not self.is_admin:
                    self.log("   ⚠️ Требуются права администратора для очистки Prefetch")
                    all_failed_files.append(("Prefetch", "Требуются права администратора"))
                else:
                    self.log("   ⚠️ Папка Prefetch не найдена")
            
            if self.ram_var.get():
                current_item += 1
                self.progress_label.config(text="Очистка RAM...")
                self.progress_bar['value'] = (current_item / total_items) * 100
                self.log("")
                self.log("💾 Очистка RAM (оперативной памяти)...")
                
                try:
                    freed = self.clear_ram_cache()
                    if freed > 0:
                        freed_space_total += freed
                        self.log(f"   ✅ Освобождено RAM: {self.format_size(freed)}")
                        deleted_files_total += 1
                    else:
                        self.log("   ⚠️ Не удалось освободить RAM")
                except Exception as e:
                    self.log(f"   ❌ Ошибка при очистке RAM: {e}")
                    all_failed_files.append(("RAM", str(e)))
            
            if self.recycle_var.get():
                current_item += 1
                self.progress_label.config(text="Очистка корзины...")
                self.progress_bar['value'] = (current_item / total_items) * 100
                self.log("")
                self.log("🗑️ Очистка корзины...")
                
                try:
                    recycle_size = self.get_recycle_bin_size()
                    if self.empty_recycle_bin():
                        deleted_files_total += 1
                        freed_space_total += recycle_size
                        self.log(f"   ✅ Корзина очищена, освобождено: {self.format_size(recycle_size)}")
                    else:
                        self.log("   ⚠️ Не удалось очистить корзину")
                        all_failed_files.append(("Корзина", "Не удалось очистить корзину"))
                except Exception as e:
                    self.log(f"   ❌ Ошибка при очистке корзины: {e}")
                    all_failed_files.append(("Корзина", str(e)))
            
            self.progress_bar['value'] = 100
            self.progress_label.config(text="Очистка завершена!")
            self.log("")
            self.log("=" * 60)
            self.log("📊 ИТОГИ ОЧИСТКИ")
            self.log("=" * 60)
            self.log(f"✅ Всего удалено/очищено: {deleted_files_total:,}")
            self.log(f"💾 Освобождено места: {self.format_size(freed_space_total)}")
            if all_failed_files:
                self.log(f"⚠️ Не удалось обработать: {len(all_failed_files)}")
            self.log("=" * 60)
            
            self.save_clean_log(deleted_files_total, freed_space_total, all_failed_files)
            
            messagebox.showinfo(
                "Очистка завершена",
                f"Tool by Yokus завершил очистку!\n\n"
                f"📁 Обработано элементов: {deleted_files_total:,}\n"
                f"💾 Освобождено места: {self.format_size(freed_space_total)}\n"
                f"📄 Журнал сохранен в папку: {self.logs_folder}"
            )
            
        except Exception as e:
            self.log(f"❌ Ошибка при очистке: {str(e)}")
            messagebox.showerror("Ошибка", f"Не удалось выполнить очистку:\n{str(e)}")
        finally:
            self.clean_btn.config(state=tk.DISABLED)
            self.analyze_btn.config(state=tk.NORMAL)
            self.progress_label.config(text="Готов к работе")
    
    def clean_folder_with_log(self, folder_path):
        if not os.path.exists(folder_path):
            return 0, 0, []
        
        deleted_count = 0
        freed_space = 0
        failed_files = []
        
        try:
            for root, dirs, files in os.walk(folder_path):
                for file in files:
                    try:
                        file_path = os.path.join(root, file)
                        file_size = os.path.getsize(file_path)
                        os.remove(file_path)
                        deleted_count += 1
                        freed_space += file_size
                    except PermissionError:
                        failed_files.append((file_path, "Отказано в доступе (файл используется)"))
                    except OSError as e:
                        failed_files.append((file_path, f"Ошибка ОС: {str(e)}"))
                    except Exception as e:
                        failed_files.append((file_path, f"Неизвестная ошибка: {str(e)}"))
                
                for dir_name in dirs:
                    try:
                        dir_path = os.path.join(root, dir_name)
                        dir_size = self.get_folder_size(dir_path)
                        shutil.rmtree(dir_path, ignore_errors=True)
                        freed_space += dir_size
                    except PermissionError:
                        failed_files.append((dir_path, "Отказано в доступе (папка используется)"))
                    except Exception as e:
                        failed_files.append((dir_path, f"Ошибка удаления папки: {str(e)}"))
        except Exception as e:
            self.log(f"   ⚠️ Ошибка при очистке: {e}")
        
        return deleted_count, freed_space, failed_files
    
    def save_clean_log(self, deleted_files_total, freed_space_total, failed_files):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_filename = f"{timestamp}_clean.txt"
        log_path = os.path.join(self.logs_folder, log_filename)
        
        with open(log_path, 'w', encoding='utf-8') as f:
            f.write("=" * 60 + "\n")
            f.write("TOOL BY YOKUS - ЖУРНАЛ ОЧИСТКИ\n")
            f.write(f"Дата и время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 60 + "\n\n")
            
            f.write("РЕЗУЛЬТАТЫ ОЧИСТКИ:\n")
            f.write("-" * 40 + "\n")
            f.write(f"Количество обработанных элементов: {deleted_files_total:,}\n")
            f.write(f"Освобождённое место: {self.format_size(freed_space_total)}\n")
            f.write("-" * 40 + "\n\n")
            
            if failed_files:
                f.write("НЕ УДАЛОСЬ ОБРАБОТАТЬ:\n")
                f.write("-" * 40 + "\n")
                f.write(f"Количество ошибок: {len(failed_files)}\n\n")
                f.write("Список и причины ошибок:\n")
                for file_path, error in failed_files:
                    f.write(f"• {file_path}\n")
                    f.write(f"  Причина: {error}\n\n")
            else:
                f.write("Все операции выполнены успешно! Ошибок не возникло.\n")
            
            f.write("\n" + "=" * 60 + "\n")
            f.write("Журнал создан Tool by Yokus\n")
        
        self.log(f"\n📄 Журнал очистки сохранен: {log_filename}")

def main():
    root = tk.Tk()
    app = ToolByYokus(root)
    root.mainloop()

if __name__ == "__main__":
    main()
