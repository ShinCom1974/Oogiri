from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'accounts'

urlpatterns = [
    # サインアップ画面（/accounts/signup/でアクセス）
    path('signup/', views.SignUpView.as_view(), name='signup'),

    # ログイン画面 (name='login' が必須でした)
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    
    # ログアウト処理
    path('logout/', auth_views.LogoutView.as_view(next_page='/'), name='logout'),
]