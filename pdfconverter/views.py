from django.shortcuts import render, redirect
from django.http import HttpResponse
from .forms import UploadFileForm
from .models import UploadedFile
from reportlab.pdfgen import canvas
from PIL import Image
from pdf2docx import Converter
import pypandoc
import os

def home(request):
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            uploaded_file = form.save()
            file_path = uploaded_file.file.path
            file_name, file_extension = os.path.splitext(file_path)
            
            if file_extension.lower() in ['.doc', '.docx']:
                pdf_path = convert_word_to_pdf(file_path)
            elif file_extension.lower() in ['.pdf']:
                word_path = convert_pdf_to_word(file_path)
                return serve_file(word_path, 'application/vnd.openxmlformats-officedocument.wordprocessingml.document')
            else:
                pdf_path = convert_to_pdf(file_path)
            
            return serve_file(pdf_path, 'application/pdf')
    else:
        form = UploadFileForm()
    return render(request, 'pdfconverter/home.html', {'form': form})

def convert_to_pdf(file_path):
    file_name, file_extension = os.path.splitext(file_path)
    pdf_path = f"{file_name}.pdf"
    
    if file_extension.lower() in ['.jpg', '.jpeg', '.png']:
        image = Image.open(file_path)
        pdf_canvas = canvas.Canvas(pdf_path)
        pdf_canvas.drawImage(file_path, 0, 0, image.width, image.height)
        pdf_canvas.showPage()
        pdf_canvas.save()
    elif file_extension.lower() in ['.txt']:
        pdf_canvas = canvas.Canvas(pdf_path)
        with open(file_path, 'r', encoding='utf-8') as text_file:
            lines = text_file.readlines()
            for line in lines:
                pdf_canvas.drawString(100, 750, line.strip())
                pdf_canvas.showPage()
        pdf_canvas.save()
    # Add more file type conversions as needed
    
    return pdf_path

def convert_word_to_pdf(file_path):
    pdf_path = f"{os.path.splitext(file_path)[0]}.pdf"
    template_path = os.path.join(os.path.dirname(__file__), 'templates', 'custom.latex')
    pypandoc.convert_file(file_path, 'pdf', outputfile=pdf_path, extra_args=['--pdf-engine=xelatex', f'--template={template_path}'])
    return pdf_path

def convert_pdf_to_word(file_path):
    word_path = f"{os.path.splitext(file_path)[0]}.docx"
    cv = Converter(file_path)
    cv.convert(word_path, start=0, end=None)
    cv.close()
    return word_path

def serve_file(file_path, content_type):
    with open(file_path, 'rb') as file:
        response = HttpResponse(file.read(), content_type=content_type)
        response['Content-Disposition'] = f'attachment; filename="{os.path.basename(file_path)}"'
        return response