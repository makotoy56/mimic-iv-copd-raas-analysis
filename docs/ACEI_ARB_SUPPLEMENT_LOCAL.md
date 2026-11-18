# ACEi-only / ARB-only：ローカルの探索的単一コントラスト

## 今回の状態

初回準備時点では、公開済み集計10件に同じモデルの係数間共分散がなく、実データの直接比較は未算出だった。その後、既存の認可済みBigQuery／ローカル環境で同一モデルを再推定し、係数・共分散の取得、ARB参照への再推定、保存した集計だけでの再計算を検証した。**直接比較はローカルで検証済み。** 数値はGit対象外の `reports/local_supplements/acei_arb_run01/supplement.md` と `contrast.json` に保存し、公開READMEや主解析には反映していない。別々のCIや丸め済みHRから共分散を補ってはいない。

元モデルは `docs/CURRENT_ANALYSIS.json` の `models.subgroups`。READMEのHR約0.683と0.805は、ACEi-onlyとARB-onlyをそれぞれneitherと比較した、このモデルの推定値である。今回の目的は、同じモデルに後から追加する **ACEi-only / ARB-only** の単一コントラストである。

- 対象：元モデルと同じ11,951入院・1,690死亡、時期5層。両クラスの処方フラグがある記録の除外と完全ケース条件は元のまま。**neither群も含める**。
- 時間・アウトカム：ICU入室から院内死亡または生存退院まで。元の死亡時刻欠損時の退院時刻フォールバックも維持。
- モデル：`acei_pre_icu + arb_pre_icu + age + gender_M`、`anchor_year_group`で層別、非罰則Cox、Efron法。同モデルにはSOFAを含めない。
- 推論：元コードはロバスト分散・クラスタリングを指定せず、通常のモデルベース分散を使う。異なる推論方法の共分散は混在させない。

## 計算と検算

`d = beta_ACEi - beta_ARB`、`Var(d) = V_AA + V_BB - 2 V_AB`。

調整後HRは `exp(d)`、95% Wald CIは `exp(d ± 1.95996398454 * sqrt(Var(d)))`。分散には同じモデルのラベル付き共分散行列を使う。別々のCIからこの分散を復元しない。

実データを再推定するローカルモードでは、元の全解析対象を維持したまま、ARBを参照に `ACEi_vs_ARB` と `neither_vs_ARB` に再パラメータ化して検算する。対象をACEi群とARB群だけに絞り直さない。元の各係数・CI・p値が保存済み参照に許容差内で一致し、再パラメータ化後のHR・CI・SE・p値と部分尤度も一致した場合にだけ結果を保存する。

## 最短の実行手順

MIMICの利用とBigQuery／ローカル処理が認められた既存環境で、リポジトリルートから実行する。この環境では実行・検証済み。再実行時は既存の結果を上書きしない新しい出力先を指定する。

```bash
.venv/bin/python scripts/acei_arb_contrast.py --refit-current --repo . --out reports/local_supplements/acei_arb_run02
```

既存のADCと、既存ローダーのドライラン・200 MB課金上限付きSELECTを使用する。テーブルを作成せず、個票・日時・識別子・残差・個人別予測を保存・表示しない。入力行はローカルメモリ内だけで扱う。保存するのは同じモデルの係数・共分散と検証済みの集計結果である。

すでに許可済みの同モデルの集計パッケージ `aggregate_model.json` がある場合は、実データへ接続せず計算できる。

```bash
.venv/bin/python scripts/acei_arb_contrast.py --aggregate reports/local_supplements/acei_arb_run01/aggregate_model.json --repo . --out reports/local_supplements/acei_arb_from_aggregate01
```

集計パッケージにはフル精度の係数、同じ順序ラベルの共分散（4×4全体、またはACEi・ARBの2×2ブロック）、元モデル・対象・推論方法・公開参照ハッシュが必要。単なるHR一覧やCI一覧は入力として受け付けない。元の4共変量モデルの指定、全解析対象の件数・死亡数・層数と参照ハッシュは、2×2ブロックの場合も必須。群別件数がなければ新たに行を取得して補わず、元の全解析対象の集計との一致で確認する。パッケージ形式は `bundle_from_fit()` が生成する。集計モードでは新たな実データ再パラメータ化をしたとは記録せず、合成データでの検算と区別する。

出力先はGit対象外の `reports/local_supplements/` 配下に限定する。既存の出力先は上書きしない。`run01` が存在する場合は新しい名前を指定する。主解析・公開README・既存図・既存数値は変更しない。

検証に合格した場合の出力は `contrast.json`、`supplement.md`、`aggregate_model.json`。向きは常に **ACEi-only / ARB-only**。HRが1未満なら、このモデル内でACEi-only処方記録群の観察ハザードがARB-only群より低い向きとなるが、実投与、因果的優劣や同等性を示すものではない。後から加えた探索的な1対比で、多重性補正は行わず、元の入院単位・非クラスタ標準誤差を引き継ぐ。

## 合成データだけで確認する

```bash
.venv/bin/python scripts/acei_arb_contrast.py --synthetic --out /tmp/acei_arb_synthetic_new
.venv/bin/python -m unittest discover -s scripts -p 'test_*.py'
```

ユニーク時刻と同時刻を含む2条件で、共分散によるコントラスト・ARB参照への再推定・PHRegの独立計算を照合した。これはMIMIC実データでの直接比較を算出・検証したことにはならない。
