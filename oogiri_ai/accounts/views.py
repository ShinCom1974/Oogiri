from django.shortcuts import render, redirect
from django.views import View
from django.contrib import messages
from django.contrib.auth import login
from .forms import CustomUserCreationForm

# サインアップ処理を行うビュー
class SignUpView(View):
    template_name = 'accounts/signup.html'
    form_class = CustomUserCreationForm

    def get(self, request):
        """GETリクエスト: フォームを表示"""
        form = self.form_class()
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        """POSTリクエスト: フォームを検証し、ユーザーを作成"""
        form = self.form_class(request.POST)
        
        if form.is_valid():
            # ユーザーをデータベースに保存
            user = form.save()
            
            # ユーザーをログインさせる (オプションだがUX向上のため実装)
            login(request, user)
            
            # 成功メッセージの追加
            messages.success(request, f'{user.nickname}さん、登録が完了しました！')
            
            # ログイン後のメイン画面（まだ作成していないが、とりあえずルートにリダイレクト）
            return redirect('/') 
            
        # バリデーションエラーがある場合、フォームを再表示
        return render(request, self.template_name, {'form': form})
