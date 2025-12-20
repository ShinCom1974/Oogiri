# oogiri/admin.py
from django.contrib import admin
from .models import Question, Answer
import json

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    # 一覧画面の表示項目
    list_display = ('question_text', 'theme', 'user', 'is_manual', 'is_excellent', 'created_at')
    
    # 絞り込み項目
    list_filter = ('theme', 'is_manual', 'is_excellent', 'created_at')
    
    # 検索対象項目
    search_fields = ('question_text', 'source_title')
    
    # 編集画面での表示順序とグループ化
    fieldsets = (
        (None, {
            'fields': ('question_text', 'theme', 'is_excellent', 'user', 'is_manual')
        }),
        ('AI情報', {
            'fields': ('source_title',),
            'description': 'AI生成時のみ使用されます。'
        }),
    )   

@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    list_display = (
        'id',                    
        'question',              
        'answer_text',           
        'score',                 
        'review_text',         
        'is_excellent_answer',   
        'user',
        'created_at',
    )
    
    list_editable = ('is_excellent_answer',)
    list_filter = ('score', 'is_excellent_answer', 'created_at')
    
    search_fields = ('answer_text', 'question__question_text', 'review_text') 

    fields = (
        'question', 
        'user', 
        'answer_text', 
        'score', 
        'review_text',           
        'is_excellent_answer' 
    )

    