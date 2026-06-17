from django.contrib import admin
from .models import Laporan, AktivitasLaporan, Notifikasi


@admin.register(Laporan)
class LaporanAdmin(admin.ModelAdmin):
    list_display = ('nomor_laporan', 'pelapor', 'kategori', 'status', 'prioritas', 'dibuat_pada')
    list_filter = ('status', 'kategori', 'prioritas')
    search_fields = ('nomor_laporan', 'deskripsi', 'alamat', 'pelapor__first_name')
    readonly_fields = ('nomor_laporan', 'dibuat_pada', 'diperbarui_pada')


@admin.register(AktivitasLaporan)
class AktivitasAdmin(admin.ModelAdmin):
    list_display = ('laporan', 'deskripsi', 'oleh', 'dibuat_pada')


@admin.register(Notifikasi)
class NotifikasiAdmin(admin.ModelAdmin):
    list_display = ('pengguna', 'judul', 'sudah_dibaca', 'dibuat_pada')
    list_filter = ('sudah_dibaca',)
