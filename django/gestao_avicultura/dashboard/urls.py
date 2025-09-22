# dashboard/urls.py
from django.urls import path
from . import views
from django.contrib.auth.views import LoginView, LogoutView

urlpatterns = [
    path('login/', LoginView.as_view(template_name='dashboard/login.html'), name='login'),
    path('logout/', LogoutView.as_view(next_page='login'), name='logout'),
    path('', views.dashboard_view, name='dashboard'),
    path('producao/', views.producao_view, name='producao'),
    # Adicione outras URLs aqui (lotes, financeiro, etc.)
]