"""Main window for SSH Tunnel Manager GUI."""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import Optional

from src.core.ssh_manager import SSHManager
from src.core.tunnel_manager import TunnelManager
from src.core.tunnel_monitor import TunnelMonitor
from src.models.connection import Connection
from src.models.tunnel import Tunnel
from src.services.config_service import ConfigService
from src.services.profile_service import ProfileService
from src.utils.constants import ConnectionStatus, TunnelStatus, TunnelType, AuthMethod
from src.utils.logger import get_logger, GUILogHandler
from src.gui.themes import get_theme, apply_theme_to_widget
from src.gui.widgets import StatusIndicator, Tooltip

logger = get_logger(__name__)


class MainWindow:
    """Main application window."""

    def __init__(self, root: tk.Tk) -> None:
        """
        Initialize main window.

        Args:
            root: Tk root window
        """
        self.root = root
        self.root.title("SSH Tunnel Manager v1.0")
        self.root.geometry("1200x800")
        self.root.minsize(1000, 700)

        # Services
        self.config_service = ConfigService()
        self.profile_service = ProfileService()

        # State
        self.ssh_manager: Optional[SSHManager] = None
        self.tunnel_manager: Optional[TunnelManager] = None
        self.tunnel_monitor = TunnelMonitor()
        self.current_connection: Optional[Connection] = None
        self.active_tunnels: list = []

        # Theme
        self.current_theme = get_theme(self.config_service.get("theme", "light"))

        # Setup UI
        self._create_menu_bar()
        self._create_status_bar()
        self._create_main_content()

        # Apply theme
        apply_theme_to_widget(self.root, self.current_theme)

        # Bind window close
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

        logger.info("Main window initialized")

    def _create_menu_bar(self) -> None:
        """Create menu bar."""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="New Profile", command=self._new_profile)
        file_menu.add_command(label="Open Profile", command=self._open_profile)
        file_menu.add_command(label="Save Profile", command=self._save_profile)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self._on_close)

        # Tools menu
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Tools", menu=tools_menu)
        tools_menu.add_command(label="Export SSH Command", command=self._export_ssh_command)
        tools_menu.add_command(label="Export Batch Script", command=self._export_batch)

        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self._show_about)

    def _create_status_bar(self) -> None:
        """Create status bar."""
        self.status_bar = ttk.Frame(self.root, relief=tk.SUNKEN)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        self.status_indicator = StatusIndicator(self.status_bar)
        self.status_indicator.pack(side=tk.LEFT, padx=5, pady=2)

        self.status_label = ttk.Label(self.status_bar, text="Disconnected")
        self.status_label.pack(side=tk.LEFT, padx=5)

        self.tunnel_count_label = ttk.Label(self.status_bar, text="0 tunnels")
        self.tunnel_count_label.pack(side=tk.RIGHT, padx=5)

    def _create_main_content(self) -> None:
        """Create main content area."""
        # Create paned window
        main_paned = ttk.PanedWindow(self.root, orient=tk.VERTICAL)
        main_paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Top frame (connection + tunnel config)
        top_frame = ttk.Frame(main_paned)
        main_paned.add(top_frame, weight=1)

        # Connection panel
        conn_frame = ttk.LabelFrame(top_frame, text="SSH Connection", padding=10)
        conn_frame.pack(fill=tk.X, padx=5, pady=5)
        self._create_connection_panel(conn_frame)

        # Tunnel config panel
        tunnel_frame = ttk.LabelFrame(top_frame, text="Tunnel Configuration", padding=10)
        tunnel_frame.pack(fill=tk.X, padx=5, pady=5)
        self._create_tunnel_config_panel(tunnel_frame)

        # Active tunnels panel
        active_frame = ttk.LabelFrame(top_frame, text="Active Tunnels", padding=10)
        active_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self._create_active_tunnels_panel(active_frame)

        # Log panel (collapsible)
        log_frame = ttk.LabelFrame(main_paned, text="Logs", padding=10)
        main_paned.add(log_frame, weight=0)
        self._create_log_panel(log_frame)

    def _create_connection_panel(self, parent: ttk.Frame) -> None:
        """Create connection panel."""
        # Host
        ttk.Label(parent, text="Host:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        self.host_entry = ttk.Entry(parent, width=30)
        self.host_entry.grid(row=0, column=1, padx=5, pady=2)

        # Port
        ttk.Label(parent, text="Port:").grid(row=0, column=2, sticky=tk.W, padx=5, pady=2)
        self.port_entry = ttk.Entry(parent, width=10)
        self.port_entry.insert(0, "22")
        self.port_entry.grid(row=0, column=3, padx=5, pady=2)

        # Username
        ttk.Label(parent, text="Username:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=2)
        self.username_entry = ttk.Entry(parent, width=30)
        self.username_entry.grid(row=1, column=1, padx=5, pady=2)

        # Auth method
        ttk.Label(parent, text="Auth:").grid(row=1, column=2, sticky=tk.W, padx=5, pady=2)
        self.auth_var = tk.StringVar(value="password")
        self.auth_combo = ttk.Combobox(
            parent,
            textvariable=self.auth_var,
            values=["password", "key_file"],
            state="readonly",
            width=12,
        )
        self.auth_combo.grid(row=1, column=3, padx=5, pady=2)
        self.auth_combo.bind("<<ComboboxSelected>>", self._on_auth_method_changed)

        # Password
        ttk.Label(parent, text="Password:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=2)
        self.password_entry = ttk.Entry(parent, show="*", width=30)
        self.password_entry.grid(row=2, column=1, padx=5, pady=2)

        # Key file
        self.key_label = ttk.Label(parent, text="Key File:")
        self.key_entry = ttk.Entry(parent, width=30)
        self.key_browse_btn = ttk.Button(parent, text="Browse", command=self._browse_key_file)

        # Buttons
        btn_frame = ttk.Frame(parent)
        btn_frame.grid(row=3, column=0, columnspan=4, pady=10)

        self.connect_btn = ttk.Button(btn_frame, text="Connect", command=self._connect)
        self.connect_btn.pack(side=tk.LEFT, padx=5)

        self.disconnect_btn = ttk.Button(btn_frame, text="Disconnect", command=self._disconnect, state=tk.DISABLED)
        self.disconnect_btn.pack(side=tk.LEFT, padx=5)

        self.test_btn = ttk.Button(btn_frame, text="Test Connection", command=self._test_connection)
        self.test_btn.pack(side=tk.LEFT, padx=5)

    def _create_tunnel_config_panel(self, parent: ttk.Frame) -> None:
        """Create tunnel configuration panel."""
        # Tunnel type
        ttk.Label(parent, text="Type:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        self.tunnel_type_var = tk.StringVar(value="local")
        ttk.Radiobutton(parent, text="Local (-L)", variable=self.tunnel_type_var, value="local").grid(
            row=0, column=1, sticky=tk.W, padx=5, pady=2
        )
        ttk.Radiobutton(parent, text="Remote (-R)", variable=self.tunnel_type_var, value="remote").grid(
            row=0, column=2, sticky=tk.W, padx=5, pady=2
        )
        ttk.Radiobutton(parent, text="Dynamic (-D)", variable=self.tunnel_type_var, value="dynamic").grid(
            row=0, column=3, sticky=tk.W, padx=5, pady=2
        )

        # Local port
        ttk.Label(parent, text="Local Port:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=2)
        self.local_port_entry = ttk.Entry(parent, width=10)
        self.local_port_entry.grid(row=1, column=1, sticky=tk.W, padx=5, pady=2)

        # Remote host
        ttk.Label(parent, text="Remote Host:").grid(row=1, column=2, sticky=tk.W, padx=5, pady=2)
        self.remote_host_entry = ttk.Entry(parent, width=20)
        self.remote_host_entry.insert(0, "localhost")
        self.remote_host_entry.grid(row=1, column=3, sticky=tk.W, padx=5, pady=2)

        # Remote port
        ttk.Label(parent, text="Remote Port:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=2)
        self.remote_port_entry = ttk.Entry(parent, width=10)
        self.remote_port_entry.grid(row=2, column=1, sticky=tk.W, padx=5, pady=2)

        # Add button
        self.add_tunnel_btn = ttk.Button(parent, text="Add Tunnel", command=self._add_tunnel, state=tk.DISABLED)
        self.add_tunnel_btn.grid(row=2, column=3, padx=5, pady=5)

    def _create_active_tunnels_panel(self, parent: ttk.Frame) -> None:
        """Create active tunnels panel."""
        # Create treeview
        columns = ("Type", "Local Port", "Remote", "Status", "Uptime")
        self.tunnels_tree = ttk.Treeview(parent, columns=columns, show="tree headings", height=8)

        # Configure columns
        self.tunnels_tree.column("#0", width=200)
        self.tunnels_tree.heading("#0", text="Name")

        for col in columns:
            self.tunnels_tree.column(col, width=100)
            self.tunnels_tree.heading(col, text=col)

        # Scrollbar
        scrollbar = ttk.Scrollbar(parent, orient=tk.VERTICAL, command=self.tunnels_tree.yview)
        self.tunnels_tree.configure(yscrollcommand=scrollbar.set)

        # Pack
        self.tunnels_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Context menu
        self.tunnel_context_menu = tk.Menu(self.root, tearoff=0)
        self.tunnel_context_menu.add_command(label="Stop Tunnel", command=self._stop_selected_tunnel)
        self.tunnel_context_menu.add_command(label="Remove Tunnel", command=self._remove_selected_tunnel)

        self.tunnels_tree.bind("<Button-3>", self._show_tunnel_context_menu)

    def _create_log_panel(self, parent: ttk.Frame) -> None:
        """Create log panel."""
        # Create text widget
        self.log_text = tk.Text(parent, height=10, wrap=tk.WORD, bg="#1e1e1e", fg="#ffffff")
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Scrollbar
        log_scrollbar = ttk.Scrollbar(parent, orient=tk.VERTICAL, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=log_scrollbar.set)
        log_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Configure tags for log levels
        self.log_text.tag_config("debug", foreground="#888888")
        self.log_text.tag_config("info", foreground="#ffffff")
        self.log_text.tag_config("warning", foreground="#ff9800")
        self.log_text.tag_config("error", foreground="#f44336")
        self.log_text.tag_config("critical", foreground="#ff0000")

        # Add GUI log handler
        gui_handler = GUILogHandler(self.log_text)
        logger.addHandler(gui_handler)

    def _on_auth_method_changed(self, event: object = None) -> None:
        """Handle auth method change."""
        auth_method = self.auth_var.get()

        if auth_method == "password":
            # Show password, hide key file
            self.password_entry.grid(row=2, column=1, padx=5, pady=2)
            self.key_label.grid_forget()
            self.key_entry.grid_forget()
            self.key_browse_btn.grid_forget()
        else:
            # Hide password, show key file
            self.password_entry.grid_forget()
            self.key_label.grid(row=2, column=0, sticky=tk.W, padx=5, pady=2)
            self.key_entry.grid(row=2, column=1, padx=5, pady=2)
            self.key_browse_btn.grid(row=2, column=2, padx=5, pady=2)

    def _browse_key_file(self) -> None:
        """Browse for SSH key file."""
        filename = filedialog.askopenfilename(
            title="Select SSH Private Key",
            filetypes=[("All Files", "*.*"), ("PEM Files", "*.pem")],
        )
        if filename:
            self.key_entry.delete(0, tk.END)
            self.key_entry.insert(0, filename)

    def _connect(self) -> None:
        """Connect to SSH server."""
        try:
            # Get connection details
            host = self.host_entry.get().strip()
            port = int(self.port_entry.get().strip())
            username = self.username_entry.get().strip()
            auth_method_str = self.auth_var.get()

            if not host or not username:
                messagebox.showerror("Error", "Host and username are required")
                return

            # Create connection object
            if auth_method_str == "password":
                password = self.password_entry.get()
                if not password:
                    messagebox.showerror("Error", "Password is required")
                    return
                connection = Connection(
                    host=host,
                    port=port,
                    username=username,
                    password=password,
                    auth_method=AuthMethod.PASSWORD,
                )
            else:
                key_file = self.key_entry.get().strip()
                if not key_file:
                    messagebox.showerror("Error", "Key file is required")
                    return
                connection = Connection(
                    host=host,
                    port=port,
                    username=username,
                    key_file=key_file,
                    auth_method=AuthMethod.KEY_FILE,
                )

            # Create SSH manager and connect
            self.ssh_manager = SSHManager(connection)
            self.ssh_manager.connect()

            # Create tunnel manager
            transport = self.ssh_manager.get_transport()
            if transport:
                self.tunnel_manager = TunnelManager(transport)

            self.current_connection = connection

            # Update UI
            self.status_indicator.set_status("connected")
            self.status_label.config(text=f"Connected to {connection.get_connection_string()}")
            self.connect_btn.config(state=tk.DISABLED)
            self.disconnect_btn.config(state=tk.NORMAL)
            self.add_tunnel_btn.config(state=tk.NORMAL)

            logger.info(f"Connected to {connection.get_connection_string()}")
            messagebox.showinfo("Success", "Connected successfully!")

        except Exception as e:
            logger.error(f"Connection failed: {e}")
            messagebox.showerror("Connection Error", str(e))

    def _disconnect(self) -> None:
        """Disconnect from SSH server."""
        try:
            # Stop all tunnels
            if self.tunnel_manager:
                self.tunnel_manager.stop_all_tunnels()

            # Disconnect SSH
            if self.ssh_manager:
                self.ssh_manager.disconnect()

            # Clear state
            self.ssh_manager = None
            self.tunnel_manager = None
            self.current_connection = None
            self.active_tunnels = []

            # Update UI
            self.status_indicator.set_status("disconnected")
            self.status_label.config(text="Disconnected")
            self.connect_btn.config(state=tk.NORMAL)
            self.disconnect_btn.config(state=tk.DISABLED)
            self.add_tunnel_btn.config(state=tk.DISABLED)

            # Clear tunnels tree
            for item in self.tunnels_tree.get_children():
                self.tunnels_tree.delete(item)

            logger.info("Disconnected")
            messagebox.showinfo("Disconnected", "Disconnected successfully")

        except Exception as e:
            logger.error(f"Disconnect error: {e}")
            messagebox.showerror("Error", str(e))

    def _test_connection(self) -> None:
        """Test SSH connection."""
        # Implementation similar to _connect but using test_connection method
        messagebox.showinfo("Test", "Connection test not yet implemented")

    def _add_tunnel(self) -> None:
        """Add tunnel."""
        if not self.tunnel_manager:
            messagebox.showerror("Error", "Not connected")
            return

        try:
            # Get tunnel details
            tunnel_type_str = self.tunnel_type_var.get()
            local_port = int(self.local_port_entry.get().strip())
            remote_host = self.remote_host_entry.get().strip()

            tunnel_type = TunnelType(tunnel_type_str)

            if tunnel_type in (TunnelType.LOCAL, TunnelType.REMOTE):
                remote_port = int(self.remote_port_entry.get().strip())
            else:
                remote_port = 0

            # Create tunnel
            tunnel = Tunnel(
                tunnel_type=tunnel_type,
                local_port=local_port,
                remote_host=remote_host,
                remote_port=remote_port,
            )

            # Start tunnel
            self.tunnel_manager.start_tunnel(tunnel)
            self.active_tunnels.append(tunnel)

            # Add to tree
            self.tunnels_tree.insert(
                "",
                tk.END,
                text=tunnel.name,
                values=(
                    tunnel.tunnel_type.value,
                    tunnel.local_port,
                    f"{tunnel.remote_host}:{tunnel.remote_port}",
                    tunnel.status.value,
                    "0s",
                ),
            )

            logger.info(f"Added tunnel: {tunnel.name}")
            self._update_tunnel_count()

        except Exception as e:
            logger.error(f"Failed to add tunnel: {e}")
            messagebox.showerror("Error", str(e))

    def _stop_selected_tunnel(self) -> None:
        """Stop selected tunnel."""
        messagebox.showinfo("Info", "Stop tunnel not yet implemented")

    def _remove_selected_tunnel(self) -> None:
        """Remove selected tunnel."""
        selected = self.tunnels_tree.selection()
        if selected:
            self.tunnels_tree.delete(selected[0])
            self._update_tunnel_count()

    def _show_tunnel_context_menu(self, event: object) -> None:
        """Show tunnel context menu."""
        if hasattr(event, "x") and hasattr(event, "y"):
            self.tunnel_context_menu.post(event.x_root, event.y_root)  # type: ignore

    def _update_tunnel_count(self) -> None:
        """Update tunnel count in status bar."""
        count = len(self.tunnels_tree.get_children())
        self.tunnel_count_label.config(text=f"{count} tunnel{'s' if count != 1 else ''}")

    def _new_profile(self) -> None:
        """Create new profile."""
        messagebox.showinfo("Info", "New profile dialog not yet implemented")

    def _open_profile(self) -> None:
        """Open profile."""
        messagebox.showinfo("Info", "Open profile dialog not yet implemented")

    def _save_profile(self) -> None:
        """Save profile."""
        messagebox.showinfo("Info", "Save profile dialog not yet implemented")

    def _export_ssh_command(self) -> None:
        """Export SSH command."""
        messagebox.showinfo("Info", "Export SSH command not yet implemented")

    def _export_batch(self) -> None:
        """Export batch script."""
        messagebox.showinfo("Info", "Export batch script not yet implemented")

    def _show_about(self) -> None:
        """Show about dialog."""
        messagebox.showinfo(
            "About SSH Tunnel Manager",
            "SSH Tunnel Manager v1.0\n\n"
            "Enterprise-grade SSH Port Forwarding GUI\n\n"
            "© 2025 SSH Tunnel Manager Team",
        )

    def _on_close(self) -> None:
        """Handle window close."""
        if self.config_service.get("confirm_on_exit", True):
            if messagebox.askyesno("Confirm Exit", "Are you sure you want to exit?"):
                self._cleanup()
                self.root.destroy()
        else:
            self._cleanup()
            self.root.destroy()

    def _cleanup(self) -> None:
        """Cleanup resources."""
        try:
            # Disconnect
            if self.ssh_manager:
                self.ssh_manager.disconnect()

            # Stop monitoring
            self.tunnel_monitor.stop_monitoring()

            # Save config
            self.config_service.save()

        except Exception as e:
            logger.error(f"Cleanup error: {e}")

    def run(self) -> None:
        """Run the application."""
        self.root.mainloop()
