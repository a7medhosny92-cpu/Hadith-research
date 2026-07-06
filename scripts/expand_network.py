"""Espande la rete شيوخ/تلاميذ integrando fonti aggiuntive.

Questo script carica la rete esistente e la espande con relazioni da fonti
come تهذيب الكمال (al-Mizzi) e الجرح والتعديل (Ibn Abi Hatim).
"""

import json
from pathlib import Path

from app.config import get_settings
from app.rijal.resolve import load_network, save_network, network_key


def load_tahdhib_relations(tahdhib_path: str) -> dict[str, set[str]]:
    """
    Carica relazioni da تهذيب الكمال (al-Mizzi).

    Formato atteso: JSON con {name: {shuyukh: [...], talamidh: [...]}}
    """
    path = Path(tahdhib_path)
    if not path.exists():
        print(f"⚠️  File non trovato: {path}")
        return {}

    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    students = {}
    for entry in data:
        name = entry.get('name', '')
        shuyukh = entry.get('shuyukh', [])

        # Per ogni shaykh, aggiungi il narratore come talamidh
        for shaykh in shuyukh:
            shaykh_key = network_key(shaykh)
            if shaykh_key not in students:
                students[shaykh_key] = set()
            students[shaykh_key].add(network_key(name))

    return students


def load_jarh_tadil_relations(path: str) -> dict[str, set[str]]:
    """
    Carica relazioni da الجرح والتعديل (Ibn Abi Hatim).

    Formato atteso: JSON con {name: {shuyukh: [...], talamidh: [...]}}
    """
    path = Path(path)
    if not path.exists():
        print(f"⚠️  File non trovato: {path}")
        return {}

    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    students = {}
    for entry in data:
        name = entry.get('name', '')
        shuyukh = entry.get('shuyukh', [])

        for shaykh in shuyukh:
            shaykh_key = network_key(shaykh)
            if shaykh_key not in students:
                students[shaykh_key] = set()
            students[shaykh_key].add(network_key(name))

    return students


def merge_networks(*networks: dict[str, set[str]]) -> dict[str, set[str]]:
    """Unisce multiple reti in una sola."""
    merged = {}
    for net in networks:
        for shaykh, talamidh_set in net.items():
            if shaykh not in merged:
                merged[shaykh] = set()
            merged[shaykh].update(talamidh_set)
    return merged


def expand_network(
    existing_path: str | None = None,
    tahdhib_path: str | None = None,
    jarh_tadil_path: str | None = None,
    output_path: str | None = None,
):
    """Espande la rete esistente con nuove fonti."""

    settings = get_settings()

    if existing_path is None:
        existing_path = str(settings.documented_network_path)
    if output_path is None:
        output_path = str(settings.documented_network_path)

    # 1. Carica rete esistente
    print("📊 Caricamento rete esistente...")
    existing = load_network(existing_path)
    print(f"   Rete esistente: {len(existing._students)} shuyukh")

    # 2. Carica nuove fonti
    networks_to_merge = [existing._students]

    if tahdhib_path:
        print("📚 Caricamento تهذيب الكمال...")
        tahdhib = load_tahdhib_relations(tahdhib_path)
        print(f"   تهذيب الكمال: {len(tahdhib)} shuyukh")
        if tahdhib:
            networks_to_merge.append(tahdhib)

    if jarh_tadil_path:
        print("📚 Caricamento الجرح والتعديل...")
        jarh_tadil = load_jarh_tadil_relations(jarh_tadil_path)
        print(f"   الجرح والتعديل: {len(jarh_tadil)} shuyukh")
        if jarh_tadil:
            networks_to_merge.append(jarh_tadil)

    # 3. Unisci
    print("✅ Unione reti...")
    merged = merge_networks(*networks_to_merge)
    print(f"   Rete unita: {len(merged)} shuyukh")

    # 4. Statistiche
    total_links = sum(len(v) for v in merged.values())
    print(f"   Link totali: {total_links}")

    # 5. Salva
    print(f"💾 Salvataggio in: {output_path}")
    save_network(merged, output_path)
    print("✅ Completato!")


def main():
    import argparse

    ap = argparse.ArgumentParser(description="Espandi la rete شيوخ/تلاميذ con fonti aggiuntive")
    ap.add_argument("--existing", help="Path alla rete esistente (default: data/documented_network.json)")
    ap.add_argument("--tahdhib", help="Path al file تهذيب الكمال relations")
    ap.add_argument("--jarh-tadil", help="Path al file الجرح والتعديل relations")
    ap.add_argument("--output", help="Path di output (default: sovrascrive existing)")

    args = ap.parse_args()

    expand_network(
        existing_path=args.existing,
        tahdhib_path=args.tahdhib,
        jarh_tadil_path=args.jarh_tadil,
        output_path=args.output,
    )


if __name__ == '__main__':
    main()
