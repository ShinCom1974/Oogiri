from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views import View
from django.contrib import messages
from django.conf import settings
from django.shortcuts import redirect
from .services import NewsService, GeminiService # ← NewsServiceとGeminiServiceをインポート！
from .models import Question, Answer # Answerモデルを追加
from .forms import AnswerForm # AnswerFormを追加

# メインの大喜利AI提案画面
# @login_required がついているため、未ログインのユーザーは自動でログイン画面にリダイレクトされる
@method_decorator(login_required, name='dispatch')
class OogiriProposalView(View):
    template_name = 'oogiri/proposal.html'
    
    def post(self, request):
        selected_theme = request.POST.get('theme')

        if not selected_theme:
            messages.error(request, 'テーマを選択してください。')
            return self.get(request)
        
        # --- 1. ニュースタイトルの取得 ---
        news_service = NewsService()
        headlines = news_service.get_recent_headlines(selected_theme)
        
        if not headlines:
            # APIキー未設定時などに備え、ダミーデータで試行
            if settings.DEBUG:
                from .services import get_dummy_headlines
                headlines = get_dummy_headlines(selected_theme)
                messages.warning(request, "【デバッグ】NewsAPIからニュースを取得できなかったため、ダミーデータを使用します。")
            else:
                messages.error(request, '現在、ニュースタイトルを取得できません。テーマを変えて再度試してください。')
                return self.get(request)

        # --- 2. Gemini AIによるお題生成 ---
        gemini_service = GeminiService()
        result = gemini_service.generate_questions(headlines, theme=selected_theme)
        
        if isinstance(result, str):
            # 戻り値が文字列の場合、エラーメッセージとして処理
            messages.error(request, f'AIお題生成中にエラーが発生しました: {result}')
            return self.get(request)
        
        # 成功の場合、結果をセッションに格納し、リダイレクトしてGETメソッドで表示させる
        # POST処理後にリダイレクトするのは、二重送信を防ぐためのベストプラクティスです (Post/Redirect/Getパターン)
        # request.session['questions'] = result
        # request.session['theme'] = selected_theme

        # 3. 成功時：お題の保存ロジック（テーマ情報を使う）
        if headlines:
            source_title = "\n".join(headlines)
        else:
         source_title = f"{selected_theme}に関するニュース"

        question_ids = [] # IDのリストを格納

        for question_text in result:
            question = Question.objects.create(
                user=request.user,
                theme=selected_theme,
                source_title=source_title, # 全てのニュースタイトルが保存されます
                question_text=question_text,
                is_manual=False
            )
            question_ids.append(question.id)

        # 4. 結果をセッションに格納し、リダイレクト
        request.session['questions_data'] = question_ids # ★IDのリストを保存
        request.session['theme'] = selected_theme
        
        messages.success(request, f'新しいお題を生成し、保存しました！')
        
        return redirect('oogiri:proposal')

    def get(self, request):
        # GETリクエスト時にセッションから結果を取得し、表示
        # ★'questions_data'（IDリスト）をセッションから取得します
        question_ids = request.session.pop('questions_data', None)
        theme = request.session.pop('theme', None)
        
        questions_with_ids = None
        if question_ids:
            # IDリストを使って Questionオブジェクトをデータベースから取得
            questions_with_ids = Question.objects.filter(id__in=question_ids).order_by('id') 
            
        themes = ['政治', '芸能', 'スポーツ', 'アニメ']
        
        context = {
            'themes': themes,
            'questions': questions_with_ids, # ★Questionオブジェクトのリストを渡す
            'selected_theme': theme,
        }
        return render(request, self.template_name, context)
    

@method_decorator(login_required, name='dispatch')
class QuestionSelectionView(View):
    """提案画面で選択されたお題IDを受け取り、回答入力画面へリダイレクトする"""
    def post(self, request):
        selected_id = request.POST.get('question_id')
        
        if not selected_id:
             messages.error(request, '回答するお題を選択してください。')
             return redirect('oogiri:proposal')

        # お題が存在するか確認（404を返すため）
        get_object_or_404(Question, pk=selected_id)

        # 正しいIDで回答入力画面へリダイレクト
        return redirect('oogiri:answer_input', question_id=selected_id)
    

@method_decorator(login_required, name='dispatch')
class AnswerInputView(View):
    """指定されたお題に対する回答を入力し、AIに評価を依頼する"""
    template_name = 'oogiri/answer_input.html'
    
    def get(self, request, question_id):
        # 1. URLから渡されたIDでお題を取得
        question = get_object_or_404(Question, pk=question_id)
        
        context = {
            'question': question,
            'form': AnswerForm(), # 空の回答フォーム
        }
        return render(request, self.template_name, context)

    def post(self, request, question_id):
        question = get_object_or_404(Question, pk=question_id)
        form = AnswerForm(request.POST)
        
        if form.is_valid():
            answer_text = form.cleaned_data['answer_text']
            
            # 2. AIによる評価を実行
            gemini_service = GeminiService()
            evaluation_result = gemini_service.evaluate_answer(question=question, answer_text=answer_text)
            
            if isinstance(evaluation_result, str):
                messages.error(request, f'AI採点中にエラーが発生しました: {evaluation_result}')
                return redirect('oogiri:proposal')
            
            # 3. 評価結果と回答をDBに保存
            answer = Answer.objects.create(
                user=request.user,
                question=question,
                answer_text=answer_text,
                score=evaluation_result['score'],
                review_text=evaluation_result['comment']
            )
            
            messages.success(request, f'回答を送信し、AIから採点（{answer.score}点）を受け取りました！')
            
            # 4. 結果画面へリダイレクト
            return redirect('oogiri:answer_result', answer_id=answer.id)
            
        context = {
            'question': question,
            'form': form,
        }
        return render(request, self.template_name, context)
    

@method_decorator(login_required, name='dispatch')
class AnswerResultView(View):
    """AIによる評価結果を表示する"""
    template_name = 'oogiri/answer_result.html'

    def get(self, request, answer_id):
        # 1. URLから渡されたIDで回答結果を取得
        # 回答した本人にしか結果を見せないよう、user=request.user でフィルタ
        answer = get_object_or_404(Answer, pk=answer_id, user=request.user)
        
        context = {
            'answer': answer,
        }
        return render(request, self.template_name, context)