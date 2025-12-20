# accounts/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import CustomUser

# カスタムパスワードバリデーション関数
# 英字と数字の両方が含まれているか、8文字以上20文字以内かを検証
def validate_custom_password(password):
    if len(password) < 8:
        raise forms.ValidationError("パスワードは8文字以上である必要があります。")
    if len(password) > 20:
        raise forms.ValidationError("パスワードは20文字以下である必要があります。")
    if not any(char.isalpha() for char in password):
        raise forms.ValidationError("パスワードには少なくとも1文字の英字が必要です。")
    if not any(char.isdigit() for char in password):
        raise forms.ValidationError("パスワードには少なくとも1文字の数字が必要です。")

class CustomUserCreationForm(UserCreationForm):
    # UserCreationFormはデフォルトで 'username' フィールドを持っているので、
    # 'email'と'nickname'を必須フィールドとして定義し直します。
    # 'nickname'のユニーク性(unique=True)と最大文字長(max_length=20)は、
    # モデルの定義（accounts/models.py）で既に設定済みです。

    # パスワードはデフォルトのフィールドを使うため、clean_passwordでバリデーションを上書きします。
    
    class Meta:
        model = CustomUser
        # UserCreationFormはpasswordの繰り返し入力（password2）を自動で含めます。
        fields = ('email', 'nickname',) # 表示するフィールド
        
    def clean_password2(self):
        """パスワードとパスワード確認が一致するか検証し、カスタムバリデーションを適用する"""
        password = self.cleaned_data.get('password')
        password2 = self.cleaned_data.get('password2')
        
        # 組み込みのバリデーション（一致チェック）
        if password and password2 and password != password2:
            raise forms.ValidationError(
                "パスワードが一致しません。"
            )
        
        # カスタムバリデーションの適用
        if password:
            validate_custom_password(password)
            
        return password2

# 管理画面用のフォーム（学習目的のため必須ではないが、標準的なセットとして定義）
class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = CustomUser
        fields = ('email', 'nickname', 'is_active', 'is_staff',)