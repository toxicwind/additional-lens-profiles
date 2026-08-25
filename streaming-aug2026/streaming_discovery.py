import argparse
import asyncio
import json
import logging
import re
from datetime import datetime
from typing import Dict, List, Optional

import aiohttp
from aiohttp import ClientSession

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Constants
GITHUB_API_URL = 'https://api.github.com/search/repositories'
GITLAB_API_URL = 'https://gitlab.com/api/v4/search'
CODEBERG_API_URL = 'https://codeberg.org/api/v1/search'
TIMEOUT = 10  # seconds

# Regex patterns
M3U_PATTERN = r'https?://[^/]+/[^/]+\.m3u[^/]*'
MANIFEST_PATTERN = r'https?://[^/]+/manifest\.json'

# Threat categories
THREAT_CATEGORIES = ['malware', 'credentials', 'abandoned']

async def search_github(session: ClientSession, query: str) -> List[Dict]:
    """Search GitHub for repositories matching the query."""
    async with session.get(GITHUB_API_URL, params={'q': query}) as response:
        if response.status != 200:
            logger.error(f'Failed to search GitHub: {response.status}')
            return []
        return await response.json()

async def search_gitlab(session: ClientSession, query: str) -> List[Dict]:
    """Search GitLab for repositories matching the query."""
    async with session.get(GITLAB_API_URL, params={'scope': 'projects', 'search': query}) as response:
        if response.status != 200:
            logger.error(f'Failed to search GitLab: {response.status}')
            return []
        return await response.json()

async def search_codeberg(session: ClientSession, query: str) -> List[Dict]:
    """Search Codeberg for repositories matching the query."""
    async with session.get(CODEBERG_API_URL, params={'q': query}) as response:
        if response.status != 200:
            logger.error(f'Failed to search Codeberg: {response.status}')
            return []
        return await response.json()

async def extract_urls(readme: str) -> Dict:
    """Extract M3U and manifest.json URLs from a README."""
    m3u_urls = re.findall(M3U_PATTERN, readme)
    manifest_urls = re.findall(MANIFEST_PATTERN, readme)
    return {'m3u': m3u_urls, 'manifest': manifest_urls}

async def validate_endpoint(session: ClientSession, url: str) -> bool:
    """Validate an endpoint with aiohttp and timeouts."""
    try:
        async with session.head(url, timeout=TIMEOUT) as response:
            return response.status == 200
    except asyncio.TimeoutError:
        logger.error(f'Timeout validating endpoint: {url}')
        return False

async def categorize_threats(session: ClientSession, urls: Dict) -> Dict:
    """Categorize threats (malware/credentials/abandoned) for a repository."""
    threats = {}
    for url_type, url_list in urls.items():
        for url in url_list:
            if await validate_endpoint(session, url):
                threats[url_type] = 'active'
            else:
                threats[url_type] = 'abandoned'
    return threats

async def generate_report(session: ClientSession, repos: List[Dict]) -> Dict:
    """Generate a JSON report with timestamps for a list of repositories."""
    report = {'timestamp': datetime.now().isoformat(), 'repositories': []}
    for repo in repos:
        readme = await fetch_readme(session, repo['html_url'])
        urls = await extract_urls(readme)
        threats = await categorize_threats(session, urls)
        report['repositories'].append({
            'name': repo['name'],
            'url': repo['html_url'],
            'urls': urls,
            'threats': threats
        })
    return report

async def fetch_readme(session: ClientSession, repo_url: str) -> str:
    """Fetch the README for a repository."""
    async with session.get(repo_url + '/README.md') as response:
        if response.status != 200:
            logger.error(f'Failed to fetch README: {response.status}')
            return ''
        return await response.text()

async def main(query: str) -> None:
    """Async main function."""
    async with ClientSession() as session:
        github_repos = await search_github(session, query)
        gitlab_repos = await search_gitlab(session, query)
        codeberg_repos = await search_codeberg(session, query)
        repos = github_repos + gitlab_repos + codeberg_repos
        report = await generate_report(session, repos)
        with open('report.json', 'w') as f:
            json.dump(report, f, indent=4)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Streaming discovery tool')
    parser.add_argument('--query', help='Search query', default='IPTV OR Stremio OR Nuvio')
    args = parser.parse_args()
    asyncio.run(main(args.query))

# Unit tests
import unittest
from unittest.mock import Mock, patch

class TestStreamingDiscovery(unittest.TestCase):
    def test_search_github(self):
        session = Mock()
        session.get.return_value.__aenter__.return_value.json.return_value = [{'name': 'repo1'}, {'name': 'repo2'}]
        repos = asyncio.run(search_github(session, 'test_query'))
        self.assertEqual(len(repos), 2)

    def test_extract_urls(self):
        readme = 'https://example.com/manifest.json https://example.com/playlist.m3u'
        urls = asyncio.run(extract_urls(readme))
        self.assertEqual(urls, {'m3u': ['https://example.com/playlist.m3u'], 'manifest': ['https://example.com/manifest.json']})

    def test_validate_endpoint(self):
        session = Mock()
        session.head.return_value.__aenter__.return_value.status = 200
        self.assertTrue(asyncio.run(validate_endpoint(session, 'https://example.com')))

if __name__ == '__main__':
    unittest.main()