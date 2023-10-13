# главный urls
from django.contrib import admin
from django.urls import path, include

app_name = 'api'

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),

]
