# 報連相チェック集計（Streamlit）

Googleフォーム「報連相チェック」の回答（スプレッドシート）を読み込んで、集計画面を表示します。画面は見るだけで、回答データはスプレッドシートのままです。

画面でできること
- 集計単位を「週ごと／月ごと」で切り替え、配信週・月をプルダウンで選ぶ
- 回答者数・回答率（目標との比較）・合計平均・いちばん弱い項目
- 項目別の平均と点数の分布、週・月ごとの推移と回答率
- 部署別の平均、声をかけたい人（2点以下の項目／合計9点以下／前の期間から3点以上低下）
- 個人別の一覧。名前を押すと、その人の毎週の点数とコメントの履歴
- 自由記述の一覧

集計のルール
- 回答は「回答日の直前の金曜日（金曜当日を含む）」の配信週にまとめる
- 同じ人が同じ週に2回答えたら、新しい回答を使う（氏名の空白は無視して同一人物とみなす）
- 回答率＝回答者数 ÷ 「分析」タブの「トライアル対象人数」。月ごとは、その月の各週の回答率の平均
- 目標の線は「分析」タブの「回答率の目標」

## フォルダ構成

```
app.py                  入口（スプレッドシートを読み、集計画面を表示）
horenso/dashboard.html  集計画面（見た目と集計の処理）
horenso/sheets.py       スプレッドシートの読み込み（読み取り専用・10分キャッシュ）
horenso/config.py       スプレッドシートID などの設定
tests/test_app.py       架空データでの動作確認
```

## 準備（最初に1回）

1. Google Cloud（プロジェクト horenso）で **Google Sheets API** を有効にする
2. サービスアカウント（例：bot-account）の「鍵」→「キーを追加」→「新しい鍵を作成」→ JSON をダウンロード
3. 「報連相チェック回答管理表」を、サービスアカウントのメールアドレスに **閲覧者** で共有する
4. Streamlit Cloud の「Manage app」→「Settings」→「Secrets」に、次の形で貼って保存する（鍵ファイルを `{` から `}` まで丸ごと）

   ```toml
   gcp_service_account_json = '''
   { …鍵ファイルの中身をそのまま… }
   '''
   ```

鍵ファイルは GitHub やチャットに貼らないでください。

## 手元で動かす

```bash
pip install -r requirements.txt
cp .streamlit/secrets.toml.example .streamlit/secrets.toml   # 鍵を書き込む
streamlit run app.py
```

## 動作確認

```bash
python tests/test_app.py      # 「すべてOK」と出れば成功
```

## 設定の変更

スプレッドシートID と読み込みの間隔（秒）は、Secrets の `[horenso]`（`SURVEY_ID` / `CACHE_TTL`）または環境変数 `HORENSO_SURVEY_ID` / `HORENSO_CACHE_TTL` で変えられます。タブ名は `horenso/config.py` の `TABS` にあります。
