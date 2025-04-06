import time
import random
import json
from datetime import datetime
from pathlib import Path
from semanticscholar import SemanticScholar
from typing import List, Dict
from ..database.session import get_session
from ..database.models import Paper
from ..config.settings import CRAWLER_CONFIG
from .utils.logger import setup_logger

logger = setup_logger(__name__)

class ScholarCrawler:
    def __init__(self):
        logger.info("Initializing crawler and database connection...")
        try:
            self.session = get_session()
            self.sch = SemanticScholar()
            # Create data directory if it doesn't exist
            self.data_dir = Path(__file__).parent / 'data'
            self.data_dir.mkdir(exist_ok=True)
            logger.info("Crawler initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize crawler: {e}")
            raise

    def __del__(self):
        """Clean up the session when the crawler is destroyed"""
        if hasattr(self, 'session'):
            logger.info("Closing database session")
            try:
                self.session.close()
            except Exception as e:
                logger.error(f"Error closing session: {e}")

    def _random_delay(self):
        """Add a random delay between requests"""
        delay = CRAWLER_CONFIG['delay_between_requests'] + random.uniform(1, 3)
        logger.debug(f"Waiting {delay:.2f} seconds before next request")
        time.sleep(delay)

    def search_papers(self, query: str = None, max_results: int = None, max_retries: int = 3) -> List[Dict]:
        """Search for papers using Semantic Scholar API"""
        query = query or CRAWLER_CONFIG['search_query']
        max_results = max_results or CRAWLER_CONFIG['max_results']
        logger.info(f"Searching for papers with query: '{query}', max_results: {max_results}")
        
        for attempt in range(max_retries):
            try:
                # Search papers with the query
                papers = self.sch.search_paper(query, limit=max_results, fields=['title', 'authors', 'abstract', 'year', 'citationCount', 'url'])
                processed_papers = []
                processed_count = 0
                
                for paper in papers:
                    if processed_count >= max_results:
                        logger.info(f"Reached maximum number of papers to process ({max_results})")
                        break
                        
                    try:
                        # Extract author names from the paper object
                        authors = ', '.join([author.name for author in paper.authors]) if paper.authors else ''
                        
                        paper_data = {
                            'title': paper.title or '',
                            'authors': authors,
                            'abstract': paper.abstract or '',
                            'year': paper.year,
                            'citations': paper.citationCount or 0,
                            'url': paper.url or ''
                        }
                        
                        # Only add papers that have at least a title
                        if paper_data['title']:
                            processed_papers.append(paper_data)
                            processed_count += 1
                            logger.info(f"Found paper: {paper_data['title']} (Year: {paper_data['year']}, Citations: {paper_data['citations']})")
                        
                        # Add small delay between processing papers
                        self._random_delay()
                    except Exception as e:
                        logger.warning(f"Error processing paper: {e}")
                        continue
                
                logger.info(f"Successfully processed {len(processed_papers)} papers")
                return processed_papers
            except Exception as e:
                if attempt < max_retries - 1:
                    logger.warning(f"Attempt {attempt + 1} failed: {e}. Retrying...")
                    self._random_delay()
                else:
                    logger.error(f"All attempts failed: {e}")
                    return []

    def store_paper(self, paper_data: Dict) -> bool:
        """Store a single paper in the database"""
        try:
            logger.info(f"Attempting to store paper: {paper_data['title']}")
            
            # Check if paper already exists
            existing_paper = self.session.query(Paper).filter_by(title=paper_data['title']).first()
            if existing_paper:
                logger.info(f"Paper already exists: {paper_data['title']}")
                return True

            # Create new paper
            paper = Paper(
                title=paper_data['title'],
                authors=paper_data['authors'],
                abstract=paper_data['abstract'],
                year=paper_data['year'],
                citations=paper_data['citations'],
                url=paper_data['url']
            )
            
            self.session.add(paper)
            try:
                self.session.commit()
                logger.info(f"Successfully committed paper to database: {paper_data['title']}")
                return True
            except Exception as e:
                logger.error(f"Error committing paper {paper_data['title']}: {e}")
                self.session.rollback()
                return False
        except Exception as e:
            logger.error(f"Error storing paper {paper_data['title']}: {e}")
            self.session.rollback()
            return False

    def save_crawled_data(self, papers: List[Dict], stored_count: int):
        """Save crawled data to a JSON file"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = self.data_dir / f"crawled_papers_{timestamp}.json"
            
            data = {
                "timestamp": timestamp,
                "total_papers_found": len(papers),
                "total_papers_stored": stored_count,
                "papers": papers
            }
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Saved crawled data to {filename}")
            return filename
        except Exception as e:
            logger.error(f"Error saving crawled data: {e}")
            return None

    def crawl_math_papers(self, max_results: int = None):
        """Main function to crawl math papers"""
        try:
            logger.info("Starting paper crawl...")
            papers = self.search_papers(max_results=max_results)
            logger.info(f"Found {len(papers)} papers to store")
            
            stored_count = 0
            for paper in papers:
                if stored_count >= (max_results or CRAWLER_CONFIG['max_results']):
                    logger.info(f"Reached maximum number of papers to store ({max_results or CRAWLER_CONFIG['max_results']})")
                    break
                    
                try:
                    if self.store_paper(paper):
                        stored_count += 1
                        logger.info(f"Successfully stored paper: {paper['title']}")
                    else:
                        logger.warning(f"Failed to store paper: {paper['title']}")
                    # Add a small delay between storing papers
                    time.sleep(0.5)
                except Exception as e:
                    logger.error(f"Error processing paper {paper['title']}: {e}")
                    continue
            
            # Save crawled data to file
            self.save_crawled_data(papers, stored_count)
            
            logger.info(f"Paper crawl completed successfully. Stored {stored_count} papers.")
            return stored_count
        except Exception as e:
            logger.error(f"Error during paper crawl: {e}")
            raise
        finally:
            # Ensure session is closed
            logger.info("Closing database session")
            try:
                self.session.close()
            except Exception as e:
                logger.error(f"Error closing session: {e}")