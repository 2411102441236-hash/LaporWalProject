from django.db import models
from django.conf import settings
import uuid
from datetime import date


def report_upload_path(instance, filename):
    """Simpan foto laporan di folder terorganisir berdasarkan tahun/bulan"""
    return f'laporan/{date.today().year}/{date.today().month}/{filename}'


class Laporan(models.Model):
    """
    Model utama untuk laporan infrastruktur dari warga.
    Setiap laporan punya: pelapor, foto, deskripsi, lokasi, kategori, dan status.
    """
    KATEGORI_CHOICES = [
        ('jalan', 'Jalan Rusak'),
        ('sampah', 'Tumpukan Sampah'),
        ('lampu', 'Lampu Jalan Mati'),
        ('lainnya', 'Lainnya'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Menunggu'),
        ('diproses', 'Diproses'),
        ('selesai', 'Selesai'),
        ('ditolak', 'Ditolak'),
    ]

    PRIORITAS_CHOICES = [
        ('rendah', 'Rendah'),
        ('sedang', 'Sedang'),
        ('tinggi', 'Tinggi'),
        ('darurat', 'Darurat'),
    ]

    # ID unik berbasis tahun, contoh: RPT-2026-0001
    nomor_laporan = models.CharField(max_length=20, unique=True, blank=True)

    # Relasi ke pengguna (ForeignKey = banyak laporan bisa dari 1 user)
    pelapor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='laporan_set',
        verbose_name="Pelapor"
    )

    foto = models.ImageField(upload_to=report_upload_path, verbose_name="Foto Laporan")
    deskripsi = models.TextField(verbose_name="Deskripsi Laporan")
    alamat = models.CharField(max_length=255, verbose_name="Alamat / Lokasi")
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

    kategori = models.CharField(max_length=20, choices=KATEGORI_CHOICES, default='lainnya')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    prioritas = models.CharField(max_length=20, choices=PRIORITAS_CHOICES, default='sedang')

    # AI classification fields
    ai_kategori = models.CharField(max_length=20, blank=True, null=True, verbose_name="Kategori AI")
    ai_confidence = models.IntegerField(default=0, verbose_name="Confidence AI (%)")

    catatan_admin = models.TextField(blank=True, verbose_name="Catatan Admin")

    # Timestamps
    dibuat_pada = models.DateTimeField(auto_now_add=True, verbose_name="Tanggal Lapor")
    diperbarui_pada = models.DateTimeField(auto_now=True, verbose_name="Terakhir Diperbarui")
    diselesaikan_pada = models.DateTimeField(null=True, blank=True, verbose_name="Tanggal Selesai")

    class Meta:
        verbose_name = "Laporan"
        verbose_name_plural = "Laporan"
        ordering = ['-dibuat_pada']

    def save(self, *args, **kwargs):
        """Auto-generate nomor laporan saat pertama kali disimpan"""
        if not self.nomor_laporan:
            year = date.today().year
            count = Laporan.objects.filter(dibuat_pada__year=year).count() + 1
            self.nomor_laporan = f"RPT-{year}-{count:04d}"
        super().save(*args, **kwargs)

    def get_kategori_emoji(self):
        emoji_map = {'jalan': '🛣️', 'sampah': '🗑️', 'lampu': '💡', 'lainnya': '📋'}
        return emoji_map.get(self.kategori, '📋')

    def get_kategori_icon(self):
        """Ikon Bootstrap Icons untuk tiap kategori (desain MAHAKAM)."""
        icon_map = {
            'jalan': 'bi-cone-striped',
            'sampah': 'bi-trash',
            'lampu': 'bi-lightbulb',
            'lainnya': 'bi-three-dots',
        }
        return icon_map.get(self.kategori, 'bi-three-dots')

    def get_kategori_warna(self):
        """Warna hex tiap kategori untuk thumbnail/ikon."""
        warna_map = {
            'jalan': '#2563EB', 'sampah': '#16A34A',
            'lampu': '#D97706', 'lainnya': '#64748B',
        }
        return warna_map.get(self.kategori, '#64748B')

    def get_status_color(self):
        color_map = {
            'pending': 'warning',
            'diproses': 'info',
            'selesai': 'success',
            'ditolak': 'danger',
        }
        return color_map.get(self.status, 'secondary')

    def get_prioritas_color(self):
        color_map = {
            'rendah': 'success',
            'sedang': 'warning',
            'tinggi': 'danger',
            'darurat': 'dark',
        }
        return color_map.get(self.prioritas, 'secondary')

    def __str__(self):
        return f"{self.nomor_laporan} - {self.deskripsi[:50]}"


class AktivitasLaporan(models.Model):
    """
    Log semua perubahan yang terjadi pada laporan.
    Ini yang jadi timeline di halaman detail laporan.
    """
    laporan = models.ForeignKey(Laporan, on_delete=models.CASCADE, related_name='aktivitas')
    deskripsi = models.CharField(max_length=255)
    oleh = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True
    )
    warna = models.CharField(max_length=20, default='primary')
    dibuat_pada = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['dibuat_pada']

    def __str__(self):
        return f"{self.laporan.nomor_laporan}: {self.deskripsi}"


class Notifikasi(models.Model):
    """Notifikasi untuk pengguna saat status laporan berubah"""
    pengguna = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifikasi')
    laporan = models.ForeignKey(Laporan, on_delete=models.CASCADE, null=True, blank=True)
    judul = models.CharField(max_length=100)
    pesan = models.CharField(max_length=255)
    sudah_dibaca = models.BooleanField(default=False)
    dibuat_pada = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-dibuat_pada']

    def __str__(self):
        return f"[{self.pengguna}] {self.judul}"
