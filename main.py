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

class VisaApplication:
    def __init__(self, root):
        self.root = root
        self.root.title("Visa Application System")
        self.root.geometry("800x600")
        
        # Load visa application fields from JSON
        with open('poa_types.json', 'r') as f:
            self.visa_fields = json.load(f)["Visa Application"]["fields"]
        
        self.current_frame = None
        self.setup_main_menu()
        
    def setup_main_menu(self):
        # Clear any existing widgets
        if self.current_frame:
            self.current_frame.destroy()
        
        self.current_frame = ttk.Frame(self.root, padding="20")
        self.current_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Title
        title_label = ttk.Label(self.current_frame, text="Visa Application System", 
                              font=('Helvetica', 16, 'bold'))
        title_label.grid(row=0, column=0, columnspan=2, pady=20)
        
        # Generate QR Code button
        ttk.Button(self.current_frame, text="Generate QR Code", 
                  command=self.generate_qr_code).grid(row=1, column=0, columnspan=2, pady=10)
        
        # Create Visa Application button
        ttk.Button(self.current_frame, text="Create Visa Application", 
                  command=self.show_form).grid(row=2, column=0, columnspan=2, pady=10)
        
    def generate_qr_code(self):
        # Use the GitHub Pages URL
        url = "https://ashrafsholok.github.io/consulate/"
        
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
        
    def show_form(self):
        # Clear current frame
        self.current_frame.destroy()
        self.current_frame = ttk.Frame(self.root, padding="20")
        self.current_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Title
        title_label = ttk.Label(self.current_frame, text="Visa Application Form", 
                              font=('Helvetica', 16, 'bold'))
        title_label.grid(row=0, column=0, columnspan=2, pady=20)
        
        # Create form fields
        self.form_data = {}
        for i, field in enumerate(self.visa_fields):
            ttk.Label(self.current_frame, text=field['label']).grid(row=i+1, column=0, pady=5, padx=5)
            if field['type'] == 'text':
                entry = ttk.Entry(self.current_frame, width=40)
                entry.grid(row=i+1, column=1, pady=5, padx=5)
                self.form_data[field['name']] = entry
            elif field['type'] == 'number':
                entry = ttk.Entry(self.current_frame, width=40)
                entry.grid(row=i+1, column=1, pady=5, padx=5)
                self.form_data[field['name']] = entry
            elif field['type'] == 'date':
                entry = ttk.Entry(self.current_frame, width=40)
                entry.grid(row=i+1, column=1, pady=5, padx=5)
                self.form_data[field['name']] = entry
        
        # Submit button
        ttk.Button(self.current_frame, text="Generate Document", 
                  command=self.generate_document).grid(row=len(self.visa_fields)+1, 
                                                     column=0, columnspan=2, pady=20)
        
        # Back button
        ttk.Button(self.current_frame, text="Back to Main Menu", 
                  command=self.setup_main_menu).grid(row=len(self.visa_fields)+2, 
                                                   column=0, columnspan=2, pady=5)
        
    def generate_document(self):
        # Collect form data
        data = {name: entry.get() for name, entry in self.form_data.items()}
        
        # Create PDF
        filename = f"visa_application_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
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
        
        # Add header
        content.append(Paragraph("Visa Application Form", title_style))
        content.append(Spacer(1, 20))
        
        # Add form data in a structured format
        for field in self.visa_fields:
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
            messagebox.showinfo("Success", "Visa application form generated and sent to printer!")
        except Exception as e:
            messagebox.showerror("Error", f"Error printing document: {str(e)}")
        
        # Clean up
        self.setup_main_menu()

if __name__ == "__main__":
    root = tk.Tk()
    app = VisaApplication(root)
    root.mainloop() 
#  khsgdkad
