from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager

# カスタムマネージャー（ユーザー作成ロジック）
class CustomUserManager(BaseUserManager):
    def create_user(self, email, nickname, password=None, **extra_fields):
        if not email:
            raise ValueError('Email address must be set.')
        if not nickname:
            raise ValueError('Nickname must be set.')
        
        email = self.normalize_email(email)
        user = self.model(email=email, nickname=nickname, **extra_fields)
        user.set_password(password) # パスワードをハッシュ化
        user.save(using=self._db)
        return user

    def create_superuser(self, email, nickname, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, nickname, password, **extra_fields)

# カスタムユーザーモデル
class CustomUser(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    nickname = models.CharField(max_length=20, unique=True) # ニックネーム要件
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'  # ログイン時に使用するフィールドをメールアドレスに設定
    REQUIRED_FIELDS = ['nickname'] # スーパーユーザー作成時に必須となるフィールド

    def __str__(self):
        return self.nickname
