# LaporWal — Aplikasi Pengaduan Infrastruktur Kota Samarinda

## Cara Menjalankan

### 1. Install dependencies
```bash
pip install django pillow
```

### 2. Masuk ke folder project
```bash
cd laporwal
```

### 3. Jalankan database migration
```bash
python manage.py migrate
```

### 4. Buat akun admin
```bash
python manage.py createsuperuser
```

### 5. Jalankan server
```bash
python manage.py runserver
```

Akses di: http://127.0.0.1:8000

---

## Akun Demo (sudah dibuat otomatis)
| Role | Username | Password |
|------|----------|----------|
| Admin Dinas | admin | admin123 |
| Warga 1 | budi | budi123 |
| Warga 2 | sari | sari123 |

---

## Struktur Project
```
laporwal/
├── manage.py              ← Perintah Django
├── laporwal/
│   ├── settings.py        ← Konfigurasi utama
│   └── urls.py            ← URL routing utama
├── accounts/
│   ├── models.py          ← Model CustomUser
│   ├── views.py           ← Login, Register, Profil
│   ├── forms.py           ← Form autentikasi
│   └── urls.py            ← URL auth
├── laporan/
│   ├── models.py          ← Model Laporan, Aktivitas, Notifikasi
│   ├── views.py           ← Semua logic halaman
│   ├── forms.py           ← Form laporan
│   └── urls.py            ← URL semua halaman
├── templates/             ← HTML templates
│   ├── base.html          ← Layout utama (navbar, footer)
│   ├── laporan/           ← Template halaman user & admin
│   └── accounts/          ← Template login, register, profil
├── static/                ← CSS, JS, gambar statis
└── media/                 ← Upload foto dari user
```

---

## URL Halaman
| URL | Halaman |
|-----|---------|
| / | Beranda publik |
| /auth/login/ | Login |
| /auth/register/ | Daftar akun |
| /auth/profil/ | Profil user |
| /buat-laporan/ | Buat laporan baru |
| /dashboard/ | Dashboard user |
| /laporan/<id>/ | Detail laporan |
| /riwayat/ | Riwayat laporan |
| /notifikasi/ | Notifikasi |
| /admin-panel/ | Dashboard admin |
| /admin-panel/laporan/ | Kelola semua laporan |
| /admin-panel/laporan/<id>/ | Detail + update laporan |
| /admin-panel/pengguna/ | Kelola pengguna |
| /django-admin/ | Django admin bawaan |
