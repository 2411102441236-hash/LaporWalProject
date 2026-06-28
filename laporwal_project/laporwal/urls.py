from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('django-admin/', admin.site.urls),
    path('accounts/', include('allauth.urls')),   # login Google (callback Google ada di sini)
    path('auth/', include('accounts.urls')),       # login/daftar/profil custom Anda
    path('', include('laporan.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
