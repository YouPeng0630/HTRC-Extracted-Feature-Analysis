import csv
import json
import bz2
import os
from pathlib import Path
from datetime import datetime

def normalize_htid(htid):
    # some csv file start with ark has format issue, need to normalize it
    if 'ark_' in htid and '.' in htid:
        prefix, rest = htid.split('.', 1)
        rest = rest.replace('ark_ ', 'ark_').replace(' ', '_')
        parts = rest.split('_')
        if len(parts) >= 3:
            return f"{prefix}.ark:/{parts[1]}/{parts[2]}"
    return htid

def htid_to_filename(htid):
    """Convert htid to EF filename"""
    return htid.replace(':', '+').replace('/', '=').replace(' ', '') + '.json.bz2'

def extract_poem(ef_file, start_page, end_page, title, htid, region):
    """Extract features for one poem"""
    poem = {
        'metadata': {
            'htid': htid,
            'region': region,
            'poem_title': title,
            'start_page': start_page,
            'end_page': end_page,
            'page_count': end_page - start_page + 1
        },
        'features': {
            'total_tokens': 0,
            'total_lines': 0,
            'total_sentences': 0,
            'word_frequencies': {},
            'pages': []
        }
    }
    
    # Load EF file
    with bz2.open(ef_file, 'rt', encoding='utf-8') as f:
        data = json.load(f)
    
    # Get volume metadata
    if 'metadata' in data:
        poem['volume_metadata'] = {
            'title': data['metadata'].get('title', ''),
            'pubDate': data['metadata'].get('pubDate', ''),
            'language': data['metadata'].get('language', '')
        }
    
    # Extract features from pages in range
    pages = data.get('features', {}).get('pages', [])
    for page in pages:
        seq = int(page.get('seq', '0'))
        if start_page <= seq <= end_page:
            poem['features']['total_tokens'] += page.get('tokenCount') or 0
            poem['features']['total_lines'] += page.get('lineCount') or 0
            poem['features']['total_sentences'] += page.get('sentenceCount') or 0
            
            # Extract tokens with POS tags
            page_tokens = []
            body = page.get('body', {})
            if body and 'tokenPosCount' in body:
                for word, pos_dict in body['tokenPosCount'].items():
                    for pos, count in pos_dict.items():
                        page_tokens.append({'word': word, 'pos': pos, 'count': count})
                        poem['features']['word_frequencies'][word] = \
                            poem['features']['word_frequencies'].get(word, 0) + count
            
            poem['features']['pages'].append({
                'seq': seq,
                'tokenCount': page.get('tokenCount') or 0,
                'lineCount': page.get('lineCount') or 0,
                'tokens': page_tokens
            })
    
    # Add top words and unique count
    sorted_words = sorted(poem['features']['word_frequencies'].items(), 
                         key=lambda x: x[1], reverse=True)
    poem['features']['top_words'] = [
        {'word': w, 'count': c} for w, c in sorted_words[:20]
    ]
    poem['features']['unique_words'] = len(poem['features']['word_frequencies'])
    
    return poem

# Main extraction
os.makedirs('poems_json', exist_ok=True)
log = open('extraction_log.txt', 'w', encoding='utf-8')

print("=" * 70)
print(f"Start: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 70)

total_volumes = 0
total_poems = 0

# Process each volume
with open('list.csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        total_volumes += 1
        htid_raw = row['htid']
        region = row['region']
        
        htid = normalize_htid(htid_raw)
        ef_file = Path(f'ef25_data/{htid_to_filename(htid)}')
        
        # Try multiple boundary file naming conventions
        # 1. New format: dul1.ark_13960_xxx.csv (single underscores)
        #    Convert "dul1.ark_ 13960 s2st3fdcwc7" -> "dul1.ark_13960_s2st3fdcwc7"
        htid_underscore = htid_raw.replace('ark_ ', 'ark_').replace(' ', '_')
        boundary_file = Path(f'boundary/{region}/{htid_underscore}.csv')
        if not boundary_file.exists():
            # 2. Old format: dul1.ark_ 13960 xxx.csv (spaces)
            boundary_file = Path(f'boundary/{region}/{htid_raw}.csv')
        
        if not ef_file.exists() or not boundary_file.exists():
            log.write(f"[{total_volumes}] {htid_raw} - ERROR: file missing\n\n")
            continue
        
        print(f"[{total_volumes}/120] {htid_raw}", end=" ")
        log.write(f"[{total_volumes}] {htid_raw}\n")
        
        # Extract each poem
        poem_count = 0
        with open(boundary_file, 'r', encoding='utf-8') as bf:
            for idx, poem_row in enumerate(csv.DictReader(bf), 1):
                # Skip empty rows
                if not poem_row or not poem_row.get('Title'):
                    continue
                
                title = poem_row['Title'].strip()
                
                # Skip if title is empty
                if not title:
                    continue
                
                # Handle missing or invalid page numbers
                try:
                    # Try new column names first, fallback to old
                    start_str = poem_row.get('File Name (start)', poem_row.get('Htrc_page_start', '')).strip()
                    end_str = poem_row.get('File Name (end)', poem_row.get('Htrc_page_end', '')).strip()
                    
                    if not start_str or not end_str:
                        log.write(f"  SKIP: {title} - missing page numbers\n")
                        continue
                    
                    start = int(float(start_str))
                    end = int(float(end_str))
                except (ValueError, TypeError, AttributeError) as e:
                    log.write(f"  SKIP: {title} - invalid page numbers\n")
                    continue
                
                try:
                    poem_json = extract_poem(ef_file, start, end, title, htid, region)
                    
                    # Create directory structure: poems_json/region/htid/
                    htid_safe = htid.replace(':', '+').replace('/', '=')
                    poem_dir = Path(f"poems_json/{region}/{htid_safe}")
                    poem_dir.mkdir(parents=True, exist_ok=True)
                    
                    # Create safe filename
                    safe_title = "".join(c if c.isalnum() or c in ' -' else '_' 
                                        for c in title).strip().replace(' ', '_')[:50]
                    filename = poem_dir / f"{idx:03d}_{safe_title}.json"
                    
                    with open(filename, 'w', encoding='utf-8') as out:
                        json.dump(poem_json, out, ensure_ascii=False, indent=2)
                    
                    log.write(f"  OK: {title}\n")
                    poem_count += 1
                    total_poems += 1
                    
                except Exception as e:
                    log.write(f"  ERROR: {title} - {e}\n")
        
        print(f"({poem_count})")
        log.write(f"  Total: {poem_count} poems\n\n")

log.close()

# Summary
print(f"\n{'='*70}")
print(f"Complete: {total_poems} poems from {total_volumes} volumes")
print(f"{'='*70}")
