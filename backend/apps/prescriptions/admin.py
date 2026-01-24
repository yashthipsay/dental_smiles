from django.contrib import admin
from django.urls import path, reverse
from unfold.admin import ModelAdmin
from django.utils.html import format_html
from .models import Medicine, Prescription, PrescriptionItem
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from weasyprint import HTML 
from django.templatetags.static import static
from django.conf import settings
from pathlib import Path

@admin.register(Medicine)
class MedicineAdmin(ModelAdmin):
    list_display = ['get_medicine_name']
    search_fields = ['name']
    ordering = ['name']

    def get_medicine_name(self, obj):
        return obj.name
    get_medicine_name.short_description = 'Medicine Name'

class PrescriptionItemInline(admin.TabularInline):
    model = PrescriptionItem
    extra = 1
    min_num = 1
    validate_min = True
    autocomplete_fields = ['medicine']

    

@admin.register(Prescription)
class PrescriptionAdmin(ModelAdmin):
    list_display = ['get_user_full_name', 'doctor_name', 'get_items_count', 'issued_at', 'actions_column']
    list_filter = ['issued_at', 'doctor_name']
    search_fields = ['user__phone_number', 'user__first_name', 'user__last_name', 'doctor_name', 'notes']
    readonly_fields = ['issued_at']
    ordering = ['-issued_at']
    inlines = [PrescriptionItemInline]
    autocomplete_fields = ['user', 'appointment', 'treatment_plan']

    @admin.display(description="User")
    def get_user_full_name(self, obj):
        if obj.user:
            return f"{obj.user.first_name} {obj.user.last_name}".strip()
        return 'N/A'
    get_user_full_name.short_description = 'User'

    def get_items_count(self, obj):
        return obj.items.count()
    get_items_count.short_description = 'Medicines'

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                '<int:pk>/download',
                self.admin_site.admin_view(self.download_prescription_pdf),
                name = 'prescription-download',
            ),
            path(
                '<int:pk>/preview',
                self.admin_site.admin_view(self.preview_prescription),
                name='prescription-preview',
            ),
            path(
                '<int:pk>/prescription_print',
                self.admin_site.admin_view(self.print_prescription),
                name='prescription-print',
            )
        ]
        return custom_urls + urls
    

    def download_prescription_pdf(self, request, pk):
        prescription = self.get_object(request, pk)

        # Get the static file path instead of URL
        image_path = Path(settings.STATIC_ROOT) / "prescriptions" / "template.png"

        background_image_url = f"file://{image_path}" if image_path.exists() else ""

        html = render_to_string(
            "prescriptions/prescription_pdf.html",
            {
                "prescription": prescription,
                "background_image": background_image_url
            }
        )

        pdf = HTML(string=html).write_pdf()

        response = HttpResponse(content_type='application/pdf')
        response["Content-Disposition"] = (
            f'attachment; filename="prescription_{pk}.pdf"'
        )
        response.write(pdf)
        return response
    
    def preview_prescription(self, request, pk):
        prescription = get_object_or_404(Prescription, pk=pk)

        context = {
            "prescription": prescription,
            "items": prescription.items.all(),
            "background_image": static("prescriptions/template.png"),
            "print_mode": False,
        }

        html = render_to_string("prescriptions/prescription_pdf.html", context)
        return HttpResponse(html)
    
    def print_prescription(self, request, pk):
        prescription = get_object_or_404(Prescription, pk=pk)

        context = {
            "prescription": prescription,
            "items": prescription.items.all(),
            "background_image": static("prescriptions/template.png"),
            "print_mode": True,
        }

        html = render_to_string("prescriptions/prescription_pdf.html", context)

        # Inject print script at the end of the body
        print_script = """
        <script>
            window.onload = function() {
                window.print();
            }
        </script>
        """

        # Insert before closing </body> tag, or append if no body tag
        if '</body>' in html:
            html = html.replace('</body>', print_script + '</body>')
        else:
            html += print_script
        
        return HttpResponse(html)
    
    def actions_column(self, obj):
        return format_html(
            '<a class="button" href="{}">Preview</a> '
            '<a class="button" href="{}">Print</a> '
            '<a class="button" href="{}">Download PDF</a>',
            reverse("admin:prescription-preview", args=[obj.pk]),
            reverse("admin:prescription-print", args=[obj.pk]),
            reverse("admin:prescription-download", args=[obj.pk]),
        )
    actions_column.short_description = "Actions"


    def get_changeform_initial_data(self, request):
        """Pre-fill user, appointment, and treatment_plan from query parameters"""
        initial = super().get_changeform_initial_data(request)
        user_id = request.GET.get('user')
        appointment_id = request.GET.get('appointment')
        treatment_plan_id = request.GET.get('treatment_plan')
        
        if user_id:
            initial['user'] = user_id
        if appointment_id:
            initial['appointment'] = appointment_id
        if treatment_plan_id:
            initial['treatment_plan'] = treatment_plan_id
        
        return initial