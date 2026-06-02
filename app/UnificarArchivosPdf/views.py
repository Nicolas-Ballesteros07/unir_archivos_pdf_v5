import os
import tempfile
from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_protect
from django.urls import reverse
from .utils import merge_pdfs, process_zip_to_pdf, read_excel_payments, sanitize_filename


@csrf_protect
def merge_zip_view(request):
    session_key = request.session.session_key
    if not session_key:
        request.session.save()
        session_key = request.session.session_key

    user_temp_dir = os.path.join(tempfile.gettempdir(), 'pdf_merger', session_key)
    os.makedirs(user_temp_dir, exist_ok=True)

    if request.method == 'POST':
        # Petición AJAX: poner nombre al PDF unificado
        if request.headers.get('x-requested-with') == 'XMLHttpRequest' and 'nombre' in request.POST:
            merged_path = request.session.get('zip_merged_pdf_path')
            if not merged_path or not os.path.exists(merged_path):
                return JsonResponse({'error': 'El archivo temporal ya no está disponible.'}, status=400)

            nombre = sanitize_filename(request.POST['nombre'])
            if not nombre.lower().endswith('.pdf'):
                nombre += '.pdf'

            final_path = os.path.join(user_temp_dir, nombre)
            os.rename(merged_path, final_path)
            request.session['zip_final_download'] = final_path
            download_url = reverse('download_zip_final')
            return JsonResponse({'download_url': download_url})

        # --- Subida de archivos (recolección corregida) ---
        # Recoger todos los archivos cuyos nombres empiecen con "pdf_"
        pdf_files = []
        for key in sorted(request.FILES.keys()):
            if key.startswith('pdf_'):
                try:
                    idx = int(key.split('_')[1])
                except (IndexError, ValueError):
                    continue
                pdf_files.append((idx, request.FILES[key]))
        # Ordenar por índice numérico
        pdf_files.sort(key=lambda x: x[0])
        pdf_files = [f for _, f in pdf_files]  # lista ordenada de archivos

        zip_file = request.FILES.get('zip_file')

        if not pdf_files and not zip_file:
            return render(request, 'merge_zip.html', {
                'error': 'Debe subir al menos un PDF o un ZIP.'
            })

        # Guardar PDFs sueltos en orden
        pdf_paths = []
        for idx, pdf in enumerate(pdf_files):
            path = os.path.join(user_temp_dir, f'pdf_{idx}.pdf')
            with open(path, 'wb+') as f:
                for chunk in pdf.chunks():
                    f.write(chunk)
            pdf_paths.append(path)

        # Procesar ZIP si existe
        zip_pdf_path = None
        if zip_file:
            zip_path = os.path.join(user_temp_dir, 'uploaded.zip')
            with open(zip_path, 'wb+') as f:
                for chunk in zip_file.chunks():
                    f.write(chunk)
            zip_pdf_path = os.path.join(user_temp_dir, 'zip_content.pdf')
            process_zip_to_pdf(zip_path, zip_pdf_path)

        # Unificar (PDFs individuales primero, luego ZIP)
        merged_pdf_path = os.path.join(user_temp_dir, 'merged_final.pdf')
        if pdf_paths and zip_pdf_path:
            if len(pdf_paths) == 1:
                sueltos_pdf = pdf_paths[0]
            else:
                sueltos_pdf = os.path.join(user_temp_dir, 'pdfs_sueltos.pdf')
                merge_pdfs(pdf_paths, sueltos_pdf)
            merge_pdfs([sueltos_pdf, zip_pdf_path], merged_pdf_path)
        elif pdf_paths:
            if len(pdf_paths) == 1:
                merged_pdf_path = pdf_paths[0]
            else:
                merge_pdfs(pdf_paths, merged_pdf_path)
        else:
            merged_pdf_path = zip_pdf_path

        request.session['zip_merged_pdf_path'] = merged_pdf_path
        default_name = "documento_unificado.pdf"
        return render(request, 'merge_zip.html', {
            'show_modal': True,
            'default_name': default_name
        })

    # GET
    return render(request, 'merge_zip.html', {'show_modal': False})


def download_zip_final(request):
    final_path = request.session.get('zip_final_download')
    if not final_path or not os.path.exists(final_path):
        return HttpResponse("Archivo no encontrado o sesión expirada.", status=404)

    with open(final_path, 'rb') as f:
        response = HttpResponse(f.read(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{os.path.basename(final_path)}"'
    os.remove(final_path)
    del request.session['zip_final_download']
    return response


@csrf_protect
def merge_excel_view(request):
    session_key = request.session.session_key
    if not session_key:
        request.session.save()
        session_key = request.session.session_key

    user_temp_dir = os.path.join(tempfile.gettempdir(), 'pdf_merger', session_key)
    os.makedirs(user_temp_dir, exist_ok=True)

    if request.method == 'POST':
        # Recolección corregida (mismo método que en ZIP)
        pdf_files = []
        for key in sorted(request.FILES.keys()):
            if key.startswith('pdf_'):
                try:
                    idx = int(key.split('_')[1])
                except (IndexError, ValueError):
                    continue
                pdf_files.append((idx, request.FILES[key]))
        pdf_files.sort(key=lambda x: x[0])
        pdf_files = [f for _, f in pdf_files]

        excel_file = request.FILES.get('excel')

        if len(pdf_files) < 1:
            return render(request, 'merge_excel.html', {
                'error': 'Debe subir al menos un archivo PDF.'
            })
        if not excel_file:
            return render(request, 'merge_excel.html', {
                'error': 'Debe subir el archivo Excel.'
            })

        pdf_names = []
        for idx, pdf in enumerate(pdf_files):
            safe_name = f"pdf_{idx}.pdf"
            path = os.path.join(user_temp_dir, safe_name)
            with open(path, 'wb+') as f:
                for chunk in pdf.chunks():
                    f.write(chunk)
            pdf_names.append(safe_name)

        ext = os.path.splitext(excel_file.name)[1]
        excel_path = os.path.join(user_temp_dir, f'datos{ext}')
        with open(excel_path, 'wb+') as f:
            for chunk in excel_file.chunks():
                f.write(chunk)

        try:
            registros = read_excel_payments(excel_path)
        except Exception as e:
            return render(request, 'merge_excel.html', {
                'error': f'Error al leer el Excel: {str(e)}'
            })

        request.session['merge_data'] = {
            'pdf_names': pdf_names,
            'registros': registros
        }
        return render(request, 'merge_excel.html', {
            'show_records': True,
            'registros': registros
        })

    return render(request, 'merge_excel.html', {'show_records': False})


def generate_named_pdf(request, record_index):
    merge_data = request.session.get('merge_data')
    if not merge_data:
        return HttpResponse("Sesión expirada o no hay datos. Vuelva a subir los archivos.", status=400)

    pdf_names = merge_data['pdf_names']
    registros = merge_data['registros']

    try:
        record_index = int(record_index)
        if record_index < 0 or record_index >= len(registros):
            raise IndexError
    except (ValueError, IndexError):
        return HttpResponse("Índice de registro inválido.", status=400)

    selected = registros[record_index]
    proveedor = selected['proveedor']
    factura = selected['factura']

    safe_proveedor = sanitize_filename(proveedor)
    safe_factura = sanitize_filename(factura)
    filename = f"Pago_{safe_proveedor}_{safe_factura}_Cuenta_cte.pdf"

    session_key = request.session.session_key
    user_temp_dir = os.path.join(tempfile.gettempdir(), 'pdf_merger', session_key)
    pdf_paths = [os.path.join(user_temp_dir, name) for name in pdf_names]

    for path in pdf_paths:
        if not os.path.exists(path):
            return HttpResponse("Los archivos PDF temporales han sido eliminados. Vuelva a subirlos.", status=400)

    temp_output = os.path.join(user_temp_dir, 'output_named.pdf')
    merge_pdfs(pdf_paths, temp_output)

    with open(temp_output, 'rb') as f:
        response = HttpResponse(f.read(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        response['Access-Control-Expose-Headers'] = 'Content-Disposition'
        return response