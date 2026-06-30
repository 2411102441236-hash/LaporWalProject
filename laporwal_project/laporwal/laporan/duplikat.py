"""
Deteksi laporan ganda untuk LaporWal.

Sebuah laporan dianggap "serupa" dengan laporan lain yang masih aktif
(status menunggu/diproses) jika:
  - kategorinya sama, DAN
  - lokasinya berdekatan (jarak GPS <= RADIUS_METER), ATAU
  - deskripsinya cukup mirip (kemiripan kata >= MIRIP_MIN).

Semua perhitungan dilakukan lokal (tanpa internet), jadi aman untuk
dijalankan di PythonAnywhere gratis.
"""

import math
import re

from .models import Laporan

# Ambang batas — bisa disesuaikan
RADIUS_METER = 150      # dua titik dianggap "lokasi sama" jika <= 150 meter
MIRIP_MIN = 0.45        # kemiripan deskripsi minimal (0..1) untuk dianggap mirip


def _haversine(lat1, lon1, lat2, lon2):
    """Hitung jarak (meter) antara dua koordinat GPS."""
    R = 6371000  # radius bumi dalam meter
    p1 = math.radians(lat1)
    p2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlmb = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlmb / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


def _kemiripan_teks(a, b):
    """Kemiripan dua teks berdasarkan irisan kata (0..1)."""
    kata_a = set(re.findall(r'\w+', (a or '').lower()))
    kata_b = set(re.findall(r'\w+', (b or '').lower()))
    if not kata_a or not kata_b:
        return 0.0
    return len(kata_a & kata_b) / len(kata_a | kata_b)


def cari_laporan_serupa(kategori, latitude, longitude, deskripsi,
                        exclude_pk=None, batas=4):
    """
    Kembalikan daftar laporan aktif yang serupa dengan laporan baru.
    Daftar kosong berarti tidak ada yang serupa.
    """
    qs = Laporan.objects.filter(status__in=['pending', 'diproses'])
    if kategori:
        qs = qs.filter(kategori=kategori)
    if exclude_pk:
        qs = qs.exclude(pk=exclude_pk)

    # Batasi jumlah yang diperiksa agar tetap ringan
    kandidat = qs.order_by('-dibuat_pada')[:300]

    hasil = []
    for lap in kandidat:
        dekat = False
        if (latitude is not None and longitude is not None
                and lap.latitude is not None and lap.longitude is not None):
            try:
                jarak = _haversine(
                    float(latitude), float(longitude),
                    float(lap.latitude), float(lap.longitude)
                )
                if jarak <= RADIUS_METER:
                    dekat = True
            except (TypeError, ValueError):
                pass

        mirip = _kemiripan_teks(deskripsi, lap.deskripsi) >= MIRIP_MIN

        if dekat or mirip:
            hasil.append(lap)
            if len(hasil) >= batas:
                break

    return hasil
