# Roguelike Brick Breaker
Pythonとtkinterで制作した、ローグライク要素を取り入れた進化型ブロック崩しです。

## 🎥 動作デモ

https://github.com/user-attachments/assets/1c7778c0-bb3e-446e-97d1-620123384025

## 🧠 プロジェクトの特徴：戦略性とリプレイ性
単なるブロック崩しではなく、ローグライク特有の「選択の重要性」をゲームシステムに組み込みました。

### 実装した主な機能
- **ローグライクなパワーアップシステム**: ステージクリアごとにランダムな3つの強化選択肢を提示。パドルの拡大、ボールの分裂、貫通能力など、状況に応じた戦略的な強化が可能です。
- **オブジェクト指向による拡張性**: クラス継承（Inheritance）を使い、特殊な挙動を持つブロックやアイテムを効率的に管理。今後のギミック追加も容易な設計にしています。
- **物理演算・衝突判定**: キャンバス座標に基づいた正確な反射角の計算と、リアルタイムなヒット判定を独自に実装。

## 🛠 使用技術
- **Language:** Python 3.11
- **Library:** tkinter
- **Key Concepts:** オブジェクト指向プログラミング (OOP), ゲームデザイン, アルゴリズム設計

## 📂 ファイル構成
- `block.py`: ゲームのメインプログラム
- `rogue-like.mp4`: 動作デモ動画（ローグライク要素）
- `block-gameplay.gif`: 通常プレイのデモ画像

## 🎮 実行方法
1. 本リポジトリをクローンまたはダウンロードします。
2. 以下のコマンドで実行してください。
   `python block.py`

🤖 To maximize development efficiency, this project fully utilized AI tools for code generation. On the other hand, I independently managed the vast majority of the development lifecycle—ranging from requirements definition, screen transitions, and feature design, to crafting precise prompts, integrating the generated code, and handling final debugging and quality assurance.

（本プロジェクトでは、開発効率を最大化するため、コードの自動生成にAIを全面的に活用しています。
一方で、要件定義、画面遷移や機能の設計、AIへの正確なプロンプト構築、出力されたコードの統合、および最終的なデバッグや動作検証に至るまで、開発プロセスの大半は自身が主体となって一貫して行いました。）
