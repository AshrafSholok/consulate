import tkinter as tk
from tkinter import ttk, messagebox
import json
from PIL import Image, ImageTk
import qrcode 
import cv2
import numpy as np
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as RLImage
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
import win32print
import win32api
from datetime import datetime
import os
import io
import socket
import subprocess
import sys

class PoAApplication:
    def __init__(self, root):
        self.root = root
        self.root.title("Government Office - PoA & Visa Services")
        self.root.geometry("800x600")
        
        # Load PoA types from JSON
        with open('poa_types.json', 'r') as f:
            self.poa_types = json.load(f)
        
        self.current_frame = None
        self.server_process = None
        self.setup_main_menu()
        
    def get_local_ip(self):
        try:
            # Get local IP address
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "localhost"
        
    def start_server(self):
        # Start the simple server in a separate process
        python_path = sys.executable
        server_script = os.path.join(os.path.dirname(__file__), 'simple_server.py')
        self.server_process = subprocess.Popen([python_path, server_script])
        
    def stop_server(self):
        if self.server_process:
            self.server_process.terminate()
            self.server_process = None
        
    def setup_main_menu(self):
        # Clear any existing widgets
        if self.current_frame:
            self.current_frame.destroy()
        
        self.current_frame = ttk.Frame(self.root, padding="20")
        self.current_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Start Server button
        ttk.Button(self.current_frame, text="Start Server", 
                  command=self.start_server).grid(row=0, column=0, pady=10)
        
        # Generate QR Code button
        ttk.Button(self.current_frame, text="Generate QR Code", 
                  command=self.generate_qr_code).grid(row=1, column=0, pady=10)
        
        # Stop Server button
        ttk.Button(self.current_frame, text="Stop Server", 
                  command=self.stop_server).grid(row=2, column=0, pady=10)
        
        # PoA type selection
        ttk.Label(self.current_frame, text="Select Document Type:").grid(row=3, column=0, pady=10)
        self.poa_var = tk.StringVar()
        poa_combo = ttk.Combobox(self.current_frame, textvariable=self.poa_var)
        poa_combo['values'] = list(self.poa_types.keys())
        poa_combo.grid(row=4, column=0, pady=5)
        poa_combo.bind('<<ComboboxSelected>>', self.show_form)
        
    def generate_qr_code(self):
        if not self.server_process:
            messagebox.showerror("Error", "Please start the server first!")
            return
            
        # Get local IP address
        ip = self.get_local_ip()
        # Create URL for the web form
        url = f"http://{ip}:8000"
        
        # Create QR code instance
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        
        # Add URL to QR code
        qr.add_data(url)
        qr.make(fit=True)
        
        # Create QR code image
        qr_image = qr.make_image(fill_color="black", back_color="white")
        
        # Save QR code
        qr_filename = f"qr_code_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        qr_image.save(qr_filename)
        
        # Show QR code in a new window
        qr_window = tk.Toplevel(self.root)
        qr_window.title("Generated QR Code")
        
        # Add instructions
        ttk.Label(qr_window, text="Scan this QR code with your mobile device\nto access the form:", 
                 justify='center').pack(pady=5)
        
        # Convert PIL image to PhotoImage
        photo = ImageTk.PhotoImage(qr_image)
        label = ttk.Label(qr_window, image=photo)
        label.image = photo  # Keep a reference
        label.pack(padx=10, pady=10)
        
        # Add close button
        ttk.Button(qr_window, text="Close", command=qr_window.destroy).pack(pady=5)
        
        # Show the URL
        ttk.Label(qr_window, text=f"URL: {url}", wraplength=300).pack(pady=5)
        
    def show_form(self, event=None):
        selected_type = self.poa_var.get()
        if not selected_type:
            return
            
        # Clear current frame
        self.current_frame.destroy()
        self.current_frame = ttk.Frame(self.root, padding="20")
        self.current_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Create form fields
        self.form_data = {}
        fields = self.poa_types[selected_type]['fields']
        
        for i, field in enumerate(fields):
            ttk.Label(self.current_frame, text=field['label']).grid(row=i, column=0, pady=5)
            if field['type'] == 'text':
                entry = ttk.Entry(self.current_frame, width=40)
                entry.grid(row=i, column=1, pady=5)
                self.form_data[field['name']] = entry
            elif field['type'] == 'number':
                entry = ttk.Entry(self.current_frame, width=40)
                entry.grid(row=i, column=1, pady=5)
                self.form_data[field['name']] = entry
            elif field['type'] == 'date':
                entry = ttk.Entry(self.current_frame, width=40)
                entry.grid(row=i, column=1, pady=5)
                self.form_data[field['name']] = entry
        
        # Submit button
        ttk.Button(self.current_frame, text="Generate Document", 
                  command=self.generate_document).grid(row=len(fields), column=0, columnspan=2, pady=20)
        
        # Back button
        ttk.Button(self.current_frame, text="Back to Main Menu", 
                  command=self.setup_main_menu).grid(row=len(fields)+1, column=0, columnspan=2, pady=5)
        
    def generate_document(self):
        # Collect form data
        data = {name: entry.get() for name, entry in self.form_data.items()}
        
        # Create PDF
        filename = f"document_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        doc = SimpleDocTemplate(filename, pagesize=letter)
        styles = getSampleStyleSheet()
        
        # Create content
        content = []
        
        # Custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            alignment=1  # Center alignment
        )
        
        header_style = ParagraphStyle(
            'CustomHeader',
            parent=styles['Heading2'],
            fontSize=16,
            spaceAfter=20,
            textColor=colors.HexColor('#2c3e50')
        )
        
        field_style = ParagraphStyle(
            'CustomField',
            parent=styles['Normal'],
            fontSize=12,
            spaceAfter=10,
            textColor=colors.HexColor('#34495e')
        )
        
        # Add header with logo (you can add your logo file)
        content.append(Paragraph("Government Office", title_style))
        content.append(Paragraph("Power of Attorney & Visa Services", header_style))
        content.append(Spacer(1, 20))
        
        # Add document type
        content.append(Paragraph(self.poa_var.get(), header_style))
        content.append(Spacer(1, 20))
        
        # Add form data in a structured format
        for field in self.poa_types[self.poa_var.get()]['fields']:
            content.append(Paragraph(f"<b>{field['label']}:</b> {data[field['name']]}", field_style))
            content.append(Spacer(1, 8))
        
        # Add footer
        content.append(Spacer(1, 30))
        content.append(Paragraph(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal']))
        
        # Build PDF
        doc.build(content)
        
        # Print the document
        try:
            win32api.ShellExecute(0, "print", filename, None, ".", 0)
            messagebox.showinfo("Success", "Document generated and sent to printer!")
        except Exception as e:
            messagebox.showerror("Error", f"Error printing document: {str(e)}")
        
        # Clean up
        self.setup_main_menu()

    def __del__(self):
        # Clean up server process when application closes
        self.stop_server()

if __name__ == "__main__":
    root = tk.Tk()
    app = PoAApplication(root)
    root.mainloop() 