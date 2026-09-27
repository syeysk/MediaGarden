from django.contrib import admin
from django.urls import include, path


urlpatterns = [
    path('admin/', admin.site.urls),
    path('base/', include('gardensunion.base.urls')),
    path('mediagarden/', include('mediagarden.urls')),
]
