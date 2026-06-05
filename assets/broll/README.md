# Libreria b-roll

Metti qui le tue clip video **royalty-free** (`.mp4`, `.mov`, `.webm`, `.mkv`)
da usare come sfondo in movimento al posto delle immagini statiche.

Attiva il b-roll con:
- CLI: `python3 cli.py "argomento" --broll`
- API: `{"broll": true}`
- Web: menu "Sfondo b-roll" → Sì

## Come vengono scelte le clip

Per ogni scena viene scelta una clip il cui **nome file** contiene parole chiave
dell'argomento o del testo della scena; se nessuna corrisponde, una a caso.
Conviene quindi nominare i file in modo descrittivo, es:

```
produttivita_scrivania.mp4
caffe_tazzina.mp4
spazio_stelle.mp4
```

I file video qui dentro **non** vengono committati (sono in `.gitignore`).

Fonti gratuite consigliate: Pexels Videos, Pixabay, Mixkit (verifica sempre la
licenza per l'uso che ne fai).
