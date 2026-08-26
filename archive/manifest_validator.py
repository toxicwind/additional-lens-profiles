import argparse
import asyncio
import aiohttp
import json
import logging
import os
import sys
import time
from typing import List, Dict
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Define constants
INPUT_FILE = '/mnt/agents/output/workspace/iptv_stremio_aug2026.jsonl'
OUTPUT_FILE = 'manifest_validator_results.json'

# Define the ManifestValidator class
class ManifestValidator:
    def __init__(self, input_file: str, output_file: str, max_concurrent: int, timeout: float):
        self.input_file = input_file
        self.output_file = output_file
        self.max_concurrent = max_concurrent
        self.timeout = timeout
        self.results = []

    async def fetch_url(self, url: str) -> Dict:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=self.timeout) as response:
                    return {'status': response.status, 'latency': response.latency, 'content_type': response.headers.get('Content-Type'), 'size': response.content_length}
        except aiohttp.ClientError as e:
            logger.error(f'Error fetching {url}: {e}')
            return {'status': None, 'latency': None, 'content_type': None, 'size': None}

    async def validate_manifest(self, manifest: Dict) -> Dict:
        m3u_url = manifest.get('m3u_url')
        if m3u_url:
            try:
                async with asyncio.Semaphore(self.max_concurrent):
                    result = await self.fetch_url(m3u_url)
                    if result['status'] == 200:
                        return {'live': True, 'latency': result['latency'], 'content_type': result['content_type'], 'size': result['size']}
                    else:
                        return {'live': False, 'latency': None, 'content_type': None, 'size': None}
            except asyncio.CancelledError:
                logger.error(f'Validation cancelled for {m3u_url}')
                return {'live': None, 'latency': None, 'content_type': None, 'size': None}
        else:
            return {'live': None, 'latency': None, 'content_type': None, 'size': None}

    async def process_manifest(self, manifest: Dict) -> Dict:
        result = await self.validate_manifest(manifest)
        return {'guess': manifest['guess'], 'result': result}

    async def process_file(self, file_path: str) -> None:
        with open(file_path, 'r') as f:
            for line in f:
                manifest = json.loads(line)
                result = await self.process_manifest(manifest)
                self.results.append(result)

    async def run(self) -> None:
        start_time = time.time()
        await self.process_file(self.input_file)
        end_time = time.time()
        logger.info(f'Processing complete in {end_time - start_time} seconds')
        with open(self.output_file, 'w') as f:
            json.dump(self.results, f, indent=4)

def main() -> None:
    parser = argparse.ArgumentParser(description='Manifest Validator')
    parser.add_argument('--input', type=str, default=INPUT_FILE, help='Input JSONL file')
    parser.add_argument('--output', type=str, default=OUTPUT_FILE, help='Output JSON file')
    parser.add_argument('--max-concurrent', type=int, default=10, help='Maximum concurrent requests')
    parser.add_argument('--timeout', type=float, default=5.0, help='Timeout in seconds')
    args = parser.parse_args()

    validator = ManifestValidator(args.input, args.output, args.max_concurrent, args.timeout)
    asyncio.run(validator.run())

if __name__ == '__main__':
    main()