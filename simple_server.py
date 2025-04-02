import http.server
import socketserver
import json
import os
from urllib.parse import parse_qs
from datetime import datetime
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

# Load PoA types from JSON
with open('poa_types.json', 'r') as f:
    POA_TYPES = json.load(f)
    print("Loaded PoA types:", POA_TYPES)
    print("Available document types:", list(POA_TYPES.keys()))

class RequestHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            # Serve the HTML file with injected PoA types
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            
            with open('templates/index.html', 'r', encoding='utf-8') as f:
                html_content = f.read()
                
            # Replace the placeholder with actual PoA types
            poa_types_json = json.dumps(POA_TYPES)
            html_content = html_content.replace(
                '{{ poa_types|tojson|safe }}',
                poa_types_json
            )
            
            self.wfile.write(html_content.encode('utf-8'))
        else:
            # Handle other GET requests (like static files)
            super().do_GET()
            
    def do_POST(self):
        if self.path == '/submit':
            # Get the POST data
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            form_data = parse_qs(post_data.decode('utf-8'))
            
            # Process the form data
            processed_data = {}
            for key, value in form_data.items():
                processed_data[key] = value[0]
            
            # Generate PDF
            document_type = processed_data.get('documentType', '')
            if document_type in POA_TYPES:
                # Create PDF
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f'documents/{document_type.replace(" ", "_")}_{timestamp}.pdf'
                os.makedirs('documents', exist_ok=True)
                
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
                content.append(Paragraph("Government Office", title_style))
                content.append(Paragraph("Power of Attorney & Visa Services", header_style))
                content.append(Spacer(1, 20))
                
                # Add document type
                content.append(Paragraph(document_type, header_style))
                content.append(Spacer(1, 20))
                
                # Add form data
                for field in POA_TYPES[document_type]['fields']:
                    field_value = processed_data.get(field['name'], '')
                    content.append(Paragraph(f"<b>{field['label']}:</b> {field_value}", field_style))
                    content.append(Spacer(1, 8))
                
                # Add footer
                content.append(Spacer(1, 30))
                content.append(Paragraph(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal']))
                
                # Build PDF
                doc.build(content)
                
                # Send success response with filename
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({
                    'status': 'success',
                    'message': 'Document generated successfully',
                    'filename': filename
                }).encode())
            else:
                # Send error response
                self.send_response(400)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({
                    'status': 'error',
                    'message': 'Invalid document type'
                }).encode())
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b'Not found')

def run_server(port=8000):
    with socketserver.TCPServer(("", port), RequestHandler) as httpd:
        print(f"Server running on port {port}")
        httpd.serve_forever()

if __name__ == '__main__':
    run_server() 