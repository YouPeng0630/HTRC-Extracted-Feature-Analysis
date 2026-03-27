"""Fetch and organize poems using HTRC Data API"""

import os
import json
import pandas as pd
import requests
from pathlib import Path
import time

def clean_htid(htid):
    """Convert HTID to clean format for API"""
    parts = htid.split('.', 1)
    if len(parts) != 2:
        return htid
    lib = parts[0]
    lib_id = parts[1].replace(':', '+').replace('/', '=')
    return f"{lib},{lib_id}"

def clean_filename(text):
    """Clean text for filename"""
    import re
    text = str(text).strip('"').strip()
    text = re.sub(r'[<>:"/\\|?*]', '', text)
    text = re.sub(r'\s+', '_', text)
    return text[:100]

def fetch_ef_data(htid):
    """Fetch EF data from API"""
    clean_htid_str = clean_htid(htid)
    url = f'https://data.htrc.illinois.edu/ef-api/volumes/{clean_htid_str}'
    
    try:
        response = requests.get(url, timeout=30)
        if response.status_code == 200:
            return response.json()['data']
        else:
            return None
    except Exception as e:
        print(f"    Error fetching: {e}")
        return None

def extract_poem_pages(ef_data, start_page, end_page):
    """Extract pages for a poem"""
    try:
        pages = ef_data.get('features', {}).get('pages', [])
        
        # Preserve original top-level info (12 lines from EF file)
        poem_data = {
            '@context': ef_data.get('@context'),
            'schemaVersion': ef_data.get('schemaVersion'),
            'id': ef_data.get('id'),
            'type': ef_data.get('type'),
            'datePublished': ef_data.get('datePublished'),
            'publisher': ef_data.get('publisher'),
            'htid': ef_data.get('htid'),
            'metadata': ef_data.get('metadata', {}),
            'features': {
                'pageCount': ef_data.get('features', {}).get('pageCount'),
                'pages': []  # Only pages from start to end
            },
            'poem_stats': {
                'start_page': start_page,
                'end_page': end_page,
                'total_pages': end_page - start_page + 1,
                'total_tokens': 0,
                'total_lines': 0,
                'total_sentences': 0
            }
        }
        
        # Filter pages: only keep start to end
        for page in pages:
            seq = page.get('seq')
            if seq:
                try:
                    seq = int(seq)
                    if start_page <= seq <= end_page:
                        poem_data['features']['pages'].append(page)
                        poem_data['poem_stats']['total_tokens'] += page.get('tokenCount', 0)
                        poem_data['poem_stats']['total_lines'] += page.get('lineCount', 0)
                        poem_data['poem_stats']['total_sentences'] += page.get('sentenceCount', 0)
                except (ValueError, TypeError):
                    continue
        
        return poem_data
        
    except Exception as e:
        print(f"    Error extracting: {e}")
        return None

def process_volume_csv(csv_path, region, output_dir, extracted_dir):
    """Process a single volume CSV using API"""
    csv_name = os.path.basename(csv_path)
    htid = csv_name.replace('.csv', '').replace(' ', '')
    
    print(f"\n  Volume: {htid}")
    
    # Fetch EF data from API
    print(f"    Fetching from API...")
    ef_data = fetch_ef_data(htid)
    
    if not ef_data:
        print(f"    ✗ Failed to fetch EF data")
        return 0
    
    # Save full EF data to extracted/ folder
    os.makedirs(extracted_dir, exist_ok=True)
    extracted_file = os.path.join(extracted_dir, f'{htid}.json')
    with open(extracted_file, 'w', encoding='utf-8') as f:
        json.dump(ef_data, f, indent=2, ensure_ascii=False)
    
    print(f"    ✓ Fetched successfully (saved to extracted/)")
    
    # Read CSV
    try:
        df = pd.read_csv(csv_path)
    except Exception as e:
        print(f"    ✗ Error reading CSV: {e}")
        return 0
    
    # Create output directory
    volume_dir = os.path.join(output_dir, 'poets', region, htid)
    os.makedirs(volume_dir, exist_ok=True)
    
    poem_count = 0
    
    # Process each poem
    for idx, row in df.iterrows():
        title = row.get('Title', f'poem_{idx}')
        start = row.get('Htrc_page_start')  # Changed from 'File Name (start)'
        end = row.get('Htrc_page_end')      # Changed from 'File Name (end)'
        
        if pd.isna(start) or pd.isna(end):
            continue
        
        start = int(start)
        end = int(end)
        
        # Extract poem data
        poem_data = extract_poem_pages(ef_data, start, end)
        
        if poem_data:
            # Save poem file
            clean_title = clean_filename(title)
            poem_file = os.path.join(volume_dir, f"{clean_title}.json")
            
            poem_data['poem_title'] = title
            poem_data['volume_id'] = htid
            poem_data['region'] = region
            
            with open(poem_file, 'w', encoding='utf-8') as f:
                json.dump(poem_data, f, indent=2, ensure_ascii=False)
            
            poem_count += 1
            print(f"    ✓ {title[:50]}... (p{start}-{end})")
    
    print(f"    Total: {poem_count} poems")
    return poem_count

def main():
    print("=" * 60)
    print("HTRC EF API - Fetch and Organize Poems")
    print("=" * 60)
    
    # Use absolute paths (recommended)
    poets_dir = r'd:\htrc_ef_api\boundary'
    output_dir = r'd:\htrc_ef_api\output'
    extracted_dir = r'd:\htrc_ef_api\extracted'
    
    # Check directories
    if not os.path.exists(poets_dir):
        print(f"\n✗ boundary/ directory not found at {poets_dir}")
        return
    
    # Get all regions
    regions = [d for d in os.listdir(poets_dir) 
               if os.path.isdir(os.path.join(poets_dir, d))]
    
    print(f"\nFound {len(regions)} regions")
    print(f"Output: {output_dir}/poets/")
    print(f"Extracted: {extracted_dir}/\n")
    
    total_volumes = 0
    total_poems = 0
    failed_volumes = []
    
    start_time = time.time()
    
    # Process each region
    for region in sorted(regions):
        print(f"\nRegion: {region}")
        print("-" * 60)
        
        region_dir = os.path.join(poets_dir, region)
        csv_files = list(Path(region_dir).glob('*.csv'))
        
        region_poems = 0
        
        for idx, csv_file in enumerate(csv_files, 1):
            print(f"\n[{idx}/{len(csv_files)}]")
            try:
                poem_count = process_volume_csv(csv_file, region, output_dir, extracted_dir)
                if poem_count > 0:
                    region_poems += poem_count
                    total_volumes += 1
                else:
                    failed_volumes.append(str(csv_file))
                
                # Rate limiting
                time.sleep(0.5)
                
            except Exception as e:
                print(f"    ✗ Error: {e}")
                failed_volumes.append(str(csv_file))
        
        total_poems += region_poems
        print(f"\n  Region total: {region_poems} poems")
    
    elapsed = time.time() - start_time
    
    # Summary
    print("\n" + "=" * 60)
    print("Complete")
    print("=" * 60)
    print(f"\nTotal volumes: {total_volumes}")
    print(f"Total poems: {total_poems}")
    print(f"Time: {elapsed/60:.1f} min")
    
    if failed_volumes:
        print(f"\nFailed volumes: {len(failed_volumes)}")
        for vol in failed_volumes[:10]:
            print(f"  {vol}")

if __name__ == "__main__":
    main()
