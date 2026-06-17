from django import forms
from .models import Laporan


class LaporanForm(forms.ModelForm):
    """Form untuk warga membuat laporan baru"""
    class Meta:
        model = Laporan
        fields = ('foto', 'deskripsi', 'alamat', 'latitude', 'longitude', 'kategori')
        widgets = {
            'deskripsi': forms.Textarea(attrs={
                'rows': 3,
                'class': 'form-control',
                'placeholder': 'Jelaskan masalah yang Anda temukan...'
            }),
            'alamat': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Contoh: Jl. Pattimura No.5, RT 03 Samarinda'
            }),
            'kategori': forms.Select(attrs={'class': 'form-select'}),
            'latitude': forms.HiddenInput(),
            'longitude': forms.HiddenInput(),
        }
        labels = {
            'foto': 'Foto Kerusakan',
            'deskripsi': 'Deskripsi Masalah',
            'alamat': 'Lokasi / Alamat',
            'kategori': 'Kategori',
        }

    def clean_foto(self):
        """Validasi: batasi ukuran maksimal 10MB dan pastikan file berupa gambar."""
        foto = self.cleaned_data.get('foto')
        if foto:
            max_size = 10 * 1024 * 1024  # 10MB
            if foto.size > max_size:
                raise forms.ValidationError('Ukuran foto maksimal 10MB.')
            valid_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/webp']
            content_type = getattr(foto, 'content_type', None)
            if content_type and content_type not in valid_types:
                raise forms.ValidationError('File harus berupa gambar (JPG, PNG, atau WEBP).')
        return foto


class UpdateStatusForm(forms.ModelForm):
    """Form untuk admin mengupdate status laporan"""
    class Meta:
        model = Laporan
        fields = ('status', 'prioritas', 'catatan_admin')
        widgets = {
            'status': forms.Select(attrs={'class': 'form-select'}),
            'prioritas': forms.Select(attrs={'class': 'form-select'}),
            'catatan_admin': forms.Textarea(attrs={
                'rows': 3,
                'class': 'form-control',
                'placeholder': 'Tambahkan catatan untuk pelapor (opsional)...'
            }),
        }
