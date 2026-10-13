# 報連相AI 管理画面（Streamlit）

管理台帳（送信履歴・TODO・リスク）と、報連相チェック（Googleフォーム）の回答を、Google スプレッドシートから直接読み込んで表示する管理画面です。画面は見るだけで、データの更新はこれまでどおりスプレッドシートで行います。

| 画面 | 内容 |
|---|---|
| ホーム | 対応が必要なリスク、未完了のTODO、最新のレポート、アンケート回答率。スペースごとの最新レポート、止まっているリスク・TODO |
| レポート履歴 | 月・スペースで絞り込んで、過去の日次レポートを見返す |
| リスク | 状態・レベル・スペースで絞り込み。レベルの高い順、経過日数の長い順 |
| TODO | 状態・担当・スペースで絞り込み。期限切れが先頭 |
| アンケート | 週ごと／月ごとの切り替え、回答率・項目別平均・分布・推移・部署別・声をかけたい人・個人別・個人の記録・自由記述 |

## フォルダ構成

```
app.py                  入口（画面の切り替えとサイドバー）
views/                  各画面
horenso/sheets.py       スプレッドシートの読み込み（読み取り専用・10分キャッシュ）
horenso/ledger.py       管理台帳の解析
horenso/survey.py       アンケートの解析と集計（集計ルールはファイル冒頭）
horenso/config.py       スプレッドシートID などの設定
tests/test_app.py       架空データでの動作確認
Dockerfile              Cloud Run 用
```

## 1. 認証の準備（最初に1回）

画面は「サービスアカウント」という、アプリ専用の Google アカウントでスプレッドシートを読みます。

1. Google Cloud コンソールでプロジェクト **horenso**（horenso-510409）を開く
2. 「API とサービス」→「ライブラリ」で **Google Sheets API** を有効にする
3. 「IAM と管理」→「サービスアカウント」→「作成」。名前は例として `horenso-dashboard`。ロールは付けなくてよい
4. 作成されたメールアドレス（`horenso-dashboard@horenso-510409.iam.gserviceaccount.com` など）を、次の2つのスプレッドシートに **閲覧者** で共有する
   - 報連相AIレポート 管理台帳
   - 報連相チェック回答管理表

## 2. 公開方法を選ぶ

### A. Cloud Run（社内向けにおすすめ）

データを Google Cloud の中だけで扱え、Google ログインで社内の人だけに見せられます。鍵ファイルは不要です。

1. GitHub のこのリポジトリを Cloud Run にデプロイする（コンソールの「Cloud Run」→「サービスを作成」→「リポジトリから継続的にデプロイ」、または Cloud Shell で `gcloud run deploy horenso-dashboard --source . --region asia-northeast1`）
2. 「セキュリティ」で、サービスアカウントに手順1で作った `horenso-dashboard` を選ぶ
3. 「認証」は「認証が必要」にし、Identity-Aware Proxy（IAP）を有効にする
4. IAP の設定で、見てよい人（またはグループ）に「IAP-secured Web App User」の役割を付ける

費用は、使った時間分の少額です（アクセスがないときは止まります）。

### B. Streamlit Community Cloud（手軽に試す）

無料ですぐ公開できます。ただしデータは Streamlit（Snowflake 社）のサーバーを通るため、社内ルールで問題ないか確認してから使ってください。非公開にできるアプリは1つまでです。

1. 手順1のサービスアカウントで「鍵を追加」→ JSON をダウンロード（組織の設定で鍵の作成が禁止されている場合は A を使う）
2. https://share.streamlit.io で「Create app」→ このリポジトリ、`app.py` を選ぶ
3. 「Advanced settings」→「Secrets」に、`.streamlit/secrets.toml.example` の形で JSON の中身を貼る
4. 公開後、「Share」→「Only specific people can view this app」にして、見る人のメールアドレスを招待する

## 3. 手元で動かす

```bash
pip install -r requirements.txt
cp .streamlit/secrets.toml.example .streamlit/secrets.toml   # 中身を自分の鍵に書き換える
streamlit run app.py
```

`gcloud auth application-default login` でログイン済みなら、`[gcp_service_account]` を書かなくても、そのアカウントの権限で読めます。

## 動作確認

```bash
python tests/test_app.py      # 「すべてOK」と出れば成功
```

## 設定の変更

スプレッドシートID と読み込みの間隔（秒）は、`secrets.toml` の `[horenso]`、または環境変数 `HORENSO_LEDGER_ID` / `HORENSO_SURVEY_ID` / `HORENSO_CACHE_TTL` で変えられます。タブ名は `horenso/config.py` の `TABS` にあります。

## 注意

- アンケートの個人別の情報は委員会内での分析用です。見られる人は、公開方法の設定（IAP の役割、または招待したメールアドレス）で絞ってください。
- `secrets.toml` と鍵の JSON は GitHub に上げないでください（`.gitignore` で除外済み）。
