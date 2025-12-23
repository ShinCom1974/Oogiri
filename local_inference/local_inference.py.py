import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline

# ダウンロードしたモデルフォルダのパスを指定
LOCAL_MODEL_PATH = "./oogiri_finetuned_model" 
DEVICE = "cpu" # CPUで実行

# 1. モデルとトークナイザーをローカルからロード
print(f"モデルをCPU ({DEVICE}) でロード中...")
model = AutoModelForCausalLM.from_pretrained(
    LOCAL_MODEL_PATH,
    # device_map=DEVICE,
    torch_dtype=torch.float32 # CPUで動作させるためfloat32
).to("cpu") # ★ 明示的にCPUへ送る設定を追加
tokenizer = AutoTokenizer.from_pretrained(LOCAL_MODEL_PATH)

# 2. 推論パイプラインの設定
generator = pipeline(
    "text-generation",
    model=model,
    tokenizer=tokenizer,
    device=DEVICE,
    # Gemma向けにBPEトークンを削除する設定
    clean_up_tokenization_spaces=True, 
)

# 3. テスト入力の準備 (タスク 1: 回答生成)
test_answer_input = [
    {"role": "user", 
     "content": "あなたはプロの大喜利回答者です。以下の情報に基いて、最高の面白さの回答を一つ生成してください。\n\n【お題】ついに判明した、トナカイの角が毎年落ちる理由とは？\n【背景ニュース】北海道でシカの角拾いブーム"
    }
]

# 4. 推論の実行
print("\n--- 回答生成タスクの推論開始 ---")
# Chatテンプレートで整形
prompt = tokenizer.apply_chat_template(test_answer_input, tokenize=False, add_generation_prompt=True)

output = generator(
    prompt,
    max_new_tokens=50,
    do_sample=True,
    temperature=0.7,
    pad_token_id=tokenizer.eos_token_id
)

# 5. 結果の整形と出力
generated_text = output[0]['generated_text']
# モデルの出力（assistantの回答部分）を抽出
if generated_text.endswith(tokenizer.eos_token):
    generated_text = generated_text[:-len(tokenizer.eos_token)]

# AIの回答部分（AssistantのContent）のみを抽出するロジックが必要
# Gemmaの出力はチャット形式全体になるため、最後のAssistant部分を切り出す
assistant_prefix = "<end_of_turn>\n<model>" 
if assistant_prefix in generated_text:
    final_answer = generated_text.split(assistant_prefix)[-1].strip()
else:
    final_answer = generated_text.strip()
    
print(f"最終的なプロンプト:\n{prompt}")
print("\n--- 推論結果 ---")
print(f"AIの回答: {final_answer}")
print("------------------\n")