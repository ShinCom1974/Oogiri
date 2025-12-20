# oogiri/services.py
from newsapi import NewsApiClient
from datetime import datetime, timedelta
from django.conf import settings
import json
from google import genai
from google.genai.errors import APIError # APIエラー処理用
from django.conf import settings # Questionモデルを使うために必要
from .models import Question, Answer

# NewsAPIと連携し、ニュースタイトルを取得するクラス
class NewsService:
    def __init__(self):
        # settings.pyからAPIキーを取得
        self.api_key = settings.NEWS_API_KEY
        # if self.api_key == settings.NEWS_API_KEY:
        #     print("警告: NewsAPIキーが設定されていません。ダミーデータを使用します。")
        
        # NewsApiClientの初期化
        self.newsapi = NewsApiClient(api_key=self.api_key)

    def get_recent_headlines(self, theme: str, max_count: int = 100) -> list[str]:
        """
        指定されたテーマと期間（過去30日間）に基づいてニュースタイトルを取得する。
        """
        
        # ニュースの期間の定義（過去30日間）
        # NewsAPIの形式: 'YYYY-MM-DD'
        today = datetime.now()
        fourteen_days_ago = today - timedelta(days=30)
        
        from_date_str = fourteen_days_ago.strftime('%Y-%m-%d')
        to_date_str = today.strftime('%Y-%m-%d')
        
        try:
            # NewsAPIの 'everything' エンドポイントを使用
            # q=テーマ, language=日本語, sortBy=新着順, 期間指定
            response = self.newsapi.get_everything(
                q=theme,
                # language='jp',
                sort_by='publishedAt',
                from_param=from_date_str, # 過去30日間に設定
                to=to_date_str,
                page_size=max_count,    # 最大100個を取得
            )

            # エラーチェック
            if response['status'] != 'ok':
                print(f"NewsAPIエラー: {response.get('code')}, {response.get('message')}")
                return []

            # タイトルをリストとして抽出
            titles = [article['title'] for article in response['articles']]
            
            # 最大100個に満たなかった場合はそのまま返す (要件2に適合)
            return titles
            
        except Exception as e:
            # APIキーが無効、ネットワークエラーなどの一般的な例外処理
            print(f"NewsServiceで予期せぬエラーが発生しました: {e}")
            return []

# テスト用ダミーデータ取得関数 (APIキー未設定時の代替)
def get_dummy_headlines(theme: str) -> list[str]:
    return [
        f"{theme}関連のニュースタイトル - ダミー1: AIが生成したタイトルがトレンドに",
        f"{theme}関連のニュースタイトル - ダミー2: 政治家の猫ミームが話題沸騰",
        f"{theme}関連のニュースタイトル - ダミー3: スポーツ選手が新しい料理に挑戦",
        f"{theme}関連のニュースタイトル - ダミー4: アニメ映画が記録的な興行収入を達成",
    ]


# Few-Shotプロンプト用のデータ取得ヘルパー関数
def get_few_shot_questions(theme: str, max_examples: int = 5) -> list[str]:
    """
    指定されたテーマと「is_excellent=True」に基づき、Few-Shotに利用するお題を取得する。
    登録日時が新しいものを優先する (要件5)。
    """
    try:
        # is_excellent=True でフィルタリング
        # ordering=['-created_at'] (新しいものを優先) は、モデルのMetaクラスで既に定義済みのため不要
        excellent_questions = Question.objects.filter(
            theme=theme,
            is_excellent=True
        ).order_by('-created_at')[:max_examples] # 上位 max_examples 件を取得

        # お題のテキストだけをリストにして返す
        return [q.question_text for q in excellent_questions]
        
    except Exception as e:
        print(f"Few-Shotデータ取得エラー: {e}")
        return []


# Gemini AIと連携し、お題を取得するクラス
class GeminiService:
    def __init__(self):
        # settings.pyからAPIキーを取得し、クライアントを初期化
        self.api_key = settings.GEMINI_API_KEY
        self.client = genai.Client(api_key=self.api_key)
        self.model = 'gemini-2.5-flash' # 応答速度を考慮してFlashモデルを選択

    def generate_questions(self, headlines: list[str], theme: str) -> list[str] | str:
        """
        ニュースタイトルリストに基づき、大喜利のお題を3つJSON形式で生成する。
        成功時はお題のリストを、失敗時はエラーメッセージを返す。
        """
        # --- 1. Few-Shot事例の取得 ---
        # トークン長を意識して、10個を上限とする
        few_shot_examples = get_few_shot_questions(theme=theme, max_examples=10)

        # --- 2. プロンプトの構築 ---
        headline_text = "\n".join([f"- {h}" for h in headlines])
        
        # Few-Shotセクションの構築
        few_shot_text = ""
        if few_shot_examples:
            example_list = "\n".join([f"  - {ex}" for ex in few_shot_examples])
            few_shot_text = (
                f"\n\n参考として、過去に面白かったお題の例を挙げます。このスタイルを参考に、新しいお題を生成してください:\n"
                f"{example_list}"
            )
        
        # システム命令：JSON形式を厳格に要求
        system_instruction = (
            "あなたは優秀な大喜利AIです。ユーザーから与えられたニュースタイトルに基づき、"
            "面白くてユニークな大喜利のお題を**3つだけ**考案し、**必ずJSON形式**で出力してください。 "
            "JSONのキーは`questions`とし、その値は3つの文字列（お題）を持つ配列とすること。"
            "**お題の文章以外のテキストは一切含めないでください。**"
            "中国語のニュースと考えられる内容は考慮しないで、日本語のニュースだけを使ってください。"
            "死、暴力あるいは戦争など悲惨なことを思い起こさせるニュースは参照せずに、大喜利のお題を考えてください。"
        )
        
        # ユーザープロンプト (RAGとFew-Shotを統合)
        user_prompt = (
            "以下のニュースタイトルを見て、3つのお題をJSON形式で提案してください。"
            "また面白いお題の例を参考にしてください:\n\n"
            f"--- ニュースタイトル ---\n"
            f"{headline_text}"
            f"--- 面白いお題の例 ---"
            f"{few_shot_text}" # Few-Shotの例をプロンプトに組み込む
        )

        try:
            # --- 2. API呼び出し ---
            # response = self.client.models.generate_content(...)
            # 簡潔にするため、 generate_content の呼び出しを仮で記述
            response = self.client.models.generate_content(
                model=self.model,
                contents=[user_prompt],
                config={"system_instruction": system_instruction}
            )

            raw_text = response.text.strip()
            
            # --- 3. JSONパースとバリデーション (フェーズ3で提案したロジック) ---
            
            # JSONブロックが検出された場合、それを抽出
            if raw_text.startswith('```json') and raw_text.endswith('```'):
                 raw_text = raw_text.strip('```json').strip('```').strip()
            
            # JSONパース
            data = json.loads(raw_text)
            
            # 構造検証
            if 'questions' not in data:
                return "AIからの応答構造が不正です: 'questions'キーが見つかりません。"
            
            questions = data['questions']
            
            if not isinstance(questions, list) or len(questions) != 3:
                return "AIからの応答構造が不正です: お題が3つのリストではありません。"
            
            return questions

        except json.JSONDecodeError:
            return "AIからの応答が不正です。JSON形式で出力されていません。"
        except APIError as e:
            return f"Gemini APIエラーが発生しました: {e}"
        except Exception as e:
            return f"予期せぬエラーが発生しました: {e}"
            
        # ----------------------------------------------------------------

    def _get_few_shot_examples(self, limit=3):
        """データベースから Few-Shot 候補の回答と評価を取得し、JSON形式の文字列に整形する"""
        
        # '特に面白い'フラグが立っている回答をランダムに3件取得
        examples = Answer.objects.filter(is_excellent_answer=True).order_by('?')[:limit]
        
        few_shot_text = []
        for example in examples:
            
            # ★★★ ここが具体的な整形ロジックです ★★★
            example_data = {
                "お題": example.question.question_text, # AnswerからQuestionオブジェクトを経由してお題を取得
                "回答": example.answer_text,
                "評価結果": {
                    "score": example.score,
                    "commentary": example.commentary
                }
            }
            # JSON文字列に変換し、日本語が化けないように ensure_ascii=False を指定
            # indent=2 で整形し、プロンプト内で見やすくする
            json_string = json.dumps(example_data, ensure_ascii=False, indent=2)
            
            # AIへの指示として「事例:」という見出しを付けて追加
            few_shot_text.append(f"事例:\n{json_string}")
            # ★★★ 整形ロジックここまで ★★★
            
        # 複数の事例を区切り文字 (---) で結合して一つの文字列として返す
        return "\n\n---\n\n".join(few_shot_text)
    

def evaluate_answer(self, question: Question, answer_text: str) -> dict | str:
        """
        お題と回答を受け取り、面白さを評価してJSONで返す。
        戻り値の形式: {"score": int, "comment": str}
        """
        
        # 1. Few-Shot 事例を取得
        # self._get_few_shot_examples メソッドが定義されていることが前提
        few_shot_examples = self._get_few_shot_examples(limit=3) 

        # 2. プロンプトの構築
        # 元ネタのニュースがある場合はコンテキストとして含める
        source_info = ""
        if question.source_title:
            source_info = f"元ネタのニュース: {question.source_title}\n"

        # 3. system_instruction (役割と出力形式の定義)
        # Few-Shotの参照指示を加え、講評の精度を高める
        system_instruction = (
            "あなたは厳しくも愛のある大喜利のプロ審査員です。"
            "提供される【評価の参考にすべき事例】を参考に、評価基準と講評のトーンを学習し、今回の回答を評価してください。"
            "ユーザーの回答を5段階で評価し、短い講評コメントを行ってください。"
            "出力は必ずJSON形式で、整数型の`score`（1〜5）と、文字列型の`comment`を含むオブジェクトにしてください。"
            "JSON以外のテキストは出力しないでください。"
        )

        # 4. user_prompt (評価対象とFew-Shot事例のコンテキスト)
        user_prompt = (
            f"以下の大喜利のお題に対する回答を評価してください。\n\n"
            
            f"---【評価の参考にすべき事例】---\n"
            f"あなたは、以下の過去の模範解答と評価結果のパターンを参考に、今回の回答を評価してください。\n"
            f"{few_shot_examples}"
            f"---------------------------------\n\n"
            
            f"【今回の評価対象】\n"
            f"{source_info}"
            f"お題: {question.question_text}\n"
            f"回答: {answer_text}\n"
        )

        try:
            response = self.client.models.generate_content(
                model=self.model,
                # contents=[user_prompt] と system_instruction を分けて渡す方式を維持
                contents=[user_prompt], 
                config={"system_instruction": system_instruction}
            )

            # ... (中略: JSONパースと構造検証ロジックはそのまま維持) ...
            raw_text = response.text.strip()
            
            if raw_text.startswith('```json') and raw_text.endswith('```'):
                 raw_text = raw_text.strip('```json').strip('```').strip()
            
            data = json.loads(raw_text)
            
            # 構造検証
            if 'score' not in data or 'comment' not in data:
                return "AIからの応答構造が不正です: scoreまたはcommentがありません。"
            
            return data # 成功時は辞書を返す

        except json.JSONDecodeError:
            return "AIからの応答が不正です。JSON形式で出力されていません。"
        except Exception as e:
            # 予期せぬエラーの場合、ログを出力することが望ましい
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"予期せぬエラーが発生しました: {e}", exc_info=True)
            return f"予期せぬエラーが発生しました: {e}"