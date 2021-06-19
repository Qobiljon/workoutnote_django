"""workoutnote_django URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from . import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.handle_index, name='index'),
    path('calculators/', views.handle_calculators, name='calculators'),
    path('strength-standards/', views.handle_strength_standards, name='strength standards'),
    path('training-log-tutorial/', views.handle_training_log_tutorial, name='training log tutorial'),
    path('one-rep-max-calculator/', views.handle_one_rep_max_calculator, name='one rep max calculator'),
    path('login/', views.handle_login_register, name='login'),
    path('register/', views.handle_login_register, name='register'),
]
