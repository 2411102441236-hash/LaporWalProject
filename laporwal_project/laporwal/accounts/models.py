from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    """
    Model pengguna kustom yang memperluas AbstractUser bawaan Django.
    Kita tambah field: nomor HP, foto profil, kota, dan status admin.
    """
    phone = models.CharField(max_length=20, blank=True, verbose_name="Nomor HP")
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True, verbose_name="Foto Profil")
    kota = models.CharField(max_length=100, default='Samarinda', verbose_name="Kota")
    is_admin_dinas = models.BooleanField(default=False, verbose_name="Admin Dinas")

    class Meta:
        verbose_name = "Pengguna"
        verbose_name_plural = "Pengguna"

    def get_initials(self):
        parts = self.get_full_name().split()
        if len(parts) >= 2:
            return parts[0][0].upper() + parts[1][0].upper()
        elif self.first_name:
            return self.first_name[:2].upper()
        return self.username[:2].upper()

    def laporan_count(self):
        return self.laporan_set.count()

    def __str__(self):
        return self.get_full_name() or self.username
