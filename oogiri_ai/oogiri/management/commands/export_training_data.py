import json
import os
from django.core.management.base import BaseCommand
from django.conf import settings
from oogiri.models import Answer, Question # Questionもimport
from pathlib import Path

class Command(BaseCommand):
    help = 'ファインチューニング用の大喜利データ（JSONL形式）を出力します。'

    def handle(self, *args, **options):
        
        # 1. 出力パスの確認とディレクトリの作成
        output_dir = settings.TRAINING_DATA_ROOT
        if not output_dir.exists():
            # ディレクトリが存在しない場合は作成
            output_dir.mkdir(parents=True, exist_ok=True)
            self.stdout.write(self.style.NOTICE(f"ディレクトリを作成しました: {output_dir}"))
            
        output_filename = 'oogiri_multitask_training_data.jsonl'
        output_path = output_dir / output_filename
        
        training_data = []
        
        # 2. 【タスク 1: 回答生成】: Answerモデルから模範回答を抽出
        excellent_answers = Answer.objects.filter(is_excellent_answer=True).select_related('question')

        # Instruction: 回答タスク用
        answer_instruction = "あなたはプロの大喜利回答者です。以下の情報に基いて、最高の面白さの回答を一つ生成してください。"
        
        for answer in excellent_answers:
            question = answer.question
            user_input_text = f"\n\n【お題】{question.question_text}"
            if question.source_title:
                user_input_text += f"\n【背景ニュース】{question.source_title}"
            
            # JSONLデータポイント: 回答タスク
            data_point = {
                "messages": [
                    {"role": "user", "content": answer_instruction + user_input_text},
                    {"role": "assistant", "content": answer.answer_text}
                ]
            }
            training_data.append(json.dumps(data_point, ensure_ascii=False))

            # training_data.append(json.dumps([
            #     {"role": "user", "content": answer_instruction + user_input_text},
            #     {"role": "assistant", "content": answer.answer_text}
            # ], ensure_ascii=False))


        # 3. 【タスク 2: お題生成】: Questionモデルから特に面白いお題を抽出
        # Instruction: お題タスク用
        question_instruction = "あなたはプロの大喜利クリエイターです。与えられたニュースタイトルを参考に、それにインスパイアされた、秀逸で面白い大喜利のお題を一つ生成してください。"
        
        # is_excellent=True (品質の良いお題) かつ source_title (元ネタ) があるものに絞る
        excellent_questions = Question.objects.filter(is_excellent=True, source_title__isnull=False).exclude(source_title="")

        for question in excellent_questions:
            # 元ネタのニュースがない場合はスキップ (お題生成タスクとして成立しないため)
            if not question.source_title:
                continue
                
            user_input_text = f"\n\n【背景ニュース】{question.source_title}"
            
            # JSONLデータポイント: お題タスク
            data_point = {
                "messages": [
                    {"role": "user", "content": question_instruction + user_input_text},
                    {"role": "assistant", "content": question.question_text}
                ]
            }
            training_data.append(json.dumps(data_point, ensure_ascii=False))
            # training_data.append(json.dumps([
            #     {"role": "user", "content": question_instruction + user_input_text},
            #     {"role": "assistant", "content": question.question_text}
            # ], ensure_ascii=False))
            
        
        if not training_data:
            self.stdout.write(self.style.WARNING("WARNING: 'is_excellent'または'is_excellent_answer'にフラグが立っているデータが見つかりませんでした。"))
            return

        # 4. ファイルへの書き出し
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                # JSONL形式として1行ずつ書き込む（各データポイントはすでにJSON文字列）
                f.write("\n".join(training_data) + '\n')
            
            self.stdout.write(self.style.SUCCESS(f'SUCCESS: {len(training_data)}件のマルチタスクデータを {output_path} に出力しました。'))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'ERROR: ファイル書き出し中にエラーが発生しました: {e}'))