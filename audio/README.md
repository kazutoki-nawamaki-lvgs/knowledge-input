# Audio Generation

このディレクトリには、ノートから生成した音声ファイルを置く。

## 当面の方針

一旦、音声生成は **OpenAI TTS** を使う。

- 低コストで試す場合: `tts-1`
- 日本語の品質を優先する場合: `gpt-4o-mini-tts`
- Google Cloud Text-to-Speech は候補として残すが、Google Cloud Billing とAPIキー設定が必要なため後回しにする

日本語の読み上げ品質は `tts-1` だと不自然に感じる場合がある。その場合は、Markdownを整形したうえで `gpt-4o-mini-tts` を使う。

## 使い方

標準設定で生成する:

```sh
python3 scripts/openai_tts.py 'saas/001_管理画面はプロダクトの裏側ではなく何なのか.md' \
  -o 'audio/001_openai.mp3'
```

日本語品質を優先して生成する:

```sh
python3 scripts/openai_tts.py 'saas/001_管理画面はプロダクトの裏側ではなく何なのか.md' \
  -o 'audio/001_openai_gpt-4o-mini-tts_marin.mp3' \
  --model gpt-4o-mini-tts \
  --voice marin \
  --instructions '日本語のビジネス向け解説として、落ち着いた自然な口調で、句読点に沿って少し間を取りながら、聞き取りやすい速度で読み上げてください。'
```

`.md` ファイルは、スクリプト側で見出し記号、太字記号、箇条書き記号、メタ情報を軽く落としてから読み上げる。

## スマホで聞く

生成したMP3は、Google DriveにアップロードしてスマホのGoogle Driveアプリから聞く。

複数本が増えて、途中再開や連続再生が欲しくなったら、private podcast化を検討する。
