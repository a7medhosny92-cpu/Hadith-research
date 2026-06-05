# Tutor di Arabo Classico/Coranico — Fondazione del sapere

Questa cartella contiene la **base di conoscenza** (il "spine" del sapere) su cui
costruiamo l'app-tutor interattiva per imparare l'arabo classico/coranico.

## File
- **`knowledge-base.md`** — il documento di conoscenza strutturato (fonetica/tajwīd,
  ortografia, ṣarf, naḥw, balāgha, lessico coranico, curriculum a livelli, errori
  tipici, disaccordi tra scuole). Sintesi di una ricerca multi-fonte verificata.
- **`sources.md`** — elenco delle fonti consultate (متون classici + accademiche moderne).

## Come questa base alimenta l'app (fasi successive)

```
docs/arabic/knowledge-base.md   (sapere umano-leggibile, questa fase)
        │
        ▼
[Fase 2] dati strutturati  →  app/arabic/knowledge/*.json|yaml
   (lettere, makhārij, ṣifāt, awzān, regole di iʿrāb, livelli, lessico per radice…)
        │
        ▼
[Fase 3] motore linguistico  →  app/arabic/engine/
   (diacritizzazione, analisi morfologica/iʿrāb, correzione — riusa nahw.py, tts.py)
        │
        ▼
[Fase 4] cervello ibrido  →  base di conoscenza (RAG) + LLM tutor (con fallback offline)
        │
        ▼
[Fase 5] finestra interattiva  →  studio · scrittura+correzione · parlato+pronuncia ·
                                   autovalutazione · chat col tutor
```

## Principi guida (dalla ricerca)
- **Iʿrāb come spina dorsale**: l'analisi dei casi attraversa ogni livello.
- **Lessico per radice e per frequenza**: ~125 parole ≈ 50% del Corano, ~300–500 radici
  ≈ 75–85%; insegnare prima le parole-funzione.
- **Tre scienze in parallelo** (naḥw + ṣarf + balāgha), non in sequenza rigida.
- **Onestà sulle divergenze**: il tutor segnala i punti dibattuti (es. polarità
  dell'العدد, lunghezze del madd per qirāʾa) invece di presentarli come assoluti.
- **Riuso degli asset esistenti**: diacritizzazione tashkīl, motore `nahw.py`, voci
  TTS arabe Piper costruiti nelle fasi precedenti.
