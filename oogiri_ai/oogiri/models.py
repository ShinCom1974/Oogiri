from django.db import models

from django.conf import settings

class Question(models.Model):
    """
    AIによって生成された、または管理者が手動で入力した大喜利のお題を保存するモデル。
    """
    # ユーザー認証モデルとの連携 (誰が生成/入力したか)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL, # ユーザーが削除されてもデータは残すため SET_NULL に変更
        related_name='generated_questions',
        verbose_name='作成/入力ユーザー',
        null=True, # 手動入力の場合、ユーザーが削除される場合を考慮し null を許可
        blank=True
    )
    
    # AIが回答したお題か、管理者が手動で入力したお題か (要件2対応)
    is_manual = models.BooleanField(default=False, verbose_name='手動入力') 

    # AI生成のソースとなったニュースタイトル (手動入力の場合は空欄可)
    source_title = models.CharField(max_length=255, verbose_name='基にしたニュースタイトル', blank=True, null=True)
    
    # AIが提案したお題の本文
    question_text = models.TextField(verbose_name='お題の本文')
    
    # お題のテーマ
    theme = models.CharField(max_length=50, verbose_name='テーマ')
    
    # 管理者による品質評価 (要件4対応)
    is_excellent = models.BooleanField(default=False, verbose_name='特に面白い') # Few-shot/RAGのフィルタリングに利用
    
    # お題が生成/入力された日時 (要件5対応 - 新しいものを優先)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='作成日時')

    class Meta:
        verbose_name = 'お題'
        verbose_name_plural = 'お題'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.theme} {"(手動)" if self.is_manual else "(AI)"} - {self.question_text[:30]}...'


class Answer(models.Model):
    """
    ユーザーの大喜利回答と、AIによる評価を保存するモデル
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='answers',
        verbose_name='回答ユーザー'
    )
    
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name='answers',
        verbose_name='対象のお題'
    )
    
    answer_text = models.TextField(verbose_name='回答内容')
    
    # AIによる評価結果
    score = models.IntegerField(verbose_name='面白さの点数', help_text='5段階評価')
    review_text = models.TextField(verbose_name='AIの講評')
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='回答日時')

    is_excellent_answer = models.BooleanField(
        default=False, 
        verbose_name='特に面白い（模範回答）'
    )

    class Meta:
        verbose_name = '回答'
        verbose_name_plural = '回答'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user.nickname}の回答 ({self.score}点)'