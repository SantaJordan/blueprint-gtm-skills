#!/usr/bin/env python3
"""
Domain Resolver - High-Confidence Company Domain Resolution
Waterfall architecture: Places → Search+KG → Scrape+LLM
"""
import asyncio
import pandas as pd
import yaml
import logging
import json
import sys
from pathlib import Path
from typing import Dict, Any, Optional, List
from tqdm.asyncio import tqdm
from datetime import datetime

# Import modules
from modules.serper import SerperClient, resolve_company
from modules.scraper import scrape_url
from modules.llm_judge import verify_with_llm
from modules.parking_detector import is_parked_domain, get_parking_confidence
from modules.discolike import DiscolikeClient, resolve_via_discolike
from modules.ocean import OceanClient, resolve_via_ocean
from modules.utils import verify_dns

# Setup logging
def setup_logging(config: Dict):
    """Configure logging"""
    log_level = getattr(logging, config.get('logging', {}).get('level', 'INFO'))
    log_file = config.get('logging', {}).get('log_file', 'logs/domain_resolver.log')

    # Create logs directory
    Path(log_file).parent.mkdir(parents=True, exist_ok=True)

    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )

logger = logging.getLogger(__name__)


class DomainResolver:
    """Main domain resolution orchestrator"""

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize resolver with configuration

        Args:
            config: Configuration dictionary from config.yaml
        """
        self.config = config

        # Initialize Serper client
        serper_key = config['api_keys']['serper']
        if not serper_key or serper_key == "YOUR_SERPER_API_KEY":
            raise ValueError("Serper API key not configured in config.yaml")

        self.serper_client = SerperClient(
            api_key=serper_key,
            timeout=config['processing']['timeout_seconds']
        )

        # Optional API keys
        self.zenrows_key = config['api_keys'].get('zenrows')
        self.discolike_key = config['api_keys'].get('discolike')
        self.ocean_key = config['api_keys'].get('ocean')

        # Initialize Discolike client if API key provided
        self.discolike_client = None
        if self.discolike_key and self.discolike_key != "YOUR_DISCOLIKE_API_KEY":
            self.discolike_client = DiscolikeClient(
                api_key=self.discolike_key,
                timeout=config['processing']['timeout_seconds']
            )
            logger.info("✓ Discolike client initialized")

        # Initialize Ocean client if API key provided
        self.ocean_client = None
        if self.ocean_key and self.ocean_key != "YOUR_OCEAN_API_KEY":
            self.ocean_client = OceanClient(
                api_key=self.ocean_key,
                timeout=config['processing']['timeout_seconds']
            )
            logger.info("✓ Ocean client initialized")

        # Thresholds
        self.auto_accept_threshold = config['thresholds']['auto_accept']
        self.needs_scraping_threshold = config['thresholds']['needs_scraping']
        self.manual_review_threshold = config['thresholds']['manual_review']

        # Results storage
        self.results = []
        self.lookup_logs = []

    async def resolve_single_company(self, company_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Resolve domain for a single company using waterfall logic

        Args:
            company_data: Dict with name, city, phone, address, context

        Returns:
            Resolution result dict
        """
        company_name = company_data.get('name', 'Unknown')
        logger.info(f"\n{'='*60}")
        logger.info(f"Resolving: {company_name}")
        logger.info(f"{'='*60}")

        start_time = datetime.now()
        result = {
            'company_name': company_name,
            'input_city': company_data.get('city'),
            'input_phone': company_data.get('phone'),
            'domain': None,
            'confidence': 0,
            'source': None,
            'method': None,
            'verified': False,
            'needs_manual_review': False,
            'stage_reached': None,
            'error': None
        }

        try:
            # === STAGE 1 & 2: Serper (Places + Search) ===
            serper_result = await resolve_company(
                self.serper_client,
                company_data,
                self.config
            )

            if serper_result:
                domain = serper_result['domain']
                confidence = serper_result['confidence']
                source = serper_result['source']
                method = serper_result['method']

                result.update({
                    'domain': domain,
                    'confidence': confidence,
                    'source': source,
                    'method': method,
                    'stage_reached': 'serper'
                })

                logger.info(f"✓ Serper result: {domain} (confidence: {confidence}, source: {source})")

                # ALWAYS trigger LLM verification (Ollama is free, no reason to skip)
                if self.config['stages'].get('use_scraping', True):
                    logger.info(f"→ Triggering LLM verification for all results (confidence: {confidence})")
                    scrape_result = await self._verify_with_scraping(company_data, domain)

                    if scrape_result:
                        result.update(scrape_result)
                        result['stage_reached'] = 'llm_verified'

                        # DNS verification for high confidence results
                        if result['confidence'] >= self.manual_review_threshold:
                            verified = verify_dns(domain)
                            result['verified'] = verified
                            logger.info(f"✓ LLM Verified: {domain} (confidence: {result['confidence']}, DNS: {verified})")
                            return result

            # === STAGE 3: Optional B2B Enrichment (Discolike or Ocean) ===
            # Try Discolike if enabled
            if self.config['stages'].get('use_discolike', False) and self.discolike_client:
                if not result['domain'] or result['confidence'] < self.manual_review_threshold:
                    logger.info("→ Trying Discolike verification")
                    discolike_result = await resolve_via_discolike(
                        self.discolike_client,
                        company_data,
                        self.config
                    )

                    if discolike_result and discolike_result.get('domain'):
                        # Use Discolike result if better than current
                        if not result['domain'] or discolike_result['confidence'] > result['confidence']:
                            result.update(discolike_result)
                            result['stage_reached'] = 'discolike'
                            logger.info(f"✓ Discolike result: {result['domain']} (confidence: {result['confidence']})")

            # Try Ocean if enabled and still need better result
            if self.config['stages'].get('use_ocean', False) and self.ocean_client:
                if not result['domain'] or result['confidence'] < self.manual_review_threshold:
                    logger.info("→ Trying Ocean.io verification")
                    ocean_result = await resolve_via_ocean(
                        self.ocean_client,
                        company_data,
                        self.config
                    )

                    if ocean_result and ocean_result.get('domain'):
                        # Use Ocean result if better than current
                        if not result['domain'] or ocean_result['confidence'] > result['confidence']:
                            result.update(ocean_result)
                            result['stage_reached'] = 'ocean'
                            logger.info(f"✓ Ocean result: {result['domain']} (confidence: {result['confidence']})")

            # Final decision
            if result['domain']:
                if result['confidence'] < self.manual_review_threshold:
                    result['needs_manual_review'] = True
                    logger.warning(f"⚠ MANUAL REVIEW NEEDED: {result['domain']} (confidence: {result['confidence']})")
                else:
                    logger.info(f"✓ RESOLVED: {result['domain']} (confidence: {result['confidence']})")
            else:
                result['needs_manual_review'] = True
                result['error'] = 'No domain found'
                logger.warning(f"✗ NOT FOUND: {company_name}")

        except Exception as e:
            logger.error(f"Error resolving {company_name}: {e}", exc_info=True)
            result['error'] = str(e)
            result['needs_manual_review'] = True

        finally:
            # Log lookup details
            duration = (datetime.now() - start_time).total_seconds()
            self._log_lookup(company_data, result, duration)

        return result

    async def _verify_with_scraping(self, company_data: Dict[str, Any],
                                   domain: str) -> Optional[Dict[str, Any]]:
        """
        Stage 4: Deep scraping + LLM verification

        Args:
            company_data: Company information
            domain: Domain to verify

        Returns:
            Updated result dict or None if failed
        """
        url = f"https://{domain}"

        try:
            # Scrape website
            logger.info(f"Scraping {url}...")
            scrape_result = await scrape_url(
                url,
                zenrows_api_key=self.zenrows_key,
                timeout=15
            )

            if not scrape_result:
                logger.warning(f"Failed to scrape {url}")
                return None

            webpage_text = scrape_result['text']
            scrape_method = scrape_result['method']

            logger.info(f"Scraped {scrape_result['char_count']} characters via {scrape_method}")

            # Check for parked domain
            is_parked, parking_reason = is_parked_domain(webpage_text, url)

            if is_parked:
                logger.warning(f"⚠ Parked domain detected: {parking_reason}")
                return {
                    'domain': None,
                    'confidence': 0,
                    'source': 'scraping',
                    'method': 'parked_domain_rejected',
                    'error': f'Parked domain: {parking_reason}'
                }

            # LLM verification
            logger.info(f"Verifying with LLM...")
            llm_result = await verify_with_llm(
                company_data,
                url,
                webpage_text,
                self.config
            )

            logger.info(f"LLM judgment: match={llm_result['match']}, confidence={llm_result['confidence']}")
            logger.info(f"Evidence: {llm_result['evidence']}")

            if llm_result['match'] and llm_result['confidence'] >= 70:
                # LLM confirmed match
                return {
                    'domain': domain,
                    'confidence': llm_result['confidence'],
                    'source': 'llm_verified',
                    'method': 'deep_scrape_verified',
                    'verified': True,
                    'llm_evidence': llm_result['evidence'],
                    'scrape_method': scrape_method
                }
            else:
                # LLM rejected or low confidence
                return {
                    'domain': None if not llm_result['match'] else domain,
                    'confidence': llm_result['confidence'],
                    'source': 'llm_verified',
                    'method': 'llm_rejected' if not llm_result['match'] else 'llm_low_confidence',
                    'llm_evidence': llm_result['evidence']
                }

        except Exception as e:
            logger.error(f"Scraping/LLM error for {domain}: {e}")
            return None

    def _log_lookup(self, company_data: Dict, result: Dict, duration: float):
        """Log detailed lookup information"""
        if self.config.get('logging', {}).get('save_lookups', True):
            log_entry = {
                'timestamp': datetime.now().isoformat(),
                'company': company_data.get('name'),
                'input_data': company_data,
                'result': result,
                'duration_seconds': duration
            }
            self.lookup_logs.append(log_entry)

    async def resolve_batch(self, companies: List[Dict[str, Any]],
                           max_workers: int = 10) -> pd.DataFrame:
        """
        Resolve domains for a batch of companies with progress bar

        Args:
            companies: List of company data dicts
            max_workers: Maximum concurrent workers

        Returns:
            DataFrame with results
        """
        logger.info(f"\n{'='*60}")
        logger.info(f"Starting batch resolution: {len(companies)} companies")
        logger.info(f"Max workers: {max_workers}")
        logger.info(f"{'='*60}\n")

        # Create semaphore for concurrency control
        semaphore = asyncio.Semaphore(max_workers)

        async def resolve_with_semaphore(company):
            async with semaphore:
                return await self.resolve_single_company(company)

        # Run with progress bar
        tasks = [resolve_with_semaphore(company) for company in companies]
        results = []

        for coro in tqdm.as_completed(tasks, total=len(tasks), desc="Resolving domains"):
            result = await coro
            results.append(result)
            self.results.append(result)

        # Convert to DataFrame
        df = pd.DataFrame(results)

        # Summary stats
        self._print_summary(df)

        return df

    def _print_summary(self, df: pd.DataFrame):
        """Print summary statistics"""
        total = len(df)
        found = df['domain'].notna().sum()
        high_conf = (df['confidence'] >= self.auto_accept_threshold).sum()
        manual_review = df['needs_manual_review'].sum()

        logger.info(f"\n{'='*60}")
        logger.info("RESOLUTION SUMMARY")
        logger.info(f"{'='*60}")
        logger.info(f"Total companies: {total}")
        logger.info(f"Domains found: {found} ({found/total*100:.1f}%)")
        logger.info(f"High confidence (≥{self.auto_accept_threshold}): {high_conf} ({high_conf/total*100:.1f}%)")
        logger.info(f"Manual review needed: {manual_review} ({manual_review/total*100:.1f}%)")
        logger.info(f"{'='*60}\n")

    def save_results(self, df: pd.DataFrame, output_path: str = "output/resolved.csv"):
        """Save results to CSV"""
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(output_path, index=False)
        logger.info(f"✓ Results saved to: {output_path}")

        # Save manual review queue
        manual_review = df[df['needs_manual_review'] == True]
        if len(manual_review) > 0:
            # Use Path operations instead of fragile string replace
            output_path_obj = Path(output_path)
            review_path = output_path_obj.parent / f"{output_path_obj.stem}_manual_review{output_path_obj.suffix}"
            manual_review.to_csv(review_path, index=False)
            logger.info(f"✓ Manual review queue saved to: {review_path}")

        # Save lookup logs
        if self.lookup_logs:
            log_path = "logs/lookups.jsonl"
            Path(log_path).parent.mkdir(parents=True, exist_ok=True)
            with open(log_path, 'w') as f:
                for log in self.lookup_logs:
                    f.write(json.dumps(log) + '\n')
            logger.info(f"✓ Lookup logs saved to: {log_path}")


async def main():
    """Main entry point"""
    # Load config
    config_path = "config.yaml"
    if not Path(config_path).exists():
        print(f"Error: {config_path} not found. Please create config.yaml from template.")
        sys.exit(1)

    with open(config_path) as f:
        config = yaml.safe_load(f)

    setup_logging(config)

    # Check for input file
    if len(sys.argv) < 2:
        print("Usage: python domain_resolver.py <input_csv>")
        print("Example: python domain_resolver.py companies.csv")
        sys.exit(1)

    input_file = sys.argv[1]
    if not Path(input_file).exists():
        print(f"Error: Input file not found: {input_file}")
        sys.exit(1)

    # Load companies
    logger.info(f"Loading companies from: {input_file}")
    df_input = pd.read_csv(input_file)

    # Convert to list of dicts
    companies = df_input.to_dict('records')
    logger.info(f"Loaded {len(companies)} companies")

    # Create resolver
    resolver = DomainResolver(config)

    # Process batch
    max_workers = config['processing']['max_workers']
    df_results = await resolver.resolve_batch(companies, max_workers=max_workers)

    # Save results
    output_path = sys.argv[2] if len(sys.argv) > 2 else "output/resolved.csv"
    resolver.save_results(df_results, output_path)

    logger.info("\n✓✓ Domain resolution complete!")


if __name__ == "__main__":
    asyncio.run(main())
