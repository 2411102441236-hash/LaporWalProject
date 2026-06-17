from django.urls import path
from . import views

urlpatterns = [
    # Publik
    path('', views.beranda, name='beranda'),

    # User
    path('buat-laporan/', views.buat_laporan, name='buat_laporan'),
    path('dashboard/', views.dashboard_user, name='dashboard_user'),
    path('laporan/<int:pk>/', views.detail_laporan, name='detail_laporan'),
    path('riwayat/', views.riwayat_laporan, name='riwayat_laporan'),
    path('notifikasi/', views.notifikasi_view, name='notifikasi'),

    # Admin
    path('admin-panel/', views.admin_dashboard, name='admin_dashboard'),
    path('admin-panel/laporan/', views.admin_laporan, name='admin_laporan'),
    path('admin-panel/laporan/<int:pk>/', views.admin_detail_laporan, name='admin_detail_laporan'),
    path('admin-panel/pengguna/', views.admin_pengguna, name='admin_pengguna'),

    # API
    path('api/notif-count/', views.api_notif_count, name='api_notif_count'),
]
