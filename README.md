# aws-cloudwatch-logwatcher

このツールは、デプロイした環境のCloudWatchログを収集して、
SNSメール通知するためのPythonコードのサンプルです。<br>
serverless.ymlファイルを編集して使ってください。

# 動作<br>
本ツールは、下記処理を実行します。<br>
1. S3から前回実行時間を取得する。(S3上の固定パスになければ1日前を前回実行時間とする。処理終了時に実行時間を更新する)
2. 前回実行時刻～現在実行時刻までの全(/aws/lambdaで始まる)ログgroupの最初のストリームをcloudwatchから取得。
3. 取得したログ情報をテキストに加工し、環境変数で設定したSNSのトピックARNへ通知する。

# 事前準備<br>
1. serverlessをインストールし、aws上のリソースにアクセスできる状態にしておく。
2. 通知先のSNSトピックを設定
3. 本ツールのserverless.ymlを編集

# serverless.yml変更必須項目<br>
下記環境変数を変更します。<br>

service: my-service
→ユニークなサービス名に変更してください。

environment:<br>
    ALERT_LOG_BUCKET: ${self:service}-alert-logs-${self:provider.stage}<br>→前回実行時刻を保存するS3バケット(任意。変更する場合、S3バケットが存在すること。)<br>
    ALERT_LOG_KEY: 'last_alert_updated_time'<br>→前回実行時刻を保存するS3オブジェクトのキー名(任意)<br>
    ALERT_LOG_PATTERN: 'Exception|Error'<br>→通知対象とするキーワード(Python のregex用正規表現)。設定しないと全ログを通知<br>
    ALERT_LOG_TOPIC_ARN: 'arn:aws:sns:us-west-2:381354997016:tmp_mail_test'<br>→通知先メールトピックのARN(事前作製したTOPIC_ARNを設定してください。)<br>
    ALERT_LOG_SUBJECT: 'subject for cloudwatch alert.'<br>→通知メールの表題(任意)<br>
    # ログ収集の粒度。カンマ区切りで複数指定可能。prefixごとの結果がメールで送信される。<br>
    ALERT_LOGS_TARGET_PREFIX: '/aws/lambda'
    
    
その他必要な変更を行ってください。<br>
たとえば、functions:の下記cron設定を変更することで、収集する周期を変更できます。
- schedule: rate(1 day)

## Copyright<br>
see ./LICENSE
