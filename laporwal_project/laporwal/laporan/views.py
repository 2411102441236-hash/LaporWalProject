from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.utils import timezone
from .models import Laporan, AktivitasLaporan, Notifikasi
from .forms import LaporanForm, UpdateStatusForm
from .deepseek_ai import analisis_laporan_dengan_ai
from accounts.models import CustomUser


# ==================== HALAMAN PUBLIK ====================

def beranda(request):
    """Halaman utama - tampilkan statistik dan laporan terbaru"""
    stats = {
        'total': Laporan.objects.count(),
        'diproses': Laporan.objects.filter(status='diproses').count(),
        'selesai': Laporan.objects.filter(status='selesai').count(),
        'pending': Laporan.objects.filter(status='pending').count(),
    }
    if stats['total'] > 0:
        stats['persen_selesai'] = round(stats['selesai'] / stats['total'] * 100)
    else:
        stats['persen_selesai'] = 0
    laporan_terbaru = Laporan.objects.select_related('pelapor').order_by('-dibuat_pada')[:6]
    return render(request, 'laporan/beranda.html', {
        'stats': stats,
        'laporan_terbaru': laporan_terbaru,
    })


# ==================== HALAMAN USER (LOGIN REQUIRED) ====================

@login_required
def buat_laporan(request):
    """Halaman form membuat laporan baru + analisis AI DeepSeek"""
    if request.method == 'POST':
        form = LaporanForm(request.POST, request.FILES)

        if form.is_valid():
            laporan = form.save(commit=False)
            laporan.pelapor = request.user

            # Simpan kategori yang dipilih user dari form
            kategori_manual = laporan.kategori

            # Analisis AI berdasarkan deskripsi dan alamat
            hasil_ai = analisis_laporan_dengan_ai(
                deskripsi=laporan.deskripsi,
                alamat=laporan.alamat
            )

            kategori_ai = hasil_ai.get("kategori", "lainnya")

            # Aturan penting:
            # Jika user memilih kategori selain kosong/lainnya, jangan ditimpa AI.
            # Jika user tidak memilih kategori atau memilih lainnya, baru pakai AI.
            if kategori_manual and kategori_manual != "lainnya":
                laporan.kategori = kategori_manual
            else:
                laporan.kategori = kategori_ai

            # Simpan hasil AI ke kolom AI
            if hasattr(laporan, "ai_kategori"):
                laporan.ai_kategori = kategori_ai

            if hasattr(laporan, "ai_confidence"):
                laporan.ai_confidence = hasil_ai.get("confidence", 0)

            if hasattr(laporan, "prioritas"):
                laporan.prioritas = hasil_ai.get("prioritas", "sedang")

            laporan.save()

            AktivitasLaporan.objects.create(
                laporan=laporan,
                deskripsi='Laporan masuk, menunggu verifikasi, dan sudah dianalisis AI DeepSeek',
                oleh=request.user,
                warna='danger'
            )

            Notifikasi.objects.create(
                pengguna=request.user,
                laporan=laporan,
                judul='Laporan berhasil dikirim!',
                pesan=f'{laporan.nomor_laporan} sedang menunggu verifikasi dan sudah dianalisis AI.'
            )

            messages.success(
                request,
                f'Laporan {laporan.nomor_laporan} berhasil dikirim dan dianalisis AI!'
            )
            return redirect('detail_laporan', pk=laporan.pk)

        else:
            messages.error(request, 'Terjadi kesalahan. Periksa form Anda.')

    else:
        form = LaporanForm()

    return render(request, 'laporan/buat_laporan.html', {'form': form})


@login_required
def dashboard_user(request):
    """Dashboard pengguna - daftar semua laporan dengan filter"""
    laporan_qs = Laporan.objects.filter(pelapor=request.user).order_by('-dibuat_pada')

    # Filter berdasarkan status dan kategori
    status_filter = request.GET.get('status', '')
    kategori_filter = request.GET.get('kategori', '')
    search = request.GET.get('q', '')

    if status_filter:
        laporan_qs = laporan_qs.filter(status=status_filter)
    if kategori_filter:
        laporan_qs = laporan_qs.filter(kategori=kategori_filter)
    if search:
        laporan_qs = laporan_qs.filter(
            Q(deskripsi__icontains=search) | Q(alamat__icontains=search) | Q(nomor_laporan__icontains=search)
        )

    # Statistik personal
    my_stats = {
        'total': request.user.laporan_set.count(),
        'pending': request.user.laporan_set.filter(status='pending').count(),
        'diproses': request.user.laporan_set.filter(status='diproses').count(),
        'selesai': request.user.laporan_set.filter(status='selesai').count(),
    }

    paginator = Paginator(laporan_qs, 10)
    page_num = request.GET.get('page', 1)
    laporan_page = paginator.get_page(page_num)

    return render(request, 'laporan/dashboard_user.html', {
        'laporan_list': laporan_page,
        'my_stats': my_stats,
        'status_filter': status_filter,
        'kategori_filter': kategori_filter,
        'search': search,
    })


@login_required
def detail_laporan(request, pk):
    """Detail laporan - bisa dilihat pelapor sendiri atau admin"""
    laporan = get_object_or_404(Laporan, pk=pk)
    # Pastikan hanya pelapor atau admin yang bisa lihat
    if laporan.pelapor != request.user and not request.user.is_admin_dinas and not request.user.is_staff:
        messages.error(request, 'Anda tidak punya akses ke laporan ini.')
        return redirect('dashboard_user')
    aktivitas = laporan.aktivitas.all()
    return render(request, 'laporan/detail_laporan.html', {
        'laporan': laporan,
        'aktivitas': aktivitas,
    })


@login_required
def riwayat_laporan(request):
    """Riwayat semua laporan milik user yang sudah selesai atau ditolak"""
    laporan_list = Laporan.objects.filter(
        pelapor=request.user,
        status__in=['selesai', 'ditolak']
    ).order_by('-dibuat_pada')
    return render(request, 'laporan/riwayat.html', {'laporan_list': laporan_list})


@login_required
def notifikasi_view(request):
    """Halaman notifikasi user"""
    notif_list = request.user.notifikasi.all()
    # Tandai semua sebagai sudah dibaca
    if request.GET.get('mark_read'):
        notif_list.update(sudah_dibaca=True)
        return redirect('notifikasi')
    return render(request, 'laporan/notifikasi.html', {'notif_list': notif_list})


# ==================== HALAMAN ADMIN ====================

def admin_required(view_func):
    """Decorator: hanya admin dinas atau staff yang bisa akses"""
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if not (request.user.is_admin_dinas or request.user.is_staff):
            messages.error(request, 'Anda tidak memiliki akses halaman admin.')
            return redirect('beranda')
        return view_func(request, *args, **kwargs)
    wrapper.__name__ = view_func.__name__
    return wrapper


@admin_required
def admin_dashboard(request):
    """Dashboard admin dengan statistik lengkap"""
    total = Laporan.objects.count()
    stats = {
        'total': total,
        'pending': Laporan.objects.filter(status='pending').count(),
        'diproses': Laporan.objects.filter(status='diproses').count(),
        'selesai': Laporan.objects.filter(status='selesai').count(),
        'ditolak': Laporan.objects.filter(status='ditolak').count(),
        'total_user': CustomUser.objects.filter(is_admin_dinas=False, is_staff=False).count(),
    }
    stats['persen_selesai'] = round(stats['selesai'] / total * 100) if total > 0 else 0

    # Data per kategori untuk chart
    kategori_data = Laporan.objects.values('kategori').annotate(jumlah=Count('kategori'))

    laporan_terbaru = Laporan.objects.select_related('pelapor').order_by('-dibuat_pada')[:8]

    return render(request, 'laporan/admin_dashboard.html', {
        'stats': stats,
        'kategori_data': kategori_data,
        'laporan_terbaru': laporan_terbaru,
    })


@admin_required
def admin_laporan(request):
    """Halaman manajemen laporan untuk admin - semua laporan dengan filter"""
    laporan_qs = Laporan.objects.select_related('pelapor').order_by('-dibuat_pada')

    status_filter = request.GET.get('status', '')
    kategori_filter = request.GET.get('kategori', '')
    search = request.GET.get('q', '')

    if status_filter:
        laporan_qs = laporan_qs.filter(status=status_filter)
    if kategori_filter:
        laporan_qs = laporan_qs.filter(kategori=kategori_filter)
    if search:
        laporan_qs = laporan_qs.filter(
            Q(deskripsi__icontains=search) |
            Q(alamat__icontains=search) |
            Q(nomor_laporan__icontains=search) |
            Q(pelapor__first_name__icontains=search)
        )

    paginator = Paginator(laporan_qs, 15)
    page_num = request.GET.get('page', 1)
    laporan_page = paginator.get_page(page_num)

    return render(request, 'laporan/admin_laporan.html', {
        'laporan_list': laporan_page,
        'status_filter': status_filter,
        'kategori_filter': kategori_filter,
        'search': search,
    })


@admin_required
def admin_detail_laporan(request, pk):
    """Admin melihat dan mengupdate detail laporan"""
    laporan = get_object_or_404(Laporan, pk=pk)
    aktivitas = laporan.aktivitas.all()

    if request.method == 'POST':
        old_status = laporan.status
        form = UpdateStatusForm(request.POST, instance=laporan)
        if form.is_valid():
            updated_laporan = form.save(commit=False)
            if updated_laporan.status == 'selesai' and not updated_laporan.diselesaikan_pada:
                updated_laporan.diselesaikan_pada = timezone.now()
            updated_laporan.save()

            # Catat aktivitas
            status_label = dict(Laporan.STATUS_CHOICES).get(updated_laporan.status, updated_laporan.status)
            color_map = {'pending': 'warning', 'diproses': 'info', 'selesai': 'success', 'ditolak': 'danger'}
            AktivitasLaporan.objects.create(
                laporan=laporan,
                deskripsi=f'Status diubah menjadi: {status_label}',
                oleh=request.user,
                warna=color_map.get(updated_laporan.status, 'secondary')
            )

            # Kirim notifikasi ke pelapor jika status berubah
            if old_status != updated_laporan.status:
                Notifikasi.objects.create(
                    pengguna=laporan.pelapor,
                    laporan=laporan,
                    judul=f'Status laporan diperbarui',
                    pesan=f'{laporan.nomor_laporan} - Status: {status_label}'
                )

            messages.success(request, 'Laporan berhasil diperbarui.')
            return redirect('admin_detail_laporan', pk=pk)
    else:
        form = UpdateStatusForm(instance=laporan)

    return render(request, 'laporan/admin_detail_laporan.html', {
        'laporan': laporan,
        'aktivitas': aktivitas,
        'form': form,
    })


@admin_required
def admin_pengguna(request):
    """Halaman manajemen pengguna"""
    search = request.GET.get('q', '')
    users = CustomUser.objects.filter(is_staff=False).annotate(
        total_laporan=Count('laporan_set')
    ).order_by('-date_joined')

    if search:
        users = users.filter(
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search) |
            Q(email__icontains=search)
        )

    paginator = Paginator(users, 15)
    page_num = request.GET.get('page', 1)
    users_page = paginator.get_page(page_num)

    return render(request, 'laporan/admin_pengguna.html', {
        'users': users_page,
        'search': search,
    })


# ==================== API ENDPOINT ====================

@login_required
def api_notif_count(request):
    """API: jumlah notifikasi belum dibaca (untuk badge di navbar)"""
    count = request.user.notifikasi.filter(sudah_dibaca=False).count()
    return JsonResponse({'count': count})
