import json
import os
from pathlib import Path

def convert_book_json_to_txt(json_file, output_file):
    """Converti un libro JSON in TXT leggibile"""
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            book = json.load(f)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            # Metadata
            f.write(f"# {book.get('title', 'Untitled Book')}\n\n")
            
            if 'author' in book:
                f.write(f"**Autore:** {book['author']}\n\n")
            
            if 'book_id' in book:
                f.write(f"**Book ID:** {book['book_id']}\n\n")
            
            f.write(f"{'='*60}\n\n")
            
            # Content - dipende dalla struttura del JSON
            if 'content' in book:
                # Se il contenuto è una stringa
                f.write(book['content'])
            
            elif 'pages' in book:
                # Se ha pagine
                for page_num, page in enumerate(book['pages'], 1):
                    f.write(f"\n\n## Page {page_num}\n")
                    if isinstance(page, str):
                        f.write(page)
                    elif isinstance(page, dict):
                        f.write(json.dumps(page, ensure_ascii=False, indent=2))
            
            elif 'chapters' in book:
                # Se ha capitoli
                for chapter in book['chapters']:
                    if isinstance(chapter, dict):
                        f.write(f"\n\n## {chapter.get('title', 'Untitled Chapter')}\n")
                        f.write(chapter.get('content', ''))
                    else:
                        f.write(f"\n\n{chapter}")
            
            elif 'entries' in book or 'data' in book:
                # Se è una lista di entry (come rijal)
                entries = book.get('entries') or book.get('data', [])
                for i, entry in enumerate(entries, 1):
                    f.write(f"\n\n{'='*60}\n")
                    f.write(f"ENTRY {i}\n")
                    f.write(f"{'='*60}\n")
                    f.write(json.dumps(entry, ensure_ascii=False, indent=2))
            
            else:
                # Fallback: dump completo ma formattato
                f.write(json.dumps(book, ensure_ascii=False, indent=2))
        
        print(f"✅ Convertito: {json_file.name} → {output_file}")
        return True
        
    except Exception as e:
        print(f"❌ Errore con {json_file.name}: {e}")
        return False

def main():
    books_folder = Path("data/raw/turath/books")
    output_folder = Path("data/notebooklm/books")
    
    output_folder.mkdir(parents=True, exist_ok=True)
    
    json_files = list(books_folder.glob("*.json"))
    print(f"📚 Trovati {len(json_files)} libri JSON\n")
    
    converted = 0
    failed = 0
    
    for json_file in json_files:
        output_file = output_folder / f"{json_file.stem}.txt"
        
        if convert_book_json_to_txt(json_file, output_file):
            converted += 1
        else:
            failed += 1
    
    print(f"\n{'='*60}")
    print(f"✅ Conversione completata!")
    print(f"   Convertiti: {converted}/{len(json_files)}")
    print(f"   Falliti: {failed}/{len(json_files)}")
    print(f"\n📁 File salvati in: {output_folder.absolute()}")
    print(f"\nOra puoi caricarli in NotebookLM!")

if __name__ == "__main__":
    main()