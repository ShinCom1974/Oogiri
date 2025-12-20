from django.urls import path
from . import views

# アプリケーションの名前空間を定義
app_name = 'oogiri'

urlpatterns = [
    # メインの大喜利提案画面 (ルートパス / または /oogiri/ でアクセス)
    path('', views.OogiriProposalView.as_view(), name='proposal'),


    # お題選択時のPOST処理用（中間ビュー）
    path('select/', views.QuestionSelectionView.as_view(), name='question_select'),
    # 回答入力画面
    path('answer/input/<int:question_id>/', views.AnswerInputView.as_view(), name='answer_input'),
    # 評価結果表示画面
    path('answer/result/<int:answer_id>/', views.AnswerResultView.as_view(), name='answer_result'),
    
]